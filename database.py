import sqlite3
import datetime

DB_FILE = 'leads.db'

def get_db_connection(db_file=None):
    if db_file is None:
        db_file = DB_FILE
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_file=None):
    conn = get_db_connection(db_file)
    with conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                business_name TEXT UNIQUE,
                type TEXT,
                city TEXT,
                phone TEXT,
                contacted INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    conn.close()

def add_lead(business_name, business_type, city, phone, db_file=None):
    conn = get_db_connection(db_file)
    try:
        with conn:
            conn.execute('''
                INSERT INTO leads (business_name, type, city, phone)
                VALUES (?, ?, ?, ?)
            ''', (business_name, business_type, city, phone))
    except sqlite3.IntegrityError:
        pass # Ignore duplicates
    finally:
        conn.close()

def get_active_leads(db_file=None):
    conn = get_db_connection(db_file)
    leads = conn.execute('''
        SELECT id, business_name, type, city, phone
        FROM leads
        WHERE contacted = 0
        ORDER BY created_at DESC
    ''').fetchall()
    conn.close()
    return [dict(row) for row in leads]

def mark_lead_contacted(lead_id, db_file=None):
    conn = get_db_connection(db_file)
    with conn:
        conn.execute('''
            UPDATE leads
            SET contacted = 1
            WHERE id = ?
        ''', (lead_id,))
    conn.close()

def get_stats(db_file=None):
    conn = get_db_connection(db_file)
    total = conn.execute('SELECT COUNT(*) FROM leads').fetchone()[0]
    contacted = conn.execute('SELECT COUNT(*) FROM leads WHERE contacted = 1').fetchone()[0]
    new = total - contacted
    conn.close()
    return {
        'total': total,
        'contacted': contacted,
        'new': new
    }
