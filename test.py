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
def run_command(cmd: List[str]):
  proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
  try:
    stdout, stderr = proc.communicate(timeout=int(os.getenv("PROCESS_TIMEOUT")))  # Ensure it doesn’t hang forever (5 mn)
  except subprocess.TimeoutExpired:
    proc.kill()  # Force stop if running too long
    return "error: process timeout"
    
  if proc.returncode != 0:
    return f"error: {stderr.strip()}"
  return stdout.strip()

if __name__ == "__main__":
  from helpers.check_for_bucket_new_message import fetch_bucket_saved_new_message
  while True:
    # this a list of new rows fetched from database
    new_rows = fetch_bucket_saved_new_message(os.getenv("LAST_MESSAGE_FETCHED_FROM_MESSAGES_BUCKET_ID_TRACKER"))
    time.sleep(30)

    # here we check that there is new rows and start agentic flow using subprocesses
    if new_rows:
      for row in new_rows:
        # catch errors
        try:
          # set env var for user initial query to be the message that will be fetched by the subprocess thread
          # in the special script to start agent which will get the message fromt he .vars.env file
          set_key(".vars.env", "USER_INITIAL_QUERY", row[1])
          load_dotenv(dotenv_path='.vars.env', override=True)

          # then start the agent. we do it like that we this is to decouple later as here we set the env var and get it when we could just pass the message directly
          user_query = os.getenv("USER_INITIAL_QUERY")

          # command need to be in a list with the first argument being the executable (here `python3`)
          commands = ["python3", "agentic_process_run.py"]

          # a little sleep moment so that the env var have time to update between messages
          # as new agentic flow starts with new message (prevent running same message in two different agentic workflows)
          time.sleep(0.5)
        
          # start the `subprocess` `ThreadPool` with max "3" workers executors for this tuto
          with concurrent.futures.ThreadPoolExecutor(max_workers=int(os.getenv("WORKERS"))) as executor:
            results = executor.map(run_command, [commands])

          # we return results as data is being processes
          for result in results:
            # we don't need to let the agent run to end if there is an error
            # we catch it promptly and stop the flow to be able to fail fats troubleshoot and fix the error
            if "error" in result:
              raise Exception(f"An error occurred while running the subprocess, agent result: {result}")
            # otherwise we keep printing the results
            print("Result: ", result)

        except Exception as e:
          print({"exception": f"An exception occured while running subprocess agentic workflow: {e}"})

  '''
  user_query = os.getenv("USER_INITIAL_QUERY")
  print(order_automation_agent_team(user_query))
  '''
