import unittest
import json
import os
import run

class TestBackendEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Setup temporary DB for Flask tests
        cls.test_db = 'test_flask.db'
        run.DB_PATH = cls.test_db
        run.app.config['TESTING'] = True
        cls.client = run.app.test_client()

    def setUp(self):
        # Create fresh DB and insert some test data
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
        run.init_db()

        conn = run.get_db_connection()
        cursor = conn.cursor()
        cursor.executemany('''
            INSERT INTO leads (business_name, type, city, phone, contacted)
            VALUES (?, ?, ?, ?, ?)
        ''', [
            ('Test Clinic', 'Clinic', 'Bahawalpur', '111', 0),
            ('Test Store', 'Store', 'Bahawalpur', '222', 1),
            ('Test Service', 'Service', 'Bahawalpur', '333', 0)
        ])
        conn.commit()
        conn.close()

    def tearDown(self):
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_get_leads(self):
        response = self.client.get('/api/leads')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        # Should only return uncontacted leads (0)
        self.assertEqual(len(data), 2)
        names = [lead['business_name'] for lead in data]
        self.assertIn('Test Clinic', names)
        self.assertIn('Test Service', names)
        self.assertNotIn('Test Store', names)

    def test_get_stats(self):
        response = self.client.get('/api/stats')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertEqual(data['total'], 3)
        self.assertEqual(data['new'], 2)
        self.assertEqual(data['contacted'], 1)

    def test_post_contact(self):
        # Get id of an uncontacted lead
        conn = run.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM leads WHERE business_name = 'Test Clinic'")
        lead_id = cursor.fetchone()['id']
        conn.close()

        # Hit contact endpoint
        response = self.client.post('/api/contact', json={'id': lead_id})
        self.assertEqual(response.status_code, 200)

        # Verify it was updated
        conn = run.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT contacted FROM leads WHERE id = ?", (lead_id,))
        contacted_status = cursor.fetchone()['contacted']
        conn.close()

        self.assertEqual(contacted_status, 1)

        # Verify stats updated
        stats_response = self.client.get('/api/stats')
        stats_data = json.loads(stats_response.data)
        self.assertEqual(stats_data['contacted'], 2)
        self.assertEqual(stats_data['new'], 1)

if __name__ == '__main__':
    unittest.main()
