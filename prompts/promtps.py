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
