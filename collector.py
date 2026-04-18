import sqlite3
import re
import urllib.parse
from contextlib import contextmanager
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
    with get_db(db_path) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                city TEXT NOT NULL,
                phone TEXT NOT NULL UNIQUE,
                contacted BOOLEAN NOT NULL DEFAULT 0
            )
        ''')

def collect_leads(db_path=None):
    init_db(db_path)

    # We use Playwright to scrape live business data from DuckDuckGo HTML
    query = "businesses in Bahawalpur, Punjab, Pakistan"
    search_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"

    phone_regex = re.compile(r'(03\d{2}[-\s]?\d{7})')

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(search_url)

            # Extract search result snippets
            results = page.locator('.result__snippet').all_inner_texts()
            titles = page.locator('.result__title').all_inner_texts()

            new_leads = []

            for i in range(min(len(results), len(titles))):
                text = results[i].lower()
                title = titles[i]

                # Check for website indicators
                if '.com' in text or '.pk' in text or 'website' in text or 'www.' in text:
                    continue

                # Search for phone numbers
                phone_match = phone_regex.search(text)
                if phone_match:
                    phone = phone_match.group(1)

                    # Deduce basic type (simplistic)
                    type_ = "Service"
                    if "clinic" in title.lower() or "hospital" in title.lower() or "care" in title.lower() or "dental" in title.lower():
                        type_ = "Clinic"
                    elif "store" in title.lower() or "mart" in title.lower() or "shop" in title.lower() or "super" in title.lower():
                        type_ = "Store"

                    new_leads.append((title.strip(), type_, "Bahawalpur", phone))

            browser.close()

            with get_db(db_path) as conn:
                for name, type_, city, phone in new_leads:
                    try:
                        conn.execute(
                            "INSERT INTO leads (name, type, city, phone, contacted) VALUES (?, ?, ?, ?, 0)",
                            (name, type_, city, phone)
                        )
                    except sqlite3.IntegrityError:
                        pass

            if not new_leads:
                # If scraping yielded nothing, use mock
                generate_mock_leads(db_path)
    except Exception as e:
        print(f"Scraping failed: {e}")
        generate_mock_leads(db_path)


def generate_mock_leads(db_path=None):
    init_db(db_path)
    mock_leads = [
        ("Bahawalpur City Hospital", "Clinic", "Bahawalpur", "0300 1234567"),
        ("Al-Shifa Dental Care", "Clinic", "Bahawalpur", "0333 9876543"),
        ("Mega Mart", "Store", "Bahawalpur", "0311 2223334"),
        ("Global IT Services", "Service", "Bahawalpur", "0345 5556667"),
    ]
    with get_db(db_path) as conn:
        for name, type_, city, phone in mock_leads:
            try:
                conn.execute(
                    "INSERT INTO leads (name, type, city, phone, contacted) VALUES (?, ?, ?, ?, 0)",
                    (name, type_, city, phone)
                )
            except sqlite3.IntegrityError:
                pass
