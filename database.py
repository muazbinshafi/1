import sqlite3
import datetime

DB_FILE = 'leads.db'

def get_connection(db_file=None):
    if db_file is None:
        db_file = DB_FILE
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_file=None):
    conn = get_connection(db_file)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_name TEXT NOT NULL,
            type TEXT NOT NULL,
            city TEXT NOT NULL,
            phone TEXT NOT NULL,
            contacted INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(business_name, phone)
        )
    ''')
    conn.commit()
    conn.close()

def add_lead(business_name, type, city, phone, db_file=None):
    conn = get_connection(db_file)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO leads (business_name, type, city, phone)
            VALUES (?, ?, ?, ?)
        ''', (business_name, type, city, phone))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Lead already exists
        return False
    finally:
        conn.close()

def get_active_leads(db_file=None):
    conn = get_connection(db_file)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, business_name, type, city, phone
        FROM leads
        WHERE contacted = 0
        ORDER BY created_at DESC
    ''')
    leads = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return leads

def mark_contacted(lead_id, db_file=None):
    conn = get_connection(db_file)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE leads
        SET contacted = 1
        WHERE id = ?
    ''', (lead_id,))
    conn.commit()
    conn.close()

def get_stats(db_file=None):
    conn = get_connection(db_file)
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
