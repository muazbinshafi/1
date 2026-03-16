from playwright.sync_api import sync_playwright
import database
import time
import re

def scrape_duckduckgo(query):
    leads = []
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # Using HTML search to bypass JS bloat
            page.goto('https://html.duckduckgo.com/html/', timeout=60000)

            page.fill('#search_form_input_homepage', query)
            page.click('#search_button_homepage')

            page.wait_for_selector('.result', timeout=15000)
            results = page.locator('.result').all()

            for result in results:
                title = result.locator('.result__title').inner_text()
                snippet = result.locator('.result__snippet').inner_text()

                # Simple extraction heuristics (not production grade, but sufficient for demonstration)
                phone_match = re.search(r'(\+92|0)\s?\d{3}\s?\d{7}|\d{4}-\d{7}', snippet)

                if phone_match:
                    phone = phone_match.group(0)
                    # Filter out those with obvious websites or URLs in the snippet
                    if 'http' not in snippet and 'www.' not in snippet:
                        leads.append({
                            'business_name': title.strip(),
                            'phone': phone.strip()
                        })

        except Exception as e:
            print(f"Scraping error: {e}")

        finally:
            if 'browser' in locals():
                browser.close()

    return leads

def collect_leads():
    """
    Background job to run the scraper and populate the DB.
    """
    print("Starting background lead collection...")

    # We will just generate mock leads here as instructed by the memory if scraping is blocked/difficult
    # In a real scenario, we'd run queries like:
    # "clinics in bahawalpur phone number"
    # "retail stores in bahawalpur phone number"
    # "plumbing services in bahawalpur phone number"

    # Run a quick scrape attempt
    scraped_leads = scrape_duckduckgo("clinics in bahawalpur phone number")

    if not scraped_leads:
        print("Scraper failed or returned no results, falling back to mock data.")
        generate_mock_leads()
    else:
        for lead in scraped_leads:
            database.add_lead(
                business_name=lead['business_name'],
                business_type="Clinic", # Hardcoded for this query
                city="Bahawalpur",
                phone=lead['phone']
            )

def generate_mock_leads():
    """Fallback mechanism to generate mock leads for testing."""
    mock_data = [
        {"business_name": "Al-Shifa Family Clinic", "type": "Clinic", "city": "Bahawalpur", "phone": "03001234567"},
        {"business_name": "Madina Medical Store", "type": "Store", "city": "Bahawalpur", "phone": "03119876543"},
        {"business_name": "Ali Auto Workshop", "type": "Service", "city": "Bahawalpur", "phone": "03335551234"},
        {"business_name": "Bismillah General Store", "type": "Store", "city": "Bahawalpur", "phone": "03011112222"},
        {"business_name": "City Care Dental Clinic", "type": "Clinic", "city": "Bahawalpur", "phone": "03456667777"}
    ]

    for item in mock_data:
        database.add_lead(
            business_name=item["business_name"],
            business_type=item["type"],
            city=item["city"],
            phone=item["phone"]
        )
    print("Mock leads generated.")

if __name__ == '__main__':
    database.init_db()
    collect_leads()
