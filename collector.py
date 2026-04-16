import sqlite3
import re
import os
import time
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
        conn.execute('''
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                business_name TEXT NOT NULL,
                type TEXT NOT NULL,
                city TEXT NOT NULL,
                phone TEXT NOT NULL,
                contacted BOOLEAN NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

def generate_mock_leads():
    """Fallback mock data generation if scraper fails."""
    mock_data = [
        ("Al-Shifa Clinic", "Clinic", "Bahawalpur", "0300-1234567"),
        ("Ahmed General Store", "Store", "Bahawalpur", "0311-9876543"),
        ("Raza Auto Services", "Service", "Bahawalpur", "0322-5556667"),
        ("City Dental Care", "Clinic", "Bahawalpur", "0333-1112223"),
        ("Bismillah Electronics", "Store", "Bahawalpur", "0344-9998887"),
    ]
    with get_db() as conn:
        for name, type_, city, phone in mock_data:
            # Check if exists
            cur = conn.execute('SELECT 1 FROM leads WHERE phone = ?', (phone,))
            if not cur.fetchone():
                conn.execute(
                    'INSERT INTO leads (business_name, type, city, phone) VALUES (?, ?, ?, ?)',
                    (name, type_, city, phone)
                )

def collect_leads():
    """Scrape DuckDuckGo HTML for Bahawalpur businesses without websites."""
    print("Starting background lead collection...")
    queries = [
        "Clinics in Bahawalpur contact number",
        "Stores in Bahawalpur contact number",
        "Services in Bahawalpur contact number"
    ]

    # regex for pakistani phone numbers
    phone_pattern = re.compile(r'(03\d{2}[-\s]?\d{7})')
    # Filter out text containing website indicators
    website_indicators = ['.com', '.pk', 'website', 'www.']

    scraped_any = False

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            for query in queries:
                b_type = "Service"
                if "Clinic" in query: b_type = "Clinic"
                if "Store" in query: b_type = "Store"

                page.goto('https://html.duckduckgo.com/html/')
                page.fill('#search_form_input_homepage', query)
                page.click('#search_button_homepage')
                page.wait_for_selector('.result__snippet', timeout=10000)

                results = page.locator('.result__snippet').all()
                for result in results:
                    text = result.inner_text().lower()
                    has_website = any(ind in text for ind in website_indicators)
                    if has_website:
                        continue

                    match = phone_pattern.search(text)
                    if match:
                        phone = match.group(1)
                        # Extract a pseudo-name from the text (just using the first few words for demo purposes)
                        # A better approach would be to get the title from the result
                        title_el = result.locator('xpath=../preceding-sibling::h2/a')
                        if title_el.count() > 0:
                            business_name = title_el.first.inner_text()
                        else:
                            business_name = text.split()[0] + " " + b_type # fallback

                        with get_db() as conn:
                            cur = conn.execute('SELECT 1 FROM leads WHERE phone = ?', (phone,))
                            if not cur.fetchone():
                                conn.execute(
                                    'INSERT INTO leads (business_name, type, city, phone) VALUES (?, ?, ?, ?)',
                                    (business_name, b_type, "Bahawalpur", phone)
                                )
                                scraped_any = True
            browser.close()
    except Exception as e:
        print(f"Scraping failed: {e}. Falling back to mock data.")

    if not scraped_any:
        print("No new leads scraped. Generating mock leads.")
        generate_mock_leads()
    print("Lead collection finished.")
