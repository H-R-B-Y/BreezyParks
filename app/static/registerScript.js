document.addEventListener("DOMContentLoaded", () =>{
    document.getElementById('regisForm').addEventListener('submit', (event) => {
        var errorDiv = document.getElementById('errorDiv');
        var password = document.getElementById('password').value;
        var email = document.getElementById('email').value;

        if(!/^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$/.test(email)){
            event.preventDefault(); // Prevent form submission
            errorDiv.textContent += "Email address does not appear to be valid.\n"
            errorDiv.style.display = 'block';
        }

        if (password.length < 8 || !/[A-Z]/.test(password) || !/\d/.test(password)) {
            event.preventDefault(); // Prevent form submission
            errorDiv.textContent += 'Password must be at least 8 characters long and contain at least one uppercase letter and one digit.\n';
            errorDiv.style.display = 'block';
        }
    });
});