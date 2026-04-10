import unittest
import os
import json
import collector
from run import app, scheduler

class TestBackendAPI(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
        self.db_path = 'test_leads_api.db'

        # Inject test database path
        collector.DB_PATH = self.db_path

        # Clean and init test db
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        collector.init_db(self.db_path)
        collector.generate_mock_leads(self.db_path)

    def tearDown(self):
        # Shut down scheduler to prevent background jobs accessing deleted DB
        if scheduler.running:
            scheduler.shutdown(wait=False)

        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_get_leads(self):
        response = self.client.get('/api/leads')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 4)
        self.assertEqual(data[0]['contacted'], 0)

    def test_get_stats(self):
        response = self.client.get('/api/stats')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['total'], 4)
        self.assertEqual(data['contacted'], 0)
        self.assertEqual(data['new'], 4)

    def test_contact_lead(self):
        # First get leads to find an ID
        leads_res = self.client.get('/api/leads')
        leads = json.loads(leads_res.data)
        lead_id = leads[0]['id']

        # Contact lead
        res = self.client.post('/api/contact', json={'id': lead_id})
        self.assertEqual(res.status_code, 200)

        # Check stats updated
        stats_res = self.client.get('/api/stats')
        stats = json.loads(stats_res.data)
        self.assertEqual(stats['contacted'], 1)
        self.assertEqual(stats['new'], 3)

        # Check leads updated
        leads_res = self.client.get('/api/leads')
        updated_leads = json.loads(leads_res.data)
        self.assertEqual(len(updated_leads), 3)

if __name__ == '__main__':
    unittest.main()
