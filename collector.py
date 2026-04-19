import sqlite3
import re
from contextlib import contextmanager
from playwright.sync_api import sync_playwright
import time
import logging

DB_PATH = 'leads.db'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                city TEXT NOT NULL,
                phone TEXT NOT NULL UNIQUE,
                contacted INTEGER DEFAULT 0
            )
        ''')

def generate_mock_leads():
    mocks = [
        ("Al-Shifa Clinic", "Clinic", "Bahawalpur", "0300-1234567"),
        ("MedCare Medical", "Clinic", "Bahawalpur", "0311-9876543"),
        ("Fashion Hub", "Retail Store", "Bahawalpur", "0322-4567890"),
        ("Tech Gadgets", "Retail Store", "Bahawalpur", "0333-1122334"),
        ("QuickFix Auto", "Service Provider", "Bahawalpur", "0344-5566778"),
        ("Pro Cleaners", "Service Provider", "Bahawalpur", "0301-9988776")
    ]
    with get_db() as conn:
        for name, type_, city, phone in mocks:
            conn.execute('''
                INSERT OR IGNORE INTO leads (name, type, city, phone)
                VALUES (?, ?, ?, ?)
            ''', (name, type_, city, phone))
    logger.info("Mock leads generated.")

def collect_leads_job():
    logger.info("Starting lead collection job...")
    queries = [
        "clinics in Bahawalpur phone number",
        "retail stores in Bahawalpur phone number",
        "services in Bahawalpur phone number"
    ]

    phone_pattern = re.compile(r'(03\d{2}[-\s]?\d{7})')
    website_indicators = ['www.', '.com', '.pk', 'website']

    found_leads = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
            )
            page = context.new_page()

            for query in queries:
                btype = "Clinic" if "clinic" in query else "Retail Store" if "retail" in query else "Service Provider"
                logger.info(f"Searching for: {query}")

                try:
                    page.goto('https://html.duckduckgo.com/html/', timeout=30000)
                    page.fill('#search_form_input_homepage', query)
                    page.click('#search_button_homepage')
                    page.wait_for_selector('.result__snippet', timeout=10000)

                    results = page.query_selector_all('.result')
                    for result in results:
                        snippet_el = result.query_selector('.result__snippet')
                        title_el = result.query_selector('.result__title')

                        if not snippet_el or not title_el:
                            continue

                        snippet_text = snippet_el.inner_text().lower()
                        title_text = title_el.inner_text()

                        has_website = any(ind in snippet_text for ind in website_indicators)
                        if has_website:
                            continue

                        phones = phone_pattern.findall(snippet_el.inner_text())
                        if phones:
                            for phone in phones:
                                found_leads.append({
                                    'name': title_text.strip(),
                                    'type': btype,
                                    'city': 'Bahawalpur',
                                    'phone': phone
                                })
                except Exception as e:
                    logger.error(f"Error scraping query {query}: {e}")

            browser.close()

    except Exception as e:
        logger.error(f"Playwright error: {e}")

    if not found_leads:
        logger.info("No leads found, generating mock leads.")
        generate_mock_leads()
    else:
        with get_db() as conn:
            for lead in found_leads:
                conn.execute('''
                    INSERT OR IGNORE INTO leads (name, type, city, phone)
                    VALUES (?, ?, ?, ?)
                ''', (lead['name'], lead['type'], lead['city'], lead['phone']))
        logger.info(f"Inserted {len(found_leads)} scraped leads.")

if __name__ == '__main__':
    init_db()
    collect_leads_job()
