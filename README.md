# GreenBite Burger Project
- Restaurant owner is receiving messages from `whatsapp`, `instagram dmns`, `text messages`... it is a mess
- The project is not focusing on those messages gathering but assumes that it has been already done in a `.csv` file.
- Here we start at the step when the agents are getting those messages listening to a database table
- We will be using a cronjob that will simulate messages arriving in the database record in a randomly timely way from our synthetic data
```bash
wc -l dataset_simulation_mix_messages_received.csv
# outputs: 
416 dataset_simulation_mix_messages_received.csv
# so here we are working with 415 rows of synthetic data, a mix of all different kind of messages that a restaurant owner could receive
```
- Agent will clasify the messages to filter out which ones are real order requests
- We will try to have the menu of the restaurant saved to a `memcached` cache as it won't change.
- Agent will classify messages as:
  - `genuine orders`
  - `fake order`
  - `not related to restaurant orders`
  - `offensive messages`
  - `order inquiries`
- There will be a discord server with different categories,
  receiving the notifications about enquiries, orders
  and what is relevant to have in the `Discord` server for the owner
  of the restaurant and his team to have access to those different groups
  with the permission set so the right staff can read messages coming from
  the right `Discord` channel category.
  And we will be using `Webhook` from agents to the `Discord` server of the restaurant.
- all the Discord server permission setup will be abstracted away but the webhook will be real to the `Creditizens` server.
- the database is `postgresql` as always, and will be more used as buckets for different tables to be accessed to by agents

## Dataset
This file `dataset_simulation_mix_messages_received.csv` has a mix of messages:
- fake orders
- real orders but asking for items that are not present in the menu
- offensive messages not related to orders
- real orders with items present in the menu
- more complex messages having order with items present and some not present in the menu

## Overall Plan
See `notes.md` for details:
- Classify messages as potential orders.
- Differentiate affirmative orders from inquiries.
- Parse and extract order details.
- Validate order items against the menu in cache.
- Register valid orders in the database.
- Send notifications via Discord.

## Agent Processing Overview
- Step 1: Polling & Initial Classification
The agent fetches new rows from this ReceivedMessages table and identifies potential orders by looking for order-related keywords (like “order:” or “I’d like to order”) and classifies messages accordingly.

- Step 2: Affirmation Check
It then distinguishes between affirmative orders and inquiries. For instance, messages ending in “?” (e.g. “Can I order a Mediterranean Burger with extra feta?”) would be flagged as inquiries rather than confirmed orders.

- Step 3: Structured Parsing & Menu Validation
For affirmative orders, the agent parses the message using structured output (e.g., extracting item names and modifiers) and then checks each ordered item against the menu stored in Memcached (using the menu’s item_name as key and description/price as value).

  - If every ordered item matches a menu item (e.g., “The Green Garden Vegan Burger” or “Grilled Chicken Avocado Burger”), the order is accepted.
  - If any item is invalid (e.g., “pork burger” or “double cheeseburger”), the order is rejected with an explanation.

- Step 4: Order Registration & Notification
Validated orders are written to the Orders table, and a separate node sends a Discord notification via webhook to alert the restaurant owner.

## Project Organization
- core `flask` app
- models to create database in `postgresql`
- agent file with the `nodes` and `edges` defined
- side folders will hold decouples agent librairies like `tools`, `prompts`, `llms`, `structured_output`, `app_utils`
- would be interesting to hava an tool using `aider` with its config on the side.. but not in the scope yet (`just good to have type`)
