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
    return "non_orders_messages_manager_agent"
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
'''
This should probably be a condition edge instead as if smilimary test is not passed those messages need to go to order enquiry or miscellaneous
'''
def score_test_message_relevance_agent(state: MessagesState):
  messages = state["messages"]
  # so here it is a bit tricky to the full `role: Tool` answer is json.dumped itself and the message is also json.dumps so we need to unwrap that
  last_message = json.loads(messages[-1].content)
  unwrapped_last_message = json.loads(last_message)["messages"][-1]["content"])
  # after the unwrapping we can now access to the tool `success` key which has the dictionary structured output from the LLM response
  tool_parsed_output = unwrapped_last_message["success"]
  # now we are going to create a list of tuple from it getting each item ordered with its quantity [(item_name, quantity), ....]
  orders_parsed: List[Tuple] = []
  for i in range(len(tool_parsed_output["item_ids"])):
    orders_parsed.append((tool_parsed_output["item_names"][i], tool_parsed_output["item_quantities"][i]))

  print("Success message output from tool parsing: in score test relevance node: ", orders_parsed, type(orders_parsed))
  '''
    Return will need to be updated as we need in this funciton to use the classifier and item name has to pass the test otherwise we will send this to enquiries or miscellaneous.
    
  '''
  return {"messages": [{"role": "ai", "content": json.dumps({"order_parsed": orders_parsed})}]}

# NODE
def non_orders_messages_manager_agent(state: MessagesState):
  messages = state["messages"]
  last_message = messages[-1].content
  return {"messages": [{"role": "ai", "content": json.dumps({"from_other_messages_manager_agent":last_message})}]}

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
workflow.add_node("non_orders_messages_manager_agent", non_orders_messages_manager_agent)
workflow.add_node("score_test_message_relevance_agent", score_test_message_relevance_agent)
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
workflow.add_edge("score_test_message_relevance_agent", "last_report_agent")
workflow.add_edge("non_orders_messages_manager_agent", "last_report_agent")
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
