import sqlite3
import re
from contextlib import contextmanager
from datetime import datetime
import traceback

DB_PATH = 'leads.db'

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
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
                phone TEXT NOT NULL UNIQUE,
                contacted INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

if __name__ == "__main__":
    init_db()
    print("Database initialized.")

def extract_phone(text):
    # Regex to extract Pakistani phone numbers (03 followed by 9 digits with optional space/hyphen)
    match = re.search(r'(03\d{2}[-\s]?\d{7})', text)
    if match:
        return match.group(1)
    return None

def has_website(text):
    # Check if text mentions website, .com, .pk, etc.
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in ['.com', '.pk', 'website', 'www.'])

def scrape_duckduckgo(query, max_results=10):
    from playwright.sync_api import sync_playwright
    import time

    results = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            # Use HTML duckduckgo version as mentioned in memory
            page.goto('https://html.duckduckgo.com/html/')
            page.fill('input[name="q"]', query)
            page.click('input[type="submit"]')

            # Wait for results
            page.wait_for_selector('.web-result', timeout=10000)

            elements = page.query_selector_all('.web-result')

            for el in elements[:max_results]:
                snippet = el.query_selector('.result__snippet')
                title = el.query_selector('.result__title')

                snippet_text = snippet.inner_text() if snippet else ""
                title_text = title.inner_text() if title else ""

                combined_text = title_text + " " + snippet_text

                phone = extract_phone(combined_text)
                if phone and not has_website(combined_text):
                    results.append({
                        'business_name': title_text.strip(),
                        'phone': phone,
                        'combined_text': combined_text
                    })

            browser.close()
    except Exception as e:
        print(f"Scraping failed: {e}")

    return results

def generate_mock_leads():
    mock_data = [
        ("Al-Shifa Clinic", "Clinic", "Bahawalpur", "03001234567"),
        ("City Medical Store", "Store", "Bahawalpur", "03217654321"),
        ("Raza Auto Workshop", "Service", "Bahawalpur", "03339876543"),
        ("Noorani Garments", "Store", "Bahawalpur", "03011122334"),
        ("Dr. Ali Dental Care", "Clinic", "Bahawalpur", "03455566778")
    ]

    with get_db() as conn:
        for name, l_type, city, phone in mock_data:
            try:
                # Check if phone already exists
                cur = conn.cursor()
                cur.execute('SELECT 1 FROM leads WHERE phone = ?', (phone,))
                if not cur.fetchone():
                    conn.execute(
                        'INSERT INTO leads (business_name, type, city, phone) VALUES (?, ?, ?, ?)',
                        (name, l_type, city, phone)
                    )
            except sqlite3.IntegrityError:
                pass

def collect_leads():
    # Use DuckDuckGo to scrape
    queries = [
        "Clinics in Bahawalpur phone number",
        "Retail stores in Bahawalpur phone number",
        "Service providers in Bahawalpur phone number"
    ]

    found_any = False

    for query in queries:
        if "Clinic" in query:
            l_type = "Clinic"
        elif "store" in query:
            l_type = "Store"
        else:
            l_type = "Service"

        results = scrape_duckduckgo(query)
        if results:
            found_any = True
            with get_db() as conn:
                for r in results:
                    try:
                        cur = conn.cursor()
                        cur.execute('SELECT 1 FROM leads WHERE phone = ?', (r['phone'],))
                        if not cur.fetchone():
                            conn.execute(
                                'INSERT INTO leads (business_name, type, city, phone) VALUES (?, ?, ?, ?)',
                                (r['business_name'], l_type, "Bahawalpur", r['phone'])
                            )
                    except sqlite3.IntegrityError:
                        pass

    if not found_any:
        print("Scraper returned no results, falling back to mock leads.")
        generate_mock_leads()
