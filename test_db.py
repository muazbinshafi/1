import unittest
import sqlite3
import os
from run import get_db, init_db

class TestDatabase(unittest.TestCase):
    db_path = 'test_leads.db'

    def setUp(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        init_db(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_init_db(self):
        with get_db(self.db_path) as conn:
            # Check if table exists
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='leads'")
            self.assertIsNotNone(cursor.fetchone())

    def test_insert_lead(self):
        with get_db(self.db_path) as conn:
            conn.execute('''
                INSERT INTO leads (business_name, type, city, phone)
                VALUES (?, ?, ?, ?)
            ''', ('Test Clinic', 'Clinic', 'Bahawalpur', '03001234567'))

            lead = conn.execute("SELECT * FROM leads WHERE phone='03001234567'").fetchone()
            self.assertIsNotNone(lead)
            self.assertEqual(lead['business_name'], 'Test Clinic')
            self.assertEqual(lead['contacted'], 0)

    def test_unique_phone(self):
        with get_db(self.db_path) as conn:
            conn.execute('''
                INSERT INTO leads (business_name, type, city, phone)
                VALUES (?, ?, ?, ?)
            ''', ('Test Clinic 1', 'Clinic', 'Bahawalpur', '03001234567'))

            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute('''
                    INSERT INTO leads (business_name, type, city, phone)
                    VALUES (?, ?, ?, ?)
                ''', ('Test Clinic 2', 'Clinic', 'Bahawalpur', '03001234567'))

    def test_update_contacted(self):
        with get_db(self.db_path) as conn:
            conn.execute('''
                INSERT INTO leads (business_name, type, city, phone)
                VALUES (?, ?, ?, ?)
            ''', ('Test Clinic', 'Clinic', 'Bahawalpur', '03001234567'))

            conn.execute("UPDATE leads SET contacted = 1 WHERE phone='03001234567'")

            lead = conn.execute("SELECT * FROM leads WHERE phone='03001234567'").fetchone()
            self.assertEqual(lead['contacted'], 1)

if __name__ == '__main__':
    unittest.main()
