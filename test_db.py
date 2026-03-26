import unittest
import sqlite3
import os
from database import get_db, init_db

class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.test_db = 'test_leads.db'
        # Ensure we start fresh
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
        init_db(self.test_db)

    def tearDown(self):
        # Clean up test database
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_schema_creation(self):
        with get_db(self.test_db) as conn:
            cursor = conn.cursor()

            # Check if table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='leads'")
            self.assertIsNotNone(cursor.fetchone())

            # Check schema structure
            cursor.execute("PRAGMA table_info(leads)")
            columns = [info['name'] for info in cursor.fetchall()]
            expected_columns = ['id', 'business_name', 'type', 'city', 'phone', 'contacted', 'created_at']
            for col in expected_columns:
                self.assertIn(col, columns)

    def test_insert_and_retrieve(self):
        with get_db(self.test_db) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO leads (business_name, type, city, phone) VALUES (?, ?, ?, ?)",
                ("Test Business", "Clinic", "Test City", "+923000000000")
            )

            cursor.execute("SELECT * FROM leads WHERE business_name = 'Test Business'")
            row = cursor.fetchone()

            self.assertIsNotNone(row)
            self.assertEqual(row['type'], 'Clinic')
            self.assertEqual(row['city'], 'Test City')
            self.assertEqual(row['phone'], '+923000000000')
            self.assertEqual(row['contacted'], 0) # Should default to 0

if __name__ == '__main__':
    unittest.main()
