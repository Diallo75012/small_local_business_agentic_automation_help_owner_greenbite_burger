import os
import json
# for typing func parameters and outputs and states
from typing import Dict, List, Tuple, Any, Optional
# one is @tool decorator and the other Tool class
from langchain_core.tools import tool, Tool
from langgraph.graph import MessagesState
from langgraph.prebuilt import ToolNode
# LLMs
from llms.llms import (
  groq_llm_mixtral_7b,
  groq_llm_mixtral_larger,
  groq_llm_llama3_70b_versatile,
)
# structured output
from structured_output.structured_output import (
  order_message_items_parser_schema,
)
# prompts
from prompts.prompts import (
  order_message_items_parser_prompt,
)
# helpers
from helpers import (
  call_llm,
  prompt_creation,
)
from helpers.similarity_search_checker import similarity_check_on_the_fly
from dotenv import load_dotenv


# load env vars
load_dotenv(dotenv_path='.env', override=False)
load_dotenv(dotenv_path=".vars", override=True)


def message_bucket_classifier(message: str, item_names: List) -> Dict:
  '''
  Description:
  Reads client message and uses LLM to get fromthe message the items and quantity (structured output)
  Uses `Alibaba-NLP/gte-modernbert-base` model to check if the item name passes the test
  
  Parameter:
  message str: the client message that need to pass the test and be classified
  item_names list: the list of item names that is used to check if the message is relevant
  
  Output:
  return the classification of the message as order, enquiry or miscellaneous  
  '''
  similarity_threshold = float(os.getenv("SIMILARITY_THRESHOLD"))
  # we use the score test first to eliminate message quick and not make llm call which will help classify it as non order for the moment
  score_test_result = similarity_check_on_the_fly(item_names, message, similarity_threshold)

  # check if key is 'failed' we just send to node that take care of other messages other than genuine orders
  if "failed" in score_test_result:
    # already a dict
    return score_test_result

  # otherwise we have the test success so message can go to an LLM evaluation
  '''
    here make code calling llm using a helper function (structured output + prompt also)
  '''
  
  return "order"

# TOOLS
# order message items parser
@tool
def order_message_items_parser(state: MessagesState = MessagesState()):
  """
  Description:
  parses the different items from the order to have separate distinct names and quantities

  Parameter:
  None

  returns:
  dictionary with item names and their quantities ordered by user
  """

  # pass in `USER_INITIAL_QUERY` to get items parsed from it
  query = prompt_creation.prompt_creation(order_message_items_parser_prompt["human"], message=os.getenv("USER_INITIAL_QUERY"))
  print("query: ",query)

  try:
    print("calling llm")
    parsed_order_items = call_llm.call_llm(query, order_message_items_parser_prompt["system"]["template"], order_message_items_parser_schema)
    print("parsed order items: ", parsed_order_items, type(parsed_order_items))
    return {"messages": [{"role": "tool", "content": json.dumps({"success": parsed_order_items})}]}
  except Exception as e:
    return {"messages": [{"role": "tool", "content": json.dumps({"error": f"An error occured while using tool to parse order items: {e}"})}]}

# message classifier tool
@tool
def message_classifier(state: MessagesState = MessagesState()):
  """
  Description:
  Classifies messages to determine if those are either genuine orders, genuine orders enquiries or miscellaneous.

  Parameter:
  None

  returns:
  The classification of the message as 'order', 'enquiry' or 'miscellaneous'
  """
  # get the message to work on
  message: os.getenv("MESSAGE_TO_EVALUTATE") # to be set by agent after fetching this from the database and looping through values fetched
  # fetch keys of resataurant items stored in env vars from when it has been recorded to cache
  cache_keys_reaturant_items_not_formatted_yet: List = json.loads(os.getenv("CACHE_KEYS"))
  # get the keys formatted as correct text chunks so that LLM can understand (space between words)
  restaurant_item_names = [ elem.replace("_", " ") for elem in cache_keys_reaturant_items_not_formatted_yet]
  try:
    '''
      function need to be coded
    '''
    classification_result = message_bucket_classifier(message, restaurant_item_names)
    return {"messages": [{"role": "ai", "content": json.dumps({"success": classification_result})}]}
  except Exception as e:
    return {"messages": [{"role": "ai", "content": json.dumps({"error": f"An error occured while trying to classify de message using LLM tool: {e}"})}]}

####################################
### THIS TO BE USED AND EXPORTED ###
####################################

# order message items parser tool
order_message_items_parser_tool_node = ToolNode([order_message_items_parser])
llm_with_order_message_items_parser_tool_choice = groq_llm_llama3_70b_versatile.bind_tools([order_message_items_parser])
