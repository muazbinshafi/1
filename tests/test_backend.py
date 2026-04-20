import unittest
import os
import json
import collector
import run

class TestBackend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        run.background_collect = lambda: None
        if run.scheduler.running:
            run.scheduler.pause()

    def setUp(self):
        self.db_path = 'test_leads_api.db'
        collector.DB_PATH = self.db_path
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

        run.app.config['TESTING'] = True
        self.client = run.app.test_client()
        collector.init_db()
        collector.generate_mock_leads()

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_get_leads(self):
        response = self.client.get('/api/leads')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(len(data) > 0)

    def test_contact_lead(self):
        response = self.client.get('/api/leads')
        data = json.loads(response.data)
        lead_id = data[0]['id']

        resp2 = self.client.post('/api/contact', json={'id': lead_id})
        self.assertEqual(resp2.status_code, 200)

        with collector.get_db(self.db_path) as db:
            contacted = db.execute("SELECT contacted FROM leads WHERE id = ?", (lead_id,)).fetchone()[0]
            self.assertEqual(contacted, 1)

if __name__ == '__main__':
    unittest.main()