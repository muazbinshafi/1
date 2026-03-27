import unittest
from unittest.mock import patch
import json
import run

class TestBackendEndpoints(unittest.TestCase):
    def setUp(self):
        run.app.config['TESTING'] = True
        self.client = run.app.test_client()

    @patch('run.collector.get_uncontacted_leads')
    def test_get_leads(self, mock_get_leads):
        mock_get_leads.return_value = [{'id': 1, 'business_name': 'Test Clinic', 'type': 'Clinic', 'city': 'Bahawalpur', 'phone': '+923001234567'}]
        response = self.client.get('/api/leads')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['business_name'], 'Test Clinic')

    @patch('run.collector.get_stats')
    def test_get_stats(self, mock_get_stats):
        mock_get_stats.return_value = {'total': 10, 'contacted': 5, 'new': 5}
        response = self.client.get('/api/stats')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['total'], 10)

    @patch('run.collector.mark_lead_contacted')
    @patch('threading.Thread.start')
    def test_contact_lead(self, mock_thread_start, mock_mark):
        response = self.client.post('/api/contact',
                                    data=json.dumps({'id': 1}),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        mock_mark.assert_called_once_with(1)
        mock_thread_start.assert_called_once()

    def test_contact_lead_missing_id(self):
        response = self.client.post('/api/contact',
                                    data=json.dumps({}),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 400)

if __name__ == '__main__':
    unittest.main()
