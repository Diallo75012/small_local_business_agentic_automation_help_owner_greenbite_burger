# `messages_from_csv_frequent_fetcher.py`: will get message and save those to database simulating incoming messages. Then will save last index row fetched in `.vars.env` so that next time it fetches again it will start from new messages if any.
import os
import json
import time
import random
import pandas as pd
from postgresql_tables_creations import (
  db,
  Messages,
)
from datetime import datetime
from dotenv import load_dotenv, set_key


load_dotenv(dotenv_path='.vars.env', override=True)

# helper that will be called to set the frequency fetching time for messages stored to db
def waiting_time(start: float = float(os.getenv("START_TIME_SECONDS_RANGE")), end: float = float(os.getenv("END_TIME_SECONDS_RANGE"))):
  simulating_waitng_next_message = time.sleep(random.uniform(start, end))
  print("simulating_waitng_next_message: ", simulating_waitng_next_message)
  pass


def fetch_messages_and_store(messages_received_csv_file: str = os.getenv("MESSAGES_RECEIVED_CSV_FILE"), message_index_tracker: int = int(os.getenv("MESSAGE_INDEX_TRACKER"))) -> str:
  '''
    description:
    will fetch all messages from the `.csv` file and use the previous index where it has stopped fetching messages and continue from there storing to database messages

    parameters:
    messages_received_csv_file str: the `.csv` file having all messages received by owner simulating gathering of `whatsapp` messages and `Instagram` DMs and `SMS` messages

    output:
    str validating that messages have been correctly stored to database or error if anything happens
  '''
  try:
    # be careful indexes are type nympy.in64 so save those as str() to env var to avoid errors and use the `.vars.env` `MESSAGE_INDEX_TRACKER` to start fetching from there
    #df = pd.read_csv(messages_received_csv_file)[message_index_tracker:]
    #print("head df:\n", df.head(), "; len: ", len(df))
    # for testing with webui
    df = pd.read_csv(messages_received_csv_file)[message_index_tracker:10]
    print(f"Len df: {len(df)}")

    # check if `df` has new messages otherwise just return to wait
    if df.empty:
      return "empty: no new messages yet..."

    # start looping over row and updating `.vars.env` index of last message treated
    for index, row in df.iterrows():
      if message_index_tracker == len(df):
        return "success: all new incoming messages have been stored for AI agent next workload."
      if index > 0:

        # 10.5s to 20.5s before adding row
        waiting_time(float(os.getenv("START_TIME_SECONDS_RANGE")), float(os.getenv("END_TIME_SECONDS_RANGE")))

        # prepare message to be saved in db
        new_message = Messages(dfidx=index, date=row.timestamp, message=row.message)
        db.session.add(new_message)
        db.session.commit()
        print(f"Data added to db: ", "index: ", index, "timestamps: ", row.timestamp, "messages: ", row.message)

        # save index to `.vars.env`
        set_key(".vars.env", "MESSAGE_INDEX_TRACKER", str(index))
        load_dotenv(dotenv_path='.vars.env', override=True)
        print("MESSAGE_INDEX_TRACKER: ", os.getenv("MESSAGE_INDEX_TRACKER"))
      message_index_tracker = int(index)
    return f"success: {len(df)} new messages have been added to the database. Last index was: {os.getenv('MESSAGE_INDEX_TRACKER')}"

  except Exception as e:
    return f"error: An error occured while trying to fetch new incoming messages and save those to database: {e} - {repr(e)}"

'''
if __name__ == "__main__":

  print(
    fetch_messages_and_store(
      os.getenv("MESSAGES_RECEIVED_CSV_FILE"),
      int(os.getenv("MESSAGE_INDEX_TRACKER"))
    )
  )
'''
