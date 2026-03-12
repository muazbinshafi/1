import sqlite3
from datetime import datetime
import os

DB_PATH = os.environ.get('DB_PATH', 'leads.db')

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
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
    conn.close()

def add_lead(business_name, type, city, phone):
    conn = get_connection()
    c = conn.cursor()

    # Check if lead already exists
    c.execute('SELECT id FROM leads WHERE phone = ?', (phone,))
    if c.fetchone():
        conn.close()
        return False

    c.execute('''
        INSERT INTO leads (business_name, type, city, phone)
        VALUES (?, ?, ?, ?)
    ''', (business_name, type, city, phone))
    conn.commit()
    conn.close()
    return True

def get_uncontacted_leads():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT * FROM leads
        WHERE contacted = 0
        ORDER BY created_at DESC
    ''')
    leads = [dict(row) for row in c.fetchall()]
    conn.close()
    return leads

def mark_contacted(lead_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('UPDATE leads SET contacted = 1 WHERE id = ?', (lead_id,))
    conn.commit()
    conn.close()
    return True

def get_stats():
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM leads')
    total = c.fetchone()[0]

    c.execute('SELECT COUNT(*) FROM leads WHERE contacted = 1')
    contacted = c.fetchone()[0]

    c.execute('SELECT COUNT(*) FROM leads WHERE contacted = 0')
    new_leads = c.fetchone()[0]

    conn.close()
    return {
        'total': total,
        'contacted': contacted,
        'new': new_leads
    }
