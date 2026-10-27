import sqlite3
from flask import g

DATABASE = 'auth_toolkit.db'

def get_db():
    """Opens a new database connection if there is none for the current application context."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def close_db(exception):
    """Closes the database at the end of the request."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db(app):
    """Initializes the SQLite database tables using parameterized schemas."""
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
