import sqlite3
import datetime
from playwright.sync_api import sync_playwright

DB_NAME = 'leads.db'

def get_db(db_path=DB_NAME):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path=DB_NAME):
    conn = get_db(db_path)
    conn.execute('''
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

def insert_lead(business_name, business_type, city, phone, db_path=DB_NAME):
    conn = get_db(db_path)
    conn.execute('''
        INSERT INTO leads (business_name, type, city, phone)
        VALUES (?, ?, ?, ?)
    ''', (business_name, business_type, city, phone))
    conn.commit()
    conn.close()

def get_uncontacted_leads(db_path=DB_NAME):
    conn = get_db(db_path)
    leads = conn.execute('SELECT * FROM leads WHERE contacted = 0 ORDER BY created_at DESC').fetchall()
    conn.close()
    return [dict(ix) for ix in leads]

def mark_contacted(lead_id, db_path=DB_NAME):
    conn = get_db(db_path)
    conn.execute('UPDATE leads SET contacted = 1 WHERE id = ?', (lead_id,))
    conn.commit()
    conn.close()

def get_stats(db_path=DB_NAME):
    conn = get_db(db_path)
    total = conn.execute('SELECT COUNT(*) FROM leads').fetchone()[0]
    contacted = conn.execute('SELECT COUNT(*) FROM leads WHERE contacted = 1').fetchone()[0]
    new = conn.execute('SELECT COUNT(*) FROM leads WHERE contacted = 0').fetchone()[0]
    conn.close()
    return {'total': total, 'contacted': contacted, 'new': new}

def collect_leads(db_path=DB_NAME):
    init_db(db_path)
    print("Collecting leads...")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            queries = [
                ("clinic Bahawalpur no website", "Clinic"),
                ("retail store Bahawalpur no website", "Store"),
                ("service Bahawalpur no website", "Service")
            ]

            for query, business_type in queries:
                print(f"Searching for: {query}")
                page.goto('https://html.duckduckgo.com/html/')
                page.fill('#search_form_input_homepage', query)
                page.click('#search_button_homepage')
                page.wait_for_selector('.result__body', timeout=10000)

                results = page.query_selector_all('.result__body')
                for result in results:
                    title_elem = result.query_selector('.result__title')
                    snippet_elem = result.query_selector('.result__snippet')

                    if title_elem and snippet_elem:
                        title = title_elem.inner_text().strip()
                        snippet = snippet_elem.inner_text().strip()

                        # Very simple heuristic: try to find a phone number in the snippet
                        import re
                        phone_match = re.search(r'\+?92\s?\d{3}\s?\d{7}|0\d{3}\s?\d{7}', snippet)

                        # If no website is evident and phone is found
                        if 'website' not in snippet.lower() and phone_match:
                            phone = phone_match.group(0)

                            # Check if already exists
                            conn = get_db(db_path)
                            existing = conn.execute('SELECT 1 FROM leads WHERE phone = ?', (phone,)).fetchone()
                            conn.close()

                            if not existing:
                                print(f"Found new lead: {title} ({phone})")
                                insert_lead(title, business_type, "Bahawalpur", phone, db_path)

            browser.close()
    except Exception as e:
        print(f"Error collecting leads: {e}")
        generate_mock_leads(db_path)

def generate_mock_leads(db_path=DB_NAME):
    print("Generating mock leads for Bahawalpur...")
    init_db(db_path)
    mock_leads = [
        ("Bahawalpur City Clinic", "Clinic", "Bahawalpur", "+92 300 1234567"),
        ("Al-Shifa Medical Center", "Clinic", "Bahawalpur", "0321 7654321"),
        ("Model Town Retail Shop", "Store", "Bahawalpur", "0333 9876543"),
        ("Super General Store", "Store", "Bahawalpur", "+92 312 3456789"),
        ("Bahawalpur Tech Repair", "Service", "Bahawalpur", "0345 1122334"),
        ("Quick Plumbing Services", "Service", "Bahawalpur", "0301 5566778"),
    ]

    conn = get_db(db_path)
    for name, b_type, city, phone in mock_leads:
        existing = conn.execute('SELECT 1 FROM leads WHERE phone = ?', (phone,)).fetchone()
        if not existing:
            insert_lead(name, b_type, city, phone, db_path)
    conn.close()
    print("Mock leads generated.")
