document.addEventListener("DOMContentLoaded", function () {
  const button = document.getElementById("start-processing");
  const resultContainer = document.getElementById("result-report");
  const scrollTopBtn = document.getElementById("scroll-top");
  const scrollMidBtn = document.getElementById("scroll-mid");
  const scrollBottomBtn = document.getElementById("scroll-bottom");

  let eventSource = null;  // Store event source globally

  button.addEventListener("click", function () {
    if (eventSource) {
      return; // Prevent multiple connections
    }

    resultContainer.innerHTML = "<p>Processing started...</p>";
    button.disabled = true;  // Disable button while processing
    button.classList.add("disabled");  // Add disabled style

    // Connect to SSE stream
    eventSource = new EventSource("/greenbite-messages-automation");

    eventSource.onmessage = function (event) {
      if (event.data === "done") {
        eventSource.close();  // Close connection when finished
        eventSource = null;
        button.disabled = false;  // Re-enable button
        button.classList.remove("disabled");  // Remove disabled style
        resultContainer.innerHTML += "<p style='color:lime;'>Process completed successfully.</p>";
        return;
      }

      // Append new messages
      const newMessage = document.createElement("p");
      newMessage.textContent = event.data;
      resultContainer.appendChild(newMessage);

      // Auto-scroll to bottom when new content arrives
      resultContainer.scrollTop = resultContainer.scrollHeight;
    };

    eventSource.onerror = function () {
      eventSource.close();
      eventSource = null;
      button.disabled = false;  // Re-enable button
      button.classList.remove("disabled");  // Remove disabled style
      resultContainer.innerHTML += "<p style='color:red;'>Process completed or error occurred.</p>";
    };
  });

  // Scroll Control Buttons
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
