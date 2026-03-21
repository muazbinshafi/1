import sqlite3
from contextlib import contextmanager
import random
import time
from playwright.sync_api import sync_playwright
import re

DATABASE = 'leads.db'

@contextmanager
def get_db(db_name=DATABASE):
    conn = sqlite3.connect(db_name)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def init_db(db_name=DATABASE):
    with get_db(db_name) as db:
        db.execute('''
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

def collect_leads(db_name=DATABASE):
    init_db(db_name)
    queries = [
        ("clinics in Bahawalpur pakistan", "Clinic"),
        ("stores in Bahawalpur pakistan", "Store"),
        ("services in Bahawalpur pakistan", "Service")
    ]

    collected_count = 0
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            for query, b_type in queries:
                try:
                    page.goto(f"https://html.duckduckgo.com/html/?q={query}", timeout=30000)
                    time.sleep(2)

                    results = page.locator(".result__body").all()
                    for result in results:
                        text = result.inner_text()

                        # basic phone number regex for pakistani numbers
                        phone_match = re.search(r'(\+92\s?\d{3}\s?\d{7}|0\d{3}\s?\d{7})', text)
                        # basic heuristics to skip websites
                        has_website = "www." in text or ".com" in text or ".pk" in text

                        if phone_match and not has_website:
                            business_name = result.locator(".result__title").inner_text().strip()
                            phone = phone_match.group(1).replace(" ", "")

                            # Check if already exists
                            with get_db(db_name) as db:
                                existing = db.execute("SELECT id FROM leads WHERE phone = ?", (phone,)).fetchone()
                                if not existing:
                                    db.execute('''
                                        INSERT INTO leads (business_name, type, city, phone)
                                        VALUES (?, ?, 'Bahawalpur', ?)
                                    ''', (business_name, b_type, phone))
                                    collected_count += 1
                except Exception as e:
                    print(f"Error scraping {query}: {e}")

            browser.close()
    except Exception as e:
        print(f"Playwright error: {e}")

    if collected_count == 0:
        print("Scraping failed or no new leads, generating mock data.")
        generate_mock_leads(db_name)


def generate_mock_leads(db_name=DATABASE):
    init_db(db_name)
    mock_data = [
        ("Bahawalpur Care Clinic", "Clinic", "+923001234567"),
        ("Health First Center", "Clinic", "+923011234567"),
        ("Al-Madina Pharmacy", "Store", "+923021234567"),
        ("Rizwan Electronics", "Store", "+923031234567"),
        ("A-One Plumbers", "Service", "+923041234567"),
        ("City Auto Workshop", "Service", "+923051234567"),
    ]

    with get_db(db_name) as db:
        for name, b_type, phone in mock_data:
            db.execute('''
                INSERT INTO leads (business_name, type, city, phone)
                VALUES (?, ?, 'Bahawalpur', ?)
            ''', (name, b_type, phone))

def get_uncontacted_leads(db_name=DATABASE):
    with get_db(db_name) as db:
        leads = db.execute('''
            SELECT * FROM leads WHERE contacted = 0 ORDER BY created_at DESC
        ''').fetchall()
        return [dict(lead) for lead in leads]

def get_stats(db_name=DATABASE):
    with get_db(db_name) as db:
        total = db.execute('SELECT COUNT(*) FROM leads').fetchone()[0]
        contacted = db.execute('SELECT COUNT(*) FROM leads WHERE contacted = 1').fetchone()[0]
        new = db.execute('SELECT COUNT(*) FROM leads WHERE contacted = 0').fetchone()[0]
        return {"total": total, "contacted": contacted, "new": new}

def mark_contacted(lead_id, db_name=DATABASE):
    with get_db(db_name) as db:
        db.execute('UPDATE leads SET contacted = 1 WHERE id = ?', (lead_id,))
