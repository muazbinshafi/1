import unittest
import os
import json
import collector
from run import app, scheduler

class TestBackendAPI(unittest.TestCase):
    db_path = 'test_leads_api.db'

    @classmethod
    def setUpClass(cls):
        # Disable scheduler for testing
        os.environ['TESTING'] = 'true'

    def setUp(self):
        # Override DB path for tests
        collector.DB_PATH = self.db_path

        if os.path.exists(self.db_path):
            os.remove(self.db_path)

        collector.init_db(self.db_path)

        # Insert mock data
        with collector.get_db(self.db_path) as db:
            db.execute("INSERT INTO leads (business_name, type, city, phone) VALUES ('B1', 'Clinic', 'Bahawalpur', '0300-1111111')")
            db.execute("INSERT INTO leads (business_name, type, city, phone, contacted) VALUES ('B2', 'Store', 'Bahawalpur', '0300-2222222', 1)")

        self.app = app.test_client()
        self.app.testing = True

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        # Ensure scheduler doesn't keep running in background if started
        if scheduler.running:
            scheduler.shutdown(wait=False)

    def test_get_leads(self):
        response = self.app.get('/api/leads')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        # Should only return uncontacted leads
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['business_name'], 'B1')
        self.assertEqual(data[0]['contacted'], 0)

    def test_get_stats(self):
        response = self.app.get('/api/stats')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        self.assertEqual(data['total'], 2)
        self.assertEqual(data['contacted'], 1)
        self.assertEqual(data['new'], 1)

    def test_contact_lead(self):
        # First get the lead ID
        response = self.app.get('/api/leads')
        data = json.loads(response.data)
        lead_id = data[0]['id']

        # Mark as contacted
        response = self.app.post('/api/contact', json={'id': lead_id})
        self.assertEqual(response.status_code, 200)

        # Verify it's contacted in DB
        with collector.get_db(self.db_path) as db:
            cur = db.execute('SELECT contacted FROM leads WHERE id=?', (lead_id,))
            row = cur.fetchone()
            self.assertEqual(row['contacted'], 1)

if __name__ == '__main__':
    unittest.main()
