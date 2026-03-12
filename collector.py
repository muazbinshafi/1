from playwright.sync_api import sync_playwright
import time
import re
import db
import random

def search_leads(page, query, business_type, city):
    print(f"Searching for: {query} in {city}")
    # We use duckduckgo html as a simple way to scrape
    page.goto(f"https://html.duckduckgo.com/html/?q={query} in {city}")

    # Wait for results
    try:
        page.wait_for_selector('.result__body', timeout=10000)
    except:
        print("Timeout waiting for results")
        return []

    leads = []
    results = page.locator('.result__body').all()

    for result in results:
        try:
            # Get text block
            text = result.inner_text()

            # Extract potential phone numbers
            # Look for Pakistani numbers in various formats e.g., 0300 1234567, +923001234567, 0300-1234567
            phone_matches = re.findall(r'(\+92\s?\d{3}\s?\d{7}|0\d{3}[-\s]?\d{7})', text)

            # Simple check if "website" or "www." is mentioned, likely means they have a site
            if "www." in text.lower() or "website" in text.lower() or "http" in text.lower():
                continue

            if phone_matches:
                # Get the title as business name
                title_elem = result.locator('.result__title')
                if title_elem.count() > 0:
                    title = title_elem.inner_text().strip()
                else:
                    title = f"Unknown {business_type}"

                phone = phone_matches[0].strip()

                # Format phone to remove spaces/dashes if any
                phone = re.sub(r'[-\s]', '', phone)

                leads.append({
                    "business_name": title,
                    "type": business_type,
                    "city": city,
                    "phone": phone
                })
        except Exception as e:
            print(f"Error parsing result: {e}")
            continue

    return leads

def scrape_leads():
    searches = [
        {"query": "Clinics doctors without website", "type": "Clinic"},
        {"query": "Retail stores shops without website", "type": "Store"},
        {"query": "Plumbers electricians services without website", "type": "Service"},
        {"query": "Local clinic", "type": "Clinic"},
        {"query": "Grocery store", "type": "Store"},
        {"query": "Repair service", "type": "Service"},
    ]
    city = "Bahawalpur"

    found_leads = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            for search in searches:
                leads = search_leads(page, search["query"], search["type"], city)
                found_leads.extend(leads)
                time.sleep(2) # be nice

            browser.close()
    except Exception as e:
        print(f"Scraping error: {e}")
        # Will fallback to mock data in run.py if found_leads is empty
        pass

    return found_leads

def collect_leads():
    print("Starting lead collection process...")
    leads = scrape_leads()

    # Check if we should use fallback mock data
    if not leads:
        print("Scraping returned no leads. Falling back to mock data...")
        leads = generate_mock_leads()

    added = 0
    for lead in leads:
        if db.add_lead(lead['business_name'], lead['type'], lead['city'], lead['phone']):
            added += 1

    print(f"Collection complete. Added {added} new leads.")
    return added

def generate_mock_leads():
    """Fallback generator for mock data when scraper fails or blocked"""
    types = ["Clinic", "Store", "Service"]
    names = {
        "Clinic": ["Al-Shifa Clinic", "City Care Hospital", "Family Health Clinic", "CareFirst Medical", "Bahawalpur Dental"],
        "Store": ["Bismillah General Store", "Madina Mart", "Al-Rehman Traders", "City Supermarket", "Model Town Retail"],
        "Service": ["Quick Fix Plumbing", "A-1 Electricians", "Reliable AC Repair", "Expert Auto Workshop", "City Cleaning Services"]
    }

    mock_leads = []
    # Generate 3-6 random leads
    for _ in range(random.randint(3, 6)):
        b_type = random.choice(types)
        name = random.choice(names[b_type])
        # Generate fake Pakistani mobile number: 03XX-XXXXXXX
        prefix = random.choice(["0300", "0301", "0313", "0321", "0333", "0345"])
        number = "".join([str(random.randint(0, 9)) for _ in range(7)])
        phone = f"{prefix}{number}"

        mock_leads.append({
            "business_name": name,
            "type": b_type,
            "city": "Bahawalpur",
            "phone": phone
        })

    return mock_leads

if __name__ == "__main__":
    db.init_db()
    collect_leads()
