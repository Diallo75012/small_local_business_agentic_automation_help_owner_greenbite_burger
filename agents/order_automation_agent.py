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
  log_analyzer_notififier_tool_node,
  llm_with_log_analyzer_notififier_tool_choice,
)
# structured output
from structured_output.structured_output import (
  message_interpreter_order_or_other_schema,
  message_classification_schema,
)
# prompts
from prompts.prompts import (
  message_interpreter_order_or_other_prompt,
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
  # 
  try:
    print("calling llm")
    decision = call_llm.call_llm(query, message_interpreter_order_or_other_prompt["system"]["template"], message_interpreter_order_or_other_schema)
    print("decision: ", decision, type(decision))
    if decision["order"].lower() == "true":
      print("!")
      # update state message
      state["messages"] + [{"role": "ai", "content": json.dumps({"order": last_message})}]
      return "order_message_items_parser_agent"
    pritn("2")
    # update state message
    state["messages"] + [{"role": "ai", "content": json.dumps({"other": last_message})}]
    return "non_orders_messages_manager_agent"
  except Exception as e:
    print("3: ", e)
    # update state message
    state["messages"] + [{"role": "ai", "content": json.dumps({"error": f"An error occured while trying to interpret if message is a genuine order or another type of message: {e}"})}]
    return "error_handler"

# NODE
def tool_notifier_agent(state: MessagesState):
  messages = state['messages']
  last_message = messages[-1].content

  # Generate a query
  query = prompt_creation.prompt_creation(tool_notifier_agent_prompt["human"], user_initial_query="I need to send logs issues notifications to Discord for the Devops security team")
  print("QUERY: ", query)

  try:
    response = llm_with_log_analyzer_notififier_tool_choice.invoke(json.dumps(query))
    print("LLM with tool choice response: ", response)
    return {"messages": [response]}
  except Exception as e:
    return {"messages": [{"role": "tool", "content": json.dumps({"error": f"An error occurred: {e}"})}]

# CONDITIONAL EDGE    

def discord_notification_flow_success_or_error(state: MessagesState):
    messages = state['messages']
    print("Messages coming from discord sent notification agent: ", messages, type(messages))
    last_message = messages[-1].content
    print("Last message content (discord notification conditional edge): ", last_message)

    try:
        # returns: {'messages': [{'role': 'ai', 'content': '{"success": {"success": "All logs have been transmitted to DeviOps/Security team."}}'}]}
        # so json.loads is done once in the full message and inside on the `.content` to be able to access `success`
        last_message_data = json.loads(json.loads(last_message)['messages'][-1]['content'])
        # Parse the content
        print("json load last message (discord notification conditional edge): ", last_message_data)
        if 'success' in last_message_data:
            return "temporary_log_files_cleaner"
        return "error_handler"
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return "error_handler"

# NODE
def order_message_items_parser_agent(state: MessagesState):
  messages = state["messages"]
  last_message = messages[-1].content
  return {"messages": [{"role": "ai", "content": json.dumps({"from_parser_agent":last_message})}]}

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
workflow.add_node("order_message_items_parser_agent", order_message_items_parser_agent)
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
workflow.add_edge("tool_notifier_agent", "log_analyzer_notififier_tool_node")
workflow.add_conditional_edges(
  "log_analyzer_notififier_tool_node",
  discord_notification_flow_success_or_error
)
workflow.add_edge("order_message_items_parser_agent", "last_report_agent")
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
  with open("retrieval_agent_team.png", "wb") as f:
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
