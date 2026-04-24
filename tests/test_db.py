import unittest
import os
import sqlite3
import collector

class TestDB(unittest.TestCase):
    def setUp(self):
        self.db_path = 'test_leads.db'
        collector.DB_PATH = self.db_path
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_setup_db(self):
        collector.setup_db(self.db_path)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='leads'")
            self.assertIsNotNone(cursor.fetchone())

    def test_generate_mock_leads(self):
        collector.setup_db(self.db_path)
        collector.generate_mock_leads(self.db_path)
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            leads = cursor.execute("SELECT * FROM leads").fetchall()
            self.assertEqual(len(leads), 3)
            self.assertEqual(leads[0]['name'], "HealthCare Clinic")
            self.assertEqual(leads[0]['city'], "Bahawalpur")

        # Test duplicate prevention
        collector.generate_mock_leads(self.db_path)
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            leads = cursor.execute("SELECT * FROM leads").fetchall()
            self.assertEqual(len(leads), 3) # Should still be 3

if __name__ == '__main__':
    unittest.main()
