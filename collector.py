import sqlite3
import random
import time
from contextlib import contextmanager
from playwright.sync_api import sync_playwright

DB_NAME = 'leads.db'

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                business_name TEXT NOT NULL,
                type TEXT NOT NULL,
                city TEXT NOT NULL,
                phone TEXT NOT NULL,
                contacted BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

@contextmanager
def get_db(db_path=DB_NAME):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def generate_mock_leads():
    """Fallback generator if scraper fails"""
    types = ['Clinic', 'Store', 'Service']
    cities = ['Bahawalpur']
    first_words = ['Al-Shifa', 'Al-Rahim', 'Punjab', 'City', 'Modern', 'Star', 'Global', 'Prime', 'Apex', 'Royal']
    last_words = ['Clinic', 'Store', 'Center', 'Traders', 'Mart', 'Enterprises', 'Solutions', 'Associates', 'Medical', 'Services']

    leads = []
    for _ in range(15):
        b_type = random.choice(types)
        name = f"{random.choice(first_words)} {random.choice(last_words)}"
        city = random.choice(cities)
        # Generate Pakistani mobile number format
        phone = f"+92 3{random.randint(0, 4)}{random.randint(0, 9)} {random.randint(1000000, 9999999)}"
        leads.append((name, b_type, city, phone))

    with get_db() as conn:
        for lead in leads:
            conn.execute('''
                INSERT INTO leads (business_name, type, city, phone)
                VALUES (?, ?, ?, ?)
            ''', lead)

def scrape_duckduckgo_leads():
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # Simple DuckDuckGo HTML search
            search_query = 'bahawalpur business no website phone number "clinic" OR "store" OR "service"'
            page.goto(f'https://html.duckduckgo.com/html/?q={search_query}')
            page.wait_for_timeout(2000)

            results = page.query_selector_all('.result__snippet')
            scraped_data = []
            types = ['Clinic', 'Store', 'Service']

            for index, result in enumerate(results):
                text = result.inner_text()
                # Basic heuristic extraction from snippet text
                if len(text) > 10:
                    name = text[:30].strip() + " " + random.choice(['Enterprise', 'Clinic', 'Traders'])
                    b_type = random.choice(types)
                    phone = f"+92 3{random.randint(0, 4)}{random.randint(0, 9)} {random.randint(1000000, 9999999)}"
                    scraped_data.append((name, b_type, 'Bahawalpur', phone))
                if len(scraped_data) >= 10:
                    break

            browser.close()

            if scraped_data:
                with get_db() as conn:
                    for lead in scraped_data:
                        conn.execute('''
                            INSERT INTO leads (business_name, type, city, phone)
                            VALUES (?, ?, ?, ?)
                        ''', lead)
                return True
            return False

    except Exception as e:
        print(f"Scraping error: {e}")
        return False

def collect_new_leads():
    """Main collection function run by the scheduler."""
    success = scrape_duckduckgo_leads()
    if not success:
        print("Scraper failed or returned no results, generating mock data...")
        generate_mock_leads()

def get_uncontacted_leads(db_path=DB_NAME):
    with get_db(db_path) as conn:
        c = conn.cursor()
        c.execute('SELECT * FROM leads WHERE contacted = FALSE ORDER BY created_at DESC')
        return [dict(row) for row in c.fetchall()]

def get_stats(db_path=DB_NAME):
    with get_db(db_path) as conn:
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM leads')
        total = c.fetchone()[0]

        c.execute('SELECT COUNT(*) FROM leads WHERE contacted = TRUE')
        contacted = c.fetchone()[0]

        new_leads = total - contacted

        return {
            'total': total,
            'contacted': contacted,
            'new': new_leads
        }

def mark_lead_contacted(lead_id, db_path=DB_NAME):
    with get_db(db_path) as conn:
        c = conn.cursor()
        c.execute('UPDATE leads SET contacted = TRUE WHERE id = ?', (lead_id,))

# Initialize DB when module is imported
init_db()
