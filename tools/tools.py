import os
import json
# for typing func parameters and outputs and states
from typing import Dict, List, Tuple, Any, Optional
# one is @tool decorator and the other Tool class
from langchain_core.tools import tool, Tool
from langgraph.graph import MessagesState
from langgraph.prebuilt import ToolNode
from langchain_community.tools import (
  # Run vs Results: Results have more information
  DuckDuckGoSearchRun,
  DuckDuckGoSearchResults
)
from agents.llms.llms import (
  groq_llm_mixtral_7b,
  groq_llm_mixtral_larger,
  groq_llm_llama3_8b,
  groq_llm_llama3_70b,
  groq_llm_llama3_70b_versatile,
  groq_llm_llama3_vision_large,
  groq_llm_gemma_7b,
)
from agents.app_utils import retrieve_answer
from common.discord_notifications import send_agent_log_report_to_discord
from django.conf import settings
from dotenv import load_dotenv


# load env vars
load_dotenv(dotenv_path='.env', override=False)
load_dotenv(dotenv_path=".vars", override=True)

# log folder from agents
LOG_AGENT_REPORTS_FOLDER = os.path.join(settings.BASE_DIR, 'log_agent_reports')


# TOOLS

## Internet Search Tool
internet_search_tool = DuckDuckGoSearchRun()
tool_internet = Tool(
    name="duckduckgo_search",
    description="Search DuckDuckGO for recent results.",
    func=internet_search_tool.run,
)
@tool
def search(query: str, state: MessagesState = MessagesState()):
    """Call to surf the web."""
    search_results = internet_search_tool.run(query)
    return {"messages": [search_results]}

# INTERNET TOOL NODES
tool_search_node = ToolNode([search])
# LLMs WITH BINDED TOOLS
llm_with_internet_search_tool = groq_llm_llama3_70b_versatile.bind_tools([search])


"""
TOOL TO PERFORM RETRIEVAL OF DATA
"""
# retrieval tool
@tool
def retrieve_answer_action(query: str, state: MessagesState = MessagesState()):
  """
  Retrieves best answer for user query from the vector database

  Parameter:
  query: str = user question

  returns:
  retrieved answer for that specific user question
  """

  # vars
  query: str = os.getenv("REPHRASED_USER_QUERY")
  # we will perform two retrieval with different scores
  score063: float = float(os.getenv("SCORE064"))
  score055: float = float(os.getenv("SCORE055"))
  top_n: int = int(os.getenv("TOP_N"))
  vector_responses: dict = {}

  # Perform vector search with score if semantic search is not relevant
  try:
    vector_response_063 = retrieve_answer.answer_retriever(query, score063, top_n)
    print("JSON RESPONSE 063: ", json.dumps(vector_response_063, indent=2))
    vector_response_055 = retrieve_answer.answer_retriever(query, score055, top_n)
    print("JSON RESPONSE 055: ", json.dumps(vector_response_055, indent=2))

    '''
      # Returns
      {
        'question': vector['question'],
        'answer': vector['answer'],
        'score': vector['score'],
      }
    '''

    if vector_response_063:
      # update to vector_response
      vector_responses["score_063"] = vector_response_063
    if vector_response_055:
      # update to vector_response
      vector_responses["score_055"] = vector_response_055
    # here in conditional adge we will look for "vector_responses" key like
    return {"messages": [{"role": "ai", "content": json.dumps(vector_responses)}]}
  except Exception as e:
    print(f"An error occured while trying to perform vectordb search query {e}")
    return {"messages": [{"role": "ai", "content": json.dumps({"error_vector": f"An error occured while trying to perform vectordb search query: {e}"})}]}

  # If no relevant result found, return a default response, and perform maybe after that an internet search and cache the query and the response
  return {"messages": [{"role": "ai", "content": json.dumps({"nothing": "nothing_in_cache_nor_vectordb"})}]}

# will use notify devops/security team in discord
@tool
def notify_devops_security(agent_report_folder_path: str = LOG_AGENT_REPORTS_FOLDER, state: MessagesState = MessagesState()):
  """
  Sends Discord notification to Devops/Security team

  Parameter:
  agent_report_folder_path: str = folder name parameter

  returns:
  The notification result
  """
  try:
    notification_result = send_agent_log_report_to_discord(agent_report_folder_path)
    return {"messages": [{"role": "ai", "content": json.dumps({"success": notification_result})}]}
  except Exception as e:
    return {"messages": [{"role": "ai", "content": json.dumps({"error": f"An error occured while trying to notify Devops/Security team: {e}"})}]}

####################################
### THIS TO BE USED AND EXPORTED ###
####################################
# retrieve_answer tool node
tool_retrieve_answer_node = ToolNode([retrieve_answer_action])
# LLMs WITH BINDED TOOLS
# trying with larger context llm as i get groq error for to large request when using llama 70b tool use
llm_with_retrieve_answer_tool_choice = groq_llm_llama3_vision_large.bind_tools([retrieve_answer_action])

# log analyzer notifier tool
log_analyzer_notififier_tool_node = groq_llm_llama3_70b_versatile.bind_tools([notify_devops_security])
llm_with_log_analyzer_notififier_tool_choice = groq_llm_llama3_vision_large.bind_tools([notify_devops_security])
