import unittest
import json
import os
from unittest.mock import patch
from run import app
from database import get_db, init_db

class TestBackendEndpoints(unittest.TestCase):
    def setUp(self):
        self.test_db = 'test_backend_leads.db'

        # Ensure test db is clean
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

        init_db(self.test_db)

        # Setup flask testing client
        app.config['TESTING'] = True
        self.client = app.test_client()

        # Insert test data
        with get_db(self.test_db) as conn:
            cursor = conn.cursor()
            cursor.executemany('''
                INSERT INTO leads (business_name, type, city, phone, contacted)
                VALUES (?, ?, ?, ?, ?)
            ''', [
                ('Clinic A', 'Clinic', 'Bahawalpur', '+92111', 0),
                ('Store B', 'Store', 'Bahawalpur', '+92222', 0),
                ('Service C', 'Service', 'Bahawalpur', '+92333', 1) # Contacted
            ])

    def tearDown(self):
        # Cleanup db
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def mock_get_db(self):
        # Mock get_db to return connection to test db instead of main db
        return get_db(self.test_db)

    def test_get_leads(self):
        with patch('run.get_db', side_effect=self.mock_get_db):
            response = self.client.get('/api/leads')
            self.assertEqual(response.status_code, 200)

            data = json.loads(response.data)
            self.assertEqual(len(data), 2) # Should only return 2 uncontacted leads

            # Check properties
            for lead in data:
                self.assertIn('business_name', lead)
                self.assertIn('phone', lead)
                self.assertEqual(lead['contacted'], 0)

    def test_get_stats(self):
        with patch('run.get_db', side_effect=self.mock_get_db):
            response = self.client.get('/api/stats')
            self.assertEqual(response.status_code, 200)

            data = json.loads(response.data)
            self.assertEqual(data['total'], 3)
            self.assertEqual(data['contacted'], 1)
            self.assertEqual(data['new'], 2)

    @patch('run.collector.collect_leads')
    def test_mark_contacted(self, mock_collect_leads):
        with patch('run.get_db', side_effect=self.mock_get_db):
            # First, find an ID to mark contacted
            with self.mock_get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM leads WHERE business_name = 'Clinic A'")
                lead_id = cursor.fetchone()['id']

            # Send POST request
            response = self.client.post('/api/contact', json={'id': lead_id})
            self.assertEqual(response.status_code, 200)

            data = json.loads(response.data)
            self.assertTrue(data['success'])

            # Verify status changed
            with self.mock_get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT contacted FROM leads WHERE id = ?", (lead_id,))
                status = cursor.fetchone()['contacted']
                self.assertEqual(status, 1)

if __name__ == '__main__':
    unittest.main()
