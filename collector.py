import random
import time
from database import add_lead
from playwright.sync_api import sync_playwright

MOCK_CITIES = ['Bahawalpur']
BUSINESS_TYPES = ['Clinic', 'Store', 'Service']

def generate_mock_lead():
    city = random.choice(MOCK_CITIES)
    b_type = random.choice(BUSINESS_TYPES)
    name = f"{b_type} {random.randint(100, 999)}"
    # Generate a random Pakistani mobile number
    phone = f"+923{random.choice(['00', '01', '02', '03', '04', '05', '06', '07', '08', '09'])}{random.randint(1000000, 9999999)}"

    return {
        'name': name,
        'business_type': b_type,
        'city': city,
        'phone': phone
    }

def scrape_google_maps_for_term(term, limit=5):
    """
    Helper function to scrape for a single term.
    """
    leads = []
    print(f"Scraping Google Maps for: {term}")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            )
            page = context.new_page()

            try:
                page.goto("https://www.google.com/maps", timeout=60000, wait_until="domcontentloaded")

                # Search
                try:
                    page.wait_for_selector("#searchboxinput", timeout=10000)
                    page.fill("#searchboxinput", term)
                    page.keyboard.press("Enter")
                except Exception as e:
                    print(f"Search box error: {e}")
                    browser.close()
                    return []

                # Wait for results
                try:
                    page.wait_for_selector('div[role="feed"]', timeout=20000)
                    time.sleep(3) # Initial load
                except Exception as e:
                    print(f"Results feed not found: {e}")
                    browser.close()
                    return []

                # Scroll
                feed = page.locator('div[role="feed"]')
                feed.evaluate("node => node.scrollTop = node.scrollHeight")
                time.sleep(2)

                # Get items
                # The selector for result items is usually a[href^="https://www.google.com/maps/place"]
                # But let's stick to the feed structure which is safer for iteration
                articles = page.locator('div[role="feed"] > div > div[role="article"]').all()
                print(f"Found {len(articles)} potential results.")

                for article in articles:
                    if len(leads) >= limit:
                        break

                    try:
                        # Click to see details
                        article.click()
                        time.sleep(2) # Wait for details panel

                        # Check if detail panel loaded
                        # Look for H1
                        if page.locator('h1.DUwDvf').count() == 0:
                            continue

                        name = page.locator('h1.DUwDvf').first.text_content()

                        # Check Website
                        # Usually a button with "Website" text or data-item-id="authority"
                        has_website = False
                        if page.locator('a[data-item-id="authority"]').count() > 0:
                             has_website = True

                        if has_website:
                            # print(f"Skipping {name}: Has website")
                            continue

                        # Get Phone
                        phone = None
                        phone_btns = page.locator('button[data-item-id^="phone:tel:"]')
                        if phone_btns.count() > 0:
                            label = phone_btns.first.get_attribute("aria-label")
                            if label:
                                phone = label.replace("Phone: ", "").strip()

                        if phone:
                            b_type = "Service"
                            if "Clinic" in term: b_type = "Clinic"
                            elif "Store" in term: b_type = "Store"

                            leads.append({
                                'name': name,
                                'business_type': b_type,
                                'city': "Bahawalpur",
                                'phone': phone
                            })
                            print(f"Scraped Lead: {name} - {phone}")

                    except Exception as e:
                        # print(f"Error processing item: {e}")
                        continue

            except Exception as e:
                print(f"Error during scraping session: {e}")
            finally:
                browser.close()

    except Exception as e:
        print(f"Playwright error: {e}")

    return leads

def collect_leads(limit=5):
    print("Starting lead collection...")

    # Try scraping first
    search_terms = ["Clinics in Bahawalpur", "Stores in Bahawalpur", "Services in Bahawalpur"]
    random.shuffle(search_terms)

    all_leads = []

    # Attempt to scrape
    try:
        for term in search_terms:
            if len(all_leads) >= limit:
                break
            term_leads = scrape_google_maps_for_term(term, limit - len(all_leads))
            all_leads.extend(term_leads)
    except Exception as e:
        print(f"Scraping failed completely: {e}")

    # Save scraped leads
    saved_count = 0
    for lead in all_leads:
        if add_lead(lead):
            saved_count += 1

    print(f"Saved {saved_count} scraped leads.")

    # Fallback if insufficient leads
    if saved_count == 0:
        print("No leads scraped (or duplicates). Generating mock data...")
        for _ in range(limit):
            lead = generate_mock_lead()
            if add_lead(lead):
                print(f"Added mock lead: {lead['name']}")

if __name__ == "__main__":
    from database import init_db
    init_db()
    collect_leads()
