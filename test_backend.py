import unittest
import os
import json
import sqlite3
import run
from unittest.mock import patch

class TestBackend(unittest.TestCase):
    def setUp(self):
        self.db_path = 'test_backend_leads.db'
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

        # Point the app to test db
        run.DATABASE = self.db_path
        # We also need to monkey patch get_db to use this db_path because it takes default arg
        self.original_get_db = run.get_db
        run.get_db = lambda db_path=self.db_path: self.original_get_db(db_path)

        run.init_db(self.db_path)

        self.app = run.app.test_client()
        self.app.testing = True

    def tearDown(self):
        run.get_db = self.original_get_db
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_get_leads_empty(self):
        response = self.app.get('/api/leads')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), [])

    def test_insert_and_get_leads(self):
        conn = run.get_db(self.db_path)
        c = conn.cursor()
        c.execute('''
            INSERT INTO leads (business_name, type, city, phone)
            VALUES (?, ?, ?, ?)
        ''', ("Test Business", "Store", "Bahawalpur", "03001234567"))
        conn.commit()
        conn.close()

        response = self.app.get('/api/leads')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['business_name'], "Test Business")

    def test_mark_contacted(self):
        conn = run.get_db(self.db_path)
        c = conn.cursor()
        c.execute('''
            INSERT INTO leads (business_name, type, city, phone)
            VALUES (?, ?, ?, ?)
        ''', ("Contact Me", "Service", "Bahawalpur", "03001234567"))
        conn.commit()
        lead_id = c.lastrowid
        conn.close()

        # Mark as contacted
        response = self.app.post('/api/contact',
                                 data=json.dumps({'id': lead_id}),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 200)

        # Verify it doesn't show in new leads
        response = self.app.get('/api/leads')
        data = json.loads(response.data)
        self.assertEqual(len(data), 0)

        # Verify stats
        response = self.app.get('/api/stats')
        stats = json.loads(response.data)
        self.assertEqual(stats['total'], 1)
        self.assertEqual(stats['contacted'], 1)
        self.assertEqual(stats['new_leads'], 0)

if __name__ == '__main__':
    unittest.main()
