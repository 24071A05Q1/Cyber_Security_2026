# Cybersecurity Authentication Toolkit

## Executive Summary
The **Cybersecurity Authentication Toolkit** is a secure, production-ready prototype built to demonstrate defense-in-depth principles for modern web application authentication workflows. It directly mitigates critical **OWASP Top 10** risks, including Broken Authentication, Injection attacks, Cross-Site Request Forgery (CSRF), and security misconfigurations.

---

## Key Security Controls & Design Decisions

### 1. Secure Password Storage & Hashing (Bcrypt)
* **Mechanism:** Passwords are never stored in plaintext. They undergo rigorous cryptographic salting and hashing utilizing **Bcrypt** with a work factor cost of `12`.
* **Why MD5/SHA1 are Unsafe:** MD5 and SHA-1 are fast cryptographic hash algorithms designed for speed. Because of this high velocity, attackers can compute billions of guesses per second utilizing graphics processing clusters or dictionary rainbow tables. Bcrypt introduces an intentional delay mechanism (adaptive work factor) alongside unique per-user salts, rendering brute-force extraction computationally infeasible.

### 2. Brute-Force & Credential Stuffing Defense (Account Lockout)
* **Mechanism:** Failed login attempts are tracked per user profile in the database. Sustaining 5 consecutive failed sign-in attempts triggers a forced **15-minute account lockout cooldown**.
* **Why:** Thwarts automated botnet-driven credential-stuffing campaigns that test exposed datasets rapidly against target platforms.

### 3. User Enumeration Mitigation
* **Mechanism:** The application returns generic warning responses (`"Invalid username or password"`) on authentication failures. Furthermore, when an unknown username is submitted, the backend runs a dummy bcrypt check to mimic real processing intervals.
* **Why:** Prevents malicious actors from probing database existence models to discover valid registered accounts.

### 4. Session Hijacking & Fixation Defenses
* **Mechanism:** Session tokens are transmitted via cryptographically signed, HTTP-only, SameSite cookies. Session identifiers are systematically regenerated and cleared post-authentication.
* **Why:** The `HttpOnly` attribute completely prevents client-side Cross-Site Scripting (XSS) payloads from reading document cookies via JavaScript. Session regeneration blocks session fixation attacks.

### 5. Injection & CSRF Defenses
* **Mechanism:** All database operations utilize **parameterized queries / prepared statements** via SQLite connectors, and state-changing forms are validated using cryptographically signed **Flask-WTF CSRF tokens**.
* **Why:** Completely decouples user-supplied inputs from database execution structures, eliminating SQL Injection (SQLi) and Cross-Site Request Forgery (CSRF) vulnerabilities.

### 6. Security Headers
* **Mechanism:** The application enforces strict response directives including:
  * `Content-Security-Policy (CSP)`
  * `X-Frame-Options: DENY` (Clickjacking defense)
  * `X-Content-Type-Options: nosniff` (MIME-sniffing defense)