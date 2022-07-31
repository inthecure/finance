document.addEventListener('DOMContentLoaded', function() {
    const togglePassword = document.querySelector('#toggle-password');
    const password = document.querySelector('#password');
    const toggleConfirmPassword = document.querySelector('#toggle-confirmation');
    const confirmPassword = document.querySelector('#confirmation');

    // For change password page only
    const toggleCurrentPassword = document.querySelector('#toggle-current-password')
    const currentPassword = document.querySelector('#current-password')

    // Make sure variable is not null
    if (togglePassword) {
        togglePassword.addEventListener('click', () => {

            // Toggle the type attribute using
            // getAttribure() method
            const type = password
                .getAttribute('type') === 'password' ?
                'text' : 'password';

            password.setAttribute('type', type);

            // Toggle the eye and bi-eye icon
            togglePassword.classList.toggle('bi-eye');

        });
    }


    // Make sure variable is not null
    if (toggleConfirmPassword) {
        toggleConfirmPassword.addEventListener('click', () => {

            // Toggle the type attribute using
            // getAttribure() method
            const type = confirmPassword
                .getAttribute('type') === 'password' ?
                'text' : 'password';

            confirmPassword.setAttribute('type', type);

            // Toggle the eye and bi-eye icon
            toggleConfirmPassword.classList.toggle('bi-eye');
        });
    }

    // Make sure variable is not null
    if (toggleCurrentPassword) {
        toggleCurrentPassword.addEventListener('click', () => {

            // Toggle the type attribute using
            // getAttribure() method
            const type = currentPassword
                .getAttribute('type') === 'password' ?
                'text' : 'password';

            currentPassword.setAttribute('type', type);

            // Toggle the eye and bi-eye icon
            toggleCurrentPassword.classList.toggle('bi-eye');

        });
    }

});