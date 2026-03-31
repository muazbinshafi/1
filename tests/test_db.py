import unittest
import os
import sqlite3
from database import init_db, get_db

class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.db_path = 'test_leads.db'
        # Ensure fresh test DB
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        init_db(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_schema_creation(self):
        with get_db(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='leads'")
            self.assertIsNotNone(cursor.fetchone())

    def test_insertion_and_defaults(self):
        with get_db(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO leads (business_name, type, city, phone) VALUES (?, ?, ?, ?)",
                ("Test Business", "Store", "Test City", "1234567890")
            )
            cursor.execute("SELECT * FROM leads WHERE business_name = 'Test Business'")
            row = cursor.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row['type'], "Store")
            self.assertEqual(row['contacted'], 0) # Default value
            self.assertIsNotNone(row['created_at'])

if __name__ == '__main__':
    unittest.main()
