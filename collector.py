import sqlite3
import re
from contextlib import contextmanager
from datetime import datetime
from playwright.sync_api import sync_playwright

DB_PATH = 'leads.db'

@contextmanager
def get_db(path=None):
    if path is None:
        path = DB_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def init_db(path=None):
    with get_db(path) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                business_name TEXT NOT NULL,
                type TEXT NOT NULL,
                city TEXT NOT NULL,
                phone TEXT NOT NULL UNIQUE,
                contacted BOOLEAN NOT NULL DEFAULT 0,
                created_at TIMESTAMP NOT NULL
            )
        ''')

def generate_mock_leads(path=None):
    mock_data = [
        ('Al-Shifa Clinic', 'Clinic', 'Bahawalpur', '0300-1234567'),
        ('Zainab Retail Store', 'Store', 'Bahawalpur', '0321-7654321'),
        ('Riaz Auto Services', 'Service', 'Bahawalpur', '0333-9876543'),
        ('City General Hospital', 'Clinic', 'Bahawalpur', '0311-1122334'),
        ('Madina Medical Store', 'Store', 'Bahawalpur', '0301-2233445'),
        ('Ali Plumbing Services', 'Service', 'Bahawalpur', '0345-5566778'),
    ]
    with get_db(path) as conn:
        for name, b_type, city, phone in mock_data:
            try:
                conn.execute(
                    'INSERT INTO leads (business_name, type, city, phone, contacted, created_at) VALUES (?, ?, ?, ?, ?, ?)',
                    (name, b_type, city, phone, 0, datetime.now())
                )
            except sqlite3.IntegrityError:
                pass

def collect_leads():
    init_db()
    queries = [
        ('Clinics in Bahawalpur', 'Clinic'),
        ('Stores in Bahawalpur', 'Store'),
        ('Services in Bahawalpur', 'Service'),
    ]

    phone_regex = re.compile(r'(03\d{2}[-\s]?\d{7})')
    bad_keywords = ['.com', '.pk', 'website', 'www.']

    leads_found = 0
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            for query, b_type in queries:
                page.goto('https://html.duckduckgo.com/html/')
                page.fill('#search_form_input_homepage', query)
                page.click('#search_button_homepage')
                page.wait_for_selector('.result')

                results = page.query_selector_all('.result')
                for result in results:
                    snippet = result.query_selector('.result__snippet')
                    if not snippet:
                        continue
                    text = snippet.inner_text()

                    if any(kw in text.lower() for kw in bad_keywords):
                        continue

                    phone_match = phone_regex.search(text)
                    if phone_match:
                        phone = phone_match.group(1)
                        title_el = result.query_selector('.result__title')
                        if title_el:
                            title = title_el.inner_text().strip()

                            with get_db() as conn:
                                try:
                                    conn.execute(
                                        'INSERT INTO leads (business_name, type, city, phone, contacted, created_at) VALUES (?, ?, ?, ?, ?, ?)',
                                        (title, b_type, 'Bahawalpur', phone, 0, datetime.now())
                                    )
                                    leads_found += 1
                                except sqlite3.IntegrityError:
                                    pass
            browser.close()
    except Exception as e:
        print(f"Scraping failed: {e}")
        # fallback to mock leads
        generate_mock_leads()
