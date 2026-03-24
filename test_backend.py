import unittest
import json
import db
from unittest.mock import patch
from run import app

class TestBackendAPI(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    @patch('run.db.get_uncontacted_leads')
    def test_get_leads(self, mock_get_leads):
        mock_leads = [
            {'id': 1, 'business_name': 'Mock Clinic', 'type': 'Clinic', 'city': 'Bahawalpur', 'phone': '0300-0000000'}
        ]
        mock_get_leads.return_value = mock_leads

        response = self.app.get('/api/leads')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['business_name'], 'Mock Clinic')

    @patch('run.db.get_stats')
    def test_get_stats(self, mock_get_stats):
        mock_stats = {'total_leads': 10, 'contacted_leads': 2, 'new_leads': 8}
        mock_get_stats.return_value = mock_stats

        response = self.app.get('/api/stats')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['total_leads'], 10)

    @patch('run.db.mark_lead_contacted')
    @patch('run.db.get_stats')
    @patch('run.scheduler.add_job')
    def test_mark_contacted(self, mock_add_job, mock_get_stats, mock_mark):
        mock_get_stats.return_value = {'total_leads': 10, 'contacted_leads': 3, 'new_leads': 7} # New > 5, no schedule

        response = self.app.post('/api/contact',
                                 data=json.dumps({'id': 1}),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        mock_mark.assert_called_once_with(1)
        mock_add_job.assert_not_called()

    @patch('run.db.mark_lead_contacted')
    @patch('run.db.get_stats')
    @patch('run.scheduler.add_job')
    def test_mark_contacted_trigger_scrape(self, mock_add_job, mock_get_stats, mock_mark):
        # Stats indicate < 5 new leads, so it should trigger a job
        mock_get_stats.return_value = {'total_leads': 10, 'contacted_leads': 7, 'new_leads': 3}

        response = self.app.post('/api/contact',
                                 data=json.dumps({'id': 1}),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 200)
        mock_add_job.assert_called_once()

if __name__ == '__main__':
    unittest.main()