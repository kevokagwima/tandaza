async function sendFetchRequest() {
  try {
    const response = await fetch("/confirm-payment/", {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (response.ok) {
      alert("ok");
      console.log("Fetch request successful:", response.status);
    } else {
      alert("error");
      console.error("Fetch request failed:", response.status);
    }
  } catch (error) {
    console.error("Error during fetch request:", error);
  }
}

// Call the function to send the fetch request
document.addEventListener("DOMContentLoaded", (event) => {
  sendFetchRequest();
});
