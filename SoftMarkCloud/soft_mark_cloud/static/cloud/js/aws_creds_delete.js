const token = document.cookie.split('=')[1];
document.getElementById("delete-button").addEventListener("click", function() {
    console.error('Token ' + token)
    fetch("/account_manager/",
        {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': token
            },
        });
    location.href = "/account_manager/";
});