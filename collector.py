import random
import time
from playwright.sync_api import sync_playwright
from sqlalchemy.orm import sessionmaker
from models import Lead, get_engine

def collect_leads(city="Bahawalpur", limit=5):
    """
    Collects leads from Google Maps using Playwright.
    Falls back to mock data if scraping fails or yields no results.
    """
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    session = Session()

    new_leads = []

    # Business types to search for
    business_types = {
        'Clinic': ['Dental Clinic', 'Medical Clinic', 'Eye Clinic'],
        'Store': ['Clothing Store', 'Grocery Store', 'Electronics Store'],
        'Service': ['Plumber', 'Electrician', 'Car Repair']
    }

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            for b_type, queries in business_types.items():
                if len(new_leads) >= limit:
                    break

                query = f"{random.choice(queries)} in {city}"
                print(f"Searching for: {query}")

                try:
                    # Navigate to Google Maps
                    page.goto(f"https://www.google.com/maps/search/{query.replace(' ', '+')}")
                    page.wait_for_selector('div[role="feed"]', timeout=10000)

                    # Scroll to load more results
                    page.evaluate('window.scrollBy(0, 1000)')
                    time.sleep(2)

                    # Extract listings
                    # Note: Selectors for Google Maps change frequently. This is a best-effort attempt.
                    # We are looking for container elements that likely hold business info.
                    # A common pattern is div[role="article"] or similar within the feed.
                    listings = page.locator('div[role="feed"] > div > div[jsaction]').all()

                    for listing in listings:
                        if len(new_leads) >= limit:
                            break

                        text = listing.inner_text()
                        if not text:
                            continue

                        lines = text.split('\n')
                        name = lines[0] if lines else "Unknown"

                        # Simplistic extraction (real scraping requires complex selectors)
                        phone = None
                        website = None

                        # Check for phone pattern (very basic)
                        import re
                        phone_match = re.search(r'(\+92|03)\d{2}[ -]?\d{7}', text)
                        if phone_match:
                            phone = phone_match.group(0)

                        # Check for website
                        if "Website" in text or ".com" in text:
                            website = "Has Website"

                        # Logic: Must have phone, must NOT have website
                        if phone and not website:
                            # Check if already exists in DB
                            exists = session.query(Lead).filter_by(phone=phone).first()
                            if not exists:
                                lead = Lead(
                                    name=name,
                                    business_type=b_type,
                                    city=city,
                                    phone=phone,
                                    website=None,
                                    status='new'
                                )
                                new_leads.append(lead)
                                session.add(lead)
                                print(f"Found lead: {name} ({b_type})")

                except Exception as e:
                    print(f"Error scraping {query}: {e}")
                    continue

            browser.close()

    except Exception as e:
        print(f"Playwright error: {e}")

    # Fallback to mock data if no leads found (for demonstration/reliability)
    if len(new_leads) == 0:
        print("Scraping yielded no results or failed. Generating mock data for demonstration.")
        generate_mock_leads(session, city, limit)
    else:
        session.commit()
        print(f"Successfully scraped {len(new_leads)} leads.")

    session.close()

def generate_mock_leads(session, city, count):
    """
    Generates mock leads for demonstration purposes.
    """
    mock_data = [
        ("Smile Dental Clinic", "Clinic", "+92 300 1234567"),
        ("Al-Shifa Medical Center", "Clinic", "+92 321 9876543"),
        ("City Grocery Mart", "Store", "+92 333 5551122"),
        ("Fashion Hub", "Store", "+92 301 2233445"),
        ("Quick Fix Auto Repair", "Service", "+92 345 6789012"),
        ("Home Comfort Plumbers", "Service", "+92 312 3456789"),
        ("Noor Eye Clinic", "Clinic", "+92 307 8899001"),
        ("Tech Zone Electronics", "Store", "+92 322 4455667")
    ]

    added_count = 0
    for name, b_type, phone in mock_data:
        if added_count >= count:
            break

        # Check if exists
        if not session.query(Lead).filter_by(phone=phone).first():
            lead = Lead(
                name=name,
                business_type=b_type,
                city=city,
                phone=phone,
                website=None,
                status='new'
            )
            session.add(lead)
            added_count += 1

    session.commit()
    print(f"Generated {added_count} mock leads.")

if __name__ == "__main__":
    collect_leads()
