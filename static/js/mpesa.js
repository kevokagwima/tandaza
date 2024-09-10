async function sendFetchRequest() {
  try {
    const response = await fetch("/confirm-payment", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        result_code: "your_result_code",
        transaction_id: "your_transaction_id",
      }),
    });

    if (response.ok) {
      alert("ok");
      console.log("Fetch request successful:", response.status);
    } else {
      alert("eror");
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
