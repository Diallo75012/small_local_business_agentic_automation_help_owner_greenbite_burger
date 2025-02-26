import os
import json
from datetime import datetime
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
)
# prompts
from prompts.prompts import (
  message_interpreter_order_or_other_prompt,
  order_message_items_parser_prompt,
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
# database
from postgresql_tables_creations import (
  db,
  Orders,
  Enquiries,
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
    state["messages"] + [{"role": "ai", "content": json.dumps({"error": f"An exception occured while trying to interpret if message is a genuine order or another type of message: {e}"})}]
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
    return {"messages": [{"role": "tool", "content": json.dumps({"error": f"An exception occurred: {e}"})}]}

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
    return "send_order_to_discord_agent"
  elif len(not_genuine_order_or_missing_something) > 0:
    return "evalutor_enquiry_or_miscellaneous_message_agent"
  return "error_handler"

# NODE
def send_order_to_discord_agent(state: MessagesState):
  messages = state['messages']
  last_message = json.loads(messages[-1].content)
  genuine_order = last_message["genuine_order"]
  print("Genuine_order: ", genuine_order, type(genuine_order))
  try:
    # use webhook helper to send notification to the right Discord room (Order)
    for order in genuine_order:
      if isinstance(order, list):
        print("genuine order list")
        send_discord_notification_to_target_room.send_file_to_discord(order[0], "Order", os.getenv("ORDERS_DISCORD_ROOM_WEBHOOK_URL"))
      elif isinstance(order, str):
        print("genuine order str")
        send_discord_notification_to_target_room.send_file_to_discord(order, "Order", os.getenv("ORDERS_DISCORD_ROOM_WEBHOOK_URL"))
    return {"messages": [{"role": "ai", "content": json.dumps({"success": "Order message successfully sent to Discord."})}]}
  except Exception as e:
    return {"messages": [{"role": "ai", "content": json.dumps({"error": f"An exception occurred while sending Order message to Discord: {e}"})}]}

# CONDITIONAL EDGE
def order_message_send_to_discord_success_or_not(state: MessagesState):
  messages = state['messages']
  last_message = json.loads(messages[-1].content)
  
  # check if `success` or `error`
  if "success" in last_message:
    return "record_message_to_order_bucket_agent" # need to do this function
  elif "error" in last_message:
    return "error_handler"
  # for anything else goes to error (whatever is catched here require code refactoring or adding logic to handle that) 
  return "error_handler"

# NODE
def record_message_to_order_bucket_agent(state: MessagesState):
  messages = state['messages']
  last_message = json.loads(messages[-1].content)
  
  try:
    # we check again if last message was ok like a double check
    if "success" in last_message:
      # we then get the previous message which holds the genuire order at index `[-2]`
      previous_message = json.loads(messages[-2].content)
      genuine_order = previous_message["genuine_order"]
   
      for order in genuine_order: # here eg: order = `['Kale & Quinoa Super Salad', 1]` so we get index `0`
        if isinstance(order, list):
          print("genuine order list")
          # we check that it is is real order, no real order can have less than 10 characters
          if len(order[0]) > 10:
            # now lets store to database:
            order = Orders(date=f"{datetime.now()}", message=order[0])
            db.session.add(order)
            db.session.commit()
        elif isinstance(order, str):
          # now lets store to database as here we are sure to have one unique line of text:
          print("genuine order str")
          order = Orders(date=f"{datetime.now()}", message=order)
          db.session.add(order)
          db.session.commit()
      return {"messages": [{"role": "ai", "content": json.dumps({"success": "Order message successfully recorded to database"})}]}
    return {"messages": [{"role": "ai", "content": json.dumps({"error": f"An error occurred while save order to database: No key names `success` in previous node message, couldn't record message to order bucket."})}]}
  except Exception as e:
    return {"messages": [{"role": "ai", "content": json.dumps({"error": f"An exception occurred while save order to database: {e}"})}]}

# CONDITIONAL EDGE
def order_recorded_to_bucket_or_not(state: MessagesState):
  messages = state['messages']
  last_message = json.loads(messages[-1].content)
  
  if "success" in last_message:
    return "last_report_agent"
  return "error_handler"

# NODE
def evalutor_enquiry_or_miscellaneous_message_agent(state: MessagesState):
  '''
    This Node will be used as center to check other messages,
    some from the beginning when evaluated as non-order messages,
    some others when passed the first filter but failed the similarity test,
    at this time we need to check if key `not_genuine_order_or_missing_something` exist in the `last_message`
  '''
  messages = state['messages']
  last_message = json.loads(messages[-1].content)
  enquiries_final_bucket = []
  miscellaneous_final_bucket = []

  try:
    # check if the key exist and do the processing otherwise just do processing of the `last_message` directly as it is already `json.loads()`
    # `last_message["not_genuine_order_or_missing_something"]` is type `List`
    if last_message["not_genuine_order_or_missing_something"]:

      # we evalute the message
      for message in last_message["not_genuine_order_or_missing_something"]:

        query = prompt_creation.prompt_creation(evalutor_enquiry_or_miscellaneous_message_prompt["human"], message=message)
        print("query: ",query)
        decision = call_llm.call_llm(query, evalutor_enquiry_or_miscellaneous_message_prompt["system"]["template"], evalutor_enquiry_or_miscellaneous_message_schema)
        print("decision: ", decision, type(decision))

        if decision["enquiry"].lower() == "true":
          # append the right bucket
          enquiries_final_bucket.append(message)
        if decision["miscellaneous"].lower() == "true":
          # append the right bucket
          miscellaneous_final_bucket.append(message)

      # update state before going to next conditional edge with the result of the evaluation `enquiry` or `miscellaneous` (next node will check message [-1] and get [-2])
      state["messages"] + [{"role": "ai", "content": json.dumps({"enquiries_final_bucket": enquiries_final_bucket, "miscellaneous_final_bucket": miscellaneous_final_bucket})}]
      return {"messages": [{"role": "ai", "content": json.dumps({"success": "message coming from similarity test faillure successfully classified."})}]}
    
    elif last_message["other"]:
      # we evaluate the message
      query = prompt_creation.prompt_creation(evalutor_enquiry_or_miscellaneous_message_prompt["human"], message=last_message["other"])
      print("query: ",query)
      decision = call_llm.call_llm(query, evalutor_enquiry_or_miscellaneous_message_prompt["system"]["template"], evalutor_enquiry_or_miscellaneous_message_schema)
      print("decision: ", decision, type(decision))
      
      if decision["enquiry"].lower() == "true":
        # update state (next node will check message [-1] and get [-2])
        state["messages"] + [{"role": "ai", "content": json.dumps({"enquiry": last_message["other"]})}]
      if decision["miscellaneous"].lower() == "true":
        # append state (next node will check message [-1] and get [-2])
        state["messages"] + [{"role": "ai", "content": json.dumps({"miscellaneous": last_message["other"]})}]
    
      return {"messages": [{"role": "ai", "content": json.dumps({"success": "message coming from initial evaluator successfully classified."})}]}
    
    # going to next step (next node will check message [-1] and go `error_handler`)
    return {"messages": [{"role": "ai", "content": json.dumps({"error": f"An error occurred while trying to evaluate message if enquiry or miscellaneous. Last message missed keys: `not_genuine_order_or_missing_something` or `other`"})}]}
  
  except Exception as e:
    # going to next step with the error message (next node will check message [-1] and go `error_handler`)
    return {"messages": [{"role": "ai", "content": json.dumps({"error": "An exception occured while trying to evalute message if enquiry or miscellaneous: {e}"})}]}

# CONDITIONAL EDGE
def evaluator_success_or_error(state: MessagesState):
  '''
    Here we check the results of the messages evaluation and catch all keys possible
    to send to the right Discord room: `record_message_to_enquiry_discord_room` or `record_message_to_miscellaneous_dicsord_room`
  '''
  messages = state["messages"]
  last_message = json.loads(messages[-1].content)
  previous_state_message_updated = json.loads(messages[-2].content)
  
  # we check if it successfull and check the updated message to know where we are going to send the message
  if "success" in last_message:
    # will check if those keys exists
    if "enquiry" or "enquiries_final_bucket" in previous_state_message_updated:
      return "record_message_to_enquiry_discord_room_agent"
    elif "miscellaneous" or "miscellaneous_final_bucket" in previous_state_message_updated:
      return "record_message_to_miscellaneous_discord_room_agent"  # need to do this function and other logic for node recording to bucket
  # otherwise just send to error node
  return "error_handler"

# NODE
def record_message_to_enquiry_discord_room_agent(state: MessagesState):
  messages = state["messages"]
  # here we just catch the previous/previous node messages to get or one message or a list and send to discord depends where it is from
  previous_state_message_updated = json.loads(messages[-2].content)
  count = 0
  # variabble set to check if we get a list for next node or a single enquiry treated as next node need to handle it differently
  success_list_enquiries_all_sent = False
  try:
    # check if it is a single message `enquiry` or a list `enquiries_final_bucket`. (checking dict keys)
    if "enquiry" in previous_state_message_updated:
      try:
        # send messages to discord in the enquiry room
        single_enquiry_sent_to_discord = send_discord_notification_to_target_room.send_file_to_discord(previous_state_message_updated["enquiry"], "Enquiry", os.getenv("ENQUIRIES_DISCORD_ROOM_WEBHOOK_URL"))
        print(f"Successfully sent message to enquiry discord room: {previous_state_message_updated['enquiry']}")
        count += 1
      except Exception as e:
        print(f"Error sending enquiry message to discord: {e}")
        return {"messages": [{"role": "ai", "content": json.dumps({"error": f"An exception occurred while sending Enquiry message to Discord: {e}"})}]}
    elif "enquiries_final_bucket" in previous_state_message_updated:
      for enquiry_message in previous_state_message_updated["enquiries_final_bucket"]:
        try:
          # send messages to discord in the enquiry room
          send_discord_notification_to_target_room.send_file_to_discord(enquiry_message, "Enquiry", os.getenv("ENQUIRIES_DISCORD_ROOM_WEBHOOK_URL"))
          print(f"Successfully sent message to enquiry discord room: {enquiry_message}")
          count += 1
          if count == len(previous_state_message_updated["enquiries_final_bucket"]):
            success_list_enquiries_all_sent = True
        except Exception as e:
          print(f"Error sending enquiry message to discord: {e}")
          return {"messages": [{"role": "ai", "content": json.dumps({"error": f"An exception occurred while sending Enquiry message to Discord: {e}"})}]}
    # we send the list to next node with key `enquiries` (plural) to next node
    if success_list_enquiries_all_sent == True:
      return {"messages": [{"role": "ai", "content": json.dumps({"succes": f"x{count} Enquiry message(s) successfully sent to discord", "enquiries": previous_state_message_updated["enquiries_final_bucket"]})}]}
    # otherwise we sent single enquiry to next node with key `enquiry` (singular)
    return {"messages": [{"role": "ai", "content": json.dumps({"succes": f"x{count} Enquiry message(s) successfully sent to discord", "enquiry": single_enquiry_sent_to_discord})}]}
  except Exception as e:
    return {"messages": [{"role": "ai", "content": json.dumps({"error": f"Something went wrong. An exception occurred while sending Enquiry message to Discord: {e}"})}]}

# CONDITIONAL EDGE
def enquiry_message_send_to_discord_success_or_not(state: MessagesState):
  messages = state['messages']
  last_message = json.loads(messages[-1].content)
  
  # check if `success` or `error`
  if "success" in last_message:
    return "record_message_to_enquiry_bucket_agent"
  # for anything else goes to error (whatever is catched here require code refactoring or adding logic to handle that) 
  return "error_handler"

# NODE
def record_message_to_enquiry_bucket_agent(state: MessagesState):
  messages = state['messages']
  last_message = json.loads(messages[-1].content)
  
  try:
    # we check for which key is present `enquiry` singular emaning it is just an  str` to handle or `enquiries` (plural) meaning it is a `list` to handle
    if "enquiry" in last_message:
      # the message is in the `[-1]` at key `enquiry`, we just fetch it
      previous_message = json.loads(messages[-1].content)
      if "enquiries" in previous_message:
         for enquiry_message in previous_message["enquiries"]:
           if isinstance(previous_message["enquires"], list):
             for message in  enquiry_message:
               # now lets store to database:
               enquiry = Enquiries(date=f"{datetime.now()}", message=message)
               db.session.add(enquiry)
               db.session.commit()

      elif "enquiry" in previous_message: 
        order_enquiry_message = previous_message["enquiry"]
    
        # now lets store to database:
        enquiry = Enquiries(date=f"{datetime.now()}", message=order_enquiry_message)
        db.session.add(enquiry)
        db.session.commit()

      return {"messages": [{"role": "ai", "content": json.dumps({"success": "Enquiry message successfully recorded to database"})}]}

    return {"messages": [{"role": "ai", "content": json.dumps({"error": f"An error occurred while save enquiry to database: No key `success` present in previous node message. Could not save anything to bucket."})}]}

  except Exception as e:
    return {"messages": [{"role": "ai", "content": json.dumps({"error": f"An exception occurred while save enquiry to database: {e}"})}]}

# CONDITIONAL EDGE
def enquiry_recorded_to_bucket_or_not(state: MessagesState):
  messages = state['messages']
  last_message = json.loads(messages[-1].content)
  
  if "success" in last_message:
    return "last_report_agent"
  return "error_handler"

# NODE
def record_message_to_miscellaneous_discord_room_agent(state: MessagesState):
  messages = state["messages"]
  # here we just catch the previous/previous node messages to get or one message or a list and send to discord depends where it is from
  previous_state_message_updated = json.loads(messages[-2].content)
  count = 0
  # variabble set to check if we get a list for next node or a single miscellaneous message treated as next node need to handle it differently
  success_list_miscellaneous_all_sent = False
  try:
    # check if it is a single message `miscellaneous` or a list `miscellaneous_final_bucket`. (checking dict keys)
    if "miscellaneous" in previous_state_message_updated:
      try:
        # send messages to discord in the miscellaneous room
        # this as success will return the message sent
        single_miscellaneous_sent_to_discord = send_discord_notification_to_target_room.send_file_to_discord(previous_state_message_updated["miscellaneous"], "Miscellaneous", os.getenv("MISCELLANEOUS_DISCORD_ROOM_WEBHOOK_URL"))
        print(f"Successfully sent message to miscellaneous discord room: {previous_state_message_updated['miscellaneous']}")
        count += 1
      except Exception as e:
        print(f"Error sending miscellaneous message to discord: {e}")
        return {"messages": [{"role": "ai", "content": json.dumps({"error": f"An exception occurred while sending miscellaneous message to Discord: {e}"})}]}
    elif "miscellaneous_final_bucket" in previous_state_message_updated:
      for miscellaneous_message in previous_state_message_updated["miscellaneous_final_bucket"]:
        try:
          # send messages to discord in the miscellaneous room
          send_discord_notification_to_target_room.send_file_to_discord(miscellaneous_message, "Miscellaneous", os.getenv("ENQUIRIES_DISCORD_ROOM_WEBHOOK_URL"))
          print(f"Successfully sent message to miscellaneous discord room: {miscellaneous_message}")
          count += 1
          if count == len(previous_state_message_updated["miscellaneous_final_bucket"]):
            success_list_miscellaneous_all_sent = True
        except Exception as e:
          print(f"Error sending miscellaneous message to discord: {e}")
          return {"messages": [{"role": "ai", "content": json.dumps({"error": f"An exception occurred while sending Miscellaneous message to Discord: {e}"})}]}
    # we send the list to next node with key `enquiries` (plural) to next node
    if success_list_miscellaneous_all_sent == True:
      return {"messages": [{"role": "ai", "content": json.dumps({"succes": f"x{count} Miscellaneous message(s) successfully sent to discord", "miscellaneous": previous_state_message_updated["miscellaneous_final_bucket"]})}]}
    # otherwise we sent single miscellaneous to next node with key `miscellaneous` (singular)
    return {"messages": [{"role": "ai", "content": json.dumps({"succes": f"x{count} Miscellaneous message(s) successfully sent to discord", "miscellaneous": single_miscellaneous_sent_to_discord})}]}
  except Exception as e:
    return {"messages": [{"role": "ai", "content": json.dumps({"error": f"Something went wrong. An exception occurred while sending Miscellaneous message to Discord: {e}"})}]}


# CONDITIONAL EDGE
def miscellaneous_message_send_to_discord_success_or_not(state: MessagesState):
  messages = state['messages']
  last_message = json.loads(messages[-1].content)
  
  # check if `success` or `error`
  if "success" in last_message:
    return "write_miscellaneous_message_to_file_agent"
  # for anything else goes to error
  return "error_handler"

# NODE
def write_miscellaneous_message_to_file_agent(state: MessagesState):
  messages = state['messages']
  last_message = json.loads(messages[-1].content)
  # miscellaneous messages are not saved to database for security reasons but those where sent anyway before to discord specific room for security team to check those.
  # we are just saving those in a filem we could use a logger system for that but here we just simply write those to a file as they come to this stream
  try:
    with open(os.getenv("MISCELLANEOUS_MESSAGES_FILE_RECORD_PATH"), "a", encoding="utf-8") as other_messages_file:
      # we check if we got a single string message and write to file
      if isinstance(last_message["miscellaneous"], str):
        time_recorded = datetime.now()
        other_messages_file.write(f"{time_recorded} - {last_message['miscellaneous']}")
        return {
          "messages": [
            {"role": "ai", "content": json.dumps({"succes": f"miscellaneous message written successfully to file {os.getenv('MISCELLANEOUS_MESSAGES_FILE_RECORD_PATH')}"})}
          ]
        }
      # otherwise we receive a list and loop over to have all written line by line
      count = 1
      for message in last_message["miscellaneous"]:
        time_recorded = datetime.now()
        other_messages_file.write(f"{count}/{len(last_message['miscellaneous'])}: {time_recorded}: {last_message['miscellaneous']}")
        count += 1
      return {
        "messages": [
          {"role": "ai", "content": json.dumps({"succes": f"{count}/{len(last_message['miscellaneous'])}: miscellaneous message written successfully to file {os.getenv('MISCELLANEOUS_MESSAGES_FILE_RECORD_PATH')}"})}
        ]
      }
  except Exception as e:
    return {"messages": [{"role": "ai", "content": json.dumps({"error": f"An exception occurred while trying to write miscellaneous messages to file: {e}"})}]}

# LAST NODE
def last_report_agent(state: MessagesState):
  messages = state["messages"]
  last_message = json.loads(messages[-1].content)
  return {"messages": [{"role": "ai", "content": json.dumps({"success": f"{last_message}"})}]}

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
workflow.add_node("send_order_to_discord_agent", send_order_to_discord_agent)
workflow.add_node("record_message_to_order_bucket_agent", record_message_to_order_bucket_agent)
workflow.add_node("record_message_to_enquiry_discord_room_agent", record_message_to_enquiry_discord_room_agent)
workflow.add_node("record_message_to_enquiry_bucket_agent", record_message_to_enquiry_bucket_agent)
workflow.add_node("record_message_to_miscellaneous_discord_room_agent", record_message_to_miscellaneous_discord_room_agent)
workflow.add_node("write_miscellaneous_message_to_file_agent", write_miscellaneous_message_to_file_agent)
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
workflow.add_conditional_edges(
  "send_order_to_discord_agent",
  order_message_send_to_discord_success_or_not
)
workflow.add_conditional_edges(
  "record_message_to_order_bucket_agent",
  order_recorded_to_bucket_or_not
)
workflow.add_conditional_edges(
  "evalutor_enquiry_or_miscellaneous_message_agent",
  evaluator_success_or_error
)
workflow.add_conditional_edges(
  "record_message_to_enquiry_discord_room_agent", 
  enquiry_message_send_to_discord_success_or_not
)
workflow.add_conditional_edges(
  "record_message_to_enquiry_bucket_agent",
  enquiry_recorded_to_bucket_or_not
)
workflow.add_conditional_edges(
  "record_message_to_miscellaneous_discord_room_agent",
  miscellaneous_message_send_to_discord_success_or_not
)
workflow.add_edge("write_miscellaneous_message_to_file_agent", "last_report_agent")
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
