import sqlite3
import random
import re
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
                business_name TEXT NOT NULL,
                type TEXT NOT NULL,
                city TEXT NOT NULL,
                phone TEXT NOT NULL UNIQUE,
                contacted INTEGER DEFAULT 0
            )
        ''')

def generate_mock_leads():
    setup_db()

    cities = ['Bahawalpur']
    types = ['Clinic', 'Retail Store', 'Service Provider']
    businesses = [
        ('Al-Shifa Care', 'Clinic'),
        ('City Med', 'Clinic'),
        ('Bahawalpur Goods', 'Retail Store'),
        ('Daily Mart', 'Retail Store'),
        ('Quick Fix Plumbers', 'Service Provider'),
        ('A1 Electricians', 'Service Provider')
    ]

    with get_db() as conn:
        for name, b_type in businesses:
            city = random.choice(cities)
            # Generate a pakistani style number: 03XX-XXXXXXX
            phone = f"03{random.randint(0,9)}{random.randint(0,9)}-{random.randint(1000000, 9999999)}"

            # Check if it already exists
            cur = conn.execute("SELECT id FROM leads WHERE phone = ?", (phone,))
            if not cur.fetchone():
                conn.execute('''
                    INSERT INTO leads (business_name, type, city, phone)
                    VALUES (?, ?, ?, ?)
                ''', (name, b_type, city, phone))

def scrape_leads():
    setup_db()

    queries = [
        "Clinics in Bahawalpur",
        "Retail stores in Bahawalpur",
        "Plumbers in Bahawalpur"
    ]

    scraped_count = 0
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for query in queries:
            try:
                page.goto("https://html.duckduckgo.com/html/")
                page.fill("#search_form_input_homepage", query)
                page.click("#search_button_homepage")
                page.wait_for_selector(".result", timeout=10000)

                results = page.locator(".result").all()
                for result in results:
                    text_content = result.inner_text()

                    # Ensure no website is mentioned
                    if re.search(r'\.com|\.pk|website|www\.', text_content, re.IGNORECASE):
                        continue

                    # Extract phone number
                    phone_match = re.search(r'(03\d{2}[-\s]?\d{7})', text_content)
                    if not phone_match:
                        continue

                    phone = phone_match.group(1)
                    title = result.locator(".result__title").inner_text()

                    b_type = "Service Provider"
                    if "Clinic" in query: b_type = "Clinic"
                    elif "Retail" in query: b_type = "Retail Store"

                    with get_db() as conn:
                        try:
                            conn.execute('''
                                INSERT INTO leads (business_name, type, city, phone)
                                VALUES (?, ?, ?, ?)
                            ''', (title, b_type, 'Bahawalpur', phone))
                            scraped_count += 1
                        except sqlite3.IntegrityError:
                            pass # Duplicate phone

            except Exception as e:
                print(f"Error scraping {query}: {e}")

        browser.close()

    if scraped_count == 0:
        print("No leads scraped. Falling back to mock data.")
        generate_mock_leads()
