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
def store_db_menu_to_cache(db_table_name: str, ttl: int = int(os.getenv("TTL")), cache: memcache.Client = CACHE, conn: psycopg.Connection = CONN) -> str:
  '''
   description:
   will save th menu from db to longlived cache

  parameter:
  db_table_name str: name of the table storing the reaturant menu
  ttl int: integer value of the time to live in cache of the menu (6 months: `TTL="15770000000"`)
  cache memcache.Client: the connection client to memcache

  output:
  str confirmation that database menu has been saved to cache or message error if any
  '''
  # create dataframe using `read_sql_query` as using c/c++ under the hood (better performance) instead of `MenuItems.query.all() and then loop over rows..
  query = "SELECT item_name, description, price FROM menuitems"
  df = pd.read_sql_query(query, conn)
  try:
    for index, row in df.iterrows():
      # save to cache: key = `item_name` and value `description` and `price` with delimiter `;`
      cache_key = row.item_name.replace(" ", "_")
      print(cache_key)
      cache.set(cache_key, f"{row.description};{row.price}", time=ttl)
    print(f"Data added to cache: key:{row.item_name}, value:{row.description};{row.price}")
    return "The menu has been saved to cache successfully."

  except Exception as e:
    return f"An error occured while trying to save menu  to cache: {e}"

if __name__ == "__main__":
  store_menu_to_cache = store_db_menu_to_cache(MenuItems, int(os.getenv("TTL")), CACHE)
  print(store_menu_to_cache)
