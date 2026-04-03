import unittest
from unittest.mock import patch
import os
import run
import collector

class TestBackend(unittest.TestCase):
    def setUp(self):
        self.db_path = 'test_leads_api.db'
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        collector.init_db(self.db_path)
        collector.generate_mock_leads(self.db_path)

        # Configure app for testing
        run.app.config['TESTING'] = True
        self.client = run.app.test_client()

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    @patch('run.collector')
    def test_get_leads(self, mock_collector):
        # We need to save reference to original function to pass custom db path
        original_get_leads = collector.get_uncontacted_leads
        mock_collector.get_uncontacted_leads.side_effect = lambda: original_get_leads(self.db_path)

        response = self.client.get('/api/leads')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertGreater(len(data), 0)

    @patch('run.collector')
    def test_get_stats(self, mock_collector):
        original_get_stats = collector.get_stats
        mock_collector.get_stats.side_effect = lambda: original_get_stats(self.db_path)

        response = self.client.get('/api/stats')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('total', data)
        self.assertIn('contacted', data)
        self.assertIn('new', data)

    @patch('run.collector.mark_contacted')
    @patch('run.scheduler')
    def test_contact_lead(self, mock_scheduler, mock_mark):
        # We don't necessarily need to trigger real db change for testing endpoint routing
        mock_mark.return_value = None

        response = self.client.post('/api/contact', json={'id': 1})
        self.assertEqual(response.status_code, 200)
        mock_mark.assert_called_once_with(1)

if __name__ == '__main__':
    unittest.main()
