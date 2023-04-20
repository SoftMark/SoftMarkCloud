const refresh_button = document.getElementById("refresh-button");

if (refresh_button) {
    refresh_button.addEventListener("click", function() {
        location.href = "/cloud_view/?refresh";
    });
}
