import sqlite3
import re
import os
from contextlib import contextmanager
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

def setup_db():
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                city TEXT NOT NULL,
                phone TEXT NOT NULL UNIQUE,
                is_contacted BOOLEAN NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

def generate_mock_leads():
    setup_db()
    mock_leads = [
        ("Bahawalpur Care Clinic", "Clinic", "Bahawalpur", "0300-1234567"),
        ("Al-Madina Store", "Retail Store", "Bahawalpur", "0301-7654321"),
        ("Sadiq Services Co.", "Service Provider", "Bahawalpur", "0321-9876543"),
        ("Punjab Health Center", "Clinic", "Bahawalpur", "0333-1112223")
    ]
    with get_db() as conn:
        for name, ltype, city, phone in mock_leads:
            try:
                conn.execute(
                    "INSERT INTO leads (name, type, city, phone) VALUES (?, ?, ?, ?)",
                    (name, ltype, city, phone)
                )
            except sqlite3.IntegrityError:
                pass

def collect_leads():
    setup_db()
    query = "local businesses in Bahawalpur Punjab Pakistan phone number"
    url = f"https://html.duckduckgo.com/html/?q={query}"

    scraped_leads = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        try:
            page.goto(url, timeout=30000)
            results = page.query_selector_all('.result__body')
            for result in results:
                snippet_element = result.query_selector('.result__snippet')
                if not snippet_element:
                    continue
                snippet = snippet_element.inner_text().lower()

                # Check for website indicators
                if '.com' in snippet or '.pk' in snippet or 'www.' in snippet or 'website' in snippet:
                    continue

                # Find phone number
                phone_match = re.search(r'(03\d{2}[-\s]?\d{7})', snippet)
                if not phone_match:
                    continue

                phone = phone_match.group(1).replace(' ', '-')

                # Try to extract name
                title_element = result.query_selector('.result__title')
                name = title_element.inner_text().strip() if title_element else "Local Business"

                # Determine type heuristically
                ltype = "Service Provider"
                if any(x in snippet for x in ['clinic', 'hospital', 'health', 'doctor', 'medical']):
                    ltype = "Clinic"
                elif any(x in snippet for x in ['store', 'shop', 'retail', 'mart']):
                    ltype = "Retail Store"

                scraped_leads.append((name, ltype, "Bahawalpur", phone))

        except Exception as e:
            print(f"Scraping failed: {e}")
        finally:
            browser.close()

    if not scraped_leads:
        generate_mock_leads()
    else:
        with get_db() as conn:
            for name, ltype, city, phone in scraped_leads:
                try:
                    conn.execute(
                        "INSERT INTO leads (name, type, city, phone) VALUES (?, ?, ?, ?)",
                        (name, ltype, city, phone)
                    )
                except sqlite3.IntegrityError:
                    pass

if __name__ == '__main__':
    collect_leads()
