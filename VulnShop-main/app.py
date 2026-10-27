from flask import Flask, request, render_template, session, redirect, abort
import sqlite3
import secrets

app = Flask(__name__)
app.secret_key = 'supersecret123'  # Weak key intentionally used for lab purposes


def get_db():
    conn = sqlite3.connect('vulnshop.db')
    conn.row_factory = sqlite3.Row
    return conn


# ─────────────────────────────────────────────
# HOME
# ─────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')


# ─────────────────────────────────────────────
# VULNERABILITY 1 — Reflected XSS
# The |safe filter disables Jinja2 auto-escaping,
# allowing injected <script> tags to execute.
# ─────────────────────────────────────────────
@app.route('/search')
def search():
    query = request.args.get('q', '')
    # VULNERABLE: user input reflected directly without sanitisation
    return render_template('search.html', query=query)


# ─────────────────────────────────────────────
# VULNERABILITY 2 — SQL Injection
# Raw f-string interpolation lets an attacker
# manipulate the WHERE clause.
# ─────────────────────────────────────────────
@app.route('/products')
def products():
    pid = request.args.get('id', '')
    conn = get_db()
    if pid:
        # VULNERABLE: unsanitised input concatenated into SQL
        query = f"SELECT * FROM products WHERE id = {pid}"
        result = conn.execute(query).fetchall()
    else:
        result = conn.execute("SELECT * FROM products").fetchall()
    return render_template('products.html', products=result)


# ─────────────────────────────────────────────
# VULNERABILITY 3a — SQL Injection → Auth Bypass
# VULNERABILITY 3b — Broken Access Control
# ─────────────────────────────────────────────
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        u = request.form['username']
        p = request.form['password']
        # VULNERABLE: raw string concatenation enables ' OR '1'='1 bypass
        q = f"SELECT * FROM users WHERE username='{u}' AND password='{p}'"
        user = get_db().execute(q).fetchone()
        if user:
            session['user'] = user['username']
            session['role'] = user['role']
            return redirect('/')
        error = 'Invalid credentials. Try again.'
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


@app.route('/register', methods=['GET', 'POST'])
def register():
    message = None
    if request.method == 'POST':
        u = request.form['username']
        p = request.form['password']
        try:
            db = get_db()
            db.execute("INSERT INTO users (username, password, role) VALUES (?, ?, 'user')", (u, p))
            db.commit()
            message = 'Account created! You can now log in.'
        except Exception:
            message = 'Username already taken.'
    return render_template('register.html', message=message)


# ─────────────────────────────────────────────
# VULNERABILITY 3b — Broken Access Control
# Route checks session exists but never verifies
# that the role is 'admin'.
# ─────────────────────────────────────────────
@app.route('/admin')
def admin():
    if 'user' not in session:
        return redirect('/login')
    # VULNERABLE: any logged-in user can reach this page
    # Secure fix: if session.get('role') != 'admin': abort(403)
    users = get_db().execute('SELECT * FROM users').fetchall()
    return render_template('admin.html', users=users)


# ─────────────────────────────────────────────
# VULNERABILITY 4 — CSRF
# No token validation; any external site can POST
# to this endpoint while the victim is logged in.
# ─────────────────────────────────────────────
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user' not in session:
        return redirect('/login')
    message = None
    if request.method == 'POST':
        new_email = request.form.get('email', '')
        # VULNERABLE: no CSRF token check
        db = get_db()
        db.execute('UPDATE users SET email=? WHERE username=?',
                   (new_email, session['user']))
        db.commit()
        message = 'Profile updated!'
    # Fetch current user data
    user = get_db().execute(
        "SELECT * FROM users WHERE username=?", (session['user'],)
    ).fetchone()
    return render_template('profile.html', user=user, message=message)


if __name__ == '__main__':
    app.run(debug=True)  # debug=True is insecure in production — intentional for lab
