import os

# Define the folder structure and file contents
files = {
    "requirements.txt": """Flask==3.0.2
Flask-WTF==1.2.1
Flask-Limiter==3.5.0
bcrypt==4.1.2
pyotp==2.9.0
qrcode==7.4.2
email-validator==2.1.1
WTForms==3.1.2
""",

    "database.py": """import sqlite3
from flask import g

DATABASE = 'auth_toolkit.db'

def get_db():
    ""\"Opens a new database connection if there is none for the current application context.""\"
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def close_db(exception):
    ""\"Closes the database at the end of the request.""\"
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db(app):
    ""\"Initializes the SQLite database tables using parameterized schemas.""\"
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        
        # User table storing credential metadata securely
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                failed_login_attempts INTEGER DEFAULT 0,
                lockout_until TIMESTAMP DEFAULT NULL,
                totp_secret TEXT DEFAULT NULL,
                is_2fa_enabled BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Active session tracking table to manage invalidations & timeouts
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS active_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_token TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        db.commit()
""",

    "models.py": """from database import get_db
import datetime

class User:
    @staticmethod
    def create(username, email, password_hash):
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email, password_hash)
        )
        db.commit()
        return cursor.lastrowid

    @staticmethod
    def get_by_username(username):
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        return cursor.fetchone()

    @staticmethod
    def get_by_id(user_id):
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        return cursor.fetchone()

    @staticmethod
    def update_failed_attempts(user_id, attempts, lockout_until):
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "UPDATE users SET failed_login_attempts = ?, lockout_until = ? WHERE id = ?",
            (attempts, lockout_until, user_id)
        )
        db.commit()

    @staticmethod
    def reset_failed_attempts(user_id):
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "UPDATE users SET failed_login_attempts = 0, lockout_until = NULL WHERE id = ?",
            (user_id,)
        )
        db.commit()

    @staticmethod
    def enable_totp(user_id, secret):
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "UPDATE users SET totp_secret = ?, is_2fa_enabled = 1 WHERE id = ?",
            (secret, user_id)
        )
        db.commit()

class SessionManager:
    @staticmethod
    def create_session(user_id, token, expires_in_minutes=30):
        db = get_db()
        cursor = db.cursor()
        expires_at = datetime.datetime.utcnow() + datetime.timedelta(minutes=expires_in_minutes)
        cursor.execute(
            "INSERT INTO active_sessions (user_id, session_token, expires_at) VALUES (?, ?, ?)",
            (user_id, token, expires_at)
        )
        db.commit()

    @staticmethod
    def get_session(token):
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "SELECT * FROM active_sessions WHERE session_token = ? AND expires_at > ?",
            (token, datetime.datetime.utcnow())
        )
        return cursor.fetchone()

    @staticmethod
    def delete_session(token):
        db = get_db()
        cursor = db.cursor()
        cursor.execute("DELETE FROM active_sessions WHERE session_token = ?", (token,))
        db.commit()
""",

    "auth_utils.py": """import re
import bcrypt
import pyotp
import io
import base64
import qrcode

BREACHED_PASSWORD_BLOCKLIST = {
    "password123", "qwerty", "12345678", "welcome123", 
    "admin123", "letmein", "password!", "iloveyou"
}

def validate_password_policy(password):
    if len(password) < 12:
        return False, "Password must be at least 12 characters long."
    if not re.search(r'[A-Z]', password):
        return False, "Password must include at least one uppercase letter."
    if not re.search(r'[a-z]', password):
        return False, "Password must include at least one lowercase letter."
    if not re.search(r'\\d', password):
        return False, "Password must include at least one numeric digit."
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must include at least one special character."
    if password.lower() in BREACHED_PASSWORD_BLOCKLIST:
        return False, "This password appears in known data breaches. Choose another."
    return True, "Password policy satisfied."

def hash_password(password):
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password, hashed_password):
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def generate_totp_secret():
    return pyotp.random_base32()

def get_totp_uri(secret, username):
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=username, issuer_name="CyberSecAuthToolkit")

def generate_qr_code(uri):
    qr = qrcode.make(uri)
    buffered = io.BytesIO()
    qr.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

def verify_totp(secret, token):
    if not secret:
        return False
    totp = pyotp.TOTP(secret)
    return totp.verify(token, valid_window=1)
""",

    "app.py": """from flask import Flask, render_template
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from database import init_db, close_db
from routes import auth_bp

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret-production-random-key-change-me'
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

csrf = CSRFProtect(app)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

app.teardown_appcontext(close_db)
app.register_blueprint(auth_bp)

@app.after_request
def set_security_headers(response):
    response.headers['Content-Security-Policy'] = "default-src 'self' https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; script-src 'self' 'unsafe-inline';"
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

@app.errorhandler(429)
def ratelimit_handler(e):
    return render_template('login.html', error="Too many requests. Please try again later."), 429

if __name__ == '__main__':
    init_db(app)
    app.run(debug=True, port=5000)
""",

    "routes.py": """from flask import Blueprint, render_template, request, redirect, url_for, session
from models import User, SessionManager
from auth_utils import validate_password_policy, hash_password, verify_password, generate_totp_secret, get_totp_uri, generate_qr_code, verify_totp
import datetime
import secrets
import bcrypt

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def index():
    if 'session_token' in session:
        return redirect(url_for('auth.dashboard'))
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not username or not email or not password:
            return render_template('register.html', error="All fields are required.")

        is_valid, msg = validate_password_policy(password)
        if not is_valid:
            return render_template('register.html', error=msg)

        if User.get_by_username(username):
            return render_template('register.html', error="Registration failed. Check parameters.")

        try:
            hashed = hash_password(password)
            User.create(username, email, hashed)
            return redirect(url_for('auth.login', success="Registration successful. Please sign in."))
        except Exception:
            return render_template('register.html', error="An error occurred during registration.")

    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = User.get_by_username(username)

        if user and user['lockout_until']:
            lockout_time = datetime.datetime.fromisoformat(user['lockout_until'])
            if datetime.datetime.utcnow() < lockout_time:
                return render_template('login.html', error="Invalid credentials or account temporarily locked.")
            else:
                User.reset_failed_attempts(user['id'])

        credentials_valid = False
        if user:
            credentials_valid = verify_password(password, user['password_hash'])
        else:
            dummy_hash = b'$2b$12$KIXp3U5v1X1X1X1X1X1X1OuK3p1X1X1X1X1X1X1X1X1X1X1X1X1X2'
            bcrypt.checkpw(password.encode('utf-8'), dummy_hash)

        if not user or not credentials_valid:
            if user:
                failed_attempts = user['failed_login_attempts'] + 1
                lockout_until = None
                if failed_attempts >= 5:
                    lockout_until = (datetime.datetime.utcnow() + datetime.timedelta(minutes=15)).isoformat()
                User.update_failed_attempts(user['id'], failed_attempts, lockout_until)
            return render_template('login.html', error="Invalid username or password.")

        User.reset_failed_attempts(user['id'])

        if user['is_2fa_enabled']:
            session['pending_2fa_user_id'] = user['id']
            return redirect(url_for('auth.verify_2fa'))

        session.clear()
        token = secrets.token_hex(32)
        SessionManager.create_session(user['id'], token, expires_in_minutes=20)
        session['session_token'] = token
        session['user_id'] = user['id']

        return redirect(url_for('auth.dashboard'))

    return render_template('login.html')

@auth_bp.route('/setup-2fa', methods=['GET', 'POST'])
def setup_2fa():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user = User.get_by_id(session['user_id'])
    if user['is_2fa_enabled']:
        return redirect(url_for('auth.dashboard'))

    if request.method == 'POST':
        secret = request.form.get('secret')
        token = request.form.get('token')
        if verify_totp(secret, token):
            User.enable_totp(user['id'], secret)
            return redirect(url_for('auth.dashboard'))
        return render_template('setup_2fa.html', secret=secret, qr_code=generate_qr_code(get_totp_uri(secret, user['username'])), error="Invalid verification code.")

    secret = generate_totp_secret()
    uri = get_totp_uri(secret, user['username'])
    qr_code = generate_qr_code(uri)
    return render_template('setup_2fa.html', secret=secret, qr_code=qr_code)

@auth_bp.route('/verify-2fa', methods=['GET', 'POST'])
def verify_2fa():
    if 'pending_2fa_user_id' not in session:
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        token = request.form.get('token')
        user_id = session['pending_2fa_user_id']
        user = User.get_by_id(user_id)

        if verify_totp(user['totp_secret'], token):
            session.pop('pending_2fa_user_id', None)
            session.clear()
            token_hex = secrets.token_hex(32)
            SessionManager.create_session(user['id'], token_hex, expires_in_minutes=20)
            session['session_token'] = token_hex
            session['user_id'] = user['id']
            return redirect(url_for('auth.dashboard'))

        return render_template('verify_2fa.html', error="Invalid authentication code.")

    return render_template('verify_2fa.html')

@auth_bp.route('/dashboard')
def dashboard():
    token = session.get('session_token')
    if not token:
        return redirect(url_for('auth.login'))

    active_sess = SessionManager.get_session(token)
    if not active_sess:
        session.clear()
        return redirect(url_for('auth.login'))

    user = User.get_by_id(active_sess['user_id'])
    return render_template('dashboard.html', user=user)

@auth_bp.route('/logout', methods=['POST'])
def logout():
    token = session.get('session_token')
    if token:
        SessionManager.delete_session(token)
    session.clear()
    return redirect(url_for('auth.login'))
""",

    "static/css/style.css": """:root {
    --bg-color: #f8fafc;
    --card-bg: #ffffff;
    --text-primary: #1e293b;
    --text-secondary: #64748b;
    --accent-color: #2563eb;
    --accent-hover: #1d4ed8;
    --border-color: #cbd5e1;
    --error-bg: #fee2e2;
    --error-text: #991b1b;
    --success-bg: #dcfce7;
    --success-text: #166534;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    background-color: var(--bg-color);
    color: var(--text-primary);
    margin: 0;
    padding: 0;
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
}

.toolkit-container {
    background-color: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    width: 100%;
    max-width: 420px;
    padding: 2.5rem;
    box-sizing: border-box;
}

h2 {
    margin-top: 0;
    font-size: 1.5rem;
    color: var(--text-primary);
    text-align: center;
    margin-bottom: 1.5rem;
}

.form-group {
    margin-bottom: 1.25rem;
}

label {
    display: block;
    font-size: 0.875rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
    color: var(--text-primary);
}

input[type="text"],
input[type="email"],
input[type="password"] {
    width: 100%;
    padding: 0.75rem;
    border: 1px solid var(--border-color);
    border-radius: 6px;
    font-size: 1rem;
    background-color: #ffffff;
    color: var(--text-primary);
    box-sizing: border-box;
}

input:focus {
    outline: none;
    border-color: var(--accent-color);
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

button {
    width: 100%;
    padding: 0.75rem;
    background-color: var(--accent-color);
    color: white;
    border: none;
    border-radius: 6px;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
}

button:hover {
    background-color: var(--accent-hover);
}

.alert-error {
    background-color: var(--error-bg);
    color: var(--error-text);
    padding: 0.75rem;
    border-radius: 6px;
    font-size: 0.875rem;
    margin-bottom: 1rem;
    border: 1px solid #f87171;
    text-align: center;
}

.alert-success {
    background-color: var(--success-bg);
    color: var(--success-text);
    padding: 0.75rem;
    border-radius: 6px;
    font-size: 0.875rem;
    margin-bottom: 1rem;
    border: 1px solid #4ade80;
    text-align: center;
}

.strength-container {
    margin-top: 0.5rem;
}

.strength-bar-bg {
    background-color: #e2e8f0;
    height: 6px;
    border-radius: 3px;
    overflow: hidden;
    margin-bottom: 0.25rem;
}

.strength-bar-fill {
    height: 100%;
    width: 0%;
    transition: width 0.3s ease, background-color 0.3s ease;
}

.strength-label {
    font-size: 0.75rem;
    color: var(--text-secondary);
    font-weight: 500;
}

.switch-auth {
    text-align: center;
    margin-top: 1.5rem;
    font-size: 0.875rem;
    color: var(--text-secondary);
}

.switch-auth a {
    color: var(--accent-color);
    text-decoration: none;
    font-weight: 600;
}
""",

    "static/js/strength.js": """document.addEventListener("DOMContentLoaded", function () {
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
        if (/\\d/.test(password)) score += 20;
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
""",

    "templates/base.html": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cybersecurity Authentication Toolkit</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
    <div class="toolkit-container">
        {% block content %}{% endblock %}
    </div>
    {% block scripts %}{% endblock %}
</body>
</html>
""",

    "templates/register.html": """{% extends "base.html" %}
{% block content %}
<h2>Create Account</h2>
{% if error %}
    <div class="alert-error">{{ error }}</div>
{% endif %}
<form method="POST" action="{{ url_for('auth.register') }}">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
    <div class="form-group">
        <label for="username">Username</label>
        <input type="text" id="username" name="username" required autocomplete="username">
    </div>
    <div class="form-group">
        <label for="email">Email Address</label>
        <input type="email" id="email" name="email" required autocomplete="email">
    </div>
    <div class="form-group">
        <label for="password">Password (Min 12 chars)</label>
        <input type="password" id="password" name="password" required autocomplete="new-password">
        <div class="strength-container">
            <div class="strength-bar-bg">
                <div id="strengthFill" class="strength-bar-fill"></div>
            </div>
            <div id="strengthText" class="strength-label">Strength: None</div>
        </div>
    </div>
    <button type="submit">Register Account</button>
</form>
<div class="switch-auth">
    Already have an account? <a href="{{ url_for('auth.login') }}">Sign In</a>
</div>
{% endblock %}
{% block scripts %}
<script src="{{ url_for('static', filename='js/strength.js') }}"></script>
{% endblock %}
""",

    "templates/login.html": """{% extends "base.html" %}
{% block content %}
<h2>Secure Sign In</h2>
{% if error %}
    <div class="alert-error">{{ error }}</div>
{% endif %}
{% if success %}
    <div class="alert-success">{{ success }}</div>
{% endif %}
<form method="POST" action="{{ url_for('auth.login') }}">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
    <div class="form-group">
        <label for="username">Username</label>
        <input type="text" id="username" name="username" required autocomplete="username">
    </div>
    <div class="form-group">
        <label for="password">Password</label>
        <input type="password" id="password" name="password" required autocomplete="current-password">
    </div>
    <button type="submit">Authenticate</button>
</form>
<div class="switch-auth">
    Need an account? <a href="{{ url_for('auth.register') }}">Register</a>
</div>
{% endblock %}
""",

    "templates/setup_2fa.html": """{% extends "base.html" %}
{% block content %}
<h2>Configure Multi-Factor Auth</h2>
<p style="font-size: 0.875rem; text-align: center; color: var(--text-secondary);">Scan this QR code using Google Authenticator.</p>
{% if error %}
    <div class="alert-error">{{ error }}</div>
{% endif %}
<div style="text-align: center; margin-bottom: 1rem;">
    <img src="data:image/png;base64,{{ qr_code }}" alt="TOTP QR Code" style="max-width: 180px; border-radius: 4px; border: 1px solid var(--border-color);">
</div>
<form method="POST" action="{{ url_for('auth.setup_2fa') }}">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
    <input type="hidden" name="secret" value="{{ secret }}">
    <div class="form-group">
        <label for="token">6-Digit Authenticator Code</label>
        <input type="text" id="token" name="token" maxlength="6" required autocomplete="one-time-code">
    </div>
    <button type="submit">Confirm & Enable 2FA</button>
</form>
{% endblock %}
""",

    "templates/verify_2fa.html": """{% extends "base.html" %}
{% block content %}
<h2>Two-Factor Verification</h2>
{% if error %}
    <div class="alert-error">{{ error }}</div>
{% endif %}
<form method="POST" action="{{ url_for('auth.verify_2fa') }}">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
    <div class="form-group">
        <label for="token">Enter 6-Digit Code</label>
        <input type="text" id="token" name="token" maxlength="6" required autocomplete="one-time-code">
    </div>
    <button type="submit">Verify Code</button>
</form>
{% endblock %}
""",

    "templates/dashboard.html": """{% extends "base.html" %}
{% block content %}
<h2>Secure Dashboard</h2>
<div style="background-color: #f1f5f9; padding: 1rem; border-radius: 6px; margin-bottom: 1.5rem; font-size: 0.9rem;">
    <p style="margin: 0 0 0.5rem 0;"><strong>Username:</strong> {{ user.username }}</p>
    <p style="margin: 0 0 0.5rem 0;"><strong>Email:</strong> {{ user.email }}</p>
    <p style="margin: 0;"><strong>2FA Status:</strong> {% if user.is_2fa_enabled %}Enabled ✅{% else %}Disabled ❌{% endif %}</p>
</div>

{% if not user.is_2fa_enabled %}
<div style="margin-bottom: 1.5rem;">
    <a href="{{ url_for('auth.setup_2fa') }}" style="display: block; text-align: center; padding: 0.6rem; background-color: #059669; color: white; text-decoration: none; border-radius: 6px; font-size: 0.9rem; font-weight: 600;">Enable Google Authenticator 2FA</a>
</div>
{% endif %}

<form method="POST" action="{{ url_for('auth.logout') }}">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
    <button type="submit" style="background-color: #ef4444;">Terminate Session (Logout)</button>
</form>
{% endblock %}
"""
}

def create_project():
    print("🚀 Generating Cybersecurity Authentication Toolkit project structure...")
    for filepath, content in files.items():
        # Create directories if they don't exist
        directory = os.path.dirname(filepath)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            
        # Write the file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Created: {filepath}")
        
    print("\n✅ Setup complete! All folders and files have been generated automatically.")
    print("Now run the following commands to start the app:")
    print("1. pip install -r requirements.txt")
    print("2. python app.py")

if __name__ == "__main__":
    create_project()