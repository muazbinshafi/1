import unittest
import os
import sqlite3
import run
import collector

class TestBackend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Disable background collect for tests to avoid timeout exceptions and disk I/O errors
        run.background_collect = lambda: None
        if run.scheduler.running:
            run.scheduler.pause()

    def setUp(self):
        self.test_db = 'test_leads_api.db'
        collector.DB_PATH = self.test_db
        collector.DB_PATH_CONTEXT = collector # for api/contact endpoint to use dynamic path
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

        collector.setup_db()
        collector.generate_mock_leads()

        self.app = run.app.test_client()
        self.app.testing = True

    def tearDown(self):
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_dashboard_route(self):
        response = self.app.get('/dashboard')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Universal Lead Collector', response.data)

    def test_api_leads(self):
        response = self.app.get('/api/leads')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        self.assertEqual(data[0]['contacted'], 0)

    def test_api_contact(self):
        # Get first lead
        leads_res = self.app.get('/api/leads')
        lead_id = leads_res.get_json()[0]['id']

        # Mark contacted
        response = self.app.post('/api/contact', json={'id': lead_id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()['status'], 'success')

        # Verify it was marked
        with sqlite3.connect(self.test_db) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute("SELECT contacted FROM leads WHERE id = ?", (lead_id,))
            self.assertEqual(cur.fetchone()['contacted'], 1)

if __name__ == '__main__':
    unittest.main()