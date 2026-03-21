import unittest
import os
import json
import collector
from run import app

TEST_DB = 'test_leads.db'

class TestBackendAPI(unittest.TestCase):
    def setUp(self):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
        collector.init_db(TEST_DB)
        collector.generate_mock_leads(TEST_DB)

        self.app = app.test_client()
        self.app.testing = True

        # Patch the functions in run.py that call collector methods without arguments
        self._original_get_uncontacted = collector.get_uncontacted_leads
        self._original_get_stats = collector.get_stats
        self._original_mark_contacted = collector.mark_contacted

        collector.get_uncontacted_leads = lambda: self._original_get_uncontacted(TEST_DB)
        collector.get_stats = lambda: self._original_get_stats(TEST_DB)
        collector.mark_contacted = lambda lead_id: self._original_mark_contacted(lead_id, TEST_DB)

    def tearDown(self):
        collector.get_uncontacted_leads = self._original_get_uncontacted
        collector.get_stats = self._original_get_stats
        collector.mark_contacted = self._original_mark_contacted
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

    def test_get_leads(self):
        res = self.app.get('/api/leads')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(len(data), 6)
        self.assertEqual(data[0]['city'], 'Bahawalpur')

    def test_get_stats(self):
        res = self.app.get('/api/stats')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data['total'], 6)
        self.assertEqual(data['new'], 6)

    def test_contact_lead(self):
        res = self.app.get('/api/leads')
        leads = json.loads(res.data)
        lead_id = leads[0]['id']

        # Mark contacted
        res = self.app.post('/api/contact', json={'id': lead_id})
        self.assertEqual(res.status_code, 200)

        # Verify stats updated
        res = self.app.get('/api/stats')
        data = json.loads(res.data)
        self.assertEqual(data['contacted'], 1)
        self.assertEqual(data['new'], 5)

if __name__ == '__main__':
    unittest.main()
