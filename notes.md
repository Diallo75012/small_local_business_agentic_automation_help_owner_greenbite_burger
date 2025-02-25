# Project Architecture Results From Brainstorming

## Overall Architecture

1. Synthetic Dataset Generation:

- A CSV (or similar) contains two columns: timestamp and message.

- Messages include a mix of:
  - Affirmative Orders: e.g., “I’d like to order The Green Garden Vegan Burger with extra avocado.”
  - Inquiries/Questions: e.g., “Can I order a pork burger with bacon?”
  - Customer Service/Other Messages: e.g., “Where can I pick up my order?” or “What items are available today?”


2. Database Ingestion via Cron Job:

- A cron job randomly adds batches of these messages into the ReceivedMessages table in your database.
- Batches can vary in size (1 message, 2 messages, 8 messages, etc.) to simulate real-world incoming traffic.


3. Agent Node Workflow (Polling the Database):

  A. Polling & Initial Classification Node:

    - The agent node periodically checks for new rows in the ReceivedMessages table.
    - It uses NLP-based keyword checks to classify messages as potential orders versus general inquiries or noise.

  B. Affirmation Classification Node:

    - Among the potential orders, the agent distinguishes between:
      - Affirmative Orders: Clearly stating an intent (e.g., “I’d like to order…”).
      - Inquiries: Messages ending with a “?” or phrasing that signals a question rather than a confirmed order.
    - Only affirmative orders move forward; inquiries are logged separately to avoid triggering production orders.

  C. Structured Output Parsing Node:

    - For affirmative orders, the agent uses an LLM (or other NLP tools) with a structured output prompt to extract order details (e.g., item names, quantity, any modifications).
    - Example output might be a JSON like:
    ```json
    {
      "ordered_items": [
        {"item": "The Green Garden Vegan Burger", "modifiers": "extra avocado"},
        {"item": "Sweet Potato Fries", "modifiers": ""}
      ]
    }
    ```
  D. Menu Validation Node (Using Memcached):

    - The validated menu is stored in Memcached as key-value pairs where:
      - Key: The canonical item_name.
      - Value: A concatenated string including description and price, delimited (for example, “The Green Garden Vegan Burger|A 100% plant-based patty with fresh veggies...|9.95”).

    - The agent node takes the structured output and uses the full menu context (from Memcached) to check each extracted item:
      - Direct Matching: Compare the extracted item name with the keys in Memcached.
      - Contextual Check: Optionally, use the description (or an embeddings similarity check) if there’s variation in naming.

    - If every ordered item matches an item in the menu, the order is validated. Otherwise, the agent either rejects the order entirely (and possibly sends a message like “Sorry, we don’t offer pork or double cheeseburgers”) or flags it for manual review.

  E. Order Registration Node:

    - Validated orders are then recorded in a dedicated Orders table.
    - This table stores details like a unique order ID, timestamp, and the structured order details.

  F. Notification Node:

    - Another agent node listens for changes in the Orders table.
    - Upon detecting a new order, it triggers a Discord webhook that sends a notification (with order details) to the restaurant owner.

### Key Considerations
- Storing the Menu:

  - Primary Storage: The full, authoritative menu is stored in a database as the source-of-truth.
  - Cache Layer: Memcached is used to store the menu’s item_name and description/price concatenated values. This ensures quick lookup during the order validation phase without overloading the database.

- Matching Logic:

  - For most cases, direct string matching on item_name may suffice.
  - If customer orders include variations, adding the description in the context (or using embeddings-based similarity) can help capture those variations and ensure accurate matching.
  - For complex orders with multiple items, the agent checks each item individually. If any item does not match, the entire order can be flagged as invalid.

- Workflow Separation:

  - By separating the nodes (initial classification, affirmation check, parsing, menu validation, registration, notification), the system is modular. This makes it easier to teach students the importance of planning and structuring data flows for real-world automation.

### Overall
- Classify messages as potential orders.
- Differentiate affirmative orders from inquiries.
- Parse and extract order details.
- Validate order items against the menu in cache.
- Register valid orders in the database.
- Send notifications via Discord.


# Python-MemCached
```python
import memcache


# Connecting to Memcached
mc = memcache.Client(['127.0.0.1:11211'], debug=1)
# how to get value:
mc.get("<Your_cache_key>")
# how to set key/value pairs
mc.set("<Your_cache_key>", "<Your_cache_value>", time=<how long in second do we keep it in cache in seconds>)
```

# flask-pgsql
We have chosen to use this library this time to make a standalone connection to `postgresql`
- How to use:
```python
# example creating tables (need to create the models first)
db.create_all()
# or you can recreate any special table
# USERS.create()
# BLOGS.create()

# example query
users = USERS.query.all()
user = USERS.query.get(id=12)

# example adding data
new_user = USERS(username="example_user")
db.session.add(new_user)
db.session.commit()

# example deleting Data
user_to_delete = USERS.query.get(id)
user_to_delete.delete()
db.session.commit()
```

# cleaning the dataset which had duplicates
```python
# install pandas
import pandas as pd


df = pd.read_csv("dataset_simulation_mix_messages_received.csv")
df.drop_duplicates(subset=["message"], keep="first", implace=True, ignore_idex=True)
df.drop_duplicates(subset=["message"], keep="first", inplace=True, ignore_index=True)
len(df)
156
df.to_csv("dataset_cleaned.csv", index=False) 
```

**be carefull**
- if running several instances like you have installed one `sudo apt install memcached`
  and you have another one which is a `python` one running from your virtual environment,
  you might face errors not finding the cache key/value when using the terminal eg.:`echo "get the_green_garden_vegan_burger" | nc localhost 11211`
  In this case, you might want to just use the programatic way in a python script to check if data has been cached properly using `cache.get(<key>)`

# diagram
- minimal diagram very high level: [diagram](https://excalidraw.com/#json=iJCmbJ1I0pwlXhDENCmzw,bxkB1DpYXkZA3WPuNWwNZg)

# Next
- [x] do script that adds to the database news records coming from the `dataset_cleaned`
     (we are not going to use cronjob but a script that will be launched and run sleeping sometimes and having random number generator
     for how many messages are added to the database)
- [] have agent starting flow by tracking the incremental id of the messages table and would save the last id in the `,vars.env`
     so it has to `order desc` those ids and take whatever is more than that id. if empty it stops, it anay, it work on each row, one by one.

# random in Python
- integers: 
```python
# in a range of intergers get interger
random.randint(0, 10)
# in a range with steps
random.ranrange(0, 10, 2)
```

- floats:
```python
# get random float number from 0 to 1
random.random()
# get float number from custom float range
random.uniform()
```

# issue with column for date
`date` column is a `date` type even if the model is using `db.DateTime` the time gets truncated and only the date is saved
```psql
restaurantdb=# SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'messages';
 column_name |     data_type     
-------------+-------------------
 id          | integer
 dfidx       | integer
 date        | date
 message     | character varying
(4 rows)
```
- need to change the column type to `timestamp` instead of `date`
to fix that had to modify the script that creates the tables and import `from sqlalchemy import DateTime`
then use for all date fields: `DateTime(timezone=False)`
- but then `sqlalchemy` way of using `DateTime` is not compatible with `flask-postgresql` python library way which expects his how `db.DateTime`:
```bash
   class Messages(db.Model):
  File "/home/creditizens/resturant_automation/greenbite_burger/postgresql_tables_creations.py", line 33, in Messages
    date = db.Column(DateTime(timezone=False), nullable=False) # if issue with DateTime just use `String(50)`
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/creditizens/resturant_automation/.venv/lib/python3.12/site-packages/flask_postgresql/__init__.py", line 142, in Column
    return (data_type.__name__,primary_key,nullable,unique,default, array)
            ^^^^^^^^^^^^^^^^^^
AttributeError: 'DateTime' object has no attribute '__name__'. Did you mean: '__ne__'?
```
- fixing this by just using `Timestamp` instead of `DateTime` and was lucky as ChatGPT didn't know and internet search not well documented. Did by using `GoKu Ultrainstinct`:
```python
date = db.Column(db.Timestamp, nullable=False)
```
- command to check
```psql
restaurantdb=# SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'messages';
 column_name |          data_type          
-------------+-----------------------------
 id          | integer
 dfidx       | integer
 date        | timestamp without time zone
 message     | character varying
(4 rows)
```

# Memcache for question answers instead of redis
- install memcached on ubuntu
```bash
sudo apt update
sudo apt install memcached
```
# systemctl start
```bash
sudo systemctl start memcached
```
# manual start 
```bash
memcached -d -m 64 -l 127.0.0.1 -p 11211
-d:		Run as a daemon.
-m 64:		Use 64MB of memory.
-l 127.0.0.1:	Listen only on localhost.
-p 11211:	Use port 11211 (default Memcached port).
source: https://medium.com/@netfluff/memcached-for-django-ecedcb74a06d
```
# python client to interact with memcached server
```python
pip install python-memcached
```
# set cache with ttl
```python
import memcache

# eg. Connecting to Memcached
cache = memcache.Client(['127.0.0.1:11211'], debug=1)
# eg. to get cache values
cache_key = "junko_shibuya_mangakissa"
chat_messages = cache.get(cache_key)
if not chat_messages:
  cache.set(cache_key, list(chat_messages), time=3600)
# eg. to set cache key vaklue
cache.set(cache_key, data, cache_time)
```

# Update logic caching and how data wil flow and fetching
- excalidraw link: [diagram with zoom in cache system](https://excalidraw.com/#json=XiSlkWmusKgpEdXS-DH6z,LIIGLgnbw-Fqi_I09hcaGQ)

1. from `menu.csv` data is saved to database using `pandas` and `python-postgresql`
2. from `postgresql`, menu is stored to cache and a list of the keys corresponding to column `name` is svaed in `.vars.env`
3. agent get user message and create a structured output which will separated the item required, so different items with quantity
4. item names are checked against the list of keys for similarity using the `Alibaba-NLP/gte-modernbert-base` model on the fly
5. keys passing threshold will be sent to next agent, if no key the message will be reclassified as enquiry and deleted from `order` database table and recorded in `enquiries` table.
6. so next agent will receive one or more keys (two best scored keys max) and will get the value description and price from cache for each and be sent the full line of the order request. Then it will return a structured output which will be telling us the order, the description and the price and why.
7. next agent will be sending notification to discord `order` category so that staff with permission to read that one will be notified to prepare the order.

# code examples to create out scripts to save data to db
```python
import os
import json
import time
import random
import pandas as pd
from dotenv import load_dotenv, set_key

load_dotenv(dotenv_path='.vars.env', override=True)

MESSAGE_INDEX_TRACKER = json.loads(os.getenv("MESSAGE_INDEX_TRACKER"))
print("Message index tracker env var value: ", MESSAGE_INDEX_TRACKER, type(MESSAGE_INDEX_TRACKER))
```
```python
# test sleep get data output frequently using `random.uniform(range)`
data = ["hello", "Shibuya", "here", "the", "world"]

for elem in data:
  number = random.uniform(0.01, 0.9)
  time.sleep(number)
  print(f"time:{number} - {elem}")
```
```python
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
```
```python
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
```

# Next
- [x] create a module with function that handles the `Alibaba Bert nlp` model similarity checker
- [x] create a script that saves the menu to database and saved the database content to cache
- [x] create the first agent that checks the messages if orders or not and send to other agents:
  - [x] agent that treat orders and creates structured output of the order
  - [] agent that classified messages as miscellaneous or order inquiry
- [] have agent starting flow by tracking the incremental `dfidx` of the messages table and would save the last `dfidx` in the `,vars.env`
     so it has to `order desc` those ids and take whatever is more than that id. if empty it stops, it anay, it work on each row, one by one.
- [] create the logic of that agent which works only with the orders and would create a notification to the discord group for `Orders`
     and checks time in the day to create a csv of orders only.
- [] have another agentic flow starting with a subprocess that record logs of steps
     and that will work on the messages filtered as not behing orders and classify those and store those to the corresponding database.

# Similarity search lesson learned for tensors and how to get value score standalone and indexin list
```python
import os
# Requires transformers>=4.48.0
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim


input_texts = [
    "what is a manga kissa?",
    "Is Hachiko story real? did he have a piece of paper and a pen next to Shibuya JR station?",
    "I like Udon from Kyushu.",
    "where is the manga kissa?",
    "what is a manga kissa coffee?",
    "I love udon from Kyushu",
    "It is the story of someone waiting at JR station, next to Hachiko with a pen paper."
]

# dimension of `Alibaba-NLP/gte-modernbert-base` embeddings is `768`
model = SentenceTransformer("Alibaba-NLP/gte-modernbert-base")
embeddings = model.encode(input_texts)
#print(embeddings.shape)


similarities = cos_sim(embeddings[1], embeddings[:1])
similarities2 = cos_sim(embeddings[1], embeddings[2:])
print(similarities[0][0].nonzero(as_tuple=True)[0].item(), input_texts[similarities[0][0].nonzero(as_tuple=True)[0].item()])
print(similarities2[0][4].item())
# outputs slowly evolving as we dig, last output is what we want corresponding to above code:
- first test -> print(similarities) and print(similarities2):
tensor([[0.5441]]) # raw printing of similarity scores
tensor([[0.5830, 0.5792, 0.5680, 0.5815, 0.8452]])
- second test -> print(similarities[0][0]) and print(similarities2[0][4]):
tensor(0.5441) # getting targetting values using normal python list indexing
tensor(0.8452)
- third test -> print(similarities[0][0]) and print(similarities2[0][4].item())
tensor(0.5441)
0.8452041149139404 # getting the value in `tensor()` using `.item()`
- fourth test -> print(similarities[0][0].nonzero(as_tuple=True)[0]) and print(similarities2[0][4].item()):
tensor([0]) # getting the index using `.nonzero(as_tuple=True)[0]`
0.8452041149139404
- fifth test -> print(similarities[0][0].nonzero(as_tuple=True)) and print(similarities2[0][4].item()):
(tensor([0]),) # checking how the tuple looks like
0.8452041149139404
- seventh test -> print(similarities[0][0].nonzero(as_tuple=True)[0].item()) and print(similarities2[0][4].item()):
0 # getting the value of the index isolated out form `tensor()` by combining `.item()` to `.nonzero(as_tuples=True)[0]`
0.8452041149139404
- last test -> print(similarities[0][0].nonzero(as_tuple=True)[0].item(), input_texts[similarities[0][0].nonzero(as_tuple=True)[0].item()]) and print(similarities2[0][4].item()):
0 what is a manga kissa? # using the index to now print the target text that correspond to score
0.8452041149139404
```


# TTL issue
when `TTL` is greater than 30 days the time is interpreted as `Unix` timestamp so you need to use calculation like:
```python
ttl = int(time.time() + 180 * 24 * 60 * 60)
```

# watchdog doc
- if wanted in the future to use watchdog that will trigger agent whenever `.csv` file is changed so lines are added for example.
[watchdoc events handler for file change](https://pythonhosted.org/watchdog/api.html?highlight=modified#watchdog.events.FileSystemEventHandler.on_modified)

# errors with tool calls
- error: **ValueError: Invalid input type <class 'dict'>. Must be a PromptValue, str, or list of BaseMessages**
  Make sure you are not mixing up the `ToolNode()` with the other llm which is a `bind_tools()`
- error: **tool_call[id]**
  When you see those errors change the LLM as some are not tool friendly. 

# issue with states messages being accessed from tools functions
```python
@tool
def <Your_Tool_Function>(<Your_Arguments>, state: MessagesState):
  # this is how you get all those messages, then use `[-1]` for last message fro eg.
  current_messages = state.get_all_messages()
```


