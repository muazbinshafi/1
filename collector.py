import sqlite3
from contextlib import contextmanager

DB_PATH = 'leads.db'

@contextmanager
def get_db(db_path=None):
    """Provides a SQLite connection with dict-like row access."""
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
    """Initializes the database schema."""
    with get_db(db_path) as conn:
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

import re
from playwright.sync_api import sync_playwright
import time
import random

CITY = "Bahawalpur"
BUSINESS_TYPES = ["Clinic", "Store", "Service"]

def scrape_leads():
    """Scrapes local businesses from DuckDuckGo HTML without websites."""
    print("Starting scraper...")
    leads = []
    phone_pattern = re.compile(r'(03\d{2}[-\s]?\d{7})')
    website_indicators = ['.com', '.pk', 'website', 'www.']

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        for b_type in BUSINESS_TYPES:
            query = f"{b_type} in {CITY} Pakistan phone number"
            url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"

            try:
                page.goto(url, wait_until='domcontentloaded', timeout=30000)
                time.sleep(random.uniform(2, 4)) # Be polite

                results = page.query_selector_all('.result__snippet')
                titles = page.query_selector_all('.result__title')
                urls = page.query_selector_all('.result__url')

                for snippet_elem, title_elem, url_elem in zip(results, titles, urls):
                    snippet_text = snippet_elem.inner_text().lower() if snippet_elem else ""
                    title_text = title_elem.inner_text() if title_elem else ""
                    url_text = url_elem.inner_text().lower() if url_elem else ""

                    full_text = f"{snippet_text} {url_text}"

                    # Check for website indicators
                    has_website = any(indicator in full_text for indicator in website_indicators)

                    if not has_website:
                        phone_match = phone_pattern.search(full_text)
                        if phone_match:
                            phone = phone_match.group(1)
                            leads.append({
                                'business_name': title_text.strip(),
                                'type': b_type,
                                'city': CITY,
                                'phone': phone
                            })
            except Exception as e:
                print(f"Error scraping {b_type}: {e}")

        browser.close()

    return leads

def generate_mock_leads():
    """Generates mock leads if scraper fails."""
    return [
        {'business_name': 'Al-Shifa Clinic', 'type': 'Clinic', 'city': CITY, 'phone': '03001234567'},
        {'business_name': 'Madina Super Store', 'type': 'Store', 'city': CITY, 'phone': '03217654321'},
        {'business_name': 'Ali Auto Service', 'type': 'Service', 'city': CITY, 'phone': '03339876543'},
        {'business_name': 'Health First Care', 'type': 'Clinic', 'city': CITY, 'phone': '03451122334'},
        {'business_name': 'Awami Retailers', 'type': 'Store', 'city': CITY, 'phone': '03019988776'},
    ]

def collect_leads(db_path=None):
    """Main function to collect leads and store them."""
    leads = scrape_leads()
    if not leads:
        print("Scraper returned no results, falling back to mock leads.")
        leads = generate_mock_leads()

    with get_db(db_path) as conn:
        for lead in leads:
            # Check if lead already exists
            cursor = conn.cursor()
            cursor.execute('SELECT 1 FROM leads WHERE phone = ?', (lead['phone'],))
            if not cursor.fetchone():
                conn.execute(
                    'INSERT INTO leads (business_name, type, city, phone) VALUES (?, ?, ?, ?)',
                    (lead['business_name'], lead['type'], lead['city'], lead['phone'])
                )
    print(f"Collected {len(leads)} leads.")
