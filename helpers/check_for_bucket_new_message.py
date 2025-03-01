# `messages_from_bucket_frequent_fetcher.py`: will be going to check if new messages are present in the bucket of `Messages` and then if any start the agentic workflow to threat those messages.
import os
import json
import time
import random
import pandas as pd
# here i will use psycopg3 to connect to db and run queries as `flask-psql` i don't like it finally
import psycopg
from postgresql_tables_creations import (
  Messages,
)
from sqlalchemy import text
from dotenv import load_dotenv, set_key


load_dotenv(dotenv_path='.vars.env', override=True)

# Retrieve database connection parameters from environment variables
hostname = os.getenv("DBHOST")
port = int(os.getenv("DBPORT"))
database = os.getenv("DBNAME")
username = os.getenv("DBUSER")
password = os.getenv("DBPASSWORD")
conn_info = f"postgresql://{username}:{password}@{hostname}:{port}/{database}"

def fetch_bucket_saved_new_message(last_message_id_tracker: str = os.getenv("LAST_MESSAGE_FETCHED_FROM_MESSAGES_BUCKET_ID_TRACKER")) -> list:
  '''
    description:
    will fetch all new messges from database and keep track of the id to start next fetching task from the same place

    parameters:
    last_message_id_tracker str: the id of the last new message 'id' that have been fetched from the bucket
    
    output:
    list: the new message or messages as we use `fetchall()` it will be a list of tuples
  '''
  try:
    query = """
    SELECT id, message FROM Messages
    WHERE id > %s
    ORDER BY id DESC;
    """
    with psycopg.connect(conn_info) as conn:
        with conn.cursor() as cur:
            cur.execute(query, (last_message_id_tracker,))
            # `fetchall()` returns a list  of tuples if we have many or one so it is good for us
            rows = cur.fetchall()

    if rows:
      latest_row = rows[0][0]
      set_key(".vars.env", "LAST_MESSAGE_FETCHED_FROM_MESSAGES_BUCKET_ID_TRACKER", str(latest_row))
      load_dotenv(dotenv_path='.vars.env', override=True)
      print(f"last id: {latest_row}; fetched new messages for agent: {rows}")
    else:
      print("No new messages for agent... please check later...")

    return rows

  except Exception as e:
    return f"error: An error occured while trying to fetch for new messages to database: {e}"


'''
if __name__ == "__main__":
  while True:
    print(fetch_bucket_saved_new_message(os.getenv("LAST_MESSAGE_FETCHED_FROM_MESSAGES_BUCKET_ID_TRACKER")))
    time.sleep(30)
'''
