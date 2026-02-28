import sqlite3
import os

def init_db():
    # Make sure static/labels exists
    labels_dir = os.path.join('static', 'labels')
    os.makedirs(labels_dir, exist_ok=True)
    
    conn = sqlite3.connect('nutrition.db')
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create label_history table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS label_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        product_name TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        compliance_score INTEGER NOT NULL,
        pdf_filename TEXT NOT NULL,
        nutrition_json TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    conn.commit()
    
    # Create user_settings table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE NOT NULL,
        default_license TEXT DEFAULT '',
        default_serving_size REAL DEFAULT 0,
        default_company_name TEXT DEFAULT '',
        default_address TEXT DEFAULT '',
        email_notifications INTEGER DEFAULT 0,
        score_alert INTEGER DEFAULT 1,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    conn.commit()
    conn.close()
    print("Database initialized successfully.")

if __name__ == '__main__':
    init_db()
