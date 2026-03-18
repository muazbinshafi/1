import unittest
import tempfile
import os
import run
import collector
from unittest.mock import patch

class TestBackend(unittest.TestCase):
    def setUp(self):
        self.fd, self.db_path = tempfile.mkstemp(suffix=".db")
        collector.init_db(self.db_path)
        collector.generate_mock_leads(self.db_path)

        # Override the app config for testing
        run.app.config['TESTING'] = True
        self.client = run.app.test_client()

        # We need to save original functions to avoid recursion when patching
        self.orig_uncontacted = collector.get_uncontacted_leads
        self.orig_stats = collector.get_stats
        self.orig_mark = collector.mark_contacted
        self.orig_init = collector.init_db

        # Patch the functions that use default db path to use our temp db
        self.patcher_uncontacted = patch('collector.get_uncontacted_leads', side_effect=lambda *args, **kwargs: self.orig_uncontacted(self.db_path))
        self.patcher_stats = patch('collector.get_stats', side_effect=lambda *args, **kwargs: self.orig_stats(self.db_path))
        self.patcher_mark = patch('collector.mark_contacted', side_effect=lambda lead_id, *args, **kwargs: self.orig_mark(lead_id, self.db_path))
        self.patcher_init = patch('collector.init_db', side_effect=lambda *args, **kwargs: self.orig_init(self.db_path))
        self.patcher_trigger = patch('run.trigger_collection') # Don't spawn threads during test

        self.patcher_uncontacted.start()
        self.patcher_stats.start()
        self.patcher_mark.start()
        self.patcher_init.start()
        self.patcher_trigger.start()

    def tearDown(self):
        self.patcher_uncontacted.stop()
        self.patcher_stats.stop()
        self.patcher_mark.stop()
        self.patcher_init.stop()
        self.patcher_trigger.stop()

        os.close(self.fd)
        os.remove(self.db_path)

    def test_index(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_api_leads(self):
        response = self.client.get('/api/leads')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 5)
        self.assertEqual(data[0]['city'], "Bahawalpur")

    def test_api_stats(self):
        response = self.client.get('/api/stats')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("Total", data)
        self.assertEqual(data["Total"], 5)
        self.assertEqual(data["Contacted"], 0)

    def test_api_contact(self):
        # First get the lead to find an ID
        response = self.client.get('/api/leads')
        data = response.get_json()
        first_lead_id = data[0]['id']

        response = self.client.post('/api/contact', json={'id': first_lead_id})
        self.assertEqual(response.status_code, 200)

        # Ensure stats updated correctly
        response = self.client.get('/api/stats')
        data = response.get_json()
        self.assertEqual(data["Contacted"], 1)

if __name__ == '__main__':
    unittest.main()
