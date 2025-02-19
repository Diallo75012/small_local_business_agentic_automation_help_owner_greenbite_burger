# file to test python different code snippets before incorporating those in app
# advantage here is that we are not altering the original `.csv` file but fetching from it what is new
# we then keep record of the row number so that next fetching will check beyond that row
import os
import json
import time
import random
import pandas as pd
from dotenv import load_dotenv, set_key

load_dotenv(dotenv_path='.vars.env', override=True)

MESSAGE_INDEX_TRACKER = json.loads(os.getenv("MESSAGE_INDEX_TRACKER"))
print("Message index tracker env var value: ", MESSAGE_INDEX_TRACKER, type(MESSAGE_INDEX_TRACKER))
  
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
