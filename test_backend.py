import unittest
import os
import sqlite3
from unittest.mock import patch, MagicMock
from run import app, init_db, get_db

TEST_DB = 'test_leads_api.db'

class TestBackendAPI(unittest.TestCase):
    def setUp(self):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
        init_db(TEST_DB)

        # Populate test db
        with get_db(TEST_DB) as db:
            db.execute('''
                INSERT INTO leads (business_name, type, city, phone)
                VALUES (?, ?, ?, ?)
            ''', ('Test Store', 'Store', 'Bahawalpur', '0300-1111111'))
            db.execute('''
                INSERT INTO leads (business_name, type, city, phone, contacted)
                VALUES (?, ?, ?, ?, ?)
            ''', ('Test Service', 'Service', 'Bahawalpur', '0300-2222222', True))

        app.config['TESTING'] = True
        self.client = app.test_client()

    def tearDown(self):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

    # Mock get_db to use TEST_DB
    def test_get_leads(self):
        with patch('run.get_db') as mock_get_db:
            # Setup mock to yield a proper connection
            conn = sqlite3.connect(TEST_DB)
            conn.row_factory = sqlite3.Row
            # Create a magic mock for the context manager
            mock_context = MagicMock()
            mock_context.__enter__.return_value = conn
            mock_get_db.return_value = mock_context

            response = self.client.get('/api/leads')
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]['business_name'], 'Test Store')
            conn.close()

    def test_get_stats(self):
        with patch('run.get_db') as mock_get_db:
            conn = sqlite3.connect(TEST_DB)
            conn.row_factory = sqlite3.Row
            mock_context = MagicMock()
            mock_context.__enter__.return_value = conn
            mock_get_db.return_value = mock_context

            response = self.client.get('/api/stats')
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertEqual(data['total'], 2)
            self.assertEqual(data['contacted'], 1)
            self.assertEqual(data['new'], 1)
            conn.close()

    @patch('run.threading.Thread')
    def test_contact_lead(self, mock_thread):
        with patch('run.get_db') as mock_get_db:
            conn = sqlite3.connect(TEST_DB)
            conn.row_factory = sqlite3.Row
            mock_context = MagicMock()
            mock_context.__enter__.return_value = conn
            mock_get_db.return_value = mock_context

            # Get the ID of the uncontacted lead
            cursor = conn.execute("SELECT id FROM leads WHERE contacted = FALSE")
            lead_id = cursor.fetchone()['id']

            response = self.client.post('/api/contact', json={'id': lead_id})
            self.assertEqual(response.status_code, 200)

            # Verify update
            cursor = conn.execute("SELECT contacted FROM leads WHERE id = ?", (lead_id,))
            contacted = cursor.fetchone()['contacted']
            self.assertEqual(contacted, 1)

            # Verify background thread triggered
            mock_thread.assert_called_once()
            conn.close()

if __name__ == '__main__':
    unittest.main()
