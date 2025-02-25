import os
import json
# for typing func parameters and outputs and states
from typing import Dict, List, Tuple, Any, Optional, Union
# models
from llms.llms import (
  groq_llm_mixtral_7b,
  groq_llm_mixtral_larger,
  groq_llm_llama3_70b_versatile,
)
# Tools
from tools.tools import (
  order_message_items_parser_tool_node,
  llm_with_order_message_items_parser_tool_choice,
)
# structured output
from structured_output.structured_output import (
  message_interpreter_order_or_other_schema,
  message_classification_schema,
)
# prompts
from prompts.prompts import (
  message_interpreter_order_or_other_prompt,
  order_message_items_parser_prompt,
  message_classification_prompt,
)
# helpers
from helpers import (
  call_llm,
  prompt_creation,
  beautiful_graph_output,
  safe_json_dumps,
  similarity_search_checker,
  send_discord_notification_to_target_room,
)
# langchain and langgraph lib
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
# from langgraph.checkpoint import MemorySaver
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph, MessagesState
# env vars
from dotenv import load_dotenv, set_key


# load env vars
load_dotenv(dotenv_path=".env", override=False)
load_dotenv(dotenv_path=".vars.env", override=True)

'''
1. fetch_new_messages # this one here need to be developped more in how we will decide to fetch those messages from db and how the main app will simulate message added to db
    > intergraph_agent > message_interpreter_order_or_other_agent   OK DONE!
2.  				> score_test_message_relevance_agent
3.  				  >>> rephrase_query_agent
3.1 				       > store_to_enquiries_bucket_agent
3.2 				         > notify_discord_order_enquiries_category_agent
3.  				  >>> store_miscellanous_messages_to_bucket_agent
3.1 				       > notify_dicord_miscellanous_messages_category_agent
3.  				  > structure_output_order_parser_agent
3.1 				     >>> rephrase_query_agent
3.1.1				        > store_to_enquiries_bucket_agent
3.1.2				          > notify_discord_order_enquiries_category_agent
3.2				      >>> store_miscellanous_messages_to_bucket_agent
3.2.1				        > notify_dicord_miscellanous_messages_category_agent
3.3				      >>> store_to_order_bucket_agent
3.3.1 				       > notify_dicord_order_category_agent
'''

# FIRST NODE
def intergraph_agent(state: MessagesState):
  messages = state["messages"]
  last_message = messages[-1].content
  return {"messages": [{"role": "ai", "content": last_message}]}

# CONDITIONAL EDGE
def message_interpreter_order_or_other_agent(state: MessagesState):
  messages = state["messages"]
  last_message = messages[-1].content

  query = prompt_creation.prompt_creation(message_interpreter_order_or_other_prompt["human"], message=last_message)
  print("query: ",query)

  try:
    print("calling llm")
    decision = call_llm.call_llm(query, message_interpreter_order_or_other_prompt["system"]["template"], message_interpreter_order_or_other_schema)
    print("decision: ", decision, type(decision))
    if decision["order"].lower() == "true":
      # update state message
      state["messages"] + [{"role": "ai", "content": json.dumps({"order": last_message})}]
      return "tool_order_message_items_parser_agent"
    # update state message
    state["messages"] + [{"role": "ai", "content": json.dumps({"other": last_message})}]
    return "evalutor_enquiry_or_miscellaneous_message_agent"
  except Exception as e:
    # update state message
    state["messages"] + [{"role": "ai", "content": json.dumps({"error": f"An error occured while trying to interpret if message is a genuine order or another type of message: {e}"})}]
    return "error_handler"

# NODE
def tool_order_message_items_parser_agent(state: MessagesState):
  messages = state['messages']
  last_message = messages[-1].content
  print("Last message received in tool_order_message_items_parser_agent: ", last_message)
  # Generate a query, we keep json.dumps() format of last_message as function need a `str` which will do!
  query = prompt_creation.prompt_creation(order_message_items_parser_prompt["tool_call_choice"], message=last_message)
  print("QUERY: ", query, type(query))

  try:
    response = llm_with_order_message_items_parser_tool_choice.invoke(query)
    print("LLM with tool choice response: ", response, type(response))
    print("reponse tool call: ", response.tool_calls, type(response.tool_calls))
    return {"messages": [response]}
  except Exception as e:
    return {"messages": [{"role": "tool", "content": json.dumps({"error": f"An error occurred: {e}"})}]}

# CONDITIONAL EDGE    
def order_message_items_parser_success_or_error(state: MessagesState):
  messages = state['messages']
  last_message = messages[-1].content
  print("tool call item parser outcome: ", last_message, type(last_message))
    
  # if success we get a dict with Dict[key:list items, key:list quantity, key:list id number]
  if "success" in last_message:
    return "score_test_message_relevance_agent"
  return "error_handler"

# NODE
def score_test_message_relevance_agent(state: MessagesState):
  messages = state["messages"]

  # so here it is a bit tricky to the full `role: Tool` answer is json.dumped itself and the message is also json.dumps so we need to unwrap that
  # eg.: # {'messages': [{'role': 'tool', 'content': '{"success": {"item_names": ["Kale & Quinoa Super Salad"], "item_quantities": [1], "item_ids": [1]}}'}]} type <Dict>
  last_message = json.loads(messages[-1].content)
  print("1: ", last_message, type(last_message)) 
  unwrapped_last_message = json.loads(last_message["messages"][-1]["content"])
  # after the unwrapping we can now access to the tool `success` key which has the dictionary structured output from the LLM response
  tool_parsed_output = unwrapped_last_message["success"]
  # now we are going to create a list of tuple from it getting each item ordered with its quantity [(item_name, quantity), ....]

  orders_parsed: List[Tuple] = []
  for i in range(len(tool_parsed_output["item_ids"])):
    orders_parsed.append((tool_parsed_output["item_names"][i], tool_parsed_output["item_quantities"][i]))

  # we set two lists which are going to divide between the items passing the test ("Are those in the menu or not?") to send those to different concerns
  genuine_order = []
  not_genuine_order_or_missing_something = []
  for elem in orders_parsed:
    # get the order item name for similarity check against the menu using our other LLM specialized in that task
    message_order_item = elem[0]
    # fetch keys of resataurant items stored in env vars from when it has been recorded to cache
    cache_keys_reaturant_items_not_formatted_yet: List = json.loads(os.getenv("CACHE_KEYS"))
    # get the keys formatted as correct text chunks so that LLM can understand (space between words)
    restaurant_item_names = [ elem.replace("_", " ") for elem in cache_keys_reaturant_items_not_formatted_yet]   
    similarity_test_result = similarity_search_checker.similarity_check_on_the_fly(restaurant_item_names, message_order_item, float(os.getenv("SIMILARITY_THRESHOLD")))

    print("Similarity_test_result score type : ", similarity_test_result["score"], type(similarity_test_result["score"]), " - Threshold: ", os.getenv("SIMILARITY_THRESHOLD"))
    # the returned value could be boolean like a yes or no but have opted for more insightful return so that code can be articulated different ways
    # here we are going to just check that the score is above the threshold
    if float(similarity_test_result["score"]) > float(os.getenv("SIMILARITY_THRESHOLD")):
      genuine_order.append(elem)
    else:
      not_genuine_order_or_missing_something.append(elem)

  return {"messages": [{"role": "ai", "content": json.dumps({"genuine_order": genuine_order, "not_genuine_order_or_missing_something": not_genuine_order_or_missing_something})}]}

# CONDITIONAL EDGE
def relevance_test_passed_or_not(state: MessagesState):
  messages = state['messages']
  last_message = json.loads(messages[-1].content)
  genuine_order = last_message["genuine_order"]
  not_genuine_order_or_missing_something = last_message["not_genuine_order_or_missing_something"]
  
  if len(genuine_order) > 0:
    return "send_order_to_discord_and_save_to_bucket"
  elif len(not_genuine_order_or_missing_something) > 0:
    return "evalutor_enquiry_or_miscellaneous_message_agent"
  return "error_handler"

# NODE
def send_order_to_discord_and_save_to_bucket(state: MessagesState):
  messages = state['messages']
  last_message = json.loads(messages[-1].content)
  genuine_order = last_message["genuine_order"]

  '''
    Need to put logic to use the discord helper that will send it to discord using the webhook
  '''
  return {"messages": [{"role": "ai", "content": genuine_order}]}

# CONDITIONAL EDGE
def evalutor_enquiry_or_miscellaneous_message_agent(state: MessagesState):
  '''
    This Node will be used as center to check other messages,
    some from the beginning when evaluated as non-order messages,
    some others when passed the first filter but failed the similarity test,
    at this time we need to check if key `not_genuine_order_or_missing_something` exist in the `last_message`
  '''
  messages = state['messages']
  last_message = json.loads(messages[-1].content)
  
  try:
    # check if the key exist and do the processing otherwise just do processing of the `last_message` directly as it is already `json.loads()`
    if last_message["not_genuine_order_or_missing_something"]
      # do the processing logic to check message using `last_message["not_genuine_order_or_missing_something"]`
      print("shibuya key present")
      # update state before going to next conditional edge with the result of the evaluation `enquiry` or `miscellameous`
      return {"messages": [{"role": "ai", "content": json.dumps({"success": "message coming from similarity test faillure successfully classified."})}]}
    elif:
      # do the processing logic to check messages isung `last_message` directly checking key `other` (last_message['other'])
      print("shibuya key not present evaluating raw message")
      # update state before going to next conditional edge with the result of the evaluation `enquiry` or `miscellameous`
      return {"messages": [{"role": "ai", "content": json.dumps({"success": "message coming from initial evaluator successfully classified."})}]}
  except Exception as e:
    # update state before going to next conditional edge with the error message
    return {"messages": [{"role": "ai", "content": json.dumps({"error": "An error occured while trying to evalute message if enquiry or miscellaneous: {e}"})}]}

  '''
  Make the evaluator function to return in the schema structured output only two keys `enquiry`/`miscellaneous` with `true` or `false`
  '''
  '''
    Here need to create logic to reevaluate message giving just two altrernatives, order enquiry or miscellaneous
  '''
  # dummy return statement for the moment
  return {"messages": [{"role": "ai", "content": last_message}]}

# CONDITIONAL EDGE
def evaluator_success_or_error(state: MessagesState):


# LAST NODE
def last_report_agent(state: MessagesState):
  messages = state["messages"]
  last_message = messages[-1].content
  return {"messages": [{"role": "ai", "content": json.dumps({"report_path": f"{last_message} - Report Path..."})}]}

# ERROR NODE
def error_handler(state: MessagesState):
  messages = state["messages"]
  last_message = messages[-1].content
  return {"messages": [{"role": "ai", "content": json.dumps({"error":last_message})}]}

###############################
###  GRAPH NODES AND EDGES  ###
###############################
# Initialize states
workflow = StateGraph(MessagesState)

# nodes
workflow.add_node("intergraph_agent", intergraph_agent)
workflow.add_node("tool_order_message_items_parser_agent", tool_order_message_items_parser_agent)
workflow.add_node("order_message_items_parser_tool_node", order_message_items_parser_tool_node)
workflow.add_node("evalutor_enquiry_or_miscellaneous_message_agent", evalutor_enquiry_or_miscellaneous_message_agent)
workflow.add_node("score_test_message_relevance_agent", score_test_message_relevance_agent)
workflow.add_node("send_order_to_discord_and_save_to_bucket", send_order_to_discord_and_save_to_bucket)
workflow.add_node("last_report_agent", last_report_agent)
workflow.add_node("error_handler", error_handler)

# edges
workflow.set_entry_point("intergraph_agent")
workflow.add_conditional_edges(
  "intergraph_agent",
  message_interpreter_order_or_other_agent,
)

workflow.add_edge("tool_order_message_items_parser_agent", "order_message_items_parser_tool_node")
workflow.add_conditional_edges(
  "order_message_items_parser_tool_node",
  order_message_items_parser_success_or_error
)
workflow.add_conditional_edges(
  "score_test_message_relevance_agent",
  relevance_test_passed_or_not
)
workflow.add_edge("send_order_to_discord_and_save_to_bucket", "last_report_agent")
workflow.add_edge("evalutor_enquiry_or_miscellaneous_message_agent", "last_report_agent")
# end
workflow.add_edge("last_report_agent", END)
workflow.add_edge("error_handler", END)

# compile
checkpointer = MemorySaver()
user_query_processing_stage = workflow.compile(checkpointer=checkpointer)

###############################
## GRAPH CODE LOGIC ABOVE IT ##
###############################
def order_automation_agent_team(user_query):
  print("ORder Automation Agents AI Team Startooooooo !!!")
  print(f"Query: '{user_query}'")
  final_output = None

  count = 0
  for step in user_query_processing_stage.stream(
    {"messages": [SystemMessage(content=user_query)]},
    config={"configurable": {"thread_id": int(os.getenv("THREAD_ID"))}}):
    count += 1

    if "messages" in step:
      final_output = step['messages'][-1].content
      output = beautiful_graph_output.beautify_output(step['messages'][-1].content)
      print(f"Step {count}: {output}")
    else:
      output = beautiful_graph_output.beautify_output(step)
      print(f"Step {count}: {output}")
      try:
        final_output = safe_json_dumps.safe_json_dumps(step)
      except TypeError as e:
        final_output = json.dumps({"error": f"Invalid final output format: {e}"})

  # subgraph drawing
  graph_image = user_query_processing_stage.get_graph().draw_png()
  with open("order_automation_agent_team.png", "wb") as f:
    f.write(graph_image)

  # Ensure final_output is JSON formatted for downstream consumption
  if isinstance(final_output, str):
    try:
      # Ensure valid JSON; if not, wrap in a standard error message
      json.loads(final_output)
    except json.JSONDecodeError:
      final_output = json.dumps({"error": "Invalid final output format"})

  return final_output


'''
if __name__ == '__main__':
  import json
  load_dotenv()
  user_query = os.getenv("USER_INITIAL_QUERY")
  order_automation_agent_team(user_query)
'''
