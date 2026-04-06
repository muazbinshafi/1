import unittest
import sqlite3
import os
from db import get_db, init_db

TEST_DB = 'test_leads.db'

class TestDatabase(unittest.TestCase):
    def setUp(self):
        # Ensure clean state
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
        init_db(TEST_DB)

    def tearDown(self):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

    def test_schema(self):
        with get_db(TEST_DB) as conn:
            cur = conn.execute("PRAGMA table_info(leads)")
            columns = [row['name'] for row in cur.fetchall()]

            self.assertIn('id', columns)
            self.assertIn('business_name', columns)
            self.assertIn('type', columns)
            self.assertIn('city', columns)
            self.assertIn('phone', columns)
            self.assertIn('contacted', columns)

    def test_insert_and_retrieve(self):
        with get_db(TEST_DB) as conn:
            conn.execute(
                "INSERT INTO leads (business_name, type, city, phone) VALUES (?, ?, ?, ?)",
                ("Test Clinic", "Clinic", "Bahawalpur", "03001234567")
            )

            cur = conn.execute("SELECT * FROM leads WHERE business_name = 'Test Clinic'")
            lead = cur.fetchone()

            self.assertIsNotNone(lead)
            self.assertEqual(lead['type'], "Clinic")
            self.assertEqual(lead['contacted'], 0)

if __name__ == '__main__':
    unittest.main()
