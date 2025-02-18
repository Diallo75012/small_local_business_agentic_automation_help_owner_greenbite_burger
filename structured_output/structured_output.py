"""
  Here we will list all the different schema for structured output
  using the `in-prompt`(desired structured output injection in prompts) technique.
"""
schema_example={
  "requirements": "A requirements.txt content corresponding to new Python script only if needed. Or a correction of the previous requirements.txt if error comes from it. answer just a str as it should be on the requirements.txt file, if there is more than one line make sure to format the str with \\n to return at the next line for next required package to install.",
  "script": "New Python script that addresses the error or the previous script if the error wasn't coming from the code but from the requirements.txt content. Make sure it is well formatted, with good indentation and line returns. use str to answer.",
  "needed": "Answer 'YES' or 'NO' depending on if the code requires a requirements.txt file."
}

analyse_user_query_safety_schema = '''
  '{
    "safe": "valid or invalid. Set to 'valid' if the user query is considered safe. Set to 'invalid' otherwise.",
    "unsafe": "valid or invalid. Set to 'valid' if the user query is considered unsafe. Set to 'invalid' otherwise."
  }'
'''

summarize_user_to_clear_question_schema = {
  "question": "user question is rephrased to a clear question and only one question."
}

retrieve_answer_schema = {
  "retrieval": "the data that have been retrieved from vector database search in valid JSON format. So here just return what you have received as data but in valid JSON format."
}

answer_to_user_schema = {
  "answer_if_063": {
    "response": "answer the user making sure that it expresses you personality trait and stay polite but warm with user and the key of the dictionary is: response. Use this answer: {answer_with_disclaimer}"
  },
  #"answer_if_055": {
  #  "response": "answer user using this disclaimer: {disclaimer} as no relevant data have been found but those are similar queries that can be asked in order to get an answer, so that user know how to formulate question. Apologize and make sure you use your personality trait to answer in a certain way but staying polite."
  #},
  "answer_if_055": {
    "response": "Apologize politely, indicating no direct answer was found. Use a disclaimer way of answering and additionally, provide a list of example questions the user could ask for relevant answers: {disclaimer}. Ensure the tone reflects your personality traits and the key of the dictionary is: response."
  },
  "answer_if_nothing": {
    "response": "Apologize politely, indicating no direct answer was found. Use a disclaimer way of answering like: {disclaimer}. Ensure the tone reflects your personality traits. and the key of the dictionary is: response"
  },
}

##############
# LOGS AGENT #
##############
advice_agent_report_creator_schema = {
  "response": "In mardown format provide advice in where those issues could come from and how to fix those issues plus some extra advice. be Precise and consice."
}
