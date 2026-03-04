import sqlite3

DB_FILE = "leads.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_name TEXT NOT NULL,
            type TEXT NOT NULL,
            city TEXT NOT NULL,
            phone TEXT NOT NULL,
            contacted BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def add_lead(business_name, type, city, phone):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # Check if lead already exists based on phone
    cursor.execute("SELECT id FROM leads WHERE phone = ?", (phone,))
    if cursor.fetchone():
        conn.close()
        return False

    cursor.execute("""
        INSERT INTO leads (business_name, type, city, phone)
        VALUES (?, ?, ?, ?)
    """, (business_name, type, city, phone))
    conn.commit()
    conn.close()
    return True

def get_uncontacted_leads():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM leads WHERE contacted = 0 ORDER BY created_at DESC")
    leads = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return leads

def mark_contacted(lead_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE leads SET contacted = 1 WHERE id = ?", (lead_id,))
    conn.commit()
    conn.close()

def get_stats():
    conn = sqlite3.connect(DB_FILE)
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
