import unittest
import os
import tempfile
import json
from run import app
import database

class TestBackend(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp()
        app.config['TESTING'] = True
        self.client = app.test_client()

        # Monkey patch the database functions to use test db
        self.original_get_db = database.get_db_connection
        database.DB_FILE = self.db_path
        database.init_db()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_dashboard_route(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Universal Lead Collector', response.data)

    def test_api_leads(self):
        database.add_lead('API Clinic', 'Clinic', 'BWP', '000')
        response = self.client.get('/api/leads')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['business_name'], 'API Clinic')

    def test_api_stats(self):
        database.add_lead('S1', 'Store', 'BWP', '111')
        database.add_lead('S2', 'Store', 'BWP', '222')
        response = self.client.get('/api/stats')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['total'], 2)
        self.assertEqual(data['new'], 2)

    def test_api_contact(self):
        database.add_lead('S3', 'Service', 'BWP', '333')
        leads = database.get_active_leads()
        lead_id = leads[0]['id']

        response = self.client.post('/api/contact', json={'id': lead_id})
        self.assertEqual(response.status_code, 200)

        active_leads = database.get_active_leads()
        self.assertEqual(len(active_leads), 0)

if __name__ == '__main__':
    unittest.main()
