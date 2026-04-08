import unittest
import os
import run
import collector
import json

class TestBackendAPI(unittest.TestCase):
    db_path = 'test_leads_api.db'

    def setUp(self):
        # Setup test db
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        collector.init_db(db_path=self.db_path)
        collector.DB_PATH = self.db_path

        # Inject some test data
        with collector.get_db(self.db_path) as conn:
            conn.execute(
                'INSERT INTO leads (business_name, type, city, phone, contacted) VALUES (?, ?, ?, ?, ?)',
                ('Api Clinic', 'Clinic', 'Bahawalpur', '03000000000', 0)
            )
            conn.execute(
                'INSERT INTO leads (business_name, type, city, phone, contacted) VALUES (?, ?, ?, ?, ?)',
                ('Api Store', 'Store', 'Bahawalpur', '03000000001', 1)
            )

        self.app = run.app.test_client()
        self.app.testing = True

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_get_leads(self):
        response = self.app.get('/api/leads')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['business_name'], 'Api Clinic')

    def test_get_stats(self):
        response = self.app.get('/api/stats')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['total'], 2)
        self.assertEqual(data['contacted'], 1)
        self.assertEqual(data['new'], 1)

    def test_mark_contacted(self):
        # Get lead id first
        response = self.app.get('/api/leads')
        data = json.loads(response.data)
        lead_id = data[0]['id']

        # Mark as contacted
        response = self.app.post('/api/contact', json={'id': lead_id})
        self.assertEqual(response.status_code, 200)

        # Verify it's no longer in active leads
        response2 = self.app.get('/api/leads')
        data2 = json.loads(response2.data)
        self.assertEqual(len(data2), 0)

if __name__ == '__main__':
    unittest.main()
