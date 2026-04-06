import unittest
import json
import os
from unittest.mock import patch
from run import app
from db import init_db, get_db

TEST_DB = 'test_leads_api.db'

# Define a function that calls get_db with our TEST_DB
def _get_uncontacted_leads():
    with get_db(TEST_DB) as conn:
        cur = conn.execute("SELECT * FROM leads WHERE contacted = 0 ORDER BY created_at DESC")
        return [dict(row) for row in cur.fetchall()]

def _get_stats():
    with get_db(TEST_DB) as conn:
        total = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
        contacted = conn.execute("SELECT COUNT(*) FROM leads WHERE contacted = 1").fetchone()[0]
        new = conn.execute("SELECT COUNT(*) FROM leads WHERE contacted = 0").fetchone()[0]
        return total, contacted, new

class TestBackend(unittest.TestCase):
    def setUp(self):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
        init_db(TEST_DB)

        # Populate test db
        with get_db(TEST_DB) as conn:
            conn.execute(
                "INSERT INTO leads (business_name, type, city, phone) VALUES (?, ?, ?, ?)",
                ("Test Store", "Store", "Bahawalpur", "03001234567")
            )

        app.config['TESTING'] = True
        self.client = app.test_client()

    def tearDown(self):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

    @patch('run.get_db')
    def test_get_leads(self, mock_get_db):
        # We don't want to patch the context manager entirely since that gets complicated.
        # Instead, we'll patch the route or just let it use the real DB but patch the connection.
        pass # Better approach: just patch the route logic or test it via integration

    # Let's test the routes directly without patching get_db inside run.py,
    # instead we will modify the run.py temporarily for tests, or better,
    # mock the functions inside run.py

    @patch('run.get_db')
    def test_stats_api(self, mock_get_db):
        # Setting up the mock context manager
        import sqlite3
        conn = sqlite3.connect(TEST_DB)
        conn.row_factory = sqlite3.Row

        mock_get_db.return_value.__enter__.return_value = conn

        response = self.client.get('/api/stats')
        data = json.loads(response.data)

        self.assertEqual(data['total'], 1)
        self.assertEqual(data['new'], 1)
        self.assertEqual(data['contacted'], 0)

        conn.close()

    @patch('run.get_db')
    def test_contact_api(self, mock_get_db):
        import sqlite3
        conn = sqlite3.connect(TEST_DB)
        conn.row_factory = sqlite3.Row
        mock_get_db.return_value.__enter__.return_value = conn

        # Get the ID of the inserted lead
        cur = conn.execute("SELECT id FROM leads LIMIT 1")
        lead_id = cur.fetchone()['id']

        response = self.client.post('/api/contact', json={'id': lead_id})
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'success')

        # Verify it was updated
        cur = conn.execute("SELECT contacted FROM leads WHERE id = ?", (lead_id,))
        self.assertEqual(cur.fetchone()['contacted'], 1)

        conn.close()

if __name__ == '__main__':
    unittest.main()
