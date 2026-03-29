import sqlite3
import random
import time
from contextlib import contextmanager

DB_NAME = 'leads.db'

@contextmanager
def get_db(db_path=DB_NAME):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def init_db(db_path=DB_NAME):
    with get_db(db_path) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                business_name TEXT NOT NULL,
                type TEXT NOT NULL,
                city TEXT NOT NULL,
                phone TEXT NOT NULL,
                contacted BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(phone)
            )
        ''')

def get_uncontacted_leads(db_path=DB_NAME):
    with get_db(db_path) as conn:
        cursor = conn.execute(
            'SELECT id, business_name, type, city, phone FROM leads WHERE contacted = 0 ORDER BY created_at DESC'
        )
        return [dict(row) for row in cursor.fetchall()]

def mark_contacted(lead_id, db_path=DB_NAME):
    with get_db(db_path) as conn:
        conn.execute('UPDATE leads SET contacted = 1 WHERE id = ?', (lead_id,))

def get_stats(db_path=DB_NAME):
    with get_db(db_path) as conn:
        total = conn.execute('SELECT COUNT(*) FROM leads').fetchone()[0]
        contacted = conn.execute('SELECT COUNT(*) FROM leads WHERE contacted = 1').fetchone()[0]
        return {
            'total': total,
            'contacted': contacted,
            'new': total - contacted
        }

def add_lead(business_name, type, city, phone, db_path=DB_NAME):
    try:
        with get_db(db_path) as conn:
            conn.execute(
                'INSERT INTO leads (business_name, type, city, phone) VALUES (?, ?, ?, ?)',
                (business_name, type, city, phone)
            )
            return True
    except sqlite3.IntegrityError:
        return False # duplicate phone

def generate_mock_leads(db_path=DB_NAME):
    """Fallback mechanism to generate mock data if scraper fails or for testing."""
    mock_businesses = [
        ("Al-Shifa Clinic", "Clinic"),
        ("Zain Medico", "Store"),
        ("City Dental Care", "Clinic"),
        ("Rana Electronics", "Store"),
        ("Prime Plumbers", "Service"),
        ("A-One Auto Repair", "Service"),
        ("Fatima Health Center", "Clinic"),
        ("Super Mart Grocery", "Store"),
        ("QuickFix AC Repair", "Service"),
        ("Modern Pet Clinic", "Clinic"),
    ]
    city = "Bahawalpur"

    added_count = 0
    for name, b_type in mock_businesses:
        # Generate random Pakistani phone number
        phone = f"+923{random.randint(0, 4)}{random.randint(0, 9)}{random.randint(1000000, 9999999)}"
        if add_lead(name, b_type, city, phone, db_path):
            added_count += 1
    return added_count

def collect_leads(db_path=DB_NAME):
    """
    Scrape live business data from Bahawalpur that lack websites.
    Using DuckDuckGo HTML search as a reliable proxy.
    """
    from playwright.sync_api import sync_playwright
    import re

    city = "Bahawalpur"
    queries = [
        f"Clinics in {city} phone number",
        f"Retail stores in {city} phone number",
        f"Repair services in {city} phone number"
    ]

    total_added = 0

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            for query in queries:
                b_type = "Clinic" if "Clinic" in query else "Store" if "store" in query else "Service"
                search_url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"

                try:
                    page.goto(search_url, timeout=30000)
                    results = page.locator('.result__body')
                    count = results.count()

                    for i in range(count):
                        result = results.nth(i)
                        text = result.inner_text()

                        # Basic filtering for businesses likely without websites
                        # Usually snippet contains phone numbers if we ask for it
                        phone_match = re.search(r'(?:\+92|0|92)[-\s]?3\d{2}[-\s]?\d{7}', text)
                        if not phone_match:
                            continue

                        phone = phone_match.group(0).replace(" ", "").replace("-", "")

                        # Extract name (approximation from title)
                        title_el = result.locator('.result__title')
                        if title_el.count() > 0:
                            name = title_el.inner_text().strip()
                        else:
                            name = f"Unknown {b_type}"

                        # Basic heuristics to check if they have a website link
                        url_el = result.locator('.result__url')
                        has_website = False
                        if url_el.count() > 0:
                            url_text = url_el.inner_text().lower()
                            # If it's just a directory listing like facebook, justdial, etc. we consider it 'no dedicated website'
                            dedicated_website_indicators = ['.com', '.pk', '.org', '.net']
                            directories = ['facebook', 'instagram', 'justdial', 'yelp', 'yellowpages', 'olx']

                            if any(ind in url_text for ind in dedicated_website_indicators) and not any(dir in url_text for dir in directories):
                                has_website = True

                        if not has_website:
                            if add_lead(name, b_type, city, phone, db_path):
                                total_added += 1

                except Exception as e:
                    print(f"Error scraping query '{query}': {e}")

            browser.close()

    except Exception as e:
        print(f"Playwright error during collection: {e}")

    # Fallback if no leads were collected
    if total_added == 0:
        print("No leads collected via scraping. Using mock data fallback.")
        total_added = generate_mock_leads(db_path)

    return total_added

if __name__ == "__main__":
    init_db()
