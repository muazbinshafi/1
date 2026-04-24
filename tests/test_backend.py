import unittest
import os
import json
import collector
import run

class TestBackend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db_path = 'test_leads_api.db'
        collector.DB_PATH = cls.db_path
        run.app.config['TESTING'] = True
        cls.client = run.app.test_client()

        # Disable background jobs for testing
        run.background_collect = lambda: None
        if run.scheduler.running:
            run.scheduler.pause()

    def setUp(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        collector.setup_db(self.db_path)
        collector.generate_mock_leads(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_api_leads(self):
        response = self.client.get('/api/leads')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 3)
        self.assertEqual(data[0]['status'], 'new')

    def test_api_contact(self):
        # Contact first lead
        response = self.client.post('/api/contact', json={'id': 1})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])

        # Verify it's not returned in active leads
        response_leads = self.client.get('/api/leads')
        leads_data = json.loads(response_leads.data)
        self.assertEqual(len(leads_data), 2)

        # Contact remaining
        self.client.post('/api/contact', json={'id': 2})
        self.client.post('/api/contact', json={'id': 3})

        # Verify empty
        response_empty = self.client.get('/api/leads')
        empty_data = json.loads(response_empty.data)
        self.assertEqual(len(empty_data), 0)

if __name__ == '__main__':
    unittest.main()
