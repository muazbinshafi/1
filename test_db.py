import unittest
import os
import sqlite3
from run import get_db, init_db

TEST_DB = 'test_leads.db'

class TestDatabase(unittest.TestCase):
    def setUp(self):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
        init_db(TEST_DB)

    def tearDown(self):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

    def test_schema_initialization(self):
        with get_db(TEST_DB) as db:
            cursor = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='leads'")
            self.assertIsNotNone(cursor.fetchone())

    def test_insert_and_retrieve_lead(self):
        with get_db(TEST_DB) as db:
            db.execute('''
                INSERT INTO leads (business_name, type, city, phone)
                VALUES (?, ?, ?, ?)
            ''', ('Test Clinic', 'Clinic', 'Bahawalpur', '0300-1234567'))

            cursor = db.execute('SELECT * FROM leads WHERE business_name = ?', ('Test Clinic',))
            row = cursor.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row['type'], 'Clinic')
            self.assertEqual(row['contacted'], 0)

if __name__ == '__main__':
    unittest.main()
