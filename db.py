import sqlite3
from contextlib import contextmanager

DATABASE = 'leads.db'

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                business_name TEXT NOT NULL,
                type TEXT NOT NULL,
                city TEXT NOT NULL,
                phone TEXT NOT NULL,
                contacted BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

@contextmanager
def get_db(db_path=DATABASE):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def add_lead(business_name, type, city, phone, db_path=DATABASE):
    with get_db(db_path) as conn:
        # Check if already exists
        cursor = conn.execute('SELECT id FROM leads WHERE phone = ?', (phone,))
        if cursor.fetchone():
            return False # Lead with this phone already exists

        conn.execute('''
            INSERT INTO leads (business_name, type, city, phone)
            VALUES (?, ?, ?, ?)
        ''', (business_name, type, city, phone))
        return True

def get_uncontacted_leads(db_path=DATABASE):
    with get_db(db_path) as conn:
        cursor = conn.execute('SELECT * FROM leads WHERE contacted = 0 ORDER BY created_at DESC')
        return [dict(row) for row in cursor.fetchall()]

def mark_contacted(lead_id, db_path=DATABASE):
    with get_db(db_path) as conn:
        conn.execute('UPDATE leads SET contacted = 1 WHERE id = ?', (lead_id,))

def get_stats(db_path=DATABASE):
    with get_db(db_path) as conn:
        total = conn.execute('SELECT COUNT(*) FROM leads').fetchone()[0]
        contacted = conn.execute('SELECT COUNT(*) FROM leads WHERE contacted = 1').fetchone()[0]
        return {
            'total': total,
            'contacted': contacted,
            'new': total - contacted
        }
