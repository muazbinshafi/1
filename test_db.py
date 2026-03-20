import unittest
import os
import sqlite3
from db import init_db, get_db

TEST_DB = 'test_leads.db'

class TestDatabase(unittest.TestCase):
    def setUp(self):
        # ensure no previous db
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
        init_db(TEST_DB)

    def tearDown(self):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

    def test_init_db(self):
        with get_db(TEST_DB) as conn:
            cursor = conn.cursor()
            # test tables creation
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='leads'")
            self.assertIsNotNone(cursor.fetchone())

    def test_insert_lead(self):
        with get_db(TEST_DB) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO leads (business_name, type, city, phone) VALUES (?, ?, ?, ?)",
                           ("Test Clinic", "Clinic", "Bahawalpur", "+92 300 1234567"))
            cursor.execute("SELECT * FROM leads WHERE phone = ?", ("+92 300 1234567",))
            row = cursor.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row['business_name'], "Test Clinic")
            self.assertEqual(row['type'], "Clinic")

if __name__ == '__main__':
    unittest.main()
