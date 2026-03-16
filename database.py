import sqlite3
import datetime

DB_PATH = 'leads.db'

def get_db(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path=DB_PATH):
    conn = get_db(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_name TEXT NOT NULL,
            type TEXT NOT NULL,
            city TEXT NOT NULL,
            phone TEXT NOT NULL,
            contacted BOOLEAN NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def add_lead(business_name, business_type, city, phone, db_path=DB_PATH):
    conn = get_db(db_path)
    cursor = conn.cursor()
    # Check if lead already exists based on phone
    cursor.execute('SELECT id FROM leads WHERE phone = ?', (phone,))
    existing = cursor.fetchone()
    if not existing:
        cursor.execute('''
            INSERT INTO leads (business_name, type, city, phone, contacted)
            VALUES (?, ?, ?, ?, 0)
        ''', (business_name, business_type, city, phone))
        conn.commit()
    conn.close()

def get_uncontacted_leads(db_path=DB_PATH):
    conn = get_db(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM leads WHERE contacted = 0 ORDER BY created_at DESC')
    leads = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return leads

def mark_contacted(lead_id, db_path=DB_PATH):
    conn = get_db(db_path)
    cursor = conn.cursor()
    cursor.execute('UPDATE leads SET contacted = 1 WHERE id = ?', (lead_id,))
    conn.commit()
    conn.close()

def get_stats(db_path=DB_PATH):
    conn = get_db(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM leads')
    total = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM leads WHERE contacted = 1')
    contacted = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM leads WHERE contacted = 0')
    new_leads = cursor.fetchone()[0]
    conn.close()
    return {
        'total': total,
        'contacted': contacted,
        'new': new_leads
    }

if __name__ == '__main__':
    init_db()
