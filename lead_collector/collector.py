import random
import time
from playwright.sync_api import sync_playwright

def generate_mock_leads(city="Bahawalpur", count=5):
    """Generates mock leads for demonstration if scraping fails."""
    leads = []
    types = ["Clinic", "Store", "Service"]

    prefixes = {
        "Clinic": ["Al-Shifa", "City", "Care", "Health", "Bahawalpur"],
        "Store": ["Fashion", "Tech", "General", "Super", "Mart"],
        "Service": ["Quick", "Expert", "Master", "Pro", "Solution"]
    }

    suffixes = {
        "Clinic": ["Clinic", "Medical Center", "Hospital", "Specialists"],
        "Store": ["Store", "Shop", "Traders", "Emporium"],
        "Service": ["Services", "Repair", "Consultants", "Agency"]
    }

    for _ in range(count):
        type_ = random.choice(types)
        name = f"{random.choice(prefixes[type_])} {random.choice(suffixes[type_])}"
        phone = f"+923{random.randint(10, 49)}{random.randint(1000000, 9999999)}"

        leads.append({
            "name": name,
            "type": type_,
            "city": city,
            "phone": phone,
            "website": None
        })
    return leads

def scrape_google_maps(city="Bahawalpur", limit=5):
    """Attempts to scrape Google Maps for leads."""
    leads = []
    queries = [f"Clinics in {city}", f"Stores in {city}", f"Services in {city}"]

    try:
        with sync_playwright() as p:
            # Launch browser
            # Note: In some environments sandbox might be an issue, use args=['--no-sandbox']
            browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            )
            page = context.new_page()

            for query in queries:
                if len(leads) >= limit:
                    break

                print(f"Scraping query: {query}")
                try:
                    page.goto(f"https://www.google.com/maps/search/{query.replace(' ', '+')}", timeout=30000, wait_until='domcontentloaded')

                    # Wait for results to load
                    try:
                        page.wait_for_selector('div[role="feed"]', timeout=10000)
                    except:
                        print("Feed not found, maybe no results or different layout.")
                        continue

                    # Scroll a bit
                    feed = page.locator('div[role="feed"]')
                    feed.evaluate("node => node.scrollTop += 2000")
                    time.sleep(2)

                    # Get listings
                    listings = page.locator('div[role="article"]').all()

                    for listing in listings:
                        if len(leads) >= limit:
                            break

                        try:
                            # Extract text to see if we can get basic info without clicking (faster/safer)
                            # text = listing.inner_text()

                            listing.click()
                            time.sleep(1) # Wait for details panel

                            # Check website
                            has_website = page.locator('a[data-item-id="authority"]').count() > 0 or \
                                          page.locator('button[data-item-id="authority"]').count() > 0 or \
                                          page.get_by_text("Website", exact=True).count() > 0

                            if has_website:
                                continue

                            # Get Phone
                            phone_locator = page.locator('button[data-item-id^="phone:"]')
                            if phone_locator.count() > 0:
                                phone = phone_locator.first.get_attribute("data-item-id").replace("phone:", "")
                            else:
                                continue # No phone, useless lead

                            # Get Name
                            name_locator = page.locator('h1.DUwDvf')
                            name = name_locator.inner_text() if name_locator.count() > 0 else "Unknown"

                            # Determine type from query
                            type_ = "Service"
                            if "Clinics" in query:
                                type_ = "Clinic"
                            elif "Stores" in query:
                                type_ = "Store"

                            lead = {
                                "name": name,
                                "type": type_,
                                "city": city,
                                "phone": phone,
                                "website": None
                            }

                            # Avoid duplicates in this run
                            if not any(l['phone'] == phone for l in leads):
                                leads.append(lead)
                                print(f"Found lead: {name}")

                        except Exception as e:
                            # print(f"Error processing listing: {e}")
                            continue

                except Exception as e:
                    print(f"Error scraping query {query}: {e}")

            browser.close()

    except Exception as e:
        print(f"Critical scraping error: {e}")
        return []

    return leads

def collect_leads(city="Bahawalpur"):
    """
    Main entry point for lead collection.
    Tries to scrape, falls back to mock data if empty.
    """
    print(f"Starting lead collection for {city}...")
    leads = scrape_google_maps(city, limit=10)

    if not leads:
        print("Scraping returned no leads. generating mock data.")
        leads = generate_mock_leads(city, count=5)

    return leads
