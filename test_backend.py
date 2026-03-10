import unittest
import run
import os
import sqlite3
import json

class TestBackendAPI(unittest.TestCase):
    def setUp(self):
        # Setup test client and test database
        run.app.config['TESTING'] = True
        self.app = run.app.test_client()
        self.db_path = 'test_backend.db'
        run.DB_PATH = self.db_path
        run.init_db(self.db_path)

        # Insert a test lead
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            INSERT INTO leads (business_name, type, city, phone)
            VALUES ('API Test Store', 'Store', 'Bahawalpur', '+923111234567')
        ''')
        conn.commit()
        conn.close()

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_get_leads(self):
        response = self.app.get('/api/leads')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(len(data) > 0)
        self.assertEqual(data[0]['business_name'], 'API Test Store')

    def test_get_stats(self):
        response = self.app.get('/api/stats')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['total'], 1)
        self.assertEqual(data['new'], 1)
        self.assertEqual(data['contacted'], 0)

    def test_mark_contacted(self):
        # Mark the lead as contacted
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT id FROM leads WHERE business_name='API Test Store'")
        lead_id = c.fetchone()[0]
        conn.close()

        response = self.app.post('/api/contact',
                                 data=json.dumps({'id': lead_id}),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')

        # Verify it was updated in DB
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT contacted FROM leads WHERE id=?", (lead_id,))
        self.assertEqual(c.fetchone()[0], 1)
        conn.close()

if __name__ == '__main__':
    unittest.main()