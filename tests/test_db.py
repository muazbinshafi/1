import unittest
import os
import sqlite3
import collector

class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.test_db_path = 'test_leads.db'
        collector.DB_PATH = self.test_db_path
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
        collector.init_db()

    def tearDown(self):
        if os.path.exists(self.test_db_path):
            try:
                os.remove(self.test_db_path)
            except PermissionError:
                pass

    def test_database_initialization(self):
        self.assertTrue(os.path.exists(self.test_db_path))
        with collector.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='leads'")
            self.assertIsNotNone(cursor.fetchone())

    def test_generate_mock_leads(self):
        collector.generate_mock_leads()
        with collector.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM leads")
            count = cursor.fetchone()['count']
            self.assertEqual(count, 6)

    def test_prevent_duplicate_mock_leads(self):
        collector.generate_mock_leads()
        collector.generate_mock_leads() # Call twice
        with collector.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM leads")
            count = cursor.fetchone()['count']
            self.assertEqual(count, 6) # Should still be 6

if __name__ == '__main__':
    unittest.main()
