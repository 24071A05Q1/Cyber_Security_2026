document.addEventListener("DOMContentLoaded", function () {
    const passwordInput = document.getElementById("password");
    const strengthFill = document.getElementById("strengthFill");
    const strengthText = document.getElementById("strengthText");

    if (!passwordInput) return;

    passwordInput.addEventListener("input", function () {
        const val = passwordInput.value;
        const result = evaluateStrength(val);

        strengthFill.style.width = result.percentage + "%";
        strengthFill.style.backgroundColor = result.color;
        strengthText.textContent = "Strength: " + result.label;
    });

    function evaluateStrength(password) {
        if (!password) return { percentage: 0, color: "#e2e8f0", label: "None" };

        let score = 0;
        if (password.length >= 12) score += 25;
        else if (password.length >= 8) score += 10;

        if (/[A-Z]/.test(password)) score += 20;
        if (/[a-z]/.test(password)) score += 20;
        if (/\d/.test(password)) score += 20;
        if (/[^A-Za-z0-9]/.test(password)) score += 15;

        const commonBlocklist = ["password123", "qwerty", "12345678", "welcome123"];
        if (commonBlocklist.includes(password.toLowerCase())) {
            return { percentage: 10, color: "#ef4444", label: "Very Weak (Breached)" };
        }

        if (score < 40) {
            return { percentage: 25, color: "#ef4444", label: "Weak" };
        } else if (score < 70) {
            return { percentage: 50, color: "#f59e0b", label: "Medium" };
        } else if (score < 95) {
            return { percentage: 75, color: "#3b82f6", label: "Strong" };
        } else {
            return { percentage: 100, color: "#10b981", label: "Very Strong" };
        }
    }
});
