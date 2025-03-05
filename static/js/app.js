document.addEventListener("DOMContentLoaded", function () {
  const button = document.getElementById("start-processing");
  const resultContainer = document.getElementById("result-report");
  const scrollTopBtn = document.getElementById("scroll-top");
  const scrollMidBtn = document.getElementById("scroll-mid");
  const scrollBottomBtn = document.getElementById("scroll-bottom");

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

  scrollTopBtn.addEventListener("click", () => {
    resultContainer.scrollTop = 0;
  });

  scrollMidBtn.addEventListener("click", () => {
    resultContainer.scrollTop = resultContainer.scrollHeight / 2;
  });

  scrollBottomBtn.addEventListener("click", () => {
    resultContainer.scrollTop = resultContainer.scrollHeight;
  });
});

