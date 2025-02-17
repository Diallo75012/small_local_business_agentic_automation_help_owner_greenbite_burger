# Database Schema Design


## Restaurant Meny Schema
1. Table: MenuCategories
This table stores broad categories to group menu items.

- Columns:
  - category_id (Primary Key, Integer)
  - category_name (String; e.g., "Burgers", "Wraps", "Salads", "Sides", "Drinks", "Desserts")
  - description (String; optional description of the category)


2. Table: MenuItems
This table stores each menu item with detailed attributes.

- Columns:
  - item_id (Primary Key, Integer)
  - category_id (Foreign Key to MenuCategories)
  - sub_category (Optional String; e.g., under Burgers, you might have "Vegan", "Poultry", "Signature")
  - item_name (String; e.g., "The Green Garden Vegan Burger")
  - description (String; detailed description of the item)
  - ingredients (String or JSON; list of ingredients for parsing and matching)
  - price (Decimal; price of the item)
  - calories (Integer; optional nutritional info)
  - dietary_tags (String or JSON; list of tags such as "Vegan", "Gluten-Free", "High Protein")
  - availability (Boolean or Enum; e.g., "Available", "Seasonal", "Out of Stock")
  - created_at (Timestamp; when the item was added/updated)

## Final Messages Classification Tables
1. Messages Table
- Columns:
  - timestamp (DateTime)
  - message (Text)

This table collects all incoming messages.


2. Orders Table
- Columns:
  - order_id (Primary Key)
  - timestamp (DateTime)
  - order_details (Structured data, e.g. JSON with extracted items)

This table will only store messages classified as affirmative orders (i.e., confirmed orders).


3. Enquiries Table
- Columns:
  - Inquiry_id (Primary Key)
  - timestamp (DateTime)
  - enquiry_details (Text/structured data)

This table will get messages that look like orders but are not classified as so (eg.: quesitons about orders...)
