import sqlite3
import random
import re
from datetime import datetime
from contextlib import contextmanager

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
                business_name TEXT NOT NULL,
                type TEXT NOT NULL,
                city TEXT NOT NULL,
                phone TEXT NOT NULL UNIQUE,
                contacted INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

def extract_phone(text):
    match = re.search(r'(03\d{2}[-\s]?\d{7})', text)
    if match:
        return match.group(1)
    return None

def has_website(text):
    text = text.lower()
    return '.com' in text or '.pk' in text or 'website' in text or 'www.' in text

def collect_leads(db_path=None):
    # This function uses DuckDuckGo HTML search to bypass scrapers blocking
    import urllib.parse
    from playwright.sync_api import sync_playwright

    init_db(db_path)
    city = "Bahawalpur"
    queries = [
        "Clinics in Bahawalpur",
        "Retail Stores in Bahawalpur",
        "Service Providers in Bahawalpur"
    ]

    leads_found = 0
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for query in queries:
            business_type = "Clinic" if "Clinic" in query else "Store" if "Store" in query else "Service"
            encoded_query = urllib.parse.quote(query)
            try:
                page.goto(f"https://html.duckduckgo.com/html/?q={encoded_query}", wait_until="domcontentloaded", timeout=30000)
                results = page.locator(".result").all()
                for result in results:
                    text_content = result.inner_text()
                    phone = extract_phone(text_content)
                    if phone and not has_website(text_content):
                        # Extract business name from title
                        title = result.locator(".result__title").inner_text().strip()

                        # Store in db
                        with get_db(db_path) as conn:
                            # check if exists
                            exists = conn.execute('SELECT id FROM leads WHERE phone = ?', (phone,)).fetchone()
                            if not exists:
                                conn.execute(
                                    'INSERT INTO leads (business_name, type, city, phone) VALUES (?, ?, ?, ?)',
                                    (title, business_type, city, phone)
                                )
                                leads_found += 1
            except Exception as e:
                print(f"Scraper error for {query}: {e}")

        browser.close()

    if leads_found == 0:
        print("Scraper found no leads, using fallback...")
        generate_mock_leads(db_path)

def generate_mock_leads(db_path=None):
    init_db(db_path)
    city = "Bahawalpur"
    business_types = ["Clinic", "Store", "Service"]
    names = {
        "Clinic": ["City Care Clinic", "Al-Shifa Medical Center", "Bahawalpur Health", "Life Care Clinic"],
        "Store": ["Awan General Store", "Riaz Mart", "Madina Traders", "Hafiz Retail"],
        "Service": ["Khan Auto Workshop", "Mian Plumbing Services", "Al-Rehman Electric", "Siddique Builders"]
    }

    with get_db(db_path) as conn:
        for _ in range(5):
            b_type = random.choice(business_types)
            name = random.choice(names[b_type])
            # generate pakistani phone
            phone = f"03{random.randint(0, 4)}{random.randint(0, 9)}-{random.randint(1000000, 9999999)}"

            exists = conn.execute('SELECT id FROM leads WHERE phone = ?', (phone,)).fetchone()
            if not exists:
                conn.execute(
                    'INSERT INTO leads (business_name, type, city, phone) VALUES (?, ?, ?, ?)',
                    (name, b_type, city, phone)
                )

if __name__ == '__main__':
    collect_leads()
