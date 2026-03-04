import time
import random
from playwright.sync_api import sync_playwright
import database

def generate_mock_leads():
    cities = ["Bahawalpur"]
    types = ["Clinic", "Store", "Service"]

    names = {
        "Clinic": ["Al-Shifa Clinic", "City Care Hospital", "Family Health Center", "Sadiq Medical Center", "Punjab Care Clinic"],
        "Store": ["Madina Mart", "Al-Rehman General Store", "Bahawalpur Supermarket", "Bismillah Traders", "Awami Karyana"],
        "Service": ["Khan Plumbers", "A-1 Electricians", "City Cleaners", "Fast Fix Auto", "Mian Builders"]
    }

    # Generate 3-5 random leads
    num_leads = random.randint(3, 5)
    for _ in range(num_leads):
        b_type = random.choice(types)
        b_name = random.choice(names[b_type]) + f" {random.randint(1, 100)}"
        city = random.choice(cities)
        # Generate a random Pakistan phone number (+923xxxxxxxxx)
        phone = f"+923{random.randint(10, 49)}{random.randint(1000000, 9999999)}"

        # Add to database
        database.add_lead(b_name, b_type, city, phone)

def collect_leads():
    success = False
    try:
        with sync_playwright() as p:
            # We use a headless browser to attempt scraping
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            queries = [
                ("clinics in Bahawalpur", "Clinic"),
                ("retail stores in Bahawalpur", "Store"),
                ("services in Bahawalpur", "Service")
            ]

            # Simple simulation of search
            for query, b_type in queries:
                print(f"Searching for {query}...")
                page.goto(f"https://www.google.com/search?q={query}")
                time.sleep(2)

            browser.close()
            # In this demo, we assume the scraping yielded nothing specific,
            # or hit a captcha, so we fall back to generating mock data.
    except Exception as e:
        print(f"Playwright scraping encountered an issue: {e}")

    if not success:
        print("Falling back to generating mock data for Bahawalpur...")
        generate_mock_leads()

if __name__ == "__main__":
    database.init_db()
    collect_leads()
