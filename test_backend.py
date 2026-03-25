import unittest
import os
import json
from unittest.mock import patch
from run import app, init_db, insert_leads, get_uncontacted_leads, get_stats, get_db

TEST_DB = 'test_backend.db'

# Save references to original functions
orig_get_uncontacted_leads = get_uncontacted_leads
orig_get_stats = get_stats

def mock_get_uncontacted_leads():
    return orig_get_uncontacted_leads(db_path=TEST_DB)

def mock_get_stats():
    return orig_get_stats(db_path=TEST_DB)

class TestBackend(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
        init_db(TEST_DB)

        mock_leads = [
            {"business_name": "API Clinic", "type": "Clinic", "city": "Bahawalpur", "phone": "03001234567"}
        ]
        insert_leads(mock_leads, db_path=TEST_DB)

    def tearDown(self):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

    @patch('run.get_uncontacted_leads', side_effect=mock_get_uncontacted_leads)
    def test_api_leads(self, mock_func):
        response = self.app.get('/api/leads')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['business_name'], "API Clinic")

    @patch('run.get_stats', side_effect=mock_get_stats)
    def test_api_stats(self, mock_func):
        response = self.app.get('/api/stats')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['total'], 1)
        self.assertEqual(data['contacted'], 0)

    # We patch get_db specifically for the context manager inside api_contact
    @patch('run.get_db')
    def test_api_contact(self, mock_get_db):
        # the context manager is used as: with get_db() as db:
        # We need mock_get_db to return a mock context manager that yields a db connection to TEST_DB

        from contextlib import contextmanager
        @contextmanager
        def _mock_get_db(db_path=TEST_DB):
            import sqlite3
            conn = sqlite3.connect(TEST_DB)
            conn.row_factory = sqlite3.Row
            try:
                yield conn
                conn.commit()
            finally:
                conn.close()

        mock_get_db.side_effect = _mock_get_db

        # Get the ID of the inserted lead
        leads = orig_get_uncontacted_leads(db_path=TEST_DB)
        lead_id = leads[0]['id']

        response = self.app.post('/api/contact', json={'id': lead_id})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])

        # Verify it was updated in the DB
        import sqlite3
        conn = sqlite3.connect(TEST_DB)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("SELECT contacted FROM leads WHERE id = ?", (lead_id,))
        row = cursor.fetchone()
        conn.close()

        self.assertEqual(row['contacted'], 1)

if __name__ == '__main__':
    unittest.main()
