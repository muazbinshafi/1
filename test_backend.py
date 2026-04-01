import unittest
import os
import json
import sqlite3
import run
from unittest.mock import patch

TEST_DB = 'test_backend.db'

def create_test_db():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    with sqlite3.connect(TEST_DB) as conn:
        conn.execute('''
            CREATE TABLE leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                business_name TEXT NOT NULL,
                type TEXT NOT NULL,
                city TEXT NOT NULL,
                phone TEXT NOT NULL,
                contacted BOOLEAN NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # Insert test data
        conn.execute('''
            INSERT INTO leads (business_name, type, city, phone, contacted)
            VALUES (?, ?, ?, ?, ?)
        ''', ("API Business 1", "Clinic", "Bahawalpur", "0300-1111111", 0))
        conn.execute('''
            INSERT INTO leads (business_name, type, city, phone, contacted)
            VALUES (?, ?, ?, ?, ?)
        ''', ("API Business 2", "Store", "Bahawalpur", "0300-2222222", 1))

class TestBackendAPI(unittest.TestCase):
    def setUp(self):
        create_test_db()
        self.app = run.app.test_client()
        self.app.testing = True

        # Patch run.get_db to use TEST_DB
        self.orig_get_db = run.get_db
        self.patcher = patch('run.get_db')
        self.mock_get_db = self.patcher.start()

        # Make the mocked get_db return the original context manager using TEST_DB
        def side_effect(*args, **kwargs):
            return self.orig_get_db(TEST_DB)

        self.mock_get_db.side_effect = side_effect

    def tearDown(self):
        self.patcher.stop()
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

    def test_api_leads(self):
        response = self.app.get('/api/leads')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertEqual(len(data), 1)  # Only 1 uncontacted
        self.assertEqual(data[0]['business_name'], "API Business 1")

    def test_api_stats(self):
        response = self.app.get('/api/stats')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertEqual(data['total'], 2)
        self.assertEqual(data['contacted'], 1)
        self.assertEqual(data['new'], 1)

    def test_api_contact(self):
        response = self.app.post('/api/contact',
                                 data=json.dumps({'id': 1}),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 200)

        # Verify it was updated
        response_stats = self.app.get('/api/stats')
        data = json.loads(response_stats.data)
        self.assertEqual(data['contacted'], 2)
        self.assertEqual(data['new'], 0)

if __name__ == '__main__':
    unittest.main()
