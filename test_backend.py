import unittest
import os
import sqlite3
from datetime import datetime
import collector
from run import app, scheduler

class TestBackend(unittest.TestCase):
    def setUp(self):
        self.db_path = 'test_leads_api.db'
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

        collector.DB_PATH = self.db_path
        app.config['TESTING'] = True
        self.client = app.test_client()

        collector.init_db()
        with collector.get_db() as conn:
            conn.execute(
                'INSERT INTO leads (business_name, type, city, phone, contacted, created_at) VALUES (?, ?, ?, ?, ?, ?)',
                ('Test Clinic', 'Clinic', 'Bahawalpur', '0300-0000000', 0, datetime.now())
            )

    def tearDown(self):
        if scheduler.running:
            scheduler.shutdown(wait=False)
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_get_leads(self):
        response = self.client.get('/api/leads')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['business_name'], 'Test Clinic')

    def test_get_stats(self):
        response = self.client.get('/api/stats')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['total'], 1)
        self.assertEqual(data['new'], 1)
        self.assertEqual(data['contacted'], 0)

    def test_contact_lead(self):
        with collector.get_db() as conn:
            lead = conn.execute('SELECT id FROM leads').fetchone()

        response = self.client.post('/api/contact', json={'id': lead['id']})
        self.assertEqual(response.status_code, 200)

        response2 = self.client.get('/api/stats')
        data = response2.get_json()
        self.assertEqual(data['contacted'], 1)
        self.assertEqual(data['new'], 0)

if __name__ == '__main__':
    unittest.main()
