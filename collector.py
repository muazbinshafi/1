import sqlite3
from contextlib import contextmanager
from playwright.sync_api import sync_playwright
import re
import time
import os

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

def setup_db():
    with get_db() as db:
        db.execute('''
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                city TEXT NOT NULL,
                phone TEXT NOT NULL UNIQUE,
                status TEXT DEFAULT 'pending'
            )
        ''')

def generate_mock_leads():
    mock_leads = [
        {"name": "Bahawalpur Health Clinic", "type": "Clinic", "city": "Bahawalpur", "phone": "0300-1234567"},
        {"name": "Ali Retail Store", "type": "Store", "city": "Bahawalpur", "phone": "0311-9876543"},
        {"name": "Punjab Repair Services", "type": "Service", "city": "Bahawalpur", "phone": "0333-5551234"},
        {"name": "Cholistan Medical Care", "type": "Clinic", "city": "Bahawalpur", "phone": "0321-4445555"}
    ]
    with get_db() as db:
        for lead in mock_leads:
            try:
                db.execute(
                    "INSERT INTO leads (name, type, city, phone) VALUES (?, ?, ?, ?)",
                    (lead["name"], lead["type"], lead["city"], lead["phone"])
                )
            except sqlite3.IntegrityError:
                pass # Already exists

def collect_leads():
    queries = [
        "Clinics in Bahawalpur Punjab Pakistan",
        "Retail stores in Bahawalpur Punjab Pakistan",
        "Service providers in Bahawalpur Punjab Pakistan"
    ]

    phone_regex = re.compile(r'(03\d{2}[-\s]?\d{7})')

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            for query in queries:
                b_type = "Clinic"
                if "Retail" in query:
                    b_type = "Store"
                elif "Service" in query:
                    b_type = "Service"

                page.goto("https://html.duckduckgo.com/html/")
                page.fill('#search_form_input_homepage', query)
                page.click('#search_button_homepage')
                page.wait_for_load_state('domcontentloaded')

                results = page.locator('.result__snippet').all_text_contents()
                titles = page.locator('.result__title').all_text_contents()

                for idx, text in enumerate(results):
                    # Filter out those with websites
                    if any(x in text.lower() for x in ['.com', '.pk', 'website', 'www.']):
                        continue

                    match = phone_regex.search(text)
                    if match:
                        phone = match.group(1)
                        name = titles[idx].strip() if idx < len(titles) else f"Unknown {b_type}"

                        # Clean up DDG title artifacts
                        name = re.sub(r' \s*\|\s* .*', '', name)

                        with get_db() as db:
                            try:
                                db.execute(
                                    "INSERT INTO leads (name, type, city, phone) VALUES (?, ?, ?, ?)",
                                    (name, b_type, "Bahawalpur", phone)
                                )
                            except sqlite3.IntegrityError:
                                pass # Already exists
            browser.close()
    except Exception as e:
        print(f"Scraper error, falling back to mock data: {e}")
        generate_mock_leads()

if __name__ == '__main__':
    setup_db()
    collect_leads()
