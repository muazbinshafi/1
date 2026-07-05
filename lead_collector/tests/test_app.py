import unittest
import json
import os
import tempfile
import sys

# Ensure we can import from lead_collector
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lead_collector import app, models
from lead_collector.scrapers import MockScraper

class LeadCollectorTestCase(unittest.TestCase):
    def setUp(self):
        # Use a temporary file for the database
        self.db_fd, self.db_path = tempfile.mkstemp()
        models.DB_PATH = self.db_path
        models.init_db()

        self.app = app.app.test_client()
        self.app.testing = True

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_db_operations(self):
        models.add_lead("Test Clinic", "Clinic", "Bahawalpur", "+923001234567")
        leads = models.get_leads()
        self.assertEqual(len(leads), 1)
        self.assertEqual(leads[0]['name'], "Test Clinic")

        models.update_lead_status(leads[0]['id'], "contacted")
        leads_new = models.get_leads(status='new')
        self.assertEqual(len(leads_new), 0)

    def test_mock_scraper(self):
        scraper = MockScraper(count=3)
        leads = scraper.fetch_leads()
        self.assertEqual(len(leads), 3)
        self.assertEqual(leads[0]['city'], "Bahawalpur")

    def test_api_leads(self):
        models.add_lead("Test Store", "Store", "Bahawalpur", "+923001112222")
        response = self.app.get('/api/leads')
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], "Test Store")

    def test_api_contact(self):
        models.add_lead("Test Service", "Service", "Bahawalpur", "+923003334444")
        leads = models.get_leads(status='new')
        lead_id = leads[0]['id']

        response = self.app.post(f'/api/leads/{lead_id}/contact')
        self.assertEqual(response.status_code, 200)

        leads_new = models.get_leads(status='new')
        self.assertEqual(len(leads_new), 0)

    def test_api_trigger(self):
        response = self.app.post('/api/trigger_collection')
        self.assertEqual(response.status_code, 200)
        leads = models.get_leads(status='new')
        self.assertGreaterEqual(len(leads), 5)

if __name__ == '__main__':
    unittest.main()
