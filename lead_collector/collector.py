import random
import time
from lead_collector.models import Lead

# Mock Data for Bahawalpur
BUSINESS_TYPES = ["Clinic", "Store", "Service"]

PREFIXES = {
    "Clinic": ["Bahawalpur Medical", "Al-Shifa", "City Care", "Noor", "Wellness"],
    "Store": ["Fashion Point", "Tech Zone", "General Store", "Super Mart", "Boutique"],
    "Service": ["Tech Solutions", "Clean Masters", "Repair Hub", "Legal Advisors", "Consultancy"]
}

SUFFIXES = {
    "Clinic": ["Centre", "Clinic", "Hospital", "Specialist"],
    "Store": ["Shop", "Outlet", "Traders", "Collection"],
    "Service": ["Provider", "Services", "Group", "Associates"]
}

def generate_mock_leads(count=5):
    """
    Generates realistic mock leads for Bahawalpur.
    """
    leads = []
    for _ in range(count):
        b_type = random.choice(BUSINESS_TYPES)
        name = f"{random.choice(PREFIXES[b_type])} {random.choice(SUFFIXES[b_type])}"
        # Pakistani mobile number format: +92 3xx xxxxxxx
        phone = f"+92 3{random.randint(0, 4)}{random.randint(0, 9)} {random.randint(1000000, 9999999)}"

        leads.append({
            "name": name,
            "type": b_type,
            "city": "Bahawalpur",
            "phone": phone,
            "website": None  # No website as per requirement
        })
    return leads

def collect_leads(city="Bahawalpur"):
    """
    Orchestrates the lead collection process.
    In a real scenario, this would call a scraper.
    Here, it generates mock data.
    """
    print(f"Starting lead collection for {city}...")

    # ---------------------------------------------------------
    # TODO: Replace this block with actual scraping logic
    # using Playwright or Google Maps API.
    # Example:
    # scraper = GoogleMapsScraper()
    # raw_leads = scraper.search(f"businesses in {city}")
    # filtered_leads = [l for l in raw_leads if not l.website and l.phone]
    # ---------------------------------------------------------

    # Using mock data for demonstration
    new_leads_data = generate_mock_leads(count=random.randint(3, 8))

    added_count = 0
    for lead_data in new_leads_data:
        # Save to DB
        result = Lead.add_lead(
            name=lead_data['name'],
            type=lead_data['type'],
            city=lead_data['city'],
            phone=lead_data['phone'],
            website=lead_data['website']
        )
        if result:
            added_count += 1

    print(f"Collection complete. Added {added_count} new leads.")
    return added_count

if __name__ == "__main__":
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from lead_collector.models import init_db
    init_db()
    collect_leads()
