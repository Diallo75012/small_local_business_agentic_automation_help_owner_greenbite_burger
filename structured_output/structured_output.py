message_interpreter_order_or_other_schema={
  "order": "answer 'true' if it is an order otherwise 'false'",
  "other": "answer 'true' if it is not an order otherwise 'false'"  
}

message_classification_schema={
  "order": "answer with only one word. 'true' if it is a genuine order otherwise 'false'. if this field is equal to 'true' all others should be 'false'",
  "enquiry": "answer with only one word. 'true' if it is not an order but a genuine enquiry otherwise 'false'. if this field is equal to 'true' all others should be 'false'",
  "miscellaneous": "answer with only one word. 'true' if you consider the message as being offensive or out of the restaurant concerns or miscellaneous, otherwise 'false'. alsways 'true' by default, unless message fits the other fields or 'order' or 'enquiry'. if this field is equal to 'true' all others should be 'false'",
}
