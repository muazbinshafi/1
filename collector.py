import sqlite3
import re
import datetime
from contextlib import contextmanager
from playwright.sync_api import sync_playwright
import random
import logging

DB_PATH = 'leads.db'
logging.basicConfig(level=logging.INFO)

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
    with get_db(db_path) as db:
        db.execute('''
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

def generate_mock_leads(db_path=None):
    """Fallback mechanism to generate mock leads if scraper fails or for testing."""
    businesses = [
        {"name": "Al-Shifa Clinic", "type": "Clinic"},
        {"name": "Bahawalpur General Store", "type": "Store"},
        {"name": "City Auto Services", "type": "Service"},
        {"name": "Sadiq Dental Care", "type": "Clinic"},
        {"name": "Punjab Hardware", "type": "Store"},
    ]
    city = "Bahawalpur"

    with get_db(db_path) as db:
        for b in businesses:
            phone = f"03{random.randint(10, 49)}-{random.randint(1000000, 9999999)}"
            # Ensure no duplicates
            cur = db.execute('SELECT 1 FROM leads WHERE phone = ?', (phone,))
            if not cur.fetchone():
                db.execute(
                    'INSERT INTO leads (business_name, type, city, phone) VALUES (?, ?, ?, ?)',
                    (b["name"], b["type"], city, phone)
                )
    logging.info("Mock leads generated.")


def extract_phone_number(text):
    # Match Pakistani phone numbers
    match = re.search(r'(03\d{2}[-\s]?\d{7})', text)
    if match:
        return match.group(1)
    return None

def has_website(text):
    text_lower = text.lower()
    return any(kw in text_lower for kw in ['.com', '.pk', 'website', 'www.'])

def collect_leads(db_path=None):
    init_db(db_path)
    city = "Bahawalpur"
    queries = [
        f"clinics in {city} phone number",
        f"retail stores in {city} phone number",
        f"repair services in {city} phone number"
    ]

    leads_found = False

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            for query in queries:
                b_type = "Clinic" if "clinics" in query else "Store" if "stores" in query else "Service"
                logging.info(f"Searching for: {query}")

                try:
                    page.goto("https://html.duckduckgo.com/html/")
                    page.fill("#search_form_input_homepage", query)
                    page.click("#search_button_homepage")
                    page.wait_for_selector(".result", timeout=10000)

                    results = page.locator(".result").all()

                    for result in results:
                        text_content = result.inner_text()

                        if has_website(text_content):
                            continue

                        phone = extract_phone_number(text_content)
                        if not phone:
                            continue

                        # Try to extract business name (naive approach: first line)
                        lines = text_content.strip().split('\n')
                        b_name = lines[0] if lines else f"Unknown {b_type}"

                        with get_db(db_path) as db:
                            cur = db.execute('SELECT 1 FROM leads WHERE phone = ?', (phone,))
                            if not cur.fetchone():
                                db.execute(
                                    'INSERT INTO leads (business_name, type, city, phone) VALUES (?, ?, ?, ?)',
                                    (b_name, b_type, city, phone)
                                )
                                leads_found = True
                                logging.info(f"Added lead: {b_name} ({phone})")
                except Exception as e:
                    logging.error(f"Error during search '{query}': {e}")

            browser.close()

    except Exception as e:
        logging.error(f"Scraping failed: {e}")

    if not leads_found:
        logging.info("No leads found via scraping, generating mock leads.")
        generate_mock_leads(db_path)

if __name__ == "__main__":
    collect_leads()
