import sqlite3
import re
from contextlib import contextmanager
from datetime import datetime
from playwright.sync_api import sync_playwright

DB_PATH = 'leads.db'

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
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

def generate_mock_leads():
    mock_data = [
        ('Al-Shifa Clinic', 'Clinic', 'Bahawalpur', '0300-1234567'),
        ('Zaman Super Store', 'Store', 'Bahawalpur', '0321-9876543'),
        ('Fast Auto Repair', 'Service', 'Bahawalpur', '0333-5555555'),
        ('City Medical Center', 'Clinic', 'Bahawalpur', '0301-1112223'),
        ('Ali Electronics', 'Store', 'Bahawalpur', '0345-4445556'),
        ('A1 Plumbing Services', 'Service', 'Bahawalpur', '0312-9998887')
    ]
    with get_db() as conn:
        for name, b_type, city, phone in mock_data:
            # Check if exists
            cursor = conn.execute('SELECT 1 FROM leads WHERE phone = ?', (phone,))
            if not cursor.fetchone():
                conn.execute(
                    'INSERT INTO leads (business_name, type, city, phone) VALUES (?, ?, ?, ?)',
                    (name, b_type, city, phone)
                )

def collect_leads():
    # Attempt to scrape DuckDuckGo for businesses in Bahawalpur lacking websites.
    # If it fails, fallback to generate_mock_leads
    queries = [
        "Clinics in Bahawalpur contact number",
        "Retail stores in Bahawalpur contact number",
        "Service providers in Bahawalpur contact number"
    ]

    leads_found = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            for query in queries:
                b_type = 'Service'
                if 'Clinic' in query:
                    b_type = 'Clinic'
                elif 'store' in query:
                    b_type = 'Store'

                page.goto('https://html.duckduckgo.com/html/')
                page.fill('#search_form_input_homepage', query)
                page.click('#search_button_homepage')
                page.wait_for_selector('.result__snippet', timeout=10000)

                results = page.locator('.result__snippet').all()
                for result in results:
                    text = result.inner_text()
                    # Filter out those with websites mentioned
                    if any(domain in text.lower() for domain in ['.com', '.pk', 'website', 'www.']):
                        continue

                    # Extract phone numbers using regex
                    phone_matches = re.findall(r'(03\d{2}[-\s]?\d{7})', text)
                    if phone_matches:
                        for phone in phone_matches:
                            # Try to extract a name before the phone number or just use a generic one if hard
                            # Since this is a simple text snippet, finding the exact business name is tricky.
                            # We'll use the title of the result if possible, but DDG HTML doesn't let us easily go up.
                            # So let's look at the result title
                            title = result.locator('..').locator('..').locator('.result__title').inner_text()
                            if title:
                                name = title.strip()
                                # Clean up common suffixes
                                name = re.sub(r' \|.*$', '', name)
                                leads_found.append((name, b_type, 'Bahawalpur', phone))

            browser.close()

            if not leads_found:
                print("No leads found via scraping, using mock data")
                generate_mock_leads()
                return

            with get_db() as conn:
                for name, b_type, city, phone in leads_found:
                    cursor = conn.execute('SELECT 1 FROM leads WHERE phone = ?', (phone,))
                    if not cursor.fetchone():
                        conn.execute(
                            'INSERT INTO leads (business_name, type, city, phone) VALUES (?, ?, ?, ?)',
                            (name, b_type, city, phone)
                        )
    except Exception as e:
        print(f"Scraping failed with error: {e}. Falling back to mock data.")
        generate_mock_leads()

if __name__ == '__main__':
    init_db()
    collect_leads()
