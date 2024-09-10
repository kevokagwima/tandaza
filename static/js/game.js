let countdownTime = 30;

function startTimer() {
  const timerDisplay = document.getElementById("timer");
  const countdownInterval = setInterval(() => {
    let minutes = Math.floor(countdownTime / 60);
    let seconds = countdownTime % 60;

    // Format time to always show two digits
    timerDisplay.textContent = `${minutes}:${
      seconds < 10 ? "0" : ""
    }${seconds}`;

    // Decrease countdown time
    countdownTime--;

    // Check if time is up
    if (countdownTime < 0) {
      clearInterval(countdownInterval);
      document.getElementById("quizForm").submit(); // Auto-submit the form
    }
  }, 1000);
}

window.onload = startTimer;
