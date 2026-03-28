import unittest
import json
import os
from unittest.mock import patch
import run
import collector

class TestBackend(unittest.TestCase):
    def setUp(self):
        self.app = run.app.test_client()
        self.app.testing = True
        self.db_path = "test_backend_leads.db"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        collector.init_db(self.db_path)

        # Save original functions to avoid max recursion
        self.orig_get_uncontacted = collector.get_uncontacted_leads
        self.orig_get_stats = collector.get_stats
        self.orig_mark_contacted = collector.mark_contacted

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    @patch('run.collector.get_uncontacted_leads')
    def test_get_leads(self, mock_get_leads):
        # Insert test data into real DB via original functions, then mock response
        collector.save_lead("Mock Business", "Store", "BWP", "123", self.db_path)
        mock_get_leads.side_effect = lambda: self.orig_get_uncontacted(self.db_path)

        response = self.app.get('/api/leads')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('leads', data)
        self.assertEqual(len(data['leads']), 1)
        self.assertEqual(data['leads'][0]['business_name'], "Mock Business")

    @patch('run.collector.get_stats')
    def test_get_stats(self, mock_stats):
        collector.save_lead("B1", "Store", "BWP", "123", self.db_path)
        collector.save_lead("B2", "Clinic", "BWP", "456", self.db_path)
        leads = self.orig_get_uncontacted(self.db_path)
        self.orig_mark_contacted(leads[0]["id"], self.db_path)

        mock_stats.side_effect = lambda: self.orig_get_stats(self.db_path)

        response = self.app.get('/api/stats')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['total'], 2)
        self.assertEqual(data['contacted'], 1)
        self.assertEqual(data['new'], 1)

    @patch('run.threading.Thread')
    @patch('run.collector.mark_contacted')
    def test_contact_lead(self, mock_mark, mock_thread):
        response = self.app.post('/api/contact', json={'id': 99})
        self.assertEqual(response.status_code, 200)

        # Check that it called mark_contacted and triggered a thread
        mock_mark.assert_called_with(99)
        mock_thread.assert_called()

if __name__ == '__main__':
    unittest.main()
