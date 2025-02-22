# this script will save the menu fetching it from the database and store it to cache with long lived `TTL`
import os
import json
import time
import random
import psycopg
import pandas as pd
from postgresql_tables_creations import (
  # db, # here not using this way using psycopg3 directly
  MenuItems,
)
import memcache
from datetime import datetime
from dotenv import load_dotenv, set_key

load_dotenv(dotenv_path='.vars.env', override=True)
# Connecting using Memcached `Client`
CACHE = memcache.Client(['127.0.0.1:11211'], debug=1)

# extra vars
menu_items_table_name = os.getenv("MENU_ITEMS_TABLE_NAME")
# if want more that 30 days need to use `time.time() * 180 * 24 * 60 * 60` (6 months)
# as when more than 30 days the seconds are seen as Unix values and will fail so use `time.time()` and calculate
time_to_live = int(os.getenv("TTL"))

# get env var for database connection
hostname = os.getenv("DBHOST")
port = os.getenv("DBPORT")
database = os.getenv("DBNAME")
username = os.getenv("DBUSER")
password = os.getenv("DBPASSWORD")

# Create a raw connection using psycopg2
CONN = psycopg.connect(
    host=hostname,
    port=port,
    dbname=database,
    user=username,
    password=password
)

print("type conn: ", type(CONN))
def store_db_menu_to_cache(db_table_name: str = os.getenv("MENU_ITEMS_TABLE_NAME"), ttl: int = int(os.getenv("TTL")), cache: memcache.Client = CACHE, conn: psycopg.Connection = CONN) -> str:
  '''
   description:
   will save th menu from db to longlived cache

  parameter:
  db_table_name str: name of the table storing the reaturant menu
  ttl int: integer value of the time to live in cache of the menu
  cache memcache.Client: the connection client to memcache

  output:
  str confirmation that database menu has been saved to cache or message error if any 
  '''
  # create dataframe using `read_sql_query` as using c/c++ under the hood (better performance) instead of `MenuItems.query.all() and then loop over rows..
  query = f"SELECT * FROM {db_table_name}"
  df = pd.read_sql_query(query, conn)
  store_key_to_env = []
  try:
    count = 0
    for index, row in df.iterrows():
      # save to cache: key = `item_name` and value `description` and `price` with delimiter `;`
      cache_key = row.item_name.strip().replace(" ", "_").lower()
      print(cache_key)
      cache_value = f"{row.description.strip()};{row.price.strip()}".lower()
      print("cache value formatted: ", cache_value)
      cache.set(cache_key, cache_value, time=ttl)
      # we will make those key available for agents to check agains those for similarity test. will be saved to env and json.dumps/loads way
      store_key_to_env.append(cache_key)      
      count += 1

    # save keys to environment variables for agents to have the list available and check against it for similarity test
    set_key(".vars.env", "CACHE_KEYS", json.dumps(store_key_to_env))
    load_dotenv(dotenv_path='.vars.env', override=True)

    #print("Cache keys list: ", store_key_to_env)
    print(f"Batch processes successfully: {count} data points have been added to cache.")
    # print(f"\n\nTest cache get 'baked_cinnamon_apples' key: {cache.get('baked_cinnamon_apples')}")
    return "The menu has been saved to cache successfully."

  except Exception as e:
    return f"An error occured while trying to save menu  to cache: {e}"


if __name__ == "__main__":
  
  store_menu_to_cache = store_db_menu_to_cache(menu_items_table_name, time_to_live, CACHE, CONN)
  print(store_menu_to_cache)

