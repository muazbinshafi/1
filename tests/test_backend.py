import unittest
from unittest.mock import patch
import json
import run
import collector
from database import init_db

class TestBackend(unittest.TestCase):
    def setUp(self):
        self.app = run.app.test_client()
        self.app.testing = True

    @patch('run.collector.get_uncontacted_leads')
    def test_api_leads(self, mock_get_uncontacted_leads):
        mock_get_uncontacted_leads.return_value = [{"id": 1, "business_name": "Test Clinic"}]
        response = self.app.get('/api/leads')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), [{"id": 1, "business_name": "Test Clinic"}])

    @patch('run.collector.get_stats')
    def test_api_stats(self, mock_get_stats):
        mock_get_stats.return_value = {"total": 10, "contacted": 2, "new": 8}
        response = self.app.get('/api/stats')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), {"total": 10, "contacted": 2, "new": 8})

    @patch('run.get_db')
    @patch('run.trigger_collection')
    def test_api_contact_success(self, mock_trigger, mock_get_db):
        # Mock database connection and cursor
        mock_conn = mock_get_db.return_value.__enter__.return_value
        mock_cursor = mock_conn.cursor.return_value
        mock_cursor.rowcount = 1

        response = self.app.post('/api/contact', json={"id": 1})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), {"success": True})
        mock_cursor.execute.assert_called_with("UPDATE leads SET contacted = 1 WHERE id = ?", (1,))
        mock_trigger.assert_called_once()

    def test_api_contact_missing_id(self):
        response = self.app.post('/api/contact', json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", json.loads(response.data))

if __name__ == '__main__':
    unittest.main()
