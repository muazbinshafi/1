import unittest
import os
import sqlite3
import collector

class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.db_path = 'test_leads.db'
        # Clean up any previous test db
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_init_db(self):
        collector.init_db(self.db_path)
        self.assertTrue(os.path.exists(self.db_path))

        with collector.get_db(self.db_path) as conn:
            # Check schema
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='leads'")
            self.assertIsNotNone(cursor.fetchone())

    def test_generate_mock_leads(self):
        collector.init_db(self.db_path)
        collector.generate_mock_leads(self.db_path)

        with collector.get_db(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM leads")
            leads = cursor.fetchall()
            self.assertEqual(len(leads), 4)
            self.assertEqual(leads[0]['business_name'], 'Al-Shifa Clinic')

    def test_extract_phone(self):
        self.assertEqual(collector.extract_phone("Call 0300-1234567"), "0300-1234567")
        self.assertEqual(collector.extract_phone("Num: 0311 9876543 here"), "0311 9876543")
        self.assertIsNone(collector.extract_phone("No number here"))

    def test_has_website(self):
        self.assertTrue(collector.has_website("Visit www.test.com"))
        self.assertTrue(collector.has_website("See our site at test.pk"))
        self.assertFalse(collector.has_website("Just a regular text without domain"))

if __name__ == '__main__':
    unittest.main()
