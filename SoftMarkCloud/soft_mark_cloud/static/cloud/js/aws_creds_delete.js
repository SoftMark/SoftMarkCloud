const token = get_csrftoken();
const del_button = document.getElementById("delete-button");

if (del_button) {
    del_button.addEventListener("click", function() {
        fetch("/account_manager/",
            {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': token
                },
            });
        location.href = "/account_manager/";
    });
}
