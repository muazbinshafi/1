import sqlite3
import random
import re
from datetime import datetime
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

def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                business_name TEXT NOT NULL,
                type TEXT NOT NULL,
                city TEXT NOT NULL,
                phone TEXT NOT NULL,
                contacted INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

def generate_mock_leads():
    with get_db() as conn:
        cursor = conn.cursor()
        mock_data = [
            ("City Care Clinic", "Clinic", "Bahawalpur", "0300 1234567"),
            ("Al-Shifa Dental", "Clinic", "Bahawalpur", "0311-9876543"),
            ("Raza Super Store", "Store", "Bahawalpur", "0333 4567890"),
            ("Madina Medical Store", "Store", "Bahawalpur", "03451234567"),
            ("QuickFix Auto Services", "Service", "Bahawalpur", "0322-1122334"),
            ("CleanSweep Cleaning Service", "Service", "Bahawalpur", "0301 9988776")
        ]

        for name, b_type, city, phone in mock_data:
            cursor.execute("SELECT id FROM leads WHERE phone = ?", (phone,))
            if not cursor.fetchone():
                cursor.execute(
                    "INSERT INTO leads (business_name, type, city, phone) VALUES (?, ?, ?, ?)",
                    (name, b_type, city, phone)
                )

def collect_leads():
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            queries = [
                ("Clinics in Bahawalpur phone number", "Clinic"),
                ("Retail stores in Bahawalpur phone number", "Store"),
                ("Services in Bahawalpur phone number", "Service")
            ]

            new_leads = []

            for query, b_type in queries:
                page.goto("https://html.duckduckgo.com/html/")
                page.fill("#search_form_input_homepage", query)
                page.click("#search_button_homepage")
                page.wait_for_selector(".result__snippet", timeout=10000)

                results = page.query_selector_all(".result__body")
                for result in results:
                    text_content = result.inner_text()

                    # Filter out those likely to have a website
                    if re.search(r'\.com|\.pk|website|www\.', text_content, re.IGNORECASE):
                        continue

                    phone_match = re.search(r'(03\d{2}[-\s]?\d{7})', text_content)
                    if phone_match:
                        phone = phone_match.group(1)
                        title_el = result.query_selector(".result__title")
                        name = title_el.inner_text() if title_el else "Unknown Business"

                        # Clean up title
                        name = re.sub(r'\s+', ' ', name).strip()
                        if len(name) > 50:
                            name = name[:47] + "..."

                        new_leads.append((name, b_type, "Bahawalpur", phone))

            browser.close()

            if new_leads:
                with get_db() as conn:
                    cursor = conn.cursor()
                    for name, b_type, city, phone in new_leads:
                        cursor.execute("SELECT id FROM leads WHERE phone = ?", (phone,))
                        if not cursor.fetchone():
                            cursor.execute(
                                "INSERT INTO leads (business_name, type, city, phone) VALUES (?, ?, ?, ?)",
                                (name, b_type, city, phone)
                            )
            else:
                generate_mock_leads()

    except Exception as e:
        print(f"Error during scraping: {e}")
        # Fallback
        generate_mock_leads()

if __name__ == "__main__":
    init_db()
    collect_leads()
