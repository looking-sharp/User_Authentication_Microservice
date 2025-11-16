// Forms
const registerForm = document.getElementById("register");
const loginForm = document.getElementById("login");
const logoutForm = document.getElementById("logout");
const verifyForm = document.getElementById("verify");

// Response areas
const registerResponse = document.getElementById("registerResponse");
const loginResponse = document.getElementById("loginResponse");
const logoutResponse = document.getElementById("logoutResponse");
const verifyResponse = document.getElementById("verifyResponse");

// Auth state (holds last JWT from successful login)
let token = null;

// ---------------------- Register ----------------------
registerForm.addEventListener("submit", async function (event) {
    event.preventDefault();

    const email = document.getElementById("regEmail").value;
    const name = document.getElementById("regName").value;
    const password = document.getElementById("regPassword").value;

    const payload = { email, name, password };

    try {
        const response = await fetch("/auth/register", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });

        const data = await response.json();
        registerResponse.textContent = JSON.stringify(data, null, 2);

        if (response.ok) {
            console.log("User created successfully:", data);
        } else {
            console.warn("Error creating user:", data);
        }
    } catch (error) {
        console.error("Fetch error:", error);
        registerResponse.textContent = "Fetch error: " + error;
    }
});

// ---------------------- Login ----------------------
loginForm.addEventListener("submit", async function (event) {
    event.preventDefault();

    const email = document.getElementById("loginEmail").value;
    const password = document.getElementById("loginPassword").value;
    const payload = { email, password };

    try {
        const response = await fetch("/auth/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });

        const data = await response.json();
        loginResponse.textContent = JSON.stringify(data, null, 2);

        if (response.ok) {
            token = data.token;  // store JWT for later logout
            console.log("Login successful:", data);
        } else {
            console.warn("Login error:", data);
            token = null;
        }
    } catch (error) {
        console.error("Fetch error:", error);
        loginResponse.textContent = "Fetch error: " + error;
        token = null;
    }
});

// ---------------------- Logout (separate UI) ----------------------
logoutForm.addEventListener("submit", async function (event) {
    event.preventDefault();

    if (!token) {
        logoutResponse.textContent = "No JWT available. Please perform a successful Login first.";
        console.warn("Logout attempted with no token stored.");
        return;
    }

    try {
        const response = await fetch("/auth/logout", {
            method: "POST",
            headers: {
                Authorization: "Bearer " + token,
            },
        });

        const data = await response.json();
        logoutResponse.textContent = JSON.stringify(data, null, 2);

        // Clear stored token after logout attempt
        token = null;

        console.log("Logout response:", data);
    } catch (error) {
        console.error("Fetch error:", error);
        logoutResponse.textContent = "Fetch error: " + error;
    }
});

// ---------------------- Verify (short token) ----------------------
verifyForm.addEventListener("submit", async function (event) {
    event.preventDefault();

    const shortToken = document.getElementById("shortToken").value;

    try {
        const response = await fetch(`/auth/user-by-short/${encodeURIComponent(shortToken)}`);
        const data = await response.json();
        verifyResponse.textContent = JSON.stringify(data, null, 2);
    } catch (error) {
        console.error("Fetch error:", error);
        verifyResponse.textContent = "Fetch error: " + error;
    }
});
