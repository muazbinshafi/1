import unittest
import os
import json
import collector
import run

class TestBackend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_db = 'test_leads_api.db'
        collector.DB_PATH = cls.test_db
        # Prevent background tasks during tests
        run.background_collect = lambda: None
        if run.scheduler.running:
            run.scheduler.pause()

    def setUp(self):
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
        collector.setup_db()
        collector.generate_mock_leads()

        self.app = run.app.test_client()
        self.app.testing = True

    def tearDown(self):
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    @classmethod
    def tearDownClass(cls):
        if run.scheduler.running:
            run.scheduler.shutdown(wait=False)

    def test_get_leads(self):
        response = self.app.get('/api/leads')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(len(data) > 0)
        self.assertIn('name', data[0])
        self.assertIn('phone', data[0])

    def test_contact_lead(self):
        # Get initial leads
        response = self.app.get('/api/leads')
        data = json.loads(response.data)
        lead_id = data[0]['id']

        # Mark as contacted
        post_response = self.app.post('/api/contact',
                                    data=json.dumps({'id': lead_id}),
                                    content_type='application/json')
        self.assertEqual(post_response.status_code, 200)

        # Verify it's removed from active leads
        response2 = self.app.get('/api/leads')
        data2 = json.loads(response2.data)
        self.assertTrue(all(l['id'] != lead_id for l in data2))

    def test_analytics(self):
        response = self.app.get('/api/analytics')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('total_leads', data)
        self.assertIn('contacted_leads', data)
        self.assertEqual(data['contacted_leads'], 0)

if __name__ == '__main__':
    unittest.main()
