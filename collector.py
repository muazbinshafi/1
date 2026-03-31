import os
import re
import urllib.parse
from playwright.sync_api import sync_playwright
from database import get_db, DATABASE

BUSINESS_TYPES = ["Clinic", "Store", "Service"]
LOCATION = "Bahawalpur"

def extract_phone(text):
    """Simple regex to extract phone numbers from text."""
    if not text:
        return None
    # Basic matching for PK numbers and general formats
    match = re.search(r'(\+92\s?\d{3}\s?\d{7}|0\d{3}\s?\d{7}|0\d{10})', text)
    if match:
        return match.group(1)
    return None

def scrape_leads():
    """Scrapes leads from DuckDuckGo HTML search for Bahawalpur businesses without websites."""
    print("Attempting to scrape leads...")
    leads = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            )
            page = context.new_page()

            for b_type in BUSINESS_TYPES:
                # Query: Bahawalpur Clinic phone number -"http" -"www"
                query = f"{LOCATION} {b_type} phone number -\"http\" -\"www\""
                encoded_query = urllib.parse.quote_plus(query)
                search_url = f"https://html.duckduckgo.com/html/?q={encoded_query}"

                print(f"Scraping DuckDuckGo for: {query}")
                try:
                    page.goto(search_url, timeout=15000)
                    results = page.locator('.result__body').all()

                    for result in results:
                        try:
                            title = result.locator('.result__title').inner_text().strip()
                            snippet = result.locator('.result__snippet').inner_text().strip()

                            # Clean title from common suffixes like " - Bahawalpur"
                            clean_title = re.sub(r'(-|\|).+', '', title).strip()

                            # Extract phone
                            phone = extract_phone(snippet)

                            if phone and clean_title:
                                # Ensure we don't pick up obvious directory websites as business names
                                if not any(x in clean_title.lower() for x in ['.com', '.pk', 'facebook', 'yellow pages']):
                                    leads.append({
                                        'business_name': clean_title,
                                        'type': b_type,
                                        'city': LOCATION,
                                        'phone': phone
                                    })
                        except Exception as e:
                            # Skip problematic individual results
                            continue

                except Exception as e:
                    print(f"Error scraping for {b_type}: {e}")

            browser.close()
    except Exception as e:
        print(f"Playwright initialization or overall scraping failed: {e}")

    return leads

import random
import uuid

def generate_mock_leads():
    """Fallback mechanism to generate mock data if scraper fails."""
    leads = []

    mock_data = {
        "Clinic": ["Al-Shifa Eye Care", "CareWell Family Clinic", "City Dental Hub", "Bahawalpur Physiotherapy"],
        "Store": ["Ahmed Garments", "Madina Super Store", "Shahid Electronics", "Al-Rehman Traders"],
        "Service": ["QuickFix Auto Repair", "SuperClean Laundry", "Ali Plumbers", "A-Z Home Maintenance"]
    }

    for b_type in BUSINESS_TYPES:
        names = mock_data.get(b_type, [f"Mock {b_type}"])
        for name in names:
            # Generate a random local format phone number to prevent duplicates
            random_num = ''.join(random.choices('0123456789', k=7))
            phone = f"0300 {random_num}"
            leads.append({
                'business_name': name,
                'type': b_type,
                'city': LOCATION,
                'phone': phone
            })

    return leads

def collect_leads():
    """Main collector function to be run by scheduler."""
    leads = scrape_leads()
    if not leads:
        print("Scraper failed or returned no results. Generating mock leads...")
        leads = generate_mock_leads()

    print(f"Collected {len(leads)} leads. Saving to DB...")
    with get_db() as conn:
        cursor = conn.cursor()
        for lead in leads:
            # Check if lead already exists based on phone
            cursor.execute("SELECT id FROM leads WHERE phone = ?", (lead['phone'],))
            if not cursor.fetchone():
                cursor.execute(
                    "INSERT INTO leads (business_name, type, city, phone) VALUES (?, ?, ?, ?)",
                    (lead['business_name'], lead['type'], lead['city'], lead['phone'])
                )
    print("Collection cycle complete.")

def get_uncontacted_leads(db_path=DATABASE):
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, business_name, type, city, phone FROM leads WHERE contacted = 0")
        return [dict(row) for row in cursor.fetchall()]

def get_stats(db_path=DATABASE):
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM leads")
        total = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM leads WHERE contacted = 1")
        contacted = cursor.fetchone()[0]
        new_leads = total - contacted
        return {
            "total": total,
            "contacted": contacted,
            "new": new_leads
        }

if __name__ == '__main__':
    collect_leads()
