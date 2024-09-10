const alerts = document.querySelectorAll(".alert");
const close_alert = document.querySelectorAll("#close");

close_alert.forEach((x) => {
  x.addEventListener("click", () => {
    alert = x.parentElement;
    alert.style.display = "none";
  });
});

const account = document.querySelector(".account-box");
const account_info = document.querySelector(".account-info");

account.addEventListener("click", () => {
  account_info.classList.toggle("show-account-info");
});

const burger = document.querySelector(".burger");
const side_nav = document.querySelector(".side-nav");
const close_nav = document.querySelector("#close-nav");

burger.addEventListener("click", () => {
  side_nav.classList.toggle("show-side-nav");
});

window.addEventListener("scroll", () => {
  side_nav.classList.remove("show-side-nav");
});

close_nav.addEventListener("click", () => {
  side_nav.classList.remove("show-side-nav");
});
