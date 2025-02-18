
"""
USER PROMPTS NEEDED:
- analyze user query to make sure that it is safe and comply with law
- summarize_user_question > get a clear question
- retrieve_answer > get document_title
- answer_to_user_in_a_special_way > get AI personality traits to formulate answer
  - if retrieval data is satisfactory we use it to answer otherwise we perform an internet search or say that we don't have the answer about this question and propose the retrieved question as potential question that we may answer to
"""
analyse_user_query_safety_prompt = {
  "system": {
    "template": "You are an assistant that evaluates user queries for safety compliance. Your task is to analyze the query below and return a JSON response that adheres strictly to the provided schema. Schema:\n{response_schema}\n\nReturn only the JSON object based on the schema. Do not include any additional text or comments.\nHere is user query: {query}\n",
    "input_variables": {}
  },
  "human": {
    "template": "{user_initial_query}",
    "input_variables": {"user_initial_query": "",}
  },
  "ai": {
    "template": "",
    "input_variables": {}
  },
}

summarize_user_to_clear_question_prompt = {
  "system": {
    "template": "You are an expert in clarification of user intent and you are summarizing and rephrasing the user query to a simple, clear question without losing the essence of the initial user query and return a JSON response that adheres strictly to the provided schema. Schema:\n{response_schema}\n\nReturn only the JSON object based on the schema. Do not include any additional text or comments.\nHere is user query: {query}\n",
    "input_variables": {}
  },
  "human": {
    "template": "{user_initial_query}",
    "input_variables": {"user_initial_query": "",}
  },
  "ai": {
    "template": "",
    "input_variables": {}
  },
}

retrieve_answer_prompt = {
  "system": {
    "template": "You are an expert in in embedding retrieval from user query and use tool available to query the vector databaseand return a JSON response that adheres strictly to the provided schema. Schema:\n{response_schema}\n\nReturn only the JSON object based on the schema. Do not include any additional text or comments.\nHere is user query: {query}\n",
    "input_variables": {"query": "", "response_schema": "",}
  },
  "human": {
    "template": "{rephrased_question}",
    "input_variables": {"rephrased_question": "",}
  },
  "ai": {
    "template": "",
    "input_variables": {}
  },
}

perform_internet_search_prompt = {
  "system": {
    "template": "You are an expert in information research and will use tools available to perform an internet search to answer to user queryand return a JSON response that adheres strictly to the provided schema. Schema:\n{response_schema}\n\nReturn only the JSON object based on the schema. Do not include any additional text or comments.\nHere is user query: {query}\n",
    "input_variables": {}
  },
  "human": {
    "template": "{user_initial_query}",
    "input_variables": {"user_initial_query": "",}
  },
  "ai": {
    "template": "",
    "input_variables": {}
  },
}

answer_to_user_prompt = {
  "system": {
    "template":  """You are an expert in formulating personalized answers for easy and enjoyable user understanding.\n

    Your task:\n
    - Personalize your answer using the provided **personality traits**: {ai_personality_traits}. These traits guide your tone and style of response, but they should not appear explicitly in your output.\n
    - Strictly adhere to the following schema for your response:\n
    Schema:\n
    {response_schema}\n

    Important:\n
    - Only return a JSON object based on the schema. Do not include any extra text, comments, or fields beyond the schema.\n
    - Place your complete answer inside the "response" field of the schema.\n
    - The personality traits are for tone/style of your writing and should not alter the schema structure.\n

    User query: {query}""",
    "input_variables": {}
  },
  "human": {
    "template": "{user_initial_query_rephrased}",
    "input_variables": {"user_initial_query_rephrased": "",}
  },
  "ai": {
    "template": "",
    "input_variables": {}
  },
}
'''
# if needed to customize
answer_to_user_prompt_055 = {
  "system": {
    "template": """You are an expert in formulating personalized answers for easy and enjoyable user understanding.\n

    Your task:\n
    - Personalize your answer using the provided **personality traits**: {ai_personality_traits}. These traits guide your tone and style of response, but they should not appear explicitly in your output.\n
    - Strictly adhere to the following schema for your response:\n
    Schema:\n
    {response_schema}\n

    Important:\n
    - Only return a JSON object based on the schema. **Do not introduce any additional keys, fields, or sections** beyond the schema.\n
    - Place all your content, including disclaimers, apologies, and examples, inside the "response" field.\n
    - The personality traits are for tone/style of your writing and should not alter the schema structure.\n

    User query: {query}
    """,
    "input_variables": {}
  },
  "human": {
    "template": "{user_initial_query_rephrased}",
    "input_variables": {"user_initial_query_rephrased": "",}
  },
  "ai": {
    "template": "",
    "input_variables": {}
  },
}
'''

# this is not langchain prompt but just a dict where we get our disclaimers from
disclaimer = {
  "nothing": "There is no relevant answer to the question you just asked {user_initial_question}.",
  "example_of_questions_having_answers": "This no relevant answer to the question you just asked {user_initial_question}.\n Those are examples of types of questions that we have answer for:\n{type_of_questions_example_show_to_user}.",
  "answer_found_but_disclaim_accuracy": "To your question: {user_initial_question}, answer have been found: {answer_found_in_vector_db}"
}

################
# LOGS  AGENTS #
################
advice_agent_report_creator_prompt = {
  "system": {
    "template":  """You are an expert in troubleshooting software logs.\n

    Your task:\n
    - Personalize your answer using the provided **personality traits**: professional, pertinent, accurate, out of the box vision of problems. These traits guide your tone and style of response, but they should not appear explicitly in your output.\n
    - Strictly adhere to the following schema for your response:\n
    Schema:\n
    {response_schema}\n

    Important:\n
    - Only return a JSON object based on the schema. Do not include any extra text, comments, or fields beyond the schema.\n
    - Place your complete answer inside the "response" field of the schema.\n
    - The personality traits are for tone/style of your writing and should not alter the schema structure.\n

    User query: {query}""",
    "input_variables": {}
  },
  "human": {
    "template": "{user_query}",
    "input_variables": {"user_query": "",}
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
