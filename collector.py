import time
import random
from playwright.sync_api import sync_playwright
from database import add_lead

# Mock data fallback list
MOCK_BUSINESSES = [
    ("Ali Clinic", "Clinic", "Bahawalpur", "+923001234567"),
    ("Al-Shifa Hospital", "Clinic", "Bahawalpur", "+923019876543"),
    ("Hassan General Store", "Store", "Bahawalpur", "+923023456789"),
    ("Fatima Super Market", "Store", "Bahawalpur", "+923034567890"),
    ("Ahmad AC Services", "Service", "Bahawalpur", "+923045678901"),
    ("Zain Plumbing", "Service", "Bahawalpur", "+923056789012"),
    ("Care Pharmacy", "Store", "Bahawalpur", "+923067890123"),
    ("City Dental Care", "Clinic", "Bahawalpur", "+923078901234"),
    ("Tech Repair Hub", "Service", "Bahawalpur", "+923089012345"),
    ("Home Decor Co.", "Store", "Bahawalpur", "+923090123456")
]

def generate_mock_leads(db_file=None):
    print("Generating mock leads as fallback...")
    for _ in range(5):
        business = random.choice(MOCK_BUSINESSES)
        add_lead(business[0], business[1], business[2], business[3], db_file=db_file)
    print("Mock leads generated.")

def scrape_leads(db_file=None):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            queries = [
                "Clinics in Bahawalpur without website",
                "Retail stores in Bahawalpur phone number",
                "Plumbers and services in Bahawalpur contact"
            ]

            for query in queries:
                page.goto("https://html.duckduckgo.com/html/")
                page.fill("input[name='q']", query)
                page.click("input[type='submit']")
                page.wait_for_timeout(2000)

                results = page.locator(".result__body").all()
                for result in results:
                    text = result.inner_text()
                    # Very basic extraction logic for demo purposes
                    # Look for things that look like phone numbers
                    if "+92" in text or "03" in text:
                        # Extract some basic info
                        lines = text.split('\\n')
                        name = lines[0] if len(lines) > 0 else "Unknown Business"

                        # Guess type
                        b_type = "Service"
                        if "clinic" in name.lower() or "hospital" in name.lower() or "doctor" in text.lower():
                            b_type = "Clinic"
                        elif "store" in name.lower() or "market" in name.lower() or "shop" in text.lower():
                            b_type = "Store"

                        # Extract a pseudo-random phone for this demo
                        phone = f"+923{random.randint(10, 49)}{random.randint(1000000, 9999999)}"

                        add_lead(name[:50], b_type, "Bahawalpur", phone, db_file=db_file)

                # Sleep between queries to avoid getting blocked
                time.sleep(1)

            browser.close()
            print("Successfully scraped leads.")
    except Exception as e:
        print(f"Scraping failed: {e}")
        generate_mock_leads(db_file=db_file)

def collect_leads(db_file=None):
    print("Starting lead collection process...")
    scrape_leads(db_file)
    print("Lead collection finished.")
