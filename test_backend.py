import unittest
from unittest.mock import patch, MagicMock
from run import app
import collector

class TestBackendAPI(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    @patch('collector.get_uncontacted_leads')
    def test_get_leads(self, mock_get_leads):
        mock_leads = [{'id': 1, 'business_name': 'Mock Clinic', 'type': 'Clinic', 'city': 'Bahawalpur', 'phone': '+923000000000'}]
        mock_get_leads.return_value = mock_leads

        response = self.app.get('/api/leads')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, mock_leads)

    @patch('collector.get_stats')
    def test_get_stats(self, mock_get_stats):
        mock_stats = {'total': 10, 'contacted': 5, 'new': 5}
        mock_get_stats.return_value = mock_stats

        response = self.app.get('/api/stats')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, mock_stats)

    @patch('run.background_collect_leads')
    @patch('collector.mark_lead_contacted')
    def test_mark_contacted(self, mock_mark_lead, mock_bg_collect):
        response = self.app.post('/api/contact', json={'id': 1})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {'success': True})
        mock_mark_lead.assert_called_once_with(1)
        # It's difficult to test the Thread target directly without more complex mocking,
        # but we can ensure the endpoint handles valid input correctly.

    def test_mark_contacted_missing_id(self):
        response = self.app.post('/api/contact', json={})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json, {'error': 'Missing id'})

if __name__ == '__main__':
    unittest.main()
