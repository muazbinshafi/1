import unittest
import json
import os
import run
import collector

class TestBackend(unittest.TestCase):
    def setUp(self):
        self.db_path = 'test_backend_leads.db'
        collector.init_db(self.db_path)

        # For the Flask API testing, the routes in run.py use collector.get_uncontacted_leads() etc
        # which default to DB_NAME. Instead of patching get_db, let's patch the functions called by routes
        # or patch DB_NAME in collector before we import run/call client
        self.original_get_uncontacted_leads = collector.get_uncontacted_leads
        self.original_get_stats = collector.get_stats
        self.original_mark_contacted = collector.mark_contacted

        collector.get_uncontacted_leads = lambda db_path=self.db_path: self.original_get_uncontacted_leads(self.db_path)
        collector.get_stats = lambda db_path=self.db_path: self.original_get_stats(self.db_path)
        collector.mark_contacted = lambda lead_id, db_path=self.db_path: self.original_mark_contacted(lead_id, self.db_path)

        run.app.testing = True
        self.client = run.app.test_client()

    def tearDown(self):
        collector.get_uncontacted_leads = self.original_get_uncontacted_leads
        collector.get_stats = self.original_get_stats
        collector.mark_contacted = self.original_mark_contacted

        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_get_leads(self):
        collector.insert_lead("API Test Clinic", "Clinic", "Bahawalpur", "03001112233", self.db_path)
        response = self.client.get('/api/leads')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['business_name'], "API Test Clinic")

    def test_contact_lead(self):
        collector.insert_lead("API Test Store", "Store", "Bahawalpur", "03001112244", self.db_path)
        leads = collector.get_uncontacted_leads(self.db_path)
        lead_id = leads[0]['id']

        response = self.client.post('/api/contact', json={'id': lead_id})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])

        # Verify it's no longer uncontacted
        leads_after = collector.get_uncontacted_leads(self.db_path)
        self.assertEqual(len(leads_after), 0)

if __name__ == '__main__':
    unittest.main()
