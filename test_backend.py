import unittest
import json
import os
import db
from run import app

TEST_DB = 'test_backend_leads.db'

# Patch get_db to use test database
from unittest.mock import patch
original_get_db = db.get_db

def mock_get_db(*args, **kwargs):
    return original_get_db(db_path=TEST_DB)

class TestBackendAPI(unittest.TestCase):
    def setUp(self):
        # Setup test client and test db
        app.config['TESTING'] = True
        self.client = app.test_client()
        db.init_db(TEST_DB)

        # Populate with initial test data
        with mock_get_db() as conn:
            conn.execute('''
                INSERT INTO leads (business_name, type, city, phone)
                VALUES (?, ?, ?, ?)
            ''', ('Backend Clinic', 'Clinic', 'Bahawalpur', '03002222222'))

            conn.execute('''
                INSERT INTO leads (business_name, type, city, phone, contacted)
                VALUES (?, ?, ?, ?, ?)
            ''', ('Backend Store', 'Store', 'Bahawalpur', '03113333333', 1))

    def tearDown(self):
        # Cleanup
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

    @patch('run.db.get_db', side_effect=mock_get_db)
    def test_get_leads(self, mock_db):
        response = self.client.get('/api/leads')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        # Should only return uncontacted leads
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['business_name'], 'Backend Clinic')
        self.assertEqual(data[0]['contacted'], 0)

    @patch('run.db.get_db', side_effect=mock_get_db)
    def test_get_stats(self, mock_db):
        response = self.client.get('/api/stats')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        self.assertEqual(data['total'], 2)
        self.assertEqual(data['contacted'], 1)
        self.assertEqual(data['new'], 1)

    @patch('run.db.get_db', side_effect=mock_get_db)
    @patch('threading.Thread.start') # Mock thread start to avoid running background collections
    def test_mark_contacted(self, mock_thread_start, mock_db):
        # First, find an uncontacted lead ID
        with mock_get_db() as conn:
            cursor = conn.execute('SELECT id FROM leads WHERE business_name = ?', ('Backend Clinic',))
            lead_id = cursor.fetchone()[0]

        # Make the request to mark as contacted
        response = self.client.post('/api/contact', json={'id': lead_id})
        self.assertEqual(response.status_code, 200)

        # Verify it was updated
        with mock_get_db() as conn:
            cursor = conn.execute('SELECT contacted FROM leads WHERE id = ?', (lead_id,))
            contacted = cursor.fetchone()[0]

        self.assertEqual(contacted, 1)

if __name__ == '__main__':
    unittest.main()
