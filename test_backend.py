import unittest
from run import app
import database
import os
import json

class TestBackend(unittest.TestCase):
    def setUp(self):
        self.db_path = 'test_backend_leads.db'
        database.init_db(self.db_path)

        # Monkey patch ALL database calls in run.py since run.py calls them without db_path
        self.original_get_uncontacted_leads = database.get_uncontacted_leads
        self.original_get_stats = database.get_stats
        self.original_mark_contacted = database.mark_contacted

        database.get_uncontacted_leads = lambda db_path=self.db_path: self.original_get_uncontacted_leads(db_path)
        database.get_stats = lambda db_path=self.db_path: self.original_get_stats(db_path)
        database.mark_contacted = lambda lead_id, db_path=self.db_path: self.original_mark_contacted(lead_id, db_path)

        app.config['TESTING'] = True
        self.client = app.test_client()

    def tearDown(self):
        database.get_uncontacted_leads = self.original_get_uncontacted_leads
        database.get_stats = self.original_get_stats
        database.mark_contacted = self.original_mark_contacted

        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_get_leads(self):
        database.add_lead("API Test", "Service", "BWP", "123", self.db_path)
        response = self.client.get('/api/leads')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['business_name'], "API Test")

    def test_contact_lead(self):
        database.add_lead("Contact Test", "Store", "BWP", "456", self.db_path)
        leads = database.get_uncontacted_leads(self.db_path)
        lead_id = leads[0]['id']

        response = self.client.post('/api/contact', json={'lead_id': lead_id})
        self.assertEqual(response.status_code, 200)

        stats_response = self.client.get('/api/stats')
        stats_data = json.loads(stats_response.data)
        self.assertEqual(stats_data['contacted'], 1)
        self.assertEqual(stats_data['new'], 0)

if __name__ == '__main__':
    unittest.main()
