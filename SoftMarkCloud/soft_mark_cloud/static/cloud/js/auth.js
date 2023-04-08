function validateForm() {
    var fields_input = document.querySelectorAll(".form-control");

    fields_input.forEach(function(e) {
        if (e.value == "") {
            return false;
        }
    })

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
//                console.log('Form submitted successfully');
//                console.log(this);
                window.location.href = '/';
            } else {
//                console.error('Form submission failed');
                let error = document.querySelector('.error-message');
                let error_child = document.querySelector('.error-message ul');
                let errors_message = JSON.parse(this.response)['errors'];
                let ul_error = document.createElement("ul");
                for (let error_message in errors_message) {
                    let field_error_messages = errors_message[error_message]
                    for (let err_msg_i in field_error_messages) {
                        let li_error = document.createElement("li");
                        li_error.textContent = field_error_messages[err_msg_i];
                        ul_error.appendChild(li_error);
                    }
                }
                error.replaceChild(ul_error, error_child);

                console.log(this);
            }
        };

}
});