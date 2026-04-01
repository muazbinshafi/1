import unittest
import os
import sqlite3
from contextlib import contextmanager
from run import get_db

TEST_DB = 'test_leads.db'

class TestDatabaseOperations(unittest.TestCase):
    def setUp(self):
        # Setup temporary test database
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

        with sqlite3.connect(TEST_DB) as conn:
            conn.execute('''
                CREATE TABLE leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    business_name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    city TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    contacted BOOLEAN NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

    def tearDown(self):
        # Clean up
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

    def test_insert_and_retrieve_lead(self):
        # Insert
        with get_db(TEST_DB) as conn:
            conn.execute('''
                INSERT INTO leads (business_name, type, city, phone, contacted)
                VALUES (?, ?, ?, ?, ?)
            ''', ("Test Business", "Clinic", "Bahawalpur", "0300-1234567", 0))

        # Retrieve
        with get_db(TEST_DB) as conn:
            leads = conn.execute('SELECT * FROM leads').fetchall()

        self.assertEqual(len(leads), 1)
        self.assertEqual(leads[0]['business_name'], "Test Business")
        self.assertEqual(leads[0]['contacted'], 0)

    def test_update_contacted_status(self):
        # Insert
        with get_db(TEST_DB) as conn:
            cursor = conn.execute('''
                INSERT INTO leads (business_name, type, city, phone, contacted)
                VALUES (?, ?, ?, ?, ?)
            ''', ("Test Business 2", "Store", "Bahawalpur", "0300-7654321", 0))
            lead_id = cursor.lastrowid

        # Update
        with get_db(TEST_DB) as conn:
            conn.execute('UPDATE leads SET contacted = 1 WHERE id = ?', (lead_id,))

        # Verify
        with get_db(TEST_DB) as conn:
            lead = conn.execute('SELECT * FROM leads WHERE id = ?', (lead_id,)).fetchone()

        self.assertEqual(lead['contacted'], 1)

if __name__ == '__main__':
    unittest.main()
