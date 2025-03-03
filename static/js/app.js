document.addEventListener("DOMContentLoaded", function () {
  const button = document.getElementById("start-processing");
  const resultContainer = document.getElementById("result-report");
  const scrollTopBtn = document.getElementById("scroll-top");
  const scrollMidBtn = document.getElementById("scroll-mid");
  const scrollBottomBtn = document.getElementById("scroll-bottom");

  let eventSource = null;

  button.addEventListener("click", function () {
    if (eventSource) return;

    resultContainer.innerHTML = "<p>Processing started...</p>";
    button.disabled = true;
    button.classList.add("disabled");

    eventSource = new EventSource("/greenbite-messages-automation");

    eventSource.onmessage = function (event) {
      if (event.data === "done") {
        eventSource.close();
        eventSource = null;
        button.disabled = false;
        button.classList.remove("disabled");
        resultContainer.innerHTML += "<p style='color:lime;'>Process completed successfully.</p>";
        return;
      }

      if (event.data === "heartbeat") return;  // ✅ Ignore heartbeat messages

      const newMessage = document.createElement("p");
      newMessage.textContent = event.data;
      resultContainer.appendChild(newMessage);
      resultContainer.scrollTop = resultContainer.scrollHeight;
    };

    eventSource.onerror = function () {
      eventSource.close();
      eventSource = null;
      button.disabled = false;
      button.classList.remove("disabled");
      resultContainer.innerHTML += "<p style='color:red;'>Connection lost. Retrying...</p>";

      // Retry connection after 5s
      setTimeout(() => button.click(), 5000);
    };
  });

  scrollTopBtn.addEventListener("click", () => resultContainer.scrollTop = 0);
  scrollMidBtn.addEventListener("click", () => resultContainer.scrollTop = resultContainer.scrollHeight / 2);
  scrollBottomBtn.addEventListener("click", () => resultContainer.scrollTop = resultContainer.scrollHeight);
});

