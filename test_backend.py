import unittest
import json
import os
from unittest.mock import patch
import run
import collector

TEST_DB = 'test_leads_backend.db'

# Use normal functions instead of lambda to avoid recursion, because lambda calls collector.get_uncontacted_leads which is mocked!
# Actually, the problem is patching run.collector but calling collector... wait, they are the same module reference.
# Let's import the original functions before patching
orig_get_uncontacted_leads = collector.get_uncontacted_leads
orig_get_stats = collector.get_stats
orig_mark_contacted = collector.mark_contacted

class TestBackend(unittest.TestCase):
    def setUp(self):
        run.app.config['TESTING'] = True
        self.client = run.app.test_client()

        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
        collector.init_db(TEST_DB)
        collector.generate_mock_leads(TEST_DB)

        # Patch the functions in the run module to use TEST_DB
        self.patcher1 = patch('run.collector.get_uncontacted_leads', side_effect=lambda *args, **kwargs: orig_get_uncontacted_leads(TEST_DB))
        self.patcher2 = patch('run.collector.get_stats', side_effect=lambda *args, **kwargs: orig_get_stats(TEST_DB))
        self.patcher3 = patch('run.collector.mark_contacted', side_effect=lambda lead_id: orig_mark_contacted(lead_id, TEST_DB))

        self.patcher1.start()
        self.patcher2.start()
        self.patcher3.start()

    def tearDown(self):
        self.patcher1.stop()
        self.patcher2.stop()
        self.patcher3.stop()
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

    def test_api_leads(self):
        response = self.client.get('/api/leads')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 6)

    def test_api_stats(self):
        response = self.client.get('/api/stats')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['total'], 6)
        self.assertEqual(data['contacted'], 0)
        self.assertEqual(data['new'], 6)

    def test_api_contact(self):
        # Get first lead id
        leads_res = self.client.get('/api/leads')
        leads = json.loads(leads_res.data)
        lead_id = leads[0]['id']

        # Post to contact
        response = self.client.post('/api/contact',
                                  json={'lead_id': lead_id})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])

        # Verify stats changed
        stats_res = self.client.get('/api/stats')
        stats = json.loads(stats_res.data)
        self.assertEqual(stats['contacted'], 1)

if __name__ == '__main__':
    unittest.main()
