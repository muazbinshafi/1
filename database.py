import sqlite3
from datetime import datetime

DB_NAME = 'leads.db'

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            business_type TEXT NOT NULL,
            city TEXT NOT NULL,
            phone TEXT NOT NULL UNIQUE,
            status TEXT DEFAULT 'new',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def add_lead(lead_data):
    """
    Adds a new lead to the database.
    lead_data: dict with name, business_type, city, phone
    Returns True if added, False if duplicate.
    """
    conn = get_db_connection()
    try:
        conn.execute('''
            INSERT INTO leads (name, business_type, city, phone)
            VALUES (?, ?, ?, ?)
        ''', (lead_data['name'], lead_data['business_type'], lead_data['city'], lead_data['phone']))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_active_leads(limit=100):
    conn = get_db_connection()
    leads = conn.execute('SELECT * FROM leads WHERE status = "new" ORDER BY created_at DESC LIMIT ?', (limit,)).fetchall()
    conn.close()
    return [dict(lead) for lead in leads]

def mark_lead_contacted(lead_id):
    conn = get_db_connection()
    conn.execute('UPDATE leads SET status = "contacted" WHERE id = ?', (lead_id,))
    conn.commit()
    conn.close()

def get_lead_count():
    conn = get_db_connection()
    count = conn.execute('SELECT COUNT(*) FROM leads WHERE status = "new"').fetchone()[0]
    conn.close()
    return count

def get_stats_data():
    conn = get_db_connection()
    total = conn.execute('SELECT COUNT(*) FROM leads').fetchone()[0]
    contacted = conn.execute('SELECT COUNT(*) FROM leads WHERE status = "contacted"').fetchone()[0]
    new = conn.execute('SELECT COUNT(*) FROM leads WHERE status = "new"').fetchone()[0]
    conn.close()
    return {
        'total': total,
        'contacted': contacted,
        'new': new
    }
