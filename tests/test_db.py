import unittest
import os
import sqlite3
import collector

TEST_DB = 'test_leads.db'

class TestDatabase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        collector.DB_PATH = TEST_DB

    def setUp(self):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
        collector.init_db()

    def tearDown(self):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

    def test_init_db(self):
        with collector.get_db() as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='leads'")
            self.assertIsNotNone(cursor.fetchone())

    def test_insert_and_duplicate(self):
        with collector.get_db() as conn:
            conn.execute('''
                INSERT INTO leads (name, type, city, phone)
                VALUES (?, ?, ?, ?)
            ''', ("Test Clinic", "Clinic", "Bahawalpur", "0300-1112223"))

            # Test duplicate ignore (should raise IntegrityError if not IGNORE, but we use IGNORE in code,
            # so let's test the IGNORE behavior manually to ensure our logic works)
            try:
                conn.execute('''
                    INSERT OR IGNORE INTO leads (name, type, city, phone)
                    VALUES (?, ?, ?, ?)
                ''', ("Test Clinic 2", "Clinic", "Bahawalpur", "0300-1112223"))
            except sqlite3.IntegrityError:
                self.fail("INSERT OR IGNORE raised IntegrityError unexpectedly!")

            count = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
            self.assertEqual(count, 1)

if __name__ == '__main__':
    unittest.main()
