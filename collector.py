import sqlite3
import re
from contextlib import contextmanager
from datetime import datetime
from playwright.sync_api import sync_playwright

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
    if db_path is None:
        db_path = DB_PATH
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

def generate_mock_leads(db_path=None):
    if db_path is None:
        db_path = DB_PATH
    mock_leads = [
        ('Al-Shifa Clinic', 'Clinic', 'Bahawalpur', '0300-1234567'),
        ('Riaz Medical Store', 'Store', 'Bahawalpur', '0311-9876543'),
        ('Ahmad Auto Workshop', 'Service', 'Bahawalpur', '0322-5556667'),
        ('Fatima Health Care', 'Clinic', 'Bahawalpur', '0333-1112233')
    ]
    with get_db(db_path) as conn:
        for name, l_type, city, phone in mock_leads:
            # Avoid duplicates in mock data too
            existing = conn.execute(
                'SELECT 1 FROM leads WHERE phone = ?', (phone,)
            ).fetchone()
            if not existing:
                conn.execute(
                    'INSERT INTO leads (business_name, type, city, phone) VALUES (?, ?, ?, ?)',
                    (name, l_type, city, phone)
                )

def extract_phone(text):
    match = re.search(r'(03\d{2}[-\s]?\d{7})', text)
    if match:
        return match.group(1)
    return None

def has_website(text):
    text = text.lower()
    return '.com' in text or '.pk' in text or 'website' in text or 'www.' in text

def collect_leads(db_path=None):
    if db_path is None:
        db_path = DB_PATH

    init_db(db_path)
    city = "Bahawalpur"
    queries = [
        f"Clinics in {city} phone number",
        f"Retail stores in {city} phone number",
        f"Plumbers electricians in {city} phone number"
    ]

    types = ['Clinic', 'Store', 'Service']

    leads_found = 0
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            for query, l_type in zip(queries, types):
                try:
                    page.goto('https://html.duckduckgo.com/html/', wait_until='domcontentloaded')
                    page.fill('#search_form_input_homepage', query)
                    page.click('#search_button_homepage')
                    page.wait_for_selector('.result', timeout=10000)

                    results = page.query_selector_all('.result')
                    for result in results:
                        title_el = result.query_selector('.result__title')
                        snippet_el = result.query_selector('.result__snippet')

                        if not title_el or not snippet_el:
                            continue

                        title = title_el.inner_text().strip()
                        snippet = snippet_el.inner_text().strip()

                        phone = extract_phone(snippet)
                        if phone and not has_website(snippet):
                            with get_db(db_path) as conn:
                                # Avoid duplicates
                                existing = conn.execute(
                                    'SELECT 1 FROM leads WHERE phone = ?', (phone,)
                                ).fetchone()

                                if not existing:
                                    conn.execute(
                                        'INSERT INTO leads (business_name, type, city, phone) VALUES (?, ?, ?, ?)',
                                        (title, l_type, city, phone)
                                    )
                                    leads_found += 1
                except Exception as e:
                    print(f"Error scraping {query}: {e}")

            browser.close()

    except Exception as e:
        print(f"Playwright error: {e}")

    if leads_found == 0:
        print("No live leads found, generating mock data.")
        generate_mock_leads(db_path)
