import random
from .base import BaseScraper

class MockScraper(BaseScraper):
    def __init__(self, count=5):
        self.count = count
        self.city = "Bahawalpur"
        self.sectors = {
            "Clinic": ["Dental Care", "Medical Center", "Health Hub", "Eye Clinic", "Physio Lab"],
            "Store": ["Electronics", "Fashion Hub", "Super Mart", "Mobile Zone", "Grocery Point"],
            "Service": ["Plumbing Pros", "Electric Fix", "Car Wash", "Event Planners", "Tech Repair"]
        }
        self.prefixes = ["Al-", "New", "The", "Best", "City", "Punjab", "Royal", "Smart"]
        self.suffixes = ["Limited", "Services", "Center", "Shop", "Store", "Clinic", "Works"]

    def _generate_phone(self):
        # Generate a random Pakistani mobile number: +92 3XX XXXXXXX
        operator_code = random.randint(0, 49)
        subscriber_number = random.randint(1000000, 9999999)
        return f"+923{operator_code:02d}{subscriber_number}"

    def fetch_leads(self):
        leads = []
        for _ in range(self.count):
            sector_type = random.choice(list(self.sectors.keys()))
            business_name = f"{random.choice(self.prefixes)} {random.choice(self.sectors[sector_type])}"

            # 20% chance to add a suffix if it makes sense, but let's keep it simple
            if random.random() > 0.7:
                 business_name += f" {random.choice(self.suffixes)}"

            phone = self._generate_phone()

            leads.append({
                "name": business_name,
                "type": sector_type,
                "city": self.city,
                "phone": phone
            })
        return leads
