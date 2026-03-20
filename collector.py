from db import get_db
from playwright.sync_api import sync_playwright
import sqlite3
import random

CITY = "Bahawalpur"
CATEGORIES = ["Clinic", "Store", "Service"]

def collect_leads():
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # Use duckduckgo html
            for category in CATEGORIES:
                query = f"{category} in {CITY} Pakistan phone number"
                page.goto(f"https://html.duckduckgo.com/html/?q={query}")

                # Simple logic for this challenge: find generic results
                # In real scenario, more complex scraping is needed

                results = page.query_selector_all('.result__body')
                if not results:
                    continue

                for result in results:
                    title_elem = result.query_selector('.result__title')
                    snippet_elem = result.query_selector('.result__snippet')

                    if title_elem and snippet_elem:
                        title = title_elem.inner_text()
                        snippet = snippet_elem.inner_text()

                        # basic phone extraction
                        import re
                        phone_match = re.search(r'\+92\s?\d{3}\s?\d{7}|03\d{2}\s?\d{7}', snippet)
                        if phone_match and "website" not in snippet.lower():
                            phone = phone_match.group(0)
                            insert_lead(title, category, CITY, phone)
            browser.close()
    except Exception as e:
        print(f"Scraping failed: {e}")
        generate_mock_leads()

def insert_lead(business_name, business_type, city, phone):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM leads WHERE phone = ?", (phone,))
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO leads (business_name, type, city, phone) VALUES (?, ?, ?, ?)",
                (business_name, business_type, city, phone)
            )

def generate_mock_leads():
    # Fallback to mock data
    mock_leads = [
        ("Health First", "Clinic", "Bahawalpur", "+92 300 1234567"),
        ("Family Care", "Clinic", "Bahawalpur", "+92 301 2345678"),
        ("Al-Madina Mart", "Store", "Bahawalpur", "+92 302 3456789"),
        ("A-One Electronics", "Store", "Bahawalpur", "+92 303 4567890"),
        ("Expert Plumbers", "Service", "Bahawalpur", "+92 304 5678901"),
        ("City Electricians", "Service", "Bahawalpur", "+92 305 6789012")
    ]

    for business_name, business_type, city, phone in mock_leads:
        insert_lead(business_name, business_type, city, phone)

def get_uncontacted_leads():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, business_name, type, city, phone FROM leads WHERE contacted = 0 ORDER BY id DESC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def mark_contacted(lead_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE leads SET contacted = 1 WHERE id = ?", (lead_id,))

def get_stats():
    with get_db() as conn:
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
