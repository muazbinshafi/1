import sqlite3
import datetime

DB_FILE = "leads.db"

def get_connection(db_file=DB_FILE):
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_file=DB_FILE):
    conn = get_connection(db_file)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_name TEXT NOT NULL,
            type TEXT NOT NULL,
            city TEXT NOT NULL,
            phone TEXT NOT NULL,
            contacted BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(business_name, city)
        )
    """)
    conn.commit()
    conn.close()

def add_lead(business_name, lead_type, city, phone, db_file=DB_FILE):
    conn = get_connection(db_file)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO leads (business_name, type, city, phone)
            VALUES (?, ?, ?, ?)
        """, (business_name, lead_type, city, phone))
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        # Lead already exists
        success = False
    conn.close()
    return success

def get_uncontacted_leads(db_file=DB_FILE):
    conn = get_connection(db_file)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM leads WHERE contacted = 0 ORDER BY created_at DESC")
    leads = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return leads

def mark_lead_contacted(lead_id, db_file=DB_FILE):
    conn = get_connection(db_file)
    cursor = conn.cursor()
    cursor.execute("UPDATE leads SET contacted = 1 WHERE id = ?", (lead_id,))
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    return success

def get_stats(db_file=DB_FILE):
    conn = get_connection(db_file)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM leads")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM leads WHERE contacted = 1")
    contacted = cursor.fetchone()[0]

    conn.close()

    return {
        "total": total,
        "contacted": contacted,
        "new": total - contacted
    }

if __name__ == "__main__":
    init_db()
