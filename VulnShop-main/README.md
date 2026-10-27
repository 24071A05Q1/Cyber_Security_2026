# 🛒 VulnShop — Vulnerable Web Application Lab



# VulnShop
🛒 VulnShop is an intentionally vulnerable Flask + SQLite web app built for cybersecurity learning and OWASP practice. It demonstrates SQL Injection, XSS, CSRF, and Broken Access Control vulnerabilities with real exploit examples and mitigation techniques. For local educational use only.

  **⚠ SECURITY NOTICE:** This application is intentionally engineered with high-severity vulnerabilities. Run exclusively on `localhost`. Never deploy to public-facing servers.

## Tech Stack
- **Backend:** Python Flask
- **Database:** SQLite
- **Frontend:** Jinja2 HTML templates + CSS
- **Target:** http://localhost:5000

---

## Setup & Installation

### 1. Install dependencies
```bash
pip install flask flask-wtf
```

### 2. Initialize the database
```bash
python database.py
```

### 3. Start the application
```bash
python app.py
```

### 4. Open in browser
```
http://localhost:5000
```

---

## Seed Credentials

| Username | Password | Role  |
|----------|----------|-------|
| admin    | admin123 | admin |
| alice    | pass123  | user  |
| bob      | bob456   | user  |

---

## Vulnerability Cheatsheet

### 1. Reflected XSS — `/search?q=`
**Exploit:**
```
http://localhost:5000/search?q=<script>alert('XSS')</script>
```
**Root cause:** `{{ query | safe }}` in `search.html` disables Jinja2 auto-escaping.  
**Fix:** Remove `| safe` — Jinja2 escapes by default.

---

### 2. SQL Injection — `/products?id=`
**Exploit:**
```
http://localhost:5000/products?id=1 OR 1=1
http://localhost:5000/products?id=0 UNION SELECT id,username,password,role FROM users
```
**Root cause:** `f"SELECT * FROM products WHERE id = {pid}"` in `app.py`.  
**Fix:** Use parameterized queries: `conn.execute("SELECT * FROM products WHERE id = ?", (pid,))`

---

### 3a. Auth Bypass (SQLi Login) — `/login`
**Exploit:**
```
Username: admin
Password: ' OR '1'='1 --
```
**Root cause:** Raw string concatenation in the login SQL query.  
**Fix:** Use parameterized queries.

### 3b. Broken Access Control — `/admin`
**Exploit:** Log in as any regular user, then visit `/admin`.  
**Root cause:** Route only checks `'user' in session`, not role.  
**Fix:**
```python
if session.get('role') != 'admin':
    abort(403)
```

---

### 4. CSRF — `/profile`
**Exploit:** Create `attack.html` and open it while logged into VulnShop:
```html
<html>
<body onload="document.forms[0].submit()">
  <form action="http://localhost:5000/profile" method="POST">
    <input name="email" value="attacker@evil.com">
  </form>
</body>
</html>
```
**Root cause:** No CSRF token validation on the profile update endpoint.  
**Fix:** Generate and validate a `secrets.token_hex(16)` token per session.

---

## Folder Structure

```
vulnshop/
├── app.py              # Flask routes (all vulnerabilities live here)
├── database.py         # DB init + seed data
├── requirements.txt    # Python dependencies
├── vulnshop.db         # SQLite DB (auto-generated)
├── README.md
├── templates/
│   ├── base.html       # Shared layout + navbar
│   ├── index.html      # Home / dashboard
│   ├── login.html      # Auth bypass lab
│   ├── register.html   # Registration
│   ├── search.html     # XSS lab
│   ├── products.html   # SQLi lab
│   ├── profile.html    # CSRF lab
│   └── admin.html      # Broken access control lab
└── static/
    └── style.css       # Dark cybersecurity theme
```

---

## Recommended Tools
- **Burp Suite Community** — intercept & replay requests
- **Firefox DevTools** — inspect DOM after XSS
- **DB Browser for SQLite** — inspect the raw database
- **curl** — CLI request crafting

---

