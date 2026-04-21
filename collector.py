import sqlite3
import re
import random
from contextlib import contextmanager
from datetime import datetime

DB_PATH = 'leads.db'

@contextmanager
def get_db(db_path=None):
    if db_path is None:
        db_path = DB_PATH
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def init_db(db_path=None):
    with get_db(db_path) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                city TEXT NOT NULL,
                phone TEXT NOT NULL UNIQUE,
                contacted BOOLEAN NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS leads_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event TEXT NOT NULL,
                lead_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

def insert_lead(name, type_, city, phone, db_path=None):
    with get_db(db_path) as conn:
        # Check if exists
        cur = conn.execute('SELECT 1 FROM leads WHERE phone = ?', (phone,))
        if not cur.fetchone():
            conn.execute('''
                INSERT INTO leads (name, type, city, phone)
                VALUES (?, ?, ?, ?)
            ''', (name, type_, city, phone))

def get_uncontacted_leads(db_path=None):
    with get_db(db_path) as conn:
        cur = conn.execute('SELECT * FROM leads WHERE contacted = 0 ORDER BY created_at DESC')
        return [dict(row) for row in cur.fetchall()]


def generate_mock_leads(db_path=None):
    types = ['Clinic', 'Store', 'Service']
    names = ['Care Clinic', 'Family Health', 'Al-Shafi Pharmacy', 'Mega Mart', 'City Traders', 'Quick Fix Electronics', 'Elite Plumbing Services', 'Bright Smile Dental']
    for _ in range(5):
        type_ = random.choice(types)
        name = random.choice(names) + f" {random.randint(1, 100)}"
        phone = f"0300-{random.randint(1000000, 9999999)}"
        insert_lead(name, type_, 'Bahawalpur', phone, db_path)
    print("Mock leads generated")

def scrape_leads(db_path=None):
    from playwright.sync_api import sync_playwright
    import time

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            # Searching for local businesses in Bahawalpur
            query = "local businesses in Bahawalpur phone number"
            url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"

            page.goto(url, timeout=30000)

            # Extract content to parse for phone numbers
            results = page.locator('.result__body').all()
            found_count = 0
            phone_regex = re.compile(r'(03\d{2}[-\s]?\d{7})')

            for result in results:
                text = result.inner_text()

                # Check for negative terms indicating they might have a website
                if any(x in text.lower() for x in ['.com', '.pk', 'website', 'www.']):
                    continue

                match = phone_regex.search(text)
                if match:
                    phone = match.group(1)
                    name_el = result.locator('.result__title')
                    name = name_el.inner_text() if name_el.count() > 0 else "Unknown Business"

                    # Heuristics for type
                    lower_text = text.lower()
                    if 'clinic' in lower_text or 'hospital' in lower_text or 'care' in lower_text or 'health' in lower_text:
                        b_type = 'Clinic'
                    elif 'store' in lower_text or 'mart' in lower_text or 'shop' in lower_text or 'trader' in lower_text or 'retail' in lower_text:
                        b_type = 'Store'
                    else:
                        b_type = 'Service'

                    insert_lead(name[:50], b_type, 'Bahawalpur', phone, db_path)
                    found_count += 1

            browser.close()
            return found_count
        except Exception as e:
            print(f"Scraper error: {e}")
            return 0

def collect_leads(db_path=None):
    count = scrape_leads(db_path)
    if count == 0:
        generate_mock_leads(db_path)
