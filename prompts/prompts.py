message_interpreter_order_or_other_prompt = {
  "system": {
    "template":  """You are an expert in restaurant order request messages identification.\n

    Your task:\n
    - Identify if message is an order and not just an enquiry or miscellaneous message.\n
    - Strictly adhere to the following schema for your response:\n
    Schema:\n
    {response_schema}\n

    Important:\n
    - Only return a JSON object based on the schema. Do not include any extra text, comments, or fields beyond the schema.\n
    - Place your complete answer inside the correct field of the schema.\n
    - Do not alter the schema structure.\n

    User query: {query}""",
    "input_variables": {}
  },
  "human": {
    "template": "{message}",
    "input_variables": {"message": "",}
  },
  "ai": {
    "template": "",
    "input_variables": {}
  },
}

order_message_items_parser_prompt = {
  "system": {
    "template":  """You are an expert in restaurant order items parsing identifying their name and quantity ordered.\n

    Your task:\n
    - Identify how many items are in the order and their corresponding quantity. if no quantity indicated use 1 as default.\n
    - Strictly adhere to the following schema for your response:\n
    Schema:\n
    {response_schema}\n
    
    Important:\n
    - Only return a JSON object based on the schema. Do not include any extra text, comments, or fields beyond the schema.\n
    - Place your complete answer inside the correct field of the schema.\n
    - Do not alter the schema structure.\n

    User query: {query}""",
    "input_variables": {}
  },
  "human": {
    "template": "{message}",
    "input_variables": {"message": "",}
  },
  "tool_call_choice": {
    "template": "Analyze user query: {message}. And choose the right tool that parses the different items from the order to have separate distinct names and quantities.",
    "input_variables": {"message": "",}
  },
  "ai": {
    "template": "",
    "input_variables": {}
  },
}

message_classification_prompt = {
  "system": {
    "template":  """You are an expert in restaurant order request messages classification.\n

    Your task:\n
    - Classify messages as order, enquiry or miscellaneous. Only one of those should be `true`.\n
    - Strictly adhere to the following schema for your response:\n
    Schema:\n
    {message_classification_schema}\n

    Important:\n
    - Only return a JSON object based on the schema. Do not include any extra text, comments, or fields beyond the schema.\n
    - Place your complete answer inside the correct field of the schema.\n
    - Do not alter the schema structure.\n

    User query: {query}""",
    "input_variables": {}
  },
  "human": {
    "template": "{message}",
    "input_variables": {"message": "",}
  },
  "ai": {
    "template": "",
    "input_variables": {}
  },
}


tool_notifier_agent_prompt = {
  "system": {
    "template": "", 
    "input_variables": {}
  },
  "human": {
    "template": "Use this folder name parameter: {folder_name_parameter}. And choose the appropriate tool to send Discord notification.", 
    "input_variables": {"folder_name_parameter": ""}
  },
  "ai": {
    "template": "", 
    "input_variables": {}
  },
}
