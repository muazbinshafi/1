import sqlite3
import datetime

def get_connection(db_path='leads.db'):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path='leads.db'):
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_name TEXT NOT NULL,
            type TEXT NOT NULL,
            city TEXT NOT NULL,
            phone TEXT NOT NULL,
            contacted INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def add_lead(db_path, business_name, type, city, phone):
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO leads (business_name, type, city, phone)
        VALUES (?, ?, ?, ?)
    ''', (business_name, type, city, phone))
    conn.commit()
    conn.close()

def get_active_leads(db_path='leads.db'):
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, business_name, type, city, phone, contacted, created_at
        FROM leads
        WHERE contacted = 0
        ORDER BY created_at DESC
    ''')
    leads = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return leads

def mark_lead_contacted(db_path, lead_id):
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE leads
        SET contacted = 1
        WHERE id = ?
    ''', (lead_id,))
    conn.commit()
    conn.close()

def get_stats(db_path='leads.db'):
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM leads')
    total_leads = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM leads WHERE contacted = 1')
    contacted_leads = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM leads WHERE contacted = 0')
    new_leads = cursor.fetchone()[0]

    conn.close()

    return {
        'total_leads': total_leads,
        'contacted_leads': contacted_leads,
        'new_leads': new_leads
    }

if __name__ == '__main__':
    init_db()
