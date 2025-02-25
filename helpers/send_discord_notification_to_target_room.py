import os
import json
from dotenv import load_dotenv
from discord_webhook import DiscordWebhook
#from django.conf import settings # can't import from setting or set env var to do that while running standalone script so we just build the BASE_DIR from here
#BASE_DIR = settings.BASE_DIR


# load env vars
load_dotenv(dotenv_path='.env', override=False)
load_dotenv(dotenv_path=".vars.env", override=True)

DISCORD_WEBHOOK_ID = os.getenv("DISCORD_WEBHOOK_ID")
DISCORD_WEBHOOK_TOKEN = os.getenv("DISCORD_WEBHOOK_TOKEN")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
log_agent_final_report_folder = os.getenv("LOG_AGENT_REPORTS_FOLDER")
LOG_AGENT_REPORTS_FOLDER = os.path.join(BASE_DIR, log_agent_final_report_folder)

# max file size is 8MB dfor discord
def send_file_to_discord(message, classification, category_room_webhook_url):
  """
  Helper function to send a notification order messages to Discord.

  parameters:
  category_room_webhook_url str: The Discord specific category (orders, enquiries or miscellaneous)webhook URL.
  message str: message to be sent to the right category
  """
  webhook = DiscordWebhook(url=f"{DISCORD_WEBHOOK_URL}/{DISCORD_WEBHOOK_ID}/{DISCORD_WEBHOOK_TOKEN}", content=f"📄 **{classification}**: {message}")
  try:
    response = webhook.execute()

    if response.status_code == 200:
      print(f"message sent successfully.")
      return "success"
    else:
      print(f"Failed to send message. HTTP Status Code: {response.status_code}")
      print(response.content)
      raise Exception(f"failed: HTTP status code was {response.status_code}")
  except Exception as e:
    print(f"An unexpected error occurred while sending message: {message}: {e}")
    return f"An exception occured while trying to send message to discord: {e}"
