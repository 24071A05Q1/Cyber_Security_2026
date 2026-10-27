from flask import Blueprint, render_template, request, redirect, url_for, session
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
