import sqlite3


def init_db():
    conn = sqlite3.connect('vulnshop.db')
    c = conn.cursor()

    # Users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            email   TEXT,
            role    TEXT DEFAULT 'user'
        )
    ''')

    # Products table
    c.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            price       REAL,
            description TEXT
        )
    ''')

    # Seed users (plaintext passwords — intentional for lab visibility)
    c.execute("INSERT OR IGNORE INTO users VALUES (1,'admin','admin123','admin@shop.com','admin')")
    c.execute("INSERT OR IGNORE INTO users VALUES (2,'alice','pass123','alice@email.com','user')")
    c.execute("INSERT OR IGNORE INTO users VALUES (3,'bob','bob456','bob@email.com','user')")

    # Seed products
    c.execute("INSERT OR IGNORE INTO products VALUES (1,'Laptop',999.99,'High-performance laptop for professionals')")
    c.execute("INSERT OR IGNORE INTO products VALUES (2,'Smartphone',499.99,'Latest flagship smartphone')")
    c.execute("INSERT OR IGNORE INTO products VALUES (3,'Tablet',299.99,'Lightweight portable tablet')")
    c.execute("INSERT OR IGNORE INTO products VALUES (4,'Wireless Headphones',149.99,'Noise-cancelling over-ear headphones')")
    c.execute("INSERT OR IGNORE INTO products VALUES (5,'Mechanical Keyboard',89.99,'Tactile clicky switches, RGB backlit')")

    conn.commit()
    conn.close()
    print('[+] Database initialized successfully!')


if __name__ == '__main__':
    init_db()
