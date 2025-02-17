
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
