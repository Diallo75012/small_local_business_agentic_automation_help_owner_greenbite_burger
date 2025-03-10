import os
import sys
import json
import time
import random
import pandas as pd
import concurrent.futures
import subprocess
from typing import List
from flask import Flask, render_template, request, jsonify, Response
from helpers.check_for_bucket_new_message import fetch_bucket_saved_new_message
from dotenv import load_dotenv, set_key


load_dotenv()

app = Flask(__name__)

def stream_results():
  last_sent_time = time.time()
  
  while True:
    # this a list of new rows fetched from database
    new_rows = fetch_bucket_saved_new_message(os.getenv("LAST_MESSAGE_FETCHED_FROM_MESSAGES_BUCKET_ID_TRACKER"))
    time.sleep(30)

    # ✅ Send heartbeat every 10 seconds to keep connection open
    if time.time() - last_sent_time > 10:
      yield "data: heartbeat\n\n"
      sys.stdout.flush()
      last_sent_time = time.time()
            
    if not new_rows:
      # No new messages, continue loop
      continue

    # here we check that there is new rows and start agentic flow using subprocesses
    if new_rows:
      for row in new_rows:
        print(f"Analysis of this row in process: {row}")
        # catch errors
        try:
          # set env var for user initial query to be the message that will be fetched by the subprocess thread
          # in the special script to start agent which will get the message fromt he .vars.env file
          set_key(".vars.env", "USER_INITIAL_QUERY", row[1])
          load_dotenv(dotenv_path='.vars.env', override=True)

          # then start the agent. we do it like that we this is to decouple later as here we set the env var and get it when we could just pass the message directly
          user_query = os.getenv("USER_INITIAL_QUERY")
          print("Message fetched: ", user_query)

          # command need to be in a list with the first argument being the executable (here `python3`)
          commands = ["python3", "agentic_process_run.py"]

          # a little sleep moment so that the env var have time to update between messages
          # as new agentic flow starts with new message (prevent running same message in two different agentic workflows)
          time.sleep(0.5)
        
          # start the `subprocess` `ThreadPool` with max "3" workers executors for this tuto
          with concurrent.futures.ThreadPoolExecutor(max_workers=int(os.getenv("WORKERS"))) as executor:
            results = executor.map(run_command, [commands])

          # we return results as data is being processes
          for result in results:
            # we don't need to let the agent run to end if there is an error
            # we catch it promptly and stop the flow to be able to fail fats troubleshoot and fix the error
            if "error" in result:
              print(f"An error occurred while running the subprocess, agent result: {result}")
              raise Exception(f"An error occurred while running the subprocess, agent result: {result}")
            # use generator to keep sending live results to the frontend
            # Note: "`SSE` (Server‐Sent Events) specification requires the server to prefix actual `data` lines with `data:`"
            # `yield` the `result` fully replacing `\n` with `\ndata: ` to get each line captured with this mandataory `data: `
            #print(f"data: {result.replace('\n', '\ndata: ')}")
            #yield f"{result.replace('\n', '\ndata: ')}\n\n"
            #sys.stdout.flush()
            # OR yield each lines
            for line in result.splitlines():
              print(f"data: {line}")
              yield f"data: {line}\n"
              sys.stdout.flush()
            yield "\n"
            sys.stdout.flush()
            
        except Exception as e:
          print(f"An exception occured while running subprocess agentic workflow: {e}")
          yield f"data: error: An exception occured while running subprocess agentic workflow {str(e)}\n\n"
          sys.stdout.flush()

    # Signal JavaScript that process is finished
    yield "data: done\n\n"
    sys.stdout.flush()
    # Allow message to be received before closing
    time.sleep(1)
    # exit the while loop
    break

def simulation_incoming_messages_from_different_sources():
  last_sent_time = time.time()
  
  while True:
    # ✅ Send heartbeat every 10 seconds to keep connection open
    if time.time() - last_sent_time > 10:
      yield "data: heartbeat\n\n"
      sys.stdout.flush()
      last_sent_time = time.time()

    try:
      # command need to be in a list with the first argument being the executable (here `python3`)
      # returns `str`: `empty`(no more messages to fetch), `success`(all new messages have been fetched), `error`(an error occured)
      commands = ["python3", "simulation_incoming_messages_run.py"]
        
      # start the `subprocess` `ThreadPool` with max "3" workers executors for this tuto
      with concurrent.futures.ThreadPoolExecutor(max_workers=int(os.getenv("WORKERS"))) as executor:
        results = executor.map(run_command, [commands])
      print("Results: ", results)

      for result in results:
        print("Result: ", result)
        # if `error`
        if "error" in result:
          print(f"An error occurred while running the subprocess, fetch_messages_and_store result: {result}")
          for line in result.splitlines():
            yield f"data: {line}\n"
            sys.stdout.flush()
          yield "\n"
          sys.stdout.flush()
        elif "success" in result:
          print(f"Successfully fetched incoming new messages and stored result: {result}")
          for line in result.splitlines():
            yield f"data: {line}\n"
            sys.stdout.flush()
          yield "\n"
          sys.stdout.flush()
        elif "empty" in result:
          print(f"No incoming new messages to fetch: {result}")
          for line in result.splitlines():
            yield f"data: {line}\n"
            sys.stdout.flush()
          yield "\n"
          sys.stdout.flush()
        else:
          print("error while looking for incoming messages, no `empty`, `error` nor `success` in result")
          yield f"data: error incoming messages.\n"
          sys.stdout.flush()

    except Exception as e:
      print(f"An exception occured while running subprocess agentic workflow: {e}")
      yield f"data: error: An exception occured while running subprocess simutating incoming messages workflow {str(e)}\n\n"
      sys.stdout.flush()
  
    # Signal JavaScript that process is finished
    yield "data: done\n\n"
    sys.stdout.flush()
    # Allow message to be received before closing
    time.sleep(1)
    # exit the while loop
    break

def run_command(cmd: List[str]):
  proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
  try:
    stdout, stderr = proc.communicate(timeout=int(os.getenv("PROCESS_TIMEOUT")))  # Ensure it doesn’t hang forever (5 mn)
  except subprocess.TimeoutExpired:
    proc.kill()  # Force stop if running too long
    return "error: process timeout"
    
  if proc.returncode != 0:
    return f"error: {stderr.strip()}"
  return stdout.strip()

# route that will be listening to bucket new messages and start agentic process constantly
@app.route('/greenbite-messages-automation', methods=['GET'])
def greenbite_messages_automation():    
  # if we go to that route `url` we see the `UI` dahsboard
  return render_template('greenbite_messages_automation.html')
  
@app.route('/greenbite-messages-automation-stream', methods=['GET'])
def greenbite_messages_automation_stream():
  return Response(stream_results(), content_type="text/event-stream")

# this route will be simulating the constant incoming messages from different sources (Whatsapp, SMS, Instragram DMs...)
# the helper functions returns `empty`(no more messages to fetch), `success`(all new messages have been fetched), `error`(an error occured)
# javascript side is going to be handling those returned values 
@app.route('/simulate-message-received', methods=['GET'])
def simulate_message_received():
  return Response(simulation_incoming_messages_from_different_sources(), content_type="text/event-stream")

if __name__ == '__main__':
  app.run(debug=True, threaded=True, host='0.0.0.0')


'''
# javascript side:
// AJAX request to post message
fetch('/clientchat/clientuserchat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
  },
  body: JSON.stringify(dataToSend),
})
.then(response => response.json())
.then(data => {
  // check what is inside data
  console.log("data from ajax call received: ", data)    

  // Append the bot response to the chat container
  appendMessage(chatContainer, data.bot_message, 'bot');

  // Scroll to the bottom after updating
  chatContainer.scrollTop = chatContainer.scrollHeight;
})

# http response to javascript
return HttpResponse(json.dumps({'error': 'Chatbot name and description are required.'}), content_type="application/json", status=400)
'''
