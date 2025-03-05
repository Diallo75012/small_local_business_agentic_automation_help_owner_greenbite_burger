# file to test python different code snippets before incorporating those in app
# advantage here is that we are not altering the original `.csv` file but fetching from it what is new
# we then keep record of the row number so that next fetching will check beyond that row
import os
import json
import time
import random
import pandas as pd
from agents.order_automation_agent import order_automation_agent_team
import concurrent.futures
import subprocess
from typing import List
from dotenv import load_dotenv, set_key

load_dotenv(dotenv_path='.vars.env', override=True)

'''
MESSAGE_INDEX_TRACKER = json.loads(os.getenv("MESSAGE_INDEX_TRACKER"))
print("Message index tracker env var value: ", MESSAGE_INDEX_TRACKER, type(MESSAGE_INDEX_TRACKER))
'''

'''
create dataframe with pandas from csv file in a priodic manner from a certain row number and record that row in the .vars.env file
'''

'''
create function that will fetch rows of the dataframe in a random number manner and in random interval time manner
'''

'''
connect to db by importing the db connector
connect to db to record those rows fetched
'''

'''
# test sleep get data output frequently using `random.uniform(range)`
data = ["hello", "Shibuya", "here", "the", "world"]

for elem in data:
  number = random.uniform(0.01, 0.9)
  time.sleep(number)
  print(f"time:{number} - {elem}")
'''
'''
# be careful indexes are type nympy.in64 so save those as str() to env var to avoid errors
df = pd.read_csv("dataset_cleaned.csv")
print(df.head())
# gets the index number of last row here `5` as we print the `.head()` only
print(df.head().index.stop)
# prints the number of rows in the dataframe `156`            
print(df.index.stop)
print(f"len df: {len(df)}")
# getting the index of a message (be carefull df indexes are type nympy.int64 need to covert to int type)
new_index = df.index[df['message'] == 'Where can I pick up my order?'][0]
print("Index of message: ", df.index[df['message'] == 'Where can I pick up my order?'][0])
# here we are making new df that have rows only from a certain index to the end
#df = df[df.index[df['message'] == 'Where can I pick up my order?'][0]+1:]
df = df[2:]
print(df.head())
print(df.index.stop)
print(f"len df: {len(df)}")
# store updated index in a `.vars.env file
print("New index: ", new_index, type(new_index))
set_key(".vars.env", "MESSAGE_INDEX_TRACKER", str(new_index))
load_dotenv(dotenv_path='.vars.env', override=True)
print("new index value in env var now: ", int(os.getenv("MESSAGE_INDEX_TRACKER")), type(int(os.getenv("MESSAGE_INDEX_TRACKER"))))
# now simulate an id 37 that you are going to use to fetch the csv file again but from that index until the end of it
df_fetch_form_index = pd.read_csv("dataset_cleaned.csv").index[37:]
print("len new df fetched from index: ", len(df_fetch_form_index))


# add messages to database using the frequency way
from postgresql_tables_creations import (
  db,
  Messages,
)
from datetime import datetime


df = pd.read_csv("dataset_cleaned.csv")[0:100]
for index, row in df.iterrows():
  # print("row: ", index, row.timestamp, row.message)
  print(row.timestamp)
  # 15s to 20 seconds before adding row (lot of orders for this Owner, nice!!)
  time.sleep(random.uniform(15, 30))
  # datetime.strptime(row.timestamp, '%Y-%m-%d %H:%M:%S')
  new_message = Messages(dfidx=index, date=row.timestamp, message=row.message)
  db.session.add(new_message)
  db.session.commit()
  print(f"Data added to db: ", index, row.timestamp, row.message)
'''
def data():
  return """'''ORder Automation Agents AI Team Startooooooo !!!
Query: 'hi there, i would like to order one Kale & Quinoa Super Salad please'
formatted_template:  hi there, i would like to order one Kale & Quinoa Super Salad please
query:  hi there, i would like to order one Kale & Quinoa Super Salad please
calling llm
Prompt before call structured output:  input_variables=['query', 'response_schema'] input_types={} partial_variables={} template='You are an expert in restaurant order request messages identification.\n\n\n    Your task:\n\n    - Identify if message is an order and not just an enquiry or miscellaneous message.\n\n    - Strictly adhere to the following schema for your response:\n\n    Schema:\n\n    {response_schema}\n\n\n    Important:\n\n    - Only return a JSON object based on the schema. Do not include any extra text, comments, or fields beyond the schema.\n\n    - Place your complete answer inside the correct field of the schema.\n\n    - Do not alter the schema structure.\n\n\n    User query: {query}'
prompt_and_model:  first=PromptTemplate(input_variables=['query', 'response_schema'], input_types={}, partial_variables={}, template='You are an expert in restaurant order request messages identification.\n\n\n    Your task:\n\n    - Identify if message is an order and not just an enquiry or miscellaneous message.\n\n    - Strictly adhere to the following schema for your response:\n\n    Schema:\n\n    {response_schema}\n\n\n    Important:\n\n    - Only return a JSON object based on the schema. Do not include any extra text, comments, or fields beyond the schema.\n\n    - Place your complete answer inside the correct field of the schema.\n\n    - Do not alter the schema structure.\n\n\n    User query: {query}') middle=[] last=ChatGroq(client=<groq.resources.chat.completions.Completions object at 0x78b54894c500>, async_client=<groq.resources.chat.completions.AsyncCompletions object at 0x78b54894d640>, temperature=0.1, model_kwargs={}, groq_api_key=SecretStr('**********'), max_tokens=8192)
RESPONSE:  {"order": "true", "other": "false"}
 '```' not in response
dictionary converted:  {'order': 'true', 'other': 'false'}
Response content dict:  {'order': 'true', 'other': 'false'}
decision:  {'order': 'true', 'other': 'false'} <class 'dict'>
Step 1: {
    "intergraph_agent": {
        "messages": [
            {
                "role": "ai",
                "content": "hi there, i would like to order one Kale & Quinoa Super Salad please"
            }
        ]
    }
}
Last message received in tool_order_message_items_parser_agent:  hi there, i would like to order one Kale & Quinoa Super Salad please
formatted_template:  Analyze user query: hi there, i would like to order one Kale & Quinoa Super Salad please. And choose the right tool that parses the different items from the order to have separate distinct names and quantities.
QUERY:  Analyze user query: hi there, i would like to order one Kale & Quinoa Super Salad please. And choose the right tool that parses the different items from the order to have separate distinct names and quantities. <class 'str'>
LLM with tool choice response:  content='' additional_kwargs={'tool_calls': [{'id': 'call_wfaa', 'function': {'arguments': '{}', 'name': 'order_message_items_parser'}, 'type': 'function'}]} response_metadata={'token_usage': {'completion_tokens': 11, 'prompt_tokens': 5055, 'total_tokens': 5066, 'completion_time': 0.04, 'prompt_time': 0.198864316, 'queue_time': 0.502176755, 'total_time': 0.238864316}, 'model_name': 'llama-3.3-70b-versatile', 'system_fingerprint': 'fp_76dc6cf67d', 'finish_reason': 'tool_calls', 'logprobs': None} id='run-6928b476-b373-4ee1-8c37-a18f539aca72-0' tool_calls=[{'name': 'order_message_items_parser', 'args': {}, 'id': 'call_wfaa', 'type': 'tool_call'}] usage_metadata={'input_tokens': 5055, 'output_tokens': 11, 'total_tokens': 5066} <class 'langchain_core.messages.ai.AIMessage'>
reponse tool call:  [{'name': 'order_message_items_parser', 'args': {}, 'id': 'call_wfaa', 'type': 'tool_call'}] <class 'list'>
Step 2: {
    "tool_order_message_items_parser_agent": {
        "messages": [
            {
                "content": "",
                "additional_kwargs": {
                    "tool_calls": [
                        {
                            "id": "call_wfaa",
                            "function": {
                                "arguments": "{}",
                                "name": "order_message_items_parser"
                            },
                            "type": "function"
                        }
                    ]
                },
                "response_metadata": {
                    "token_usage": {
                        "completion_tokens": 11,
                        "prompt_tokens": 5055,
                        "total_tokens": 5066,
                        "completion_time": 0.04,
                        "prompt_time": 0.198864316,
                        "queue_time": 0.502176755,
                        "total_time": 0.238864316
                    },
                    "model_name": "llama-3.3-70b-versatile",
                    "system_fingerprint": "fp_76dc6cf67d",
                    "finish_reason": "tool_calls",
                    "logprobs": null
                },
                "tool_calls": [
                    {
                        "name": "order_message_items_parser",
                        "args": {},
                        "id": "call_wfaa",
                        "type": "tool_call"
                    }
                ],
                "usage_metadata": {
                    "input_tokens": 5055,
                    "output_tokens": 11,
                    "total_tokens": 5066
                },
                "id": "run-6928b476-b373-4ee1-8c37-a18f539aca72-0",
                "role": null
            }
        ]
    }
}
formatted_template:  hi there, i would like to order one Kale & Quinoa Super Salad please
query:  hi there, i would like to order one Kale & Quinoa Super Salad please
calling llm
Prompt before call structured output:  input_variables=['query', 'response_schema'] input_types={} partial_variables={} template='You are an expert in restaurant order items parsing identifying their name and quantity ordered.\n\n\n    Your task:\n\n    - Identify how many items are in the order and their corresponding quantity. if no quantity indicated use 1 as default.\n\n    - Strictly adhere to the following schema for your response:\n\n    Schema:\n\n    {response_schema}\n\n    \n    Important:\n\n    - Only return a JSON object based on the schema. Do not include any extra text, comments, or fields beyond the schema.\n\n    - Place your complete answer inside the correct field of the schema.\n\n    - Do not alter the schema structure.\n\n\n    User query: {query}'
prompt_and_model:  first=PromptTemplate(input_variables=['query', 'response_schema'], input_types={}, partial_variables={}, template='You are an expert in restaurant order items parsing identifying their name and quantity ordered.\n\n\n    Your task:\n\n    - Identify how many items are in the order and their corresponding quantity. if no quantity indicated use 1 as default.\n\n    - Strictly adhere to the following schema for your response:\n\n    Schema:\n\n    {response_schema}\n\n    \n    Important:\n\n    - Only return a JSON object based on the schema. Do not include any extra text, comments, or fields beyond the schema.\n\n    - Place your complete answer inside the correct field of the schema.\n\n    - Do not alter the schema structure.\n\n\n    User query: {query}') middle=[] last=ChatGroq(client=<groq.resources.chat.completions.Completions object at 0x78b54894c500>, async_client=<groq.resources.chat.completions.AsyncCompletions object at 0x78b54894d640>, temperature=0.1, model_kwargs={}, groq_api_key=SecretStr('**********'), max_tokens=8192)
RESPONSE:  {
  'item_names': ['Kale & Quinoa Super Salad'],
  'item_quantities': [1],
  'item_ids': [1]
}
 '```' not in response
dictionary converted:  {'item_names': ['Kale & Quinoa Super Salad'], 'item_quantities': [1], 'item_ids': [1]}
Response content dict:  {'item_names': ['Kale & Quinoa Super Salad'], 'item_quantities': [1], 'item_ids': [1]}
parsed order items:  {'item_names': ['Kale & Quinoa Super Salad'], 'item_quantities': [1], 'item_ids': [1]} <class 'dict'>
tool call item parser outcome:  {"messages": [{"role": "tool", "content": "{\"success\": {\"item_names\": [\"Kale & Quinoa Super Salad\"], \"item_quantities\": [1], \"item_ids\": [1]}}"}]} <class 'str'>
Step 3: {
    "order_message_items_parser_tool_node": {
        "messages": [
            {
                "content": "{\"messages\": [{\"role\": \"tool\", \"content\": \"{\\\"success\\\": {\\\"item_names\\\": [\\\"Kale & Quinoa Super Salad\\\"], \\\"item_quantities\\\": [1], \\\"item_ids\\\": [1]}}\"}]}",
                "additional_kwargs": {},
                "response_metadata": {},
                "tool_calls": null,
                "usage_metadata": null,
                "id": "de619f51-8a43-49f9-84e6-d9aae5aacae5",
                "role": null
            }
        ]
    }
}
1:  {'messages': [{'role': 'tool', 'content': '{"success": {"item_names": ["Kale & Quinoa Super Salad"], "item_quantities": [1], "item_ids": [1]}}'}]} <class 'dict'>
['the mediterranean burger', 'grilled veggie & hummus wrap', 'chicken caesar wrap', 'turkey avocado flatbread', 'kale & quinoa super salad', 'mediterranean chickpea salad', 'citrus avocado salad', 'sweet potato fries', 'kale chips', 'fresh fruit cup', 'cold brew coffee', 'freshly squeezed juices', 'kombucha', 'herbal iced tea', 'fruit parfait', 'chia pudding', 'baked cinnamon apples', 'the mediterranean burger', 'grilled veggie & hummus wrap', 'chicken caesar wrap', 'turkey avocado flatbread', 'kale & quinoa super salad', 'mediterranean chickpea salad', 'citrus avocado salad', 'sweet potato fries', 'kale chips', 'fresh fruit cup', 'cold brew coffee', 'freshly squeezed juices', 'kombucha', 'herbal iced tea', 'fruit parfait', 'chia pudding', 'baked cinnamon apples', 'Kale & Quinoa Super Salad']
max_similar:  0.9584131836891174
idx: 4 - <class 'int'>
similarities: 0.9584131836891174 - <class 'torch.Tensor'>
menu_item_names: kale & quinoa super salad
Similarity_test_result score type :  0.9584131836891174 <class 'float'>  - Threshold:  0.7
Step 4: {
    "score_test_message_relevance_agent": {
        "messages": [
            {
                "role": "ai",
                "content": "{\"genuine_order\": [[\"Kale & Quinoa Super Salad\", 1]], \"not_genuine_order_or_missing_something\": []}"
            }
        ]
    }
}
Genuine_order:  [['Kale & Quinoa Super Salad', 1]] <class 'list'>
genuine order list
message sent successfully.
Step 5: {
    "send_order_to_discord_agent": {
        "messages": [
            {
                "role": "ai",
                "content": "{\"success\": \"Order message successfully sent to Discord.\"}"
            }
        ]
    }
}
genuine order list
Step 6: {
    "record_message_to_order_bucket_agent": {
        "messages": [
            {
                "role": "ai",
                "content": "{\"success\": \"Order message successfully recorded to database\"}"
            }
        ]
    }
}
Step 7: {
    "last_report_agent": {
        "messages": [
            {
                "role": "ai",
                "content": "{\"success\": \"{'success': 'Order message successfully recorded to database'}\"}"
            }
        ]
    }
}
'''
"""
print(data())
