import unittest
from unittest.mock import patch
import json
import run
import collector

class TestBackend(unittest.TestCase):
    def setUp(self):
        run.app.config['TESTING'] = True
        self.client = run.app.test_client()

    @patch('collector.get_uncontacted_leads')
    def test_get_leads(self, mock_get_leads):
        mock_leads = [{"id": 1, "business_name": "Clinic XYZ", "type": "Clinic", "city": "Bahawalpur", "phone": "123"}]
        mock_get_leads.return_value = mock_leads

        response = self.client.get('/api/leads')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['business_name'], "Clinic XYZ")

    @patch('collector.get_stats')
    def test_get_stats(self, mock_get_stats):
        mock_get_stats.return_value = {"total": 5, "contacted": 2, "new": 3}

        response = self.client.get('/api/stats')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['total'], 5)
        self.assertEqual(data['new'], 3)

    @patch('threading.Thread.start')
    @patch('collector.mark_contacted')
    def test_mark_contacted(self, mock_mark, mock_thread_start):
        response = self.client.post('/api/contact',
                                  data=json.dumps({"id": 1}),
                                  content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        mock_mark.assert_called_once_with(1)
        mock_thread_start.assert_called_once()

    def test_mark_contacted_missing_id(self):
        response = self.client.post('/api/contact',
                                  data=json.dumps({}),
                                  content_type='application/json')
        self.assertEqual(response.status_code, 400)

if __name__ == '__main__':
    unittest.main()
