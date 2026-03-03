import unittest
import json
from run import app, init_db
import sqlite3
import os

class LeadCollectorTestCase(unittest.TestCase):

    def setUp(self):
        # Set up a test database
        app.config['TESTING'] = True
        self.client = app.test_client()

        # We will use the main leads.db but empty it for consistent tests
        # In a real app we'd mock the DB connection to use an in-memory DB or test.db
        # but for this script, we can just clear the table
        init_db()
        conn = sqlite3.connect('leads.db')
        conn.execute('DELETE FROM leads')

        # Insert mock data
        conn.execute('''
            INSERT INTO leads (business_name, type, city, phone, contacted)
            VALUES
            ('Test Clinic 1', 'Clinic', 'Bahawalpur', '+92111111111', 0),
            ('Test Store 1', 'Store', 'Bahawalpur', '+92222222222', 1),
            ('Test Service 1', 'Service', 'Bahawalpur', '+92333333333', 0)
        ''')
        conn.commit()
        conn.close()

    def test_get_leads(self):
        # Should only return contacted = 0
        response = self.client.get('/api/leads')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertEqual(len(data), 2)
        names = [lead['business_name'] for lead in data]
        self.assertIn('Test Clinic 1', names)
        self.assertNotIn('Test Store 1', names)

    def test_get_stats(self):
        response = self.client.get('/api/stats')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertEqual(data['total'], 3)
        self.assertEqual(data['contacted'], 1)
        self.assertEqual(data['new'], 2)

    def test_mark_contacted(self):
        # First find a lead ID that is not contacted
        conn = sqlite3.connect('leads.db')
        conn.row_factory = sqlite3.Row
        lead = conn.execute('SELECT id FROM leads WHERE contacted = 0 LIMIT 1').fetchone()
        conn.close()

        lead_id = lead['id']

        # Mark it contacted
        response = self.client.post(f'/api/mark_contacted/{lead_id}')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertTrue(data['success'])

        # Verify in DB
        conn = sqlite3.connect('leads.db')
        contacted = conn.execute('SELECT contacted FROM leads WHERE id = ?', (lead_id,)).fetchone()[0]
        conn.close()

        self.assertEqual(contacted, 1)

if __name__ == '__main__':
    unittest.main()
