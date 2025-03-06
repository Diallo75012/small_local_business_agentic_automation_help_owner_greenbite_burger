document.addEventListener("DOMContentLoaded", function () {
  // agent job part
  const button = document.getElementById("start-processing");
  const resultContainer = document.getElementById("result-report");
  // scrolling part
  const scrollTopBtn = document.getElementById("scroll-top");
  const scrollMidBtn = document.getElementById("scroll-mid");
  const scrollBottomBtn = document.getElementById("scroll-bottom");
  // simulation incoming messages part (display is `none` and visibility `hidden` in styles.css)
  const incomingMessagesSimulatorButton = document.getElementById("start-incoming-messages-simulation");
  const resultIncomingMessagesSimulationContainer = document.getElementById("result-simulation-incoming-messages");

  // AGENT JOB PART
  let eventSource = null;

  button.addEventListener("click", function () {
    // If the EventSource is already open, do nothing.
    if (eventSource) return;

    resultContainer.innerHTML = "<p>Processing started...</p>";
    button.disabled = true;
    button.classList.add("disabled");

    // Make sure this route returns SSE on GET, not HTML
    eventSource = new EventSource("/greenbite-messages-automation-stream");

    eventSource.onmessage = function (event) {
      // Note: `event.data` cleans up the prefix `data: ` that it requires for sending messages
      // If our Flask generator sends "data: done\n\n", we treat it as a completion signal
      if (event.data === "done") {
        eventSource.close();
        eventSource = null;
        button.disabled = false;
        button.classList.remove("disabled");
        resultContainer.innerHTML += "<p style='color:lime;'>Process completed successfully.</p>";
        return;
      }

      // If it’s just a “heartbeat,” ignore it
      if (event.data === "heartbeat") {
        return;
      }


      // display in webui the agent response
      const line = event.data;
      console.log("Full Event: ", event)
      const div = document.createElement("div");
      div.textContent = line;
      resultContainer.appendChild(div);
     
      resultContainer.scrollTop = resultContainer.scrollHeight;
    };

    // If there’s a connection error, close and retry after 5s
    eventSource.onerror = function () {
      eventSource.close();
      eventSource = null;
      button.disabled = false;
      button.classList.remove("disabled");
      resultContainer.innerHTML += "<p style='color:red;'>Connection lost. Retrying...</p>";

      setTimeout(() => button.click(), 5000);
    };
  });

  // SCROLLING PART
  scrollTopBtn.addEventListener("click", () => {
    resultContainer.scrollTop = 0;
  });

  scrollMidBtn.addEventListener("click", () => {
    resultContainer.scrollTop = resultContainer.scrollHeight / 2;
  });

  scrollBottomBtn.addEventListener("click", () => {
    resultContainer.scrollTop = resultContainer.scrollHeight;
  });

  // SIMULATION INCOMING MESSAGES PART
  let eventSimulationSource = null;

  incomingMessagesSimulatorButton.addEventListener("click", function () {
    // If the eventSimulationSource is already open, do nothing as we wait to receive message from backend.
    if (eventSimulationSource) return;

    resultIncomingMessagesSimulationContainer.innerHTML = "<p>Processing started...</p>";
    incomingMessagesSimulatorButton.disabled = true;
    incomingMessagesSimulatorButton.classList.add("disabled");

    // Make sure this route returns SSE on GET, not HTML
    eventSimulationSource = new EventSource("/simulate-message-received");

    eventSimulationSource.onmessage = function (event) {
      // Note: `event.data` cleans up the prefix `data: ` that it requires for sending messages
      // If our Flask generator sends "data: done\n\n", we treat it as a completion signal
      if (event.data === "done") {
        eventSimulationSource.close();
        eventSimulationSource = null;
        incomingMessagesSimulatorButton.disabled = false;
        incomingMessagesSimulatorButton.classList.remove("disabled");
        resultIncomingMessagesSimulationContainer.innerHTML += "<p style='color:lime;'>Process completed successfully.</p>";
        return;
      }

      // If it’s just a “heartbeat,” ignore it
      if (event.data === "heartbeat") {
        return;
      }

      // here we return different messages depending on received backend `error`, `empty` or `success`
      if (event.data.indexOf("error") !== -1) {
        // display in webui the agent response making the `div` visible
        const line = event.data;
        console.log("Error in Incoming messages simulator result: ", event)
        const div = document.createElement("div");
        div.textContent = `Incoming Messages Result:\n${line}`;
        resultIncomingMessagesSimulationContainer.appendChild(div);
      } else if (event.data.indexOf("empty") !== -1) {
        // display in webui the agent response making the `div` visible
        const line = event.data;
        console.log("Empty Incoming messages simulator result: ", event)
        const div = document.createElement("div");
        div.textContent = `Incoming Messages Result:\n${line}`;
        resultIncomingMessagesSimulationContainer.appendChild(div);
      } else {
        // if we are here that means that we had found new messages `success`
        // display in webui the agent response making the `div` visible
        const line = event.data;
        console.log("Success Incoming messages simulator result: ", event)
        const div = document.createElement("div");
        div.textContent = `Incoming Messages Result:\n${line}`;
        resultIncomingMessagesSimulationContainer.appendChild(div);    
      }
    };

    // If there’s a connection error, close and retry after 5s
    eventSimulationSource.onerror = function () {
      eventSimulationSource.close();
      eeventSimulationSource = null;
      incomingMessagesSimulatorButton.disabled = false;
      incomingMessagesSimulatorButton.classList.remove("disabled");
      resultIncomingMessagesSimulationContainer.innerHTML += "<p style='color:red;'>Connection lost. Retrying...</p>";

      setTimeout(() => incomingMessagesSimulatorButton.click(), 5000);
    };
  });

});

