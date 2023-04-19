// TODO: Implement import from cookie.js

function getCookie(name) {
  var cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    var cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      var cookie = cookies[i].trim();
      // Does this cookie string begin with the name we want?
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

function get_csrftoken() {
    var token = getCookie('csrftoken')
    if (token == null) {
        alert("Error. Sing Out and try again. CSRFToken not found.")
    }
    return token
}

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
