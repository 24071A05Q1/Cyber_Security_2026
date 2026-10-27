from flask import Flask, render_template
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
