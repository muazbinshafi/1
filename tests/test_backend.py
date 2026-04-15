import unittest
import os
import json
import collector
import run

class TestBackend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Override the background function at class level to avoid any execution
        cls.original_collect = collector.collect_leads
        collector.collect_leads = lambda: None

    @classmethod
    def tearDownClass(cls):
        collector.collect_leads = cls.original_collect

    def setUp(self):
        self.test_db_path = 'test_leads_api.db'
        collector.DB_PATH = self.test_db_path
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)

        collector.init_db()
        collector.generate_mock_leads()

        run.app.config['TESTING'] = True
        self.client = run.app.test_client()

        # Pause scheduler so it doesn't trigger scrape during tests
        if run.scheduler.running:
            run.scheduler.pause()

    def tearDown(self):
        # Prevent the background job from running using a mock flag
        run.is_collecting = True

        # Shut down scheduler gracefully
        if run.scheduler.running:
            run.scheduler.shutdown(wait=False)

        # Clear out jobs
        for job in run.scheduler.get_jobs():
            job.remove()

        if os.path.exists(self.test_db_path):
            try:
                os.remove(self.test_db_path)
            except Exception:
                pass

    def test_api_stats(self):
        response = self.client.get('/api/stats')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        self.assertEqual(data['total'], 6)
        self.assertEqual(data['contacted'], 0)
        self.assertEqual(data['new'], 6)
        self.assertEqual(len(data['leads']), 6)

    def test_api_contact(self):
        # First, get a lead
        stats_resp = self.client.get('/api/stats')
        lead_id = json.loads(stats_resp.data)['leads'][0]['id']

        # Mark it as contacted
        contact_resp = self.client.post('/api/contact',
                                      data=json.dumps({'id': lead_id}),
                                      content_type='application/json')
        self.assertEqual(contact_resp.status_code, 200)

        # Verify it was updated
        stats_resp2 = self.client.get('/api/stats')
        data2 = json.loads(stats_resp2.data)

        self.assertEqual(data2['contacted'], 1)
        self.assertEqual(data2['new'], 5)

if __name__ == '__main__':
    unittest.main()
