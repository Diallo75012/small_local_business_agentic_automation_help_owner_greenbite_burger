'''
This script will run the thread process that will run the agentic workflow for the message to work on
'''
import os
import json
from dotenv import load_dotenv
from agents.order_automation_agent import order_automation_agent_team

def run_agents():
  try:
    user_query = os.getenv("USER_INITIAL_QUERY")
    message_analyst_agent = order_automation_agent_team(user_query)
    return json.dumps({"succes": message_analyst_agent})
  except Exception as e:
    return json.dumps({"exception": f"An exception Occurred while trying to run agentic worklfow from 'agentic_process_run': {e}"})

load_dotenv(dotenv_path='.vars.env', override=True)

if __name__ == "__main__":
  run_agents()
