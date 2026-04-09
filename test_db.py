import unittest
import os
import sqlite3
import collector

class TestDB(unittest.TestCase):
    def setUp(self):
        self.db_path = 'test_leads.db'
        collector.DB_PATH = self.db_path
        collector.init_db()

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='leads'")
            self.assertIsNotNone(cursor.fetchone())

    def test_mock_leads(self):
        collector.generate_mock_leads()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT count(*) FROM leads")
            count = cursor.fetchone()[0]
            self.assertGreater(count, 0)

if __name__ == '__main__':
    unittest.main()
