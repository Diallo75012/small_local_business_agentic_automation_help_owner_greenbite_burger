'''
This script will run the thread process that will run the agentic workflow for the message to work on
'''
import os
import json
from dotenv import load_dotenv
from helpers.messages_csv_frequent_fetcher_db_storer import fetch_messages_and_store


load_dotenv(dotenv_path='.vars.env', override=True)

def run_simulation_incoming_messages():
  try:
    # will return a str containing: `success`, `empty` or `error`
    new_messages_incoming_result = fetch_messages_and_store(os.getenv("MESSAGES_RECEIVED_CSV_FILE"), int(os.getenv("MESSAGE_INDEX_TRACKER")))
    print("new_messages_incoming_result: ", new_messages_incoming_result)
    if "success" in new_messages_incoming_result:
      print("success new incoming messages fetched")
      return new_messages_incoming_result
    elif "empty" in new_messages_incoming_result:
      print("empty no new messages")
      return new_messages_incoming_result
    else:
      # here mean that there is an `error`
      print("an error probably occurred")
      return new_messages_incoming_result

  except Exception as e:
    return json.dumps({"exception": f"An exception occurred while trying to check incoming new message: {e}"})



if __name__ == "__main__":
  run_simulation_incoming_messages()
