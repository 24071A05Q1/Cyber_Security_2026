import re
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
    if not re.search(r'\d', password):
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
