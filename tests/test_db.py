import unittest
import os
import sqlite3
import collector

class TestDB(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db_path = 'test_leads.db'

    def setUp(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        collector.init_db(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_init_db(self):
        with collector.get_db(self.db_path) as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='leads'")
            self.assertIsNotNone(cursor.fetchone())

    def test_generate_mock_leads(self):
        collector.generate_mock_leads(self.db_path)
        with collector.get_db(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM leads")
            count = cursor.fetchone()[0]
            self.assertEqual(count, 4)

    def test_unique_phone(self):
        with collector.get_db(self.db_path) as conn:
            conn.execute("INSERT INTO leads (name, type, city, phone) VALUES (?, ?, ?, ?)",
                         ('Test', 'Store', 'Bahawalpur', '0300 1111111'))
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute("INSERT INTO leads (name, type, city, phone) VALUES (?, ?, ?, ?)",
                             ('Test 2', 'Store', 'Bahawalpur', '0300 1111111'))

if __name__ == '__main__':
    unittest.main()
