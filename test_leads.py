import unittest
import sqlite3
import os
from collector import init_db, save_lead, generate_mock_leads, scrape_leads, collect_leads

class TestCollector(unittest.TestCase):
    def setUp(self):
        self.db_name = 'test_leads.db'
        init_db(self.db_name)

    def tearDown(self):
        if os.path.exists(self.db_name):
            os.remove(self.db_name)

    def test_init_db(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='leads'")
        self.assertIsNotNone(cursor.fetchone())
        conn.close()

    def test_save_lead(self):
        lead = {
            'business_name': 'Test Business',
            'type': 'Store',
            'city': 'Bahawalpur',
            'phone': '+923001234567'
        }
        save_lead(lead, self.db_name)

        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM leads WHERE phone=?", (lead['phone'],))
        row = cursor.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row[1], 'Test Business')
        self.assertEqual(row[4], '+923001234567')
        conn.close()

    def test_generate_mock_leads(self):
        leads = generate_mock_leads()
        self.assertEqual(len(leads), 3)
        for lead in leads:
            self.assertIn('business_name', lead)
            self.assertIn('type', lead)
            self.assertIn('city', lead)
            self.assertIn('phone', lead)
            self.assertEqual(lead['city'], 'Bahawalpur')
            self.assertIn(lead['type'], ['Clinic', 'Store', 'Service'])

    def test_collect_leads(self):
        collect_leads(self.db_name)

        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM leads")
        count = cursor.fetchone()[0]
        self.assertGreater(count, 0)
        conn.close()

if __name__ == '__main__':
    unittest.main()
