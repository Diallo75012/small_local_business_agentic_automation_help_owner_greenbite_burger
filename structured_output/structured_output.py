message_interpreter_order_or_other_schema={
  "order": "answer 'true' if it is an order otherwise 'false'. make sure it is valid JSON str.",
  "other": "answer 'true' if it is not an order otherwise 'false'. make sure it is valid JSON str."  
}

#order_message_items_parser_schema={
# "item_names": "a list containing strictly the names of the item order identified in the message. make sure it is valid JSON str.", 
# "item_quantities": "a list containing strictly respective to items_names, the quantities numbers requested for each item_names list. 1 is default if no quantity is mentioned in the order. make sure it is valid JSON str.", 
# "id": "a list containing strictly respective to item_names the count number of that item if more than one item identified in the order so that we can count those later, start at 1 and increment by 1 at every new items_names. make sure it is valid JSON str.", 
#}

order_message_items_parser_schema={
  "item_names": "An array of strings representing the names of the ordered items.",
  "item_quantities": "An array of integers representing the quantity for each item (default to 1 if not specified).",
  "item_ids": "An array of integers, where each number is a sequential identifier for the ordered items, starting at 1."
}


message_classification_schema={
  "order": "answer with only one word. 'true' if it is a genuine order otherwise 'false'. if this field is equal to 'true' all others should be 'false'. make sure it is valid JSON str.",
  "enquiry": "answer with only one word. 'true' if it is not an order but a genuine enquiry otherwise 'false'. if this field is equal to 'true' all others should be 'false'. make sure it is valid JSON str.",
  "miscellaneous": "answer with only one word. 'true' if you consider the message as being offensive or out of the restaurant concerns or miscellaneous, otherwise 'false'. alsways 'true' by default, unless message fits the other fields or 'order' or 'enquiry'. if this field is equal to 'true' all others should be 'false'. make sure it is valid JSON str.",
}
