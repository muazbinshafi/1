import unittest
import os
import sqlite3
import json
from run import app
from database import init_db, add_lead

class TestFlaskAPI(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
        self.db_path = 'leads.db'

        # Reset DB for tests
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        init_db(self.db_path)

        # Add test data
        add_lead(self.db_path, "API Clinic", "Clinic", "Bahawalpur", "+923001111111")

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_get_leads(self):
        response = self.client.get('/api/leads')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['business_name'], "API Clinic")

    def test_contact_lead(self):
        # First get the lead ID
        response = self.client.get('/api/leads')
        data = json.loads(response.data)
        lead_id = data[0]['id']

        # Mark as contacted
        response = self.client.post('/api/contact',
                                   json={'lead_id': lead_id})
        self.assertEqual(response.status_code, 200)

        # Verify it's no longer active
        response2 = self.client.get('/api/leads')
        data2 = json.loads(response2.data)
        self.assertEqual(len(data2), 0)

    def test_get_stats(self):
        response = self.client.get('/api/stats')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['total_leads'], 1)

if __name__ == '__main__':
    unittest.main()
