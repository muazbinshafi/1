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
        collector.init_db()

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_schema_created(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='leads'")
            self.assertIsNotNone(cursor.fetchone())

    def test_mock_data_insertion(self):
        collector.generate_mock_leads()
        with collector.get_db() as conn:
            count = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
            self.assertGreater(count, 0)

            # test no duplicates
            collector.generate_mock_leads()
            count2 = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
            self.assertEqual(count, count2)
