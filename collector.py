import sqlite3
import random
from datetime import datetime
from playwright.sync_api import sync_playwright

DB_FILE = 'leads.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_name TEXT NOT NUll,
            type TEXT NOT NULL,
            city TEXT NOT NULL,
            phone TEXT NOT NULL,
            contacted BOOLEAN NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def mock_leads():
    types = ['Clinic', 'Store', 'Service']
    leads = []
    for _ in range(3):
        business_type = random.choice(types)
        leads.append({
            'business_name': f"Sample {business_type} {random.randint(100, 999)}",
            'type': business_type,
            'city': 'Bahawalpur',
            'phone': f"+92 300 {random.randint(1000000, 9999999)}"
        })
    return leads

def collect_leads():
    leads = []
    queries = [
        {"type": "Clinic", "query": "clinics in Bahawalpur"},
        {"type": "Store", "query": "retail stores in Bahawalpur"},
        {"type": "Service", "query": "services in Bahawalpur"}
    ]

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            for q in queries:
                print(f"Searching for: {q['query']}")
                try:
                    page.goto(f"https://www.google.com/maps/search/{q['query'].replace(' ', '+')}")
                    page.wait_for_selector('a[href*="https://www.google.com/maps/place/"]', timeout=10000)

                    # Extract initial results
                    elements = page.query_selector_all('a[href*="https://www.google.com/maps/place/"]')
                    urls = [el.get_attribute("href") for el in elements[:5]] # Limit to 5 per category to save time

                    for url in urls:
                        try:
                            page.goto(url)
                            page.wait_for_selector('h1', timeout=5000)

                            business_name = page.query_selector('h1').inner_text() if page.query_selector('h1') else None

                            # Check for website link (Google Maps typically uses specific data attributes or icons)
                            website_el = page.query_selector('a[data-item-id="authority"]')

                            if not website_el and business_name:
                                # Look for phone number
                                phone_el = page.query_selector('button[data-tooltip="Copy phone number"]')
                                if phone_el:
                                    phone = phone_el.get_attribute("aria-label").replace("Phone: ", "")
                                    leads.append({
                                        'business_name': business_name,
                                        'type': q['type'],
                                        'city': 'Bahawalpur',
                                        'phone': phone
                                    })
                                    print(f"Found lead: {business_name}")
                        except Exception as inner_e:
                            print(f"Error scraping individual listing: {inner_e}")
                            continue
                except Exception as cat_e:
                     print(f"Error searching category {q['query']}: {cat_e}")
                     continue

            browser.close()

        if not leads:
             raise Exception("No real leads found.")

    except Exception as e:
        print(f"Scraping failed or no leads found: {e}. Falling back to mock data.")
        leads = mock_leads()

    save_leads(leads)

def save_leads(leads):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    now = datetime.now().isoformat()
    for lead in leads:
        # Avoid exact duplicates based on phone number
        c.execute('SELECT id FROM leads WHERE phone = ?', (lead['phone'],))
        if not c.fetchone():
            c.execute('''
                INSERT INTO leads (business_name, type, city, phone, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (lead['business_name'], lead['type'], lead['city'], lead['phone'], now))
    conn.commit()
    conn.close()
    print(f"Saved {len(leads)} leads.")

if __name__ == '__main__':
    init_db()
    collect_leads()
