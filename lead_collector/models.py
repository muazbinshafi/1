import sqlite3
import os
from datetime import datetime

DB_PATH = 'lead_collector/leads.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            city TEXT NOT NULL,
            phone TEXT NOT NULL UNIQUE,
            status TEXT DEFAULT 'new',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def add_lead(name, type, city, phone):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute('INSERT INTO leads (name, type, city, phone) VALUES (?, ?, ?, ?)',
                  (name, type, city, phone))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_leads(status=None):
    conn = get_db_connection()
    c = conn.cursor()
    if status:
        c.execute('SELECT * FROM leads WHERE status = ? ORDER BY created_at DESC', (status,))
    else:
        c.execute('SELECT * FROM leads ORDER BY created_at DESC')
    leads = [dict(row) for row in c.fetchall()]
    conn.close()
    return leads

def update_lead_status(lead_id, new_status):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('UPDATE leads SET status = ? WHERE id = ?', (new_status, lead_id))
    conn.commit()
    conn.close()

def delete_lead(lead_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('DELETE FROM leads WHERE id = ?', (lead_id,))
    conn.commit()
    conn.close()
