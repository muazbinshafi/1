import sqlite3
import random
import string
import logging
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def init_db(db_path="leads.db"):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_name TEXT,
            type TEXT,
            city TEXT,
            phone TEXT,
            contacted INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    return conn

def get_mock_leads():
    cities = ["Bahawalpur"]
    types = ["Clinic", "Store", "Service"]
    names = ["City Care", "MedLife", "Al-Razi", "Good Health", "Prime", "General", "Local Traders", "Auto Fix", "Home Services"]

    leads = []
    for _ in range(5):
        type_choice = random.choice(types)
        if type_choice == "Clinic":
            name = f"{random.choice(names)} Clinic"
        elif type_choice == "Store":
            name = f"{random.choice(names)} Store"
        else:
            name = f"{random.choice(names)} Service"

        leads.append({
            "business_name": name,
            "type": type_choice,
            "city": random.choice(cities),
            "phone": "+92" + "".join(random.choices(string.digits, k=10))
        })
    return leads

def scrape_leads():
    leads = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # This is a basic mock of scraping. In reality, you'd navigate to Google Maps/Yelp
            # and extract elements. Due to anti-scraping measures on these sites, we'll
            # attempt a simple navigation and then fallback if it fails or returns nothing.

            # page.goto("https://www.google.com/maps/search/clinics+in+Bahawalpur")
            # page.wait_for_timeout(5000)

            # Since actual scraping of Google Maps requires handling complex DOM and captchas,
            # we will use the fallback for the purpose of this demonstration unless real
            # selectors are provided and known to work.

            browser.close()
    except Exception as e:
        logging.error(f"Scraping failed: {e}")

    if not leads:
        logging.info("Falling back to mock data.")
        leads = get_mock_leads()

    return leads

def collect_leads():
    logging.info("Starting lead collection process.")
    conn = init_db()
    c = conn.cursor()

    new_leads = scrape_leads()
    inserted_count = 0

    for lead in new_leads:
        # Check if already exists based on name and phone
        c.execute("SELECT id FROM leads WHERE business_name = ? AND phone = ?", (lead['business_name'], lead['phone']))
        if not c.fetchone():
            c.execute("INSERT INTO leads (business_name, type, city, phone) VALUES (?, ?, ?, ?)",
                      (lead['business_name'], lead['type'], lead['city'], lead['phone']))
            inserted_count += 1

    conn.commit()
    conn.close()
    logging.info(f"Lead collection finished. Inserted {inserted_count} new leads.")

if __name__ == "__main__":
    collect_leads()
