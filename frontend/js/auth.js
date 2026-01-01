/**
 * Authentication Page JavaScript
 * Handles student login/signup
 */

document.addEventListener("DOMContentLoaded", function () {

    // ---------- AUTO REDIRECT IF ALREADY LOGGED IN ----------
    if (isLoggedIn()) {
        const user = getUser();
        if (user?.role === "admin") {
            window.location.href = "/admin";
        } else {
            window.location.href = "/dashboard";
        }
        return;
    }

    const loginStep = document.getElementById("loginStep");
    const registerStep = document.getElementById("registerStep");
    const loginForm = document.getElementById("loginForm");
    const registerForm = document.getElementById("registerForm");
    const showRegister = document.getElementById("showRegister");
    const showLogin = document.getElementById("showLogin");
    const alertContainer = document.getElementById("alertContainer");

    // ---------- ALERT ----------
    function showAlert(message, type = "error") {
        alertContainer.innerHTML = `
            <div class="alert alert-${type}">
                ${message}
            </div>
        `;
        setTimeout(() => (alertContainer.innerHTML = ""), 4000);
    }

    // ---------- TOGGLE ----------
    showRegister?.addEventListener("click", (e) => {
        e.preventDefault();
        loginStep.classList.add("hidden");
        registerStep.classList.remove("hidden");
    });

    showLogin?.addEventListener("click", (e) => {
        e.preventDefault();
        registerStep.classList.add("hidden");
        loginStep.classList.remove("hidden");
    });

    // ---------- LOGIN ----------
    loginForm?.addEventListener("submit", async function (e) {
        e.preventDefault();

        const email = document.getElementById("email").value.trim();
        const password = document.getElementById("password").value;

        const submitBtn = loginForm.querySelector("button[type='submit']");
        submitBtn.disabled = true;
        submitBtn.textContent = "Logging in...";

        try {
            const response = await fetch("/auth/login", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password })
            });

            const result = await response.json();

            if (result.success) {
                localStorage.setItem("token", result.token);
                localStorage.setItem("user", JSON.stringify(result.user));

                // ✅ ROLE-BASED REDIRECT
                if (result.user.role === "admin") {
                    window.location.href = "/admin";
                } else {
                    window.location.href = "/dashboard";
                }
            } else {
                showAlert(result.message || "Login failed");
            }
        } catch (err) {
            showAlert("Server connection error");
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = "Login";
        }
    });

    // ---------- REGISTER ----------
    registerForm?.addEventListener("submit", async function (e) {
        e.preventDefault();

        const payload = {
            username: document.getElementById("fullName").value.trim(),
            email: document.getElementById("regEmail").value.trim(),
            password: document.getElementById("regPassword").value,
            mobile_number: document.getElementById("phone").value.trim(),
            dcet_reg_number: document.getElementById("regNo").value.trim(),
            college_name: document.getElementById("college").value.trim()
        };

        const submitBtn = registerForm.querySelector("button[type='submit']");
        submitBtn.disabled = true;
        submitBtn.textContent = "Registering...";

        try {
            const response = await fetch("/auth/register", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            const result = await response.json();

            if (result.success) {
                localStorage.setItem("token", result.token);
                localStorage.setItem("user", JSON.stringify(result.user));

                // ✅ NEW USERS → DASHBOARD
                window.location.href = "/dashboard";
            } else {
                showAlert(result.message || "Registration failed");
            }
        } catch (err) {
            showAlert("Server connection error");
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = "Register";
        }
    });
});
