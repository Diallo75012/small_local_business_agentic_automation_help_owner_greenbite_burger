import os
import json
from dotenv import load_dotenv
from discord_webhook import DiscordWebhook


# load env vars
load_dotenv(dotenv_path='.env', override=False)
load_dotenv(dotenv_path=".vars.env", override=True)

# max file size is 8MB dfor discord
def send_file_to_discord(message: str, classification: str, category_room_webhook_url: str):
  """
  Helper function to send a notification order messages to Discord.

  parameters:
  category_room_webhook_url str: The Discord specific category (orders, enquiries or miscellaneous)webhook URL.
  message str: message to be sent to the right category
  """
  webhook = DiscordWebhook(url=category_room_webhook_url, content=f"📄 **{classification}**: {message}")
  try:
    response = webhook.execute()

    if response.status_code == 200:
      print(f"message sent successfully.")
      return f"{message}"
    else:
      print(f"Failed to send message. HTTP Status Code: {response.status_code}")
      print(response.content)
      raise Exception(f"failed: HTTP status code was {response.status_code}")
  except Exception as e:
    print(f"An unexpected error occurred while sending message: {message}: {e}")
    return f"An exception occured while trying to send message to discord: {e}"
