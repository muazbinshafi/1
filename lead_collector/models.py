import sqlite3
import datetime
import os

DB_NAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "leads.db")

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    with conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                city TEXT NOT NULL,
                phone TEXT NOT NULL,
                website TEXT,
                status TEXT DEFAULT 'new',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    conn.close()

class Lead:
    @staticmethod
    def add_lead(name, type, city, phone, website=None):
        conn = get_db_connection()
        try:
            with conn:
                # Check for duplicates based on phone number
                existing = conn.execute('SELECT id FROM leads WHERE phone = ?', (phone,)).fetchone()
                if existing:
                    return None

                cursor = conn.execute('''
                    INSERT INTO leads (name, type, city, phone, website)
                    VALUES (?, ?, ?, ?, ?)
                ''', (name, type, city, phone, website))
                return cursor.lastrowid
        finally:
            conn.close()

    @staticmethod
    def get_leads(status='new'):
        conn = get_db_connection()
        leads = conn.execute('SELECT * FROM leads WHERE status = ? ORDER BY created_at DESC', (status,)).fetchall()
        conn.close()
        return [dict(lead) for lead in leads]

    @staticmethod
    def update_status(lead_id, status):
        conn = get_db_connection()
        with conn:
            conn.execute('UPDATE leads SET status = ? WHERE id = ?', (status, lead_id))
        conn.close()

    @staticmethod
    def get_analytics():
        conn = get_db_connection()
        new_count = conn.execute("SELECT COUNT(*) FROM leads WHERE status = 'new'").fetchone()[0]
        contacted_count = conn.execute("SELECT COUNT(*) FROM leads WHERE status = 'contacted'").fetchone()[0]
        conn.close()
        return {
            "new_leads": new_count,
            "contacted_leads": contacted_count
        }
