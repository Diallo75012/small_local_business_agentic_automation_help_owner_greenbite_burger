import os
import json
# for typing func parameters and outputs and states
from typing import Dict, List, Tuple, Any, Optional
# for llm call with func or tool and prompts formatting
from langchain_groq import ChatGroq
from langchain_core.messages import (
  AIMessage,
  HumanMessage,
  SystemMessage,
  ToolMessage
)
from langchain.prompts import (
  PromptTemplate,
  ChatPromptTemplate,
  SystemMessagePromptTemplate,
  HumanMessagePromptTemplate,
  AIMessagePromptTemplate
)
from helpers.formatters import string_to_dict
# to run next graphs
from llms.llms import (
  groq_llm_mixtral_7b,
  groq_llm_mixtral_larger,
  groq_llm_llama3_70b_versatile,
)
# for env. vars
from dotenv import load_dotenv, set_key


# load env vars
load_dotenv(dotenv_path='.env', override=False)
load_dotenv(dotenv_path=".vars", override=True)


def call_llm(query: str, prompt_template_part: str, schema: str, partial_variables={}) -> Dict:
  '''
  Description:
  formatting prompt with input variables needed then calling llm that will answer using structure output following desired schema
  
  Parameters:
  query str: query of user query formatted injecting the query in the pre-defined human side of the prompt
  prompt_template str: it is the system side of the prompt which will be formatted here by injecting the input variables
  schema: is the corresponding desired schema for the structured output desired returned by the llm
  partial_variables dict: empty dictionary to be able to add extra variable to prompt if any so we can have flexibility to inject some more variables if needed
  
  Output:
  a structured output dictionary corresponding to the schema desired response from LLM
  '''

  prompt = PromptTemplate(
    template=prompt_template_part,
    input_variables=["query", "response_schema"],
    # this has to be a dict
    partial_variables=partial_variables,
  )
  print("Prompt before call structured output: ", prompt)

  # And a query intended to prompt a language model to populate the data structure. groq_llm_llama3_70b as many code sent so long context
  try:
    # llm will be called here by importing it and using it in this scope
    from llms.llms import groq_llm_mixtral_7b
    
    prompt_and_model = prompt | groq_llm_mixtral_7b
    print("prompt_and_model: ", prompt_and_model)
    response = prompt_and_model.invoke({"query": query, "response_schema": schema})
    print("RESPONSE: ", response.content)
    # parse content from dict
    if "```markdown" in response.content:
      print(" '```markdown' in response")
      # parse response and clean it to limit errors of not valid json error when transforming to dictionary
      response_parsed = response.content.split("```")[1].strip("markdown").strip().replace("`", "")

      # 1. Replace escaped underscores first to avoid double-replacing backslashes.
      response_parsed = response_parsed.replace("\\_", "_")
      print("Parsed response underscores: ", response_parsed)

    else:
      if "```python" in response.content:
        print(" '```python' in response")
        # parse response and clean it to limit errors of not valid json error when transforming to dictionary
        response_parsed = response.content.split("```")[1].strip("python").strip().replace("`", "")
        response_parsed = response_parsed.replace("\\_", "_")
        print("Parsed response underscores: ", response_parsed)
      elif "```json" in response.content:
        print(" '```json' in response")
        # parse response and clean it to limit errors of not valid json error when transforming to dictionary
        response_parsed = response.content.split("```")[1].strip("json").strip().replace("`", "")
        response_parsed = response_parsed.replace("\\_", "_")
        print("Parsed response underscores: ", response_parsed)
      else:
        print(" '```' not in response")
        response_parsed = response.content
    # transform to dict
    # response_content_to_dict = string_to_dict(response_parsed)
    response_content_to_dict = string_to_dict(response_parsed.replace("'", "\""))
    print("Response content dict: ", response_content_to_dict)
    return response_content_to_dict

  except Exception as e:
    raise Exception(f"An error occured while calling llm: {str(e)}")
