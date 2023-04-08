function validateForm() {
    var username = document.forms[0]["username"].value;
    var email = document.forms[0]["email"].value;
    var password1 = document.forms[0]["password1"].value;
    var password2 = document.forms[0]["password2"].value;

    if (username == "" || email == "" || password1 == "" || password2 == "") {
        alert("Please fill in all fields");
        return false;
    }

    if (password1 != password2) {
        alert("Passwords do not match");
        return false;
    }

    return true;
}

document.querySelector('form.auth-form').addEventListener('submit', function(event) {
    event.preventDefault();
    if (validateForm()) {
        const xhr = new XMLHttpRequest();
        const formData = new FormData(this);
        xhr.open('POST', '');
        xhr.send(formData);

        xhr.onload = function() {
            if (xhr.status === 200) {
                console.log('Form submitted successfully');
                console.log(this);
                window.location.href = '/';
            } else {
                console.error('Form submission failed');
                console.log(this);
            }
        };

}
});