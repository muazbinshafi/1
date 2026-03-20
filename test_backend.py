import unittest
import json
import os
from run import app
import db
import collector

class TestBackend(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

        # setup test db
        self.test_db = 'test_backend.db'
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

        db.init_db(self.test_db)

        # Patch db connection for tests
        self.original_get_db = db.get_db
        db.get_db = lambda *args, **kwargs: self.original_get_db(self.test_db)

        # We also need to patch the imported db inside collector, since it imports get_db directly
        self.original_collector_get_db = collector.get_db
        collector.get_db = lambda *args, **kwargs: self.original_get_db(self.test_db)

        # Insert mock data
        with db.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO leads (business_name, type, city, phone, contacted) VALUES (?, ?, ?, ?, ?)",
                ("API Clinic", "Clinic", "Bahawalpur", "+92 300 0000000", 0)
            )

    def tearDown(self):
        db.get_db = self.original_get_db
        collector.get_db = self.original_collector_get_db
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_get_leads(self):
        response = self.app.get('/api/leads')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['business_name'], "API Clinic")

    def test_get_stats(self):
        response = self.app.get('/api/stats')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['total'], 1)
        self.assertEqual(data['contacted'], 0)
        self.assertEqual(data['new'], 1)

    def test_contact_lead(self):
        with db.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM leads WHERE phone = ?", ("+92 300 0000000",))
            lead_id = cursor.fetchone()['id']

        response = self.app.post('/api/contact', json={'id': lead_id})
        self.assertEqual(response.status_code, 200)

        with db.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT contacted FROM leads WHERE id = ?", (lead_id,))
            contacted = cursor.fetchone()['contacted']
            self.assertEqual(contacted, 1)

if __name__ == '__main__':
    unittest.main()
