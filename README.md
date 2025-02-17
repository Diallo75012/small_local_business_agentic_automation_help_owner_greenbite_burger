
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
