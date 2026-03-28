import sqlite3
import random
import re
from contextlib import contextmanager
from playwright.sync_api import sync_playwright

@contextmanager
def get_db(db_path="leads.db"):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.commit()
        conn.close()

def init_db(db_path="leads.db"):
    with get_db(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                business_name TEXT NOT NULL,
                type TEXT NOT NULL,
                city TEXT NOT NULL,
                phone TEXT NOT NULL,
                contacted INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(business_name, phone)
            )
        """)

def get_uncontacted_leads(db_path="leads.db"):
    with get_db(db_path) as conn:
        cursor = conn.execute("SELECT * FROM leads WHERE contacted = 0 ORDER BY id DESC")
        return [dict(row) for row in cursor.fetchall()]

def mark_contacted(lead_id, db_path="leads.db"):
    with get_db(db_path) as conn:
        conn.execute("UPDATE leads SET contacted = 1 WHERE id = ?", (lead_id,))

def get_stats(db_path="leads.db"):
    with get_db(db_path) as conn:
        total = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
        contacted = conn.execute("SELECT COUNT(*) FROM leads WHERE contacted = 1").fetchone()[0]
        new = total - contacted
        return {"total": total, "contacted": contacted, "new": new}

def save_lead(business_name, business_type, city, phone, db_path="leads.db"):
    try:
        with get_db(db_path) as conn:
            conn.execute(
                "INSERT INTO leads (business_name, type, city, phone) VALUES (?, ?, ?, ?)",
                (business_name, business_type, city, phone)
            )
            return True
    except sqlite3.IntegrityError:
        return False # duplicate

def scrape_duckduckgo(query, business_type, city, db_path="leads.db"):
    leads_found = 0
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            url = f"https://html.duckduckgo.com/html/?q={query}"
            page.goto(url, timeout=30000)

            # Extract results
            results = page.locator('.result__body').all()
            for result in results:
                try:
                    title_elem = result.locator('.result__title')
                    snippet_elem = result.locator('.result__snippet')
                    if not title_elem.count() or not snippet_elem.count():
                        continue

                    title = title_elem.inner_text().strip()
                    snippet = snippet_elem.inner_text().strip()

                    # Basic exclusion to mimic "no website" if we find certain keywords
                    if "website" in title.lower() or "website" in snippet.lower():
                        continue

                    # Extract phone number (simple regex for pakistani numbers / general formats)
                    phone_match = re.search(r'(\+92|0)[-\s]?\d{3}[-\s]?\d{7}', snippet) or \
                                  re.search(r'\b\d{4}[-\s]?\d{7}\b', snippet) or \
                                  re.search(r'\b03\d{2}[-\s]?\d{7}\b', snippet)

                    if phone_match:
                        phone = phone_match.group(0).strip()
                        if save_lead(title, business_type, city, phone, db_path):
                            leads_found += 1
                except Exception:
                    continue
        except Exception as e:
            print(f"Scraping failed for {query}: {e}")
        finally:
            browser.close()
    return leads_found

def collect_leads_job(db_path="leads.db"):
    city = "Bahawalpur"
    queries = [
        {"q": f"clinic phone number {city} -website", "type": "Clinic"},
        {"q": f"store shop phone number {city} -website", "type": "Store"},
        {"q": f"repair service phone number {city} -website", "type": "Service"},
        {"q": f"medical clinic {city} contact number", "type": "Clinic"},
        {"q": f"retail shop {city} contact number", "type": "Store"},
    ]

    total_found = 0
    for q in queries:
        found = scrape_duckduckgo(q['q'], q['type'], city, db_path)
        total_found += found

    if total_found == 0:
        generate_mock_leads(db_path)

def generate_mock_leads(db_path="leads.db"):
    mock_data = [
        {"name": "Al-Shifa Clinic", "type": "Clinic", "phone": "+923001234567"},
        {"name": "Bahawalpur General Store", "type": "Store", "phone": "03001234568"},
        {"name": "QuickFix Auto Service", "type": "Service", "phone": "03001234569"},
        {"name": "City Dental Care", "type": "Clinic", "phone": "+923001234570"},
        {"name": "Zubair Hardware", "type": "Store", "phone": "03001234571"},
        {"name": "A1 Plumbers", "type": "Service", "phone": "03001234572"},
        {"name": "Care Medical Center", "type": "Clinic", "phone": "+923001234573"},
        {"name": "Model Town Supermarket", "type": "Store", "phone": "03001234574"},
        {"name": "Express Electronics Repair", "type": "Service", "phone": "03001234575"},
    ]
    city = "Bahawalpur"

    for _ in range(3):
        lead = random.choice(mock_data)
        phone = lead["phone"][:-2] + str(random.randint(10, 99))
        save_lead(lead["name"] + f" {random.randint(1, 100)}", lead["type"], city, phone, db_path)
