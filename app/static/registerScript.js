document.addEventListener("DOMContentLoaded", () =>{
    document.getElementById('regisForm').addEventListener('submit', (event) => {
        var password = document.getElementById('password').value;

        if (password.length < 8 || !/[A-Z]/.test(password) || !/\d/.test(password)) {
            event.preventDefault(); // Prevent form submission

            var errorDiv = document.getElementById('errorDiv');
            errorDiv.textContent = 'Password must be at least 8 characters long and contain at least one uppercase letter and one digit.';
            errorDiv.style.display = 'block';
        }
    });
});