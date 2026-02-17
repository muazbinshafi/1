from typing import List, Dict, Optional
import random

class LeadCollector:
    def __init__(self):
        # Mock data representing businesses in Bahawalpur, Punjab, Pakistan
        # These are fictional businesses for demonstration purposes
        self.mock_data = [
            {
                "id": 1,
                "name": "Bahawalpur Medical Centre",
                "type": "Clinic",
                "city": "Bahawalpur",
                "phone": "+923001234567",
                "website": None
            },
            {
                "id": 2,
                "name": "Al-Rehman General Store",
                "type": "Store",
                "city": "Bahawalpur",
                "phone": "+923217654321",
                "website": None
            },
            {
                "id": 3,
                "name": "City Electronics Repair",
                "type": "Service",
                "city": "Bahawalpur",
                "phone": "+923339876543",
                "website": None
            },
            {
                "id": 4,
                "name": "Care Dental Clinic",
                "type": "Clinic",
                "city": "Bahawalpur",
                "phone": "+923012345678",
                "website": None
            },
            {
                "id": 5,
                "name": "Punjab Fashion House",
                "type": "Store",
                "city": "Bahawalpur",
                "phone": "+923023456789",
                "website": None
            },
            {
                "id": 6,
                "name": "Quick Fix Plumbers",
                "type": "Service",
                "city": "Bahawalpur",
                "phone": "+923034567890",
                "website": None
            },
            {
                "id": 7,
                "name": "Healthy Life Pharmacy",
                "type": "Clinic", # Categorized as Clinic/Health related for pitch
                "city": "Bahawalpur",
                "phone": "+923045678901",
                "website": None
            },
            {
                "id": 8,
                "name": "Bahawalpur Auto Workshop",
                "type": "Service",
                "city": "Bahawalpur",
                "phone": "+923056789012",
                "website": None
            }
        ]

    def collect_leads(self) -> List[Dict]:
        """
        Simulates collecting leads from third-party platforms.
        In a real scenario, this would use an API (e.g., Google Places API)
        to search for businesses in a specific location and filter by
        those without a website field.
        """
        # Return mock data
        return self.mock_data

    # Example of how a real Google Maps API integration might look:
    # def search_google_maps(self, api_key: str, location: str, query: str):
    #     import googlemaps
    #     gmaps = googlemaps.Client(key=api_key)
    #     places = gmaps.places(query=query, location=location)
    #     results = []
    #     for place in places['results']:
    #         # check for website field
    #         if 'website' not in place:
    #             results.append({
    #                 "name": place['name'],
    #                 "address": place['formatted_address'],
    #                 # ... other fields
    #             })
    #     return results
