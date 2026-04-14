import unittest
import os
import json
import sqlite3
import run
import collector

class TestBackend(unittest.TestCase):
    def setUp(self):
        self.db_path = 'test_leads_api.db'
        collector.DB_PATH = self.db_path
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

        collector.init_db()
        self.app = run.app.test_client()

        # Populate with mock data for testing
        with collector.get_db() as conn:
            conn.execute('INSERT INTO leads (business_name, type, city, phone) VALUES (?, ?, ?, ?)',
                         ('ApiTest', 'Store', 'Bahawalpur', '03001234567'))

    def tearDown(self):
        # Shut down scheduler explicitly to prevent operational errors
        if run.scheduler.running:
            run.scheduler.shutdown(wait=False)

        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_get_stats(self):
        response = self.app.get('/api/stats')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['total'], 1)
        self.assertEqual(data['contacted'], 0)
        self.assertEqual(data['new'], 1)

    def test_get_leads(self):
        response = self.app.get('/api/leads')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['business_name'], 'ApiTest')

    def test_mark_contacted(self):
        # First get the lead to find its ID
        response = self.app.get('/api/leads')
        lead_id = json.loads(response.data)[0]['id']

        # Mark as contacted
        response = self.app.post('/api/contact', json={'id': lead_id})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(json.loads(response.data)['success'])

        # Verify stats changed
        response = self.app.get('/api/stats')
        data = json.loads(response.data)
        self.assertEqual(data['contacted'], 1)
        self.assertEqual(data['new'], 0)

if __name__ == '__main__':
    unittest.main()
