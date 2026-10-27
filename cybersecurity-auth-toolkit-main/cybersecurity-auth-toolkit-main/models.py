from database import get_db
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
