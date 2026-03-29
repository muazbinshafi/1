import unittest
import json
import os
from unittest.mock import patch
import run
import collector

class TestBackendAPI(unittest.TestCase):
    def setUp(self):
        self.app = run.app.test_client()
        self.app.testing = True
        self.db_path = 'test_leads.db'

        # We need to monkeypatch the functions in run to use our test DB path,
        # or we mock the functions entirely. Mocking is safer for API tests to isolate logic.

    @patch('run.collector.get_uncontacted_leads')
    def test_get_leads(self, mock_get_leads):
        mock_get_leads.return_value = [
            {'id': 1, 'business_name': 'Test1', 'type': 'Clinic', 'city': 'BWP', 'phone': '123'}
        ]
        response = self.app.get('/api/leads')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['business_name'], 'Test1')

    @patch('run.collector.get_stats')
    def test_get_stats(self, mock_get_stats):
        mock_get_stats.return_value = {'total': 10, 'contacted': 5, 'new': 5}
        response = self.app.get('/api/stats')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['total'], 10)

    @patch('run.collector.mark_contacted')
    @patch('run.scheduler.add_job')
    def test_mark_contacted(self, mock_add_job, mock_mark_contacted):
        # Valid request
        response = self.app.post('/api/contact', json={'id': 1})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        mock_mark_contacted.assert_called_once_with(1)
        mock_add_job.assert_called_once()

        # Invalid request missing ID
        response_invalid = self.app.post('/api/contact', json={})
        self.assertEqual(response_invalid.status_code, 400)

if __name__ == '__main__':
    unittest.main()
