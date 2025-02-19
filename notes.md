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

# diagram
- minimal diagram very high level: [diagram](https://excalidraw.com/#json=iJCmbJ1I0pwlXhDENCmzw,bxkB1DpYXkZA3WPuNWwNZg)

# Next
- [] do script that adds to the database news records coming from the `dataset_cleaned`
     (we are not going to use cronjob but a script that will be launched and run sleeping sometimes and having random number generator
     for how many messages are added to the database)
- [] have agent starting flow by tracking the incremental id of the messages table and would save the last id in the `,vars.env`
     so it has to `order desc` those ids and take whatever is more than that id. if empty it stops, it anay, it work on each row, one by one.
