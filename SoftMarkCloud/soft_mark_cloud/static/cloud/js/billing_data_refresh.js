const refresh_button = document.getElementById("billing-refresh-button");

if (refresh_button) {
    refresh_button.addEventListener("click", function() {
        location.href = "/billing/?refresh";
    });
}
