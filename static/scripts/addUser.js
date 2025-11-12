const registerForm = document.getElementById("register");
const loginForm = document.getElementById("login");
const verifyForm = document.getElementById("verify");
const logout = document.getElementById("logoutBtn");

const registerResponse = document.getElementById("registerResponse");
const loginResponse = document.getElementById("loginResponse");
const verifyResponse = document.getElementById("verifyResponse")

registerForm.addEventListener('submit', async function(event) {
    event.preventDefault();
    const email = document.getElementById('regEmail').value;
    const name = document.getElementById('regName').value;
    const password = document.getElementById('regPassword').value;

    const payload = { email, name, password };

    try {
        const response = await fetch('/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await response.json();
        registerResponse.textContent = JSON.stringify(data, null, 2);
        if (response.ok) {
            console.log('User created successfully:', data);
        } else {
            console.warn('Error creating user:', data);
        }
    } catch (error) {
        console.error('Fetch error:', error);
        registerResponse.textContent = 'Fetch error: ' + error;
    }
});

let token = null; 
const logoutBtn = document.getElementById('logoutBtn');
const deleteBtn = document.getElementById('deleteBtn');

loginForm.addEventListener('submit', async function(event) {
    event.preventDefault();

    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;
    const payload = { email, password };

    try {
        const response = await fetch('/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await response.json();
        loginResponse.textContent = JSON.stringify(data, null, 2);

        if (response.ok) {
            token = data.token;
            logoutBtn.style.display = "initial";
            deleteBtn.style.display = "initial";
            document.getElementById("loginBtn").style.display = "none";
            console.log('Login successful:', data);
        } else {
            console.warn('Login error:', data);
            token = null;
        }
    } catch (error) {
        console.error('Fetch error:', error);
        loginResponse.textContent = 'Fetch error: ' + error;
        token = null;
    }
});

logoutBtn.addEventListener('click', async function() {
    if (!token) {
        alert('No token found. Please log in first.');
        return;
    }
    try {
        const response = await fetch('/auth/logout', {
            method: 'POST',
            headers: { 
                'Authorization': 'Bearer ' + token
            }
        });
        const data = await response.json();
        token = null;
        loginResponse.textContent = JSON.stringify(data, null, 2);

        logoutBtn.style.display = "none";
        deleteBtn.style.display = "none";
        document.getElementById("loginBtn").style.display = "initial";
        console.log('Logout successful:', data);
    } catch (error) {
        console.error('Fetch error:', error);
        loginResponse.textContent = 'Fetch error: ' + error;
    }
});

deleteBtn.addEventListener('click', async function() {
    if (!token) {
        alert('No token found. Please log in first.');
        return;
    }
    try {
        const response = await fetch('/auth/delete-account', {
            method: 'POST',
            headers: { 
                'Authorization': 'Bearer ' + token
            }
        });
        const data = await response.json();
        token = null;
        loginResponse.textContent = JSON.stringify(data, null, 2);

        logoutBtn.style.display = "none";
        deleteBtn.style.display = "none";
        document.getElementById("loginBtn").style.display = "initial";
        console.log('Deletion successful:', data);
    } catch (error) {
        console.error('Fetch error:', error);
        loginResponse.textContent = 'Fetch error: ' + error;
    }
});

verifyForm.addEventListener('submit', async function(event) {
    event.preventDefault();
    const token = document.getElementById("shortToken").value;
    try {
        const response = await fetch(`/auth/user-by-short/${token}`)
        const data = await response.json();
        verifyResponse.textContent = JSON.stringify(data, null, 2);
    }
    catch (error) {
        console.error('Fetch error:', error);
        verifyResponse.textContent = 'Fetch error: ' + error;
    }
});