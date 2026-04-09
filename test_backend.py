import unittest
import os
import json
import collector
from run import app, scheduler

class TestBackend(unittest.TestCase):
    def setUp(self):
        self.db_path = 'test_leads_api.db'
        collector.DB_PATH = self.db_path
        app.config['TESTING'] = True
        self.client = app.test_client()
        collector.init_db()
        collector.generate_mock_leads()

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_get_leads(self):
        response = self.client.get('/api/leads')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(len(data) > 0)
        self.assertIn('business_name', data[0])
        self.assertIn('phone', data[0])

    def test_get_stats(self):
        response = self.client.get('/api/stats')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('total', data)
        self.assertIn('contacted', data)
        self.assertIn('new', data)

    def test_contact_lead(self):
        # Get first lead
        response = self.client.get('/api/leads')
        leads = json.loads(response.data)
        lead_id = leads[0]['id']

        # Contact it
        response = self.client.post('/api/contact',
                                  data=json.dumps({'id': lead_id}),
                                  content_type='application/json')
        self.assertEqual(response.status_code, 200)

        # Verify it's no longer in /api/leads (since they are uncontacted)
        response = self.client.get('/api/leads')
        new_leads = json.loads(response.data)
        self.assertNotIn(lead_id, [l['id'] for l in new_leads])

if __name__ == '__main__':
    unittest.main()
