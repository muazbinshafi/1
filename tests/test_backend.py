import unittest
import os
import json
import run
import collector

class TestBackendRoutes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Override background task to prevent execution during tests
        collector.collect_leads = lambda: None

        # Stop scheduler from running tasks during teardown
        if run.scheduler.running:
            run.scheduler.pause()

        # Point to a temporary test DB specific to API testing
        collector.DB_PATH = 'test_leads_api.db'

    def setUp(self):
        run.app.config['TESTING'] = True
        self.client = run.app.test_client()

        # Setup fresh DB
        if os.path.exists(collector.DB_PATH):
            os.remove(collector.DB_PATH)
        collector.init_db()

    def tearDown(self):
        if os.path.exists(collector.DB_PATH):
            os.remove(collector.DB_PATH)

    def test_get_leads_empty(self):
        res = self.client.get('/api/leads')
        data = res.get_json()
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(data['leads']), 0)
        self.assertEqual(data['analytics']['total_leads'], 0)

    def test_get_leads_with_data(self):
        collector.generate_mock_leads()
        res = self.client.get('/api/leads')
        data = res.get_json()
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(data['leads']), 5)
        self.assertEqual(data['analytics']['total_leads'], 5)
        self.assertEqual(data['analytics']['contacted_leads'], 0)

    def test_contact_lead(self):
        collector.generate_mock_leads()

        # Get a lead to contact
        res = self.client.get('/api/leads')
        lead_id = res.get_json()['leads'][0]['id']

        # Contact lead
        res_contact = self.client.post('/api/contact', json={'id': lead_id})
        self.assertEqual(res_contact.status_code, 200)

        # Verify analytics updated
        res_after = self.client.get('/api/leads')
        data_after = res_after.get_json()
        self.assertEqual(len(data_after['leads']), 4)
        self.assertEqual(data_after['analytics']['contacted_leads'], 1)

if __name__ == '__main__':
    unittest.main()