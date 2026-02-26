import unittest
import os
import sqlite3
import json
import run
from run import app, init_db

class LeadCollectorTestCase(unittest.TestCase):
    def setUp(self):
        # Clean state for DB
        self.db_name = 'leads.db'
        if os.path.exists(self.db_name):
            os.remove(self.db_name)

        # Re-initialize DB
        run.init_db()

        self.app = app.test_client()
        self.app.testing = True

    def tearDown(self):
        if os.path.exists(self.db_name):
            os.remove(self.db_name)

    def test_api_endpoints(self):
        # 1. Add a dummy lead
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute("INSERT INTO leads (business_name, type, city, phone) VALUES (?, ?, ?, ?)",
                  ('Test Clinic', 'Clinic', 'Test City', '1234567890'))
        lead_id = c.lastrowid
        conn.commit()
        conn.close()

        # 2. GET /api/leads
        response = self.app.get('/api/leads')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['business_name'], 'Test Clinic')

        # 3. GET /api/stats
        response = self.app.get('/api/stats')
        self.assertEqual(response.status_code, 200)
        stats = json.loads(response.data)
        self.assertEqual(stats['total'], 1)
        self.assertEqual(stats['contacted'], 0)
        self.assertEqual(stats['new'], 1)

        # 4. POST /api/contacted/<id>
        response = self.app.post(f'/api/contacted/{lead_id}')
        self.assertEqual(response.status_code, 200)

        # 5. Verify lead is gone from /api/leads
        response = self.app.get('/api/leads')
        data = json.loads(response.data)
        self.assertEqual(len(data), 0)

        # 6. Verify stats updated
        response = self.app.get('/api/stats')
        stats = json.loads(response.data)
        self.assertEqual(stats['contacted'], 1)
        self.assertEqual(stats['new'], 0)

if __name__ == '__main__':
    unittest.main()
