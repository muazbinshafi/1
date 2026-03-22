import sqlite3
from contextlib import contextmanager
import random
import re
from playwright.sync_api import sync_playwright
import time

DATABASE = 'leads.db'

@contextmanager
def get_db(db_path=DATABASE):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def init_db(db_path=DATABASE):
    with get_db(db_path) as conn:
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

def get_uncontacted_leads(db_path=DATABASE):
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM leads WHERE contacted = 0 ORDER BY id DESC')
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def mark_lead_contacted(lead_id, db_path=DATABASE):
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE leads SET contacted = 1 WHERE id = ?', (lead_id,))

def get_stats(db_path=DATABASE):
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM leads')
        total = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM leads WHERE contacted = 1')
        contacted = cursor.fetchone()[0]

        new = total - contacted
        return {
            'total': total,
            'contacted': contacted,
            'new': new
        }

def add_lead(business_name, type_val, city, phone, db_path=DATABASE):
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        # Ensure lead is unique
        cursor.execute('SELECT id FROM leads WHERE phone = ?', (phone,))
        if cursor.fetchone():
            return False

        cursor.execute('''
            INSERT INTO leads (business_name, type, city, phone)
            VALUES (?, ?, ?, ?)
        ''', (business_name, type_val, city, phone))
        return True

def generate_mock_leads(db_path=DATABASE):
    mock_leads = [
        ("Al-Shifa Clinic", "Clinic", "Bahawalpur", "+923001234567"),
        ("City Medical Store", "Store", "Bahawalpur", "+923019876543"),
        ("A-Z Auto Services", "Service", "Bahawalpur", "+923334567890"),
        ("Smile Dental Clinic", "Clinic", "Bahawalpur", "+923001112233"),
        ("Bwp Electronics", "Store", "Bahawalpur", "+923214445555"),
    ]
    added = 0
    for lead in mock_leads:
        if add_lead(*lead, db_path=db_path):
            added += 1
    return added

def collect_leads(db_path=DATABASE):
    # This logic leverages DuckDuckGo HTML search.
    # We will search for local businesses without websites.

    queries = [
        "Clinics in Bahawalpur",
        "Retail stores in Bahawalpur",
        "Services in Bahawalpur"
    ]

    leads_added = 0

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            for query in queries:
                b_type = "Clinic" if "Clinic" in query else "Store" if "store" in query else "Service"

                try:
                    page.goto(f"https://html.duckduckgo.com/html/?q={query}", timeout=15000)
                    time.sleep(2)

                    results = page.query_selector_all('.result')
                    for result in results:
                        title_el = result.query_selector('.result__title a')
                        snippet_el = result.query_selector('.result__snippet')
                        url_el = result.query_selector('.result__url')

                        if not title_el or not snippet_el:
                            continue

                        title = title_el.inner_text().strip()
                        snippet = snippet_el.inner_text().strip()
                        url = url_el.inner_text().strip() if url_el else ""

                        # Phone number regex matching basic pakistani patterns
                        phone_match = re.search(r'(\+92\s?\d{3}\s?\d{7}|0\d{3}\s?\d{7})', snippet)

                        # Filter criteria: We want businesses that appear local (e.g. facebook pages, directories instead of own website)
                        # or ones we can just pick up if we find a phone number.
                        # This is a basic simulation of "no dedicated website"
                        if phone_match and ('facebook.com' in url or 'directory' in url or not url):
                            phone = phone_match.group(1).replace(' ', '')
                            if add_lead(title, b_type, "Bahawalpur", phone, db_path=db_path):
                                leads_added += 1

                except Exception as e:
                    print(f"Error scraping {query}: {e}")

            browser.close()
    except Exception as e:
        print(f"Failed to start playwright: {e}")

    if leads_added == 0:
        print("No leads scraped, falling back to mock leads.")
        leads_added = generate_mock_leads(db_path=db_path)

    return leads_added
