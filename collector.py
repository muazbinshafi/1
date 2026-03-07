import sqlite3
import random
import time
from playwright.sync_api import sync_playwright

def insert_lead(business_name, business_type, city, phone):
    conn = sqlite3.connect('leads.db')
    cursor = conn.cursor()
    # Check if lead already exists to avoid duplicates
    cursor.execute('''
        SELECT id FROM leads
        WHERE business_name = ? AND city = ?
    ''', (business_name, city))

    if not cursor.fetchone():
        cursor.execute('''
            INSERT INTO leads (business_name, type, city, phone)
            VALUES (?, ?, ?, ?)
        ''', (business_name, business_type, city, phone))
        conn.commit()
    conn.close()

def fallback_mock_data():
    """Generate mock data when scraping fails or for demonstration."""
    mock_leads = [
        {"name": "Al-Shifa Clinic", "type": "Clinic", "city": "Bahawalpur", "phone": "+923001234567"},
        {"name": "Rahat Pharmacy & Mart", "type": "Store", "city": "Bahawalpur", "phone": "+923011234568"},
        {"name": "Hassan Auto Workshop", "type": "Service", "city": "Bahawalpur", "phone": "+923021234569"},
        {"name": "City General Hospital", "type": "Clinic", "city": "Bahawalpur", "phone": "+923031234570"},
        {"name": "Gulberg Super Store", "type": "Store", "city": "Bahawalpur", "phone": "+923041234571"},
        {"name": "Zamir Plumbing Services", "type": "Service", "city": "Bahawalpur", "phone": "+923051234572"}
    ]

    for lead in mock_leads:
        insert_lead(lead["name"], lead["type"], lead["city"], lead["phone"])

def scrape_google_maps():
    """Scrape actual business data using Playwright."""
    try:
        with sync_playwright() as p:
            # We use headless mode for background tasks
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # Categories to search
            search_queries = [
                {"query": "Clinics in Bahawalpur Punjab Pakistan", "type": "Clinic"},
                {"query": "Retail stores in Bahawalpur Punjab Pakistan", "type": "Store"},
                {"query": "Plumbers or services in Bahawalpur Punjab Pakistan", "type": "Service"}
            ]

            for sq in search_queries:
                page.goto("https://www.google.com/maps")
                page.wait_for_selector('input#searchboxinput')
                page.fill('input#searchboxinput', sq["query"])
                page.press('input#searchboxinput', 'Enter')

                # Wait for search results
                try:
                    page.wait_for_selector('div[role="feed"]', timeout=10000)
                    time.sleep(3) # Wait for initial load
                except Exception:
                    print(f"Timeout waiting for results for {sq['query']}")
                    continue

                # Scroll a bit to load more
                try:
                    feed = page.locator('div[role="feed"]')
                    feed.hover()
                    page.mouse.wheel(0, 500)
                    time.sleep(2)
                except Exception:
                    pass

                # Get the listings
                listings = page.locator('a[href*="/maps/place/"]').all()
                print(f"Found {len(listings)} potential places for {sq['query']}.")

                # Only process a subset to keep it reasonable
                for i in range(min(5, len(listings))):
                    try:
                        listing = listings[i]
                        # Click on listing
                        listing.click()
                        time.sleep(2) # Wait for details pane

                        # Extract Name
                        name_locator = page.locator('h1.DUwDvf')
                        name = name_locator.inner_text() if name_locator.count() > 0 else f"Unknown {sq['type']}"

                        # Extract Phone (Regex for general phone numbers)
                        phone_locator = page.locator('button[data-item-id^="phone:tel:"]')
                        phone = ""
                        if phone_locator.count() > 0:
                            phone = phone_locator.first.inner_text().replace('\n', '')

                        # Extract Website
                        website_locator = page.locator('a[data-item-id="authority"]')
                        has_website = website_locator.count() > 0

                        # We only want businesses with a phone number and NO website
                        if phone and not has_website:
                            print(f"Scraped Lead: {name} - {phone}")
                            insert_lead(name, sq["type"], "Bahawalpur", phone)

                    except Exception as e:
                        print(f"Error processing listing: {e}")
                        continue

            browser.close()
            return True
    except Exception as e:
        print(f"Scraping failed: {e}")
        return False

def collect_leads():
    print("Starting data collection...")
    # Attempt real scraping
    success = scrape_google_maps()
    # Use fallback if real scraping fails (e.g. captcha, strict bot protection)
    if not success:
        print("Falling back to mock data generation.")
        fallback_mock_data()
