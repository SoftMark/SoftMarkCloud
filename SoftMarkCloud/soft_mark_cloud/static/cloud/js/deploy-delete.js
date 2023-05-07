const token = get_csrftoken();
const del_button = document.getElementById("deploy-delete-button");

if (del_button) {
    del_button.addEventListener("click", function() {
        fetch("/deploy/",
            {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': token
                },
            });
        location.href = "/deploy/";
    });
}