import unittest
import os
from flask import json
import collector
import run

class TestBackend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db_path = 'test_leads_api.db'
        collector.DB_PATH = cls.db_path
        run.app.config['TESTING'] = True
        cls.client = run.app.test_client()

        # Override background collect
        run.background_collect = lambda: None

        if run.scheduler.running:
            run.scheduler.pause()

    def setUp(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        collector.generate_mock_leads(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_get_leads(self):
        response = self.client.get('/api/leads')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(len(data) > 0)
        self.assertIn('name', data[0])

    def test_contact_lead(self):
        # Fetch first to get a valid ID
        response = self.client.get('/api/leads')
        data = json.loads(response.data)
        lead_id = data[0]['id']

        response = self.client.post('/api/contact', json={'id': lead_id})
        self.assertEqual(response.status_code, 200)

        # Verify it's no longer in the fetched leads
        response = self.client.get('/api/leads')
        new_data = json.loads(response.data)
        self.assertEqual(len(new_data), len(data) - 1)

if __name__ == '__main__':
    unittest.main()
