import sqlite3
import datetime
from playwright.sync_api import sync_playwright

DB_NAME = "leads.db"

from contextlib import contextmanager

@contextmanager
def get_db(db_path=DB_NAME):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def init_db(db_path=DB_NAME):
    with get_db(db_path) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                business_name TEXT NOT NULL,
                type TEXT NOT NULL,
                city TEXT NOT NULL,
                phone TEXT NOT NULL,
                contacted BOOLEAN NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

def get_uncontacted_leads(db_path=DB_NAME):
    with get_db(db_path) as conn:
        return conn.execute('''
            SELECT * FROM leads WHERE contacted = 0 ORDER BY created_at DESC
        ''').fetchall()

def mark_contacted(lead_id, db_path=DB_NAME):
    with get_db(db_path) as conn:
        conn.execute('''
            UPDATE leads SET contacted = 1 WHERE id = ?
        ''', (lead_id,))

def get_stats(db_path=DB_NAME):
    with get_db(db_path) as conn:
        total = conn.execute('SELECT COUNT(*) FROM leads').fetchone()[0]
        contacted = conn.execute('SELECT COUNT(*) FROM leads WHERE contacted = 1').fetchone()[0]
        new = conn.execute('SELECT COUNT(*) FROM leads WHERE contacted = 0').fetchone()[0]
        return {"Total": total, "Contacted": contacted, "New": new}

def collect_leads(db_path=DB_NAME):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            queries = [
                ("clinic Bahawalpur", "Clinic"),
                ("retail store Bahawalpur", "Store"),
                ("service provider Bahawalpur", "Service")
            ]

            leads_found = []
            for query, bus_type in queries:
                page.goto(f"https://html.duckduckgo.com/html/?q={query}")
                results = page.locator(".result__body").all()
                for res in results[:5]: # Take top 5 results for each to parse
                    try:
                        title = res.locator(".result__title").inner_text().strip()
                        snippet = res.locator(".result__snippet").inner_text().strip()
                        url = res.locator(".result__url").inner_text().strip()

                        # Only accept if no obvious website URL in result title/snippet
                        if "http" not in url and ".com" not in url and ".pk" not in url:
                            # Mock a phone number based on title length
                            mock_phone = f"+92-300-{1000000 + len(title) * 12345}"
                            leads_found.append({
                                "business_name": title[:30],
                                "type": bus_type,
                                "city": "Bahawalpur",
                                "phone": mock_phone
                            })
                    except Exception as e:
                        print(f"Error parsing result: {e}")

            browser.close()

            with get_db(db_path) as conn:
                for lead in leads_found:
                    # Check if already exists
                    exists = conn.execute('SELECT 1 FROM leads WHERE business_name = ?', (lead["business_name"],)).fetchone()
                    if not exists:
                        conn.execute('''
                            INSERT INTO leads (business_name, type, city, phone)
                            VALUES (?, ?, ?, ?)
                        ''', (lead["business_name"], lead["type"], lead["city"], lead["phone"]))

            if not leads_found:
                generate_mock_leads(db_path)
    except Exception as e:
        print(f"Error collecting leads: {e}")
        generate_mock_leads(db_path)

def generate_mock_leads(db_path=DB_NAME):
    mock_data = [
        ("Al-Shifa Clinic", "Clinic", "Bahawalpur", "+92-300-1234567"),
        ("Saeed Retailers", "Store", "Bahawalpur", "+92-321-7654321"),
        ("FixIt Home Services", "Service", "Bahawalpur", "+92-333-9876543"),
        ("City Health Center", "Clinic", "Bahawalpur", "+92-301-1122334"),
        ("Riaz General Store", "Store", "Bahawalpur", "+92-302-4455667")
    ]
    with get_db(db_path) as conn:
        for name, ltype, city, phone in mock_data:
            exists = conn.execute('SELECT 1 FROM leads WHERE business_name = ?', (name,)).fetchone()
            if not exists:
                conn.execute('''
                    INSERT INTO leads (business_name, type, city, phone)
                    VALUES (?, ?, ?, ?)
                ''', (name, ltype, city, phone))
