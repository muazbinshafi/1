import re
import random
from playwright.sync_api import sync_playwright

def scrape_leads():
    """
    Scrapes DuckDuckGo HTML search for local businesses in Bahawalpur lacking websites.
    """
    queries = [
        "Clinics in Bahawalpur contact number",
        "Retail Stores in Bahawalpur contact number",
        "Services in Bahawalpur contact number"
    ]

    leads = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        try:
            for query in queries:
                b_type = "Clinic" if "Clinics" in query else "Store" if "Stores" in query else "Service"
                url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"

                # Navigate to the DuckDuckGo HTML search results page
                page.goto(url, wait_until="domcontentloaded", timeout=15000)

                # Extract search results
                results = page.locator(".result__body").all()
                for result in results:
                    title_elem = result.locator(".result__title")
                    snippet_elem = result.locator(".result__snippet")

                    if not title_elem.count() or not snippet_elem.count():
                        continue

                    title = title_elem.inner_text().strip()
                    snippet = snippet_elem.inner_text().strip()

                    # Look for Pakistani phone numbers (03XX-XXXXXXX or 03XXXXXXXXX)
                    phone_match = re.search(r'(03\d{2}[-\s]?\d{7})', snippet)

                    # Filter out businesses that seem to have a website
                    lower_snippet = snippet.lower()
                    has_website = any(ext in lower_snippet for ext in [".com", ".pk", "website", "www."])

                    if phone_match and not has_website:
                        phone = phone_match.group(1).replace("-", "").replace(" ", "")
                        leads.append({
                            "business_name": title[:50], # Truncate to keep it clean
                            "type": b_type,
                            "city": "Bahawalpur",
                            "phone": phone
                        })

        except Exception as e:
            print(f"Scraping error: {e}")
        finally:
            browser.close()

    return leads

def generate_mock_leads():
    """
    Generates mock local leads from Bahawalpur in case scraping fails.
    """
    mock_businesses = [
        {"name": "Al-Shifa Family Clinic", "type": "Clinic"},
        {"name": "Bahawalpur General Store", "type": "Store"},
        {"name": "Riaz Auto Repair", "type": "Service"},
        {"name": "Madina Medical Center", "type": "Clinic"},
        {"name": "Tariq Kiryana Store", "type": "Store"},
        {"name": "City Plumbers", "type": "Service"}
    ]

    leads = []
    for biz in mock_businesses:
        prefix = "03" + str(random.randint(0, 4)) + str(random.randint(0, 9))
        suffix = "".join([str(random.randint(0, 9)) for _ in range(7)])
        phone = prefix + suffix

        leads.append({
            "business_name": biz["name"],
            "type": biz["type"],
            "city": "Bahawalpur",
            "phone": phone
        })

    return leads

def get_uncontacted_leads(db_path="leads.db"):
    """
    Retrieves uncontacted leads from the database. (Mocked here for now).
    """
    pass

if __name__ == "__main__":
    leads = scrape_leads()
    if not leads:
        print("Scraping returned no leads, using mock data...")
        leads = generate_mock_leads()

    for lead in leads:
        print(lead)
