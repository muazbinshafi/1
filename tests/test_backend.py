import unittest
import run
import collector
import json
import sqlite3

class TestBackend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Disable background collect to prevent hangs in tests
        run.background_collect = lambda: None
        if run.scheduler.running:
            run.scheduler.pause()

        cls.client = run.app.test_client()
        collector.DB_PATH = 'test_leads_api.db'

    def setUp(self):
        collector.setup_db()
        # Ensure clean state
        with collector.get_db() as db:
            db.execute("DELETE FROM leads")

    def tearDown(self):
        with collector.get_db() as db:
            db.execute("DELETE FROM leads")

    def test_get_leads_empty(self):
        response = self.client.get('/api/leads')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['leads'], [])
        self.assertEqual(data['stats']['total'], 0)

    def test_get_leads_with_data(self):
        collector.generate_mock_leads()
        response = self.client.get('/api/leads')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data['leads']), 4)
        self.assertEqual(data['stats']['total'], 4)
        self.assertEqual(data['stats']['pending'], 4)
        self.assertEqual(data['stats']['contacted'], 0)

    def test_contact_lead(self):
        collector.generate_mock_leads()

        # Get lead id
        with collector.get_db() as db:
            cursor = db.execute("SELECT id FROM leads LIMIT 1")
            lead_id = cursor.fetchone()['id']

        response = self.client.post('/api/contact', json={'id': lead_id})
        self.assertEqual(response.status_code, 200)

        # Verify status updated
        with collector.get_db() as db:
            cursor = db.execute("SELECT status FROM leads WHERE id=?", (lead_id,))
            status = cursor.fetchone()['status']
            self.assertEqual(status, 'contacted')

        # Verify get_leads excludes contacted
        response = self.client.get('/api/leads')
        data = json.loads(response.data)
        self.assertEqual(len(data['leads']), 3)
        self.assertEqual(data['stats']['contacted'], 1)

if __name__ == '__main__':
    unittest.main()
