import unittest
import sqlite3
import os
import collector

class TestDB(unittest.TestCase):
    def setUp(self):
        self.test_db = 'test_leads.db'
        collector.DB_PATH = self.test_db
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def tearDown(self):
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_setup_db(self):
        collector.setup_db()
        with collector.get_db() as conn:
            # Check if table exists
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='leads'")
            self.assertIsNotNone(cursor.fetchone())

    def test_generate_mock_leads(self):
        collector.generate_mock_leads()
        with collector.get_db() as conn:
            cursor = conn.execute("SELECT COUNT(*) as count FROM leads")
            row = cursor.fetchone()
            self.assertTrue(row['count'] > 0)

    def test_row_factory(self):
        collector.generate_mock_leads()
        with collector.get_db() as conn:
            cursor = conn.execute("SELECT * FROM leads LIMIT 1")
            row = cursor.fetchone()
            # Verify dict-like access
            self.assertIn('name', row.keys())
            self.assertIn('phone', row.keys())

    def test_unique_phone(self):
        collector.setup_db()
        with collector.get_db() as conn:
            conn.execute("INSERT INTO leads (name, type, city, phone) VALUES ('A', 'Clinic', 'BWP', '0300-1111111')")
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute("INSERT INTO leads (name, type, city, phone) VALUES ('B', 'Store', 'BWP', '0300-1111111')")

if __name__ == '__main__':
    unittest.main()
