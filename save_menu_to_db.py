# this is a script to run under the python3.12 virtual env activated with all `requirements.txt` installed
# this script will save to database the menu fromt he `.csv` file (run it once), another script will be run to store menu from database to cache
import os
import json
import time
import random
import pandas as pd
from postgresql_tables_creations import (
  db,
  MenuItems,
)
from datetime import datetime
from dotenv import load_dotenv, set_key


load_dotenv(dotenv_path='.vars.env', override=True)

def store_menu_csv_to_db(menu_csv_file: str = os.getenv("MENU_CSV_FILE")) -> str:
  '''
   description:
   while save the static menu to the database item by item

  parameter:
  menu_csv_file str: name of the menu `.csv` file

  output:
  str confirmation of menu saved or error message if any issues
  '''
  df = pd.read_csv(menu_csv_file)
  print("DF: ", df)
  try:
    for index, row in df.iterrows():
      print("Row: ", row)
      print("index: ", index)
      # prepare message to be saved in db
      menu_item = MenuItems(item_name=row.item_name, description=row.description , price=row.price)
      db.session.add(menu_item)
    db.session.commit()
    print(f"Data added to db: ", "item_name: ", row.item_name, "description: ", row.description, "price: ", row.price)
    return "The menu has been saved to database successfully."

  except Exception as e:
    return f"An error occured while trying to save menu in database: {e}"

'''
if __name__ == "__main__":
  store_menu = store_menu_csv_to_db(os.getenv("MENU_CSV_FILE"))
  print(store_menu)
'''
