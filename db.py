import sqlite3
from contextlib import contextmanager

DB_NAME = 'leads.db'

@contextmanager
def get_db(db_path=DB_NAME):
    """Safely yields a SQLite database connection that commits and closes automatically."""
    conn = sqlite3.connect(db_path)
    # Enable named columns
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def init_db(db_path=DB_NAME):
    """Initializes the database schema if it doesn't already exist."""
    with get_db(db_path) as conn:
        conn.execute('''
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

def add_lead(business_name, business_type, city, phone, db_path=DB_NAME):
    """Inserts a new lead into the database. Ignores duplicates based on business_name and phone."""
    try:
        with get_db(db_path) as conn:
            conn.execute('''
                INSERT OR IGNORE INTO leads (business_name, type, city, phone)
                VALUES (?, ?, ?, ?)
            ''', (business_name, business_type, city, phone))
    except sqlite3.Error as e:
        print(f"Database error adding lead: {e}")

def get_uncontacted_leads(db_path=DB_NAME):
    """Returns a list of all uncontacted leads as dictionaries."""
    with get_db(db_path) as conn:
        cursor = conn.execute('''
            SELECT id, business_name, type, city, phone, contacted, created_at
            FROM leads
            WHERE contacted = 0
            ORDER BY created_at DESC
        ''')
        return [dict(row) for row in cursor.fetchall()]

def mark_lead_contacted(lead_id, db_path=DB_NAME):
    """Updates the contacted status of a specific lead to 1 (True)."""
    with get_db(db_path) as conn:
        conn.execute('UPDATE leads SET contacted = 1 WHERE id = ?', (lead_id,))

def get_stats(db_path=DB_NAME):
    """Returns statistics about total leads and contacted leads."""
    with get_db(db_path) as conn:
        total = conn.execute('SELECT COUNT(*) FROM leads').fetchone()[0]
        contacted = conn.execute('SELECT COUNT(*) FROM leads WHERE contacted = 1').fetchone()[0]
        uncontacted = conn.execute('SELECT COUNT(*) FROM leads WHERE contacted = 0').fetchone()[0]
        return {
            'total_leads': total,
            'contacted_leads': contacted,
            'new_leads': uncontacted
        }
