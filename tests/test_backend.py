import sqlite3
import unittest
import os
import run  # Import the module to modify its DB_NAME

class TestBackend(unittest.TestCase):
    def setUp(self):
        # Configure the app for testing
        run.app.config['TESTING'] = True
        self.client = run.app.test_client()

        # Override the database path in the run module
        self.original_db_name = run.DB_NAME
        run.DB_NAME = 'test_leads.db'

        # Initialize test DB using the function from run.py
        # It will use the modified DB_NAME
        run.init_db()

    def tearDown(self):
        # Restore original DB name
        run.DB_NAME = self.original_db_name

        # Clean up test database
        if os.path.exists('test_leads.db'):
            os.remove('test_leads.db')

    def test_database_initialization(self):
        # Check if the file was created and table exists
        self.assertTrue(os.path.exists('test_leads.db'))
        conn = sqlite3.connect('test_leads.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='leads';")
        table_exists = cursor.fetchone()
        conn.close()
        self.assertIsNotNone(table_exists, "Table 'leads' should exist in test_leads.db")

    def test_api_stats(self):
        response = self.client.get('/api/stats')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('total', data)
        self.assertIn('contacted', data)
        self.assertIn('new', data)

    def test_api_leads(self):
        # Insert a dummy lead directly into the test DB
        conn = sqlite3.connect('test_leads.db')
        c = conn.cursor()
        c.execute("INSERT INTO leads (business_name, type, city, phone) VALUES (?, ?, ?, ?)",
                     ('Test Business', 'Clinic', 'Bahawalpur', '0300-1234567'))
        conn.commit()
        conn.close()

        response = self.client.get('/api/leads')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(len(data) >= 1)
        # Check if our inserted lead is in the response
        found = any(lead['business_name'] == 'Test Business' for lead in data)
        self.assertTrue(found)

    def test_contact_lead(self):
        # Insert a dummy lead
        conn = sqlite3.connect('test_leads.db')
        c = conn.cursor()
        c.execute("INSERT INTO leads (business_name, type, city, phone) VALUES (?, ?, ?, ?)",
                     ('Test Business 2', 'Clinic', 'Bahawalpur', '0300-7654321'))
        lead_id = c.lastrowid
        conn.commit()
        conn.close()

        # Mark as contacted
        response = self.client.post(f'/api/contact/{lead_id}')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()['success'])

        # Verify it's no longer in the "new" list
        response = self.client.get('/api/leads')
        data = response.get_json()
        found = any(lead['id'] == lead_id for lead in data)
        self.assertFalse(found, "Contacted lead should not appear in /api/leads")

if __name__ == '__main__':
    unittest.main()
