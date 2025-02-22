import os
import json
# for typing func parameters and outputs and states
from typing import Dict, List, Tuple, Any, Optional, Union
# models
from llms.llms import (
  groq_llm_mixtral_7b,
  groq_llm_llama3_70b_versatile,
)
# Tools
from tools.tools import (
)
# structured output
from structured_output.structured_output import (
  message_classification_schema,
)
# prompts
from prompts.prompts import (
)
# langchain and langgraph lib
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
# from langgraph.checkpoint import MemorySaver
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph, MessagesState
# env vars
from dotenv import load_dotenv, set_key


# load env vars
load_dotenv(dotenv_path='.env', override=False)
load_dotenv(dotenv_path=".vars.env", override=True)

'''
1. fetch_new_messages # this one here need to be developped more in how we will decide to fetch those messages from db and how the main app will simulate message added to db

2.  > score_test_message_relevance_agent
3.    >>> rephrase_query_agent
3.1        > store_to_enquiries_bucket_agent
3.2          > notify_discord_order_enquiries_category_agent
3.    >>> store_miscellanous_messages_to_bucket_agent
3.1        > notify_dicord_miscellanous_messages_category_agent
3.    > structure_output_order_parser_agent
3.1      >>> rephrase_query_agent
3.1.1        > store_to_enquiries_bucket_agent
3.1.2          > notify_discord_order_enquiries_category_agent
3.2      >>> store_miscellanous_messages_to_bucket_agent
3.2.1        > notify_dicord_miscellanous_messages_category_agent
3.3      >>> store_to_order_bucket_agent
3.3.1        > notify_dicord_order_category_agent
'''

###############################
###  GRAPH NODES AND EDGES  ###
###############################
# Initialize states
workflow = StateGraph(MessagesState)

# nodes
workflow.add_node("error_handler", error_handler)

# edges
workflow.set_entry_point("analyse_user_query_safety")
workflow.add_conditional_edges(
  "analyse_user_query_safety",
  safe_or_not
)
# end
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
        final_output = safe_json_dumps(step)
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

  # final_output_agent content should be of type json.dumps() as we json.dumped all transmitted messages
  #final_output_agent = final_output["messages"][-1]["content"]
  with open("logs/retrieval_agent_final_output.log", "w", encoding="utf-8") as final_output_log:
    final_output_log.write(json.dumps({"final_output": final_output}))
  return final_output


"""
if __name__ == '__main__':
  import json
  load_dotenv()
  user_query = os.getenv("USER_INITIAL_QUERY")
  order_automation_agent_team(user_query)
"""
