import random
import time
import sqlite3

# Mock data for fallback
MOCK_BUSINESSES = [
    {"name": "Bahawalpur Medic Care", "type": "Clinic", "city": "Bahawalpur"},
    {"name": "Punjab Fabrics Store", "type": "Store", "city": "Bahawalpur"},
    {"name": "Ahmed Auto Repair", "type": "Service", "city": "Bahawalpur"},
    {"name": "City Dental Clinic", "type": "Clinic", "city": "Bahawalpur"},
    {"name": "Noor General Store", "type": "Store", "city": "Bahawalpur"},
    {"name": "Fast Tech Services", "type": "Service", "city": "Bahawalpur"},
    {"name": "Al-Shifa Hospital", "type": "Clinic", "city": "Bahawalpur"},
    {"name": "Madina Supermarket", "type": "Store", "city": "Bahawalpur"},
    {"name": "Khan Plumbing", "type": "Service", "city": "Bahawalpur"},
    {"name": "Sunshine Pharmacy", "type": "Clinic", "city": "Bahawalpur"},
]

def generate_phone():
    return f"+92 3{random.randint(10, 49)} {random.randint(1000000, 9999999)}"

def collect_leads():
    """
    Simulates scraping leads from third-party platforms.
    Returns a list of dictionaries.
    """
    print("Starting lead collection...")
    # In a real scenario, Playwright would be used here to scrape Google Maps.
    # Due to environment restrictions and complexity, we use a fallback mechanism
    # to generate realistic data for Bahawalpur.

    leads = []
    # Simulate scraping delay
    time.sleep(1)

    # Generate 5-10 leads
    count = random.randint(5, 10)
    for _ in range(count):
        business = random.choice(MOCK_BUSINESSES)
        lead = {
            "name": business["name"],
            "type": business["type"],
            "city": business["city"],
            "phone": generate_phone(),
            "website": None  # Ensure no website
        }
        leads.append(lead)

    print(f"Collected {len(leads)} leads.")
    return leads
