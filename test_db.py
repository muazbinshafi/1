import unittest
import os
import sqlite3
import collector

class TestDB(unittest.TestCase):
    def setUp(self):
        self.db_path = 'test_leads.db'
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        collector.DB_PATH = self.db_path

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_init_db(self):
        collector.init_db()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='leads';")
            self.assertIsNotNone(cursor.fetchone())

    def test_generate_mock_leads(self):
        collector.init_db()
        collector.generate_mock_leads()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM leads;")
            count = cursor.fetchone()[0]
            self.assertEqual(count, 6)

            # Test duplicates
            collector.generate_mock_leads()
            cursor.execute("SELECT COUNT(*) FROM leads;")
            count2 = cursor.fetchone()[0]
            self.assertEqual(count2, 6)

if __name__ == '__main__':
    unittest.main()
