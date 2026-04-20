import sqlite3
import random
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

def init_db():
    with get_db() as db:
        db.execute('''
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
    init_db()
    mock_businesses = [
        ("Health First", "Clinic", "Bahawalpur", "0300-1234567"),
        ("Al-Shifa Care", "Clinic", "Bahawalpur", "0301-7654321"),
        ("Fashion Hub", "Retail Store", "Bahawalpur", "0312-3456789"),
        ("City Mart", "Retail Store", "Bahawalpur", "0333-9876543"),
        ("Tech Fixers", "Service Provider", "Bahawalpur", "0345-1122334"),
        ("Home Sparkle", "Service Provider", "Bahawalpur", "0321-4455667")
    ]
    with get_db() as db:
        for name, type_, city, phone in mock_businesses:
            cursor = db.execute("SELECT 1 FROM leads WHERE phone = ?", (phone,))
            if not cursor.fetchone():
                db.execute('''
                    INSERT INTO leads (name, type, city, phone)
                    VALUES (?, ?, ?, ?)
                ''', (name, type_, city, phone))

def parse_phone(text):
    match = re.search(r'(03\d{2}[-\s]?\d{7})', text)
    if match:
        return match.group(1)
    return None

def has_website(text):
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in ['.com', '.pk', 'website', 'www.'])

def scrape_leads():
    init_db()
    queries = [
        "Clinics Bahawalpur",
        "Retail stores Bahawalpur",
        "Service providers Bahawalpur"
    ]

    new_leads = 0
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            for query in queries:
                biz_type = "Clinic" if "Clinics" in query else "Retail Store" if "Retail" in query else "Service Provider"

                search_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
                try:
                    page.goto(search_url, wait_until='domcontentloaded', timeout=15000)
                    results = page.locator('.result__snippet').all_inner_texts()
                    titles = page.locator('.result__title').all_inner_texts()

                    for i in range(min(len(results), len(titles))):
                        snippet = results[i]
                        title = titles[i].strip()

                        if has_website(snippet):
                            continue

                        phone = parse_phone(snippet)
                        if phone:
                            with get_db() as db:
                                cursor = db.execute("SELECT 1 FROM leads WHERE phone = ?", (phone,))
                                if not cursor.fetchone():
                                    db.execute('''
                                        INSERT INTO leads (name, type, city, phone)
                                        VALUES (?, ?, ?, ?)
                                    ''', (title, biz_type, "Bahawalpur", phone))
                                    new_leads += 1
                except Exception as e:
                    print(f"Error scraping {query}: {e}")

            browser.close()
    except Exception as e:
        print(f"Playwright error: {e}")

    if new_leads == 0:
        # Fallback if scraper fails or finds nothing
        print("Scraper found no leads, using mock data")
        generate_mock_leads()

if __name__ == "__main__":
    scrape_leads()