import os
import json
# for typing func parameters and outputs and states
from typing import Dict, List, Tuple, Any, Optional
# prompts formatting
from langchain.prompts import (
  PromptTemplate,
  ChatPromptTemplate,
  SystemMessagePromptTemplate,
  HumanMessagePromptTemplate,
  AIMessagePromptTemplate
)


# creation of prompts
def prompt_creation(target_prompt_human_system_or_ai: Dict[str, Any], **kwargs: Any) -> str: #-> PromptTemplate:
    """
      formatitng a prompt using two parts: the base of the prompt with the expected input variables
      and the kwargs to which are input variables to inject in the prompt
    """
    input_variables = target_prompt_human_system_or_ai.get("input_variables", [])

    prompt = PromptTemplate(
        template=target_prompt_human_system_or_ai["template"],
        input_variables=input_variables
    )

    formatted_template = prompt.format(**kwargs) if input_variables else target_prompt_human_system_or_ai["template"]
    print("formatted_template: ", formatted_template)
    return formatted_template
