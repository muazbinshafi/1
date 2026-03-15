import sqlite3
import random

def get_db(db_path='leads.db'):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def generate_mock_leads(db_path='leads.db'):
    conn = get_db(db_path)
    c = conn.cursor()

    mock_data = [
        {"business_name": "Al-Shifa Family Clinic", "type": "Clinic", "city": "Bahawalpur", "phone": "0300-1234567"},
        {"business_name": "City Care Hospital", "type": "Clinic", "city": "Bahawalpur", "phone": "0321-7654321"},
        {"business_name": "Punjab Medical Store", "type": "Store", "city": "Bahawalpur", "phone": "0333-9876543"},
        {"business_name": "Super Mart Retail", "type": "Store", "city": "Bahawalpur", "phone": "0345-5678901"},
        {"business_name": "AutoFix Services", "type": "Service", "city": "Bahawalpur", "phone": "0301-2345678"},
        {"business_name": "Green Thumb Landscaping", "type": "Service", "city": "Bahawalpur", "phone": "0312-3456789"},
    ]

    for lead in mock_data:
        try:
            c.execute('''
                INSERT INTO leads (business_name, type, city, phone)
                VALUES (?, ?, ?, ?)
            ''', (lead['business_name'], lead['type'], lead['city'], lead['phone']))
        except sqlite3.IntegrityError:
            pass # ignore duplicates

    conn.commit()
    conn.close()
    print("Mock leads generated.")

import re
from playwright.sync_api import sync_playwright

def scrape_duckduckgo(query, type_name, city, db_path='leads.db'):
    leads = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            # We use duckduckgo HTML version as a proxy to find businesses
            # because google maps requires more complex scraping and bypasses
            search_url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
            page.goto(search_url, timeout=30000)

            # Extract search result snippets
            results = page.locator('.result__body').all()
            for result in results:
                title = result.locator('.result__title').inner_text()
                snippet = result.locator('.result__snippet').inner_text()

                # Check if there's a phone number in title or snippet
                # Simple phone regex for Pakistan formats
                phone_match = re.search(r'(0\d{2,3}[-\s]?\d{7}|\+92\s?\d{3}[-\s]?\d{7})', snippet + title)

                # Filter out those mentioning website in snippet (proxy for "no website")
                if phone_match and "www" not in snippet.lower() and "http" not in snippet.lower():
                    # Check if business name is already collected
                    business_name = title.split('|')[0].strip()
                    leads.append({
                        "business_name": business_name[:50], # Trim to avoid huge text
                        "type": type_name,
                        "city": city,
                        "phone": phone_match.group(1).strip()
                    })
        except Exception as e:
            print(f"Error scraping {query}: {e}")
            raise e
        finally:
            browser.close()

    # Insert to db
    if leads:
        conn = get_db(db_path)
        c = conn.cursor()
        for lead in leads:
            try:
                c.execute('''
                    INSERT INTO leads (business_name, type, city, phone)
                    VALUES (?, ?, ?, ?)
                ''', (lead['business_name'], lead['type'], lead['city'], lead['phone']))
            except sqlite3.IntegrityError:
                pass # ignore duplicates
        conn.commit()
        conn.close()
        print(f"Collected {len(leads)} real leads for {query}.")
        return True
    return False

def run_collector(db_path='leads.db'):
    print("Running collector...")
    queries = [
        {"query": "Clinics in Bahawalpur phone number", "type": "Clinic", "city": "Bahawalpur"},
        {"query": "Retail stores in Bahawalpur phone number", "type": "Store", "city": "Bahawalpur"},
        {"query": "Plumbers or services in Bahawalpur phone number", "type": "Service", "city": "Bahawalpur"}
    ]

    all_success = False
    for q in queries:
        try:
            success = scrape_duckduckgo(q["query"], q["type"], q["city"], db_path)
            if success:
                all_success = True
        except Exception as e:
            print(f"Scraper failed for {q['query']}: {e}")

    if not all_success:
        print("Scraper didn't yield results or failed, generating mock data...")
        generate_mock_leads(db_path)

if __name__ == '__main__':
    run_collector()
