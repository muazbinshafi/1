import unittest
import sqlite3
import os
import run

class TestDatabase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Use a temporary DB file for testing instead of leads.db
        cls.test_db = 'test_leads.db'
        run.DB_PATH = cls.test_db

    def setUp(self):
        # Ensure fresh DB for each test
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
        run.init_db()

    def tearDown(self):
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_init_db(self):
        conn = run.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='leads'")
        table_exists = cursor.fetchone()
        conn.close()
        self.assertIsNotNone(table_exists)

    def test_insert_lead(self):
        conn = run.get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO leads (business_name, type, city, phone)
            VALUES ('Test Clinic', 'Clinic', 'Bahawalpur', '+92 300 1234567')
        ''')
        conn.commit()

        cursor.execute("SELECT * FROM leads WHERE business_name='Test Clinic'")
        lead = cursor.fetchone()
        conn.close()

        self.assertIsNotNone(lead)
        self.assertEqual(lead['type'], 'Clinic')
        self.assertEqual(lead['contacted'], 0)

    def test_update_contacted_status(self):
        conn = run.get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO leads (business_name, type, city, phone)
            VALUES ('Test Store', 'Store', 'Bahawalpur', '+92 301 7654321')
        ''')
        conn.commit()
        lead_id = cursor.lastrowid

        cursor.execute("UPDATE leads SET contacted = 1 WHERE id = ?", (lead_id,))
        conn.commit()

        cursor.execute("SELECT contacted FROM leads WHERE id = ?", (lead_id,))
        contacted_status = cursor.fetchone()['contacted']
        conn.close()

        self.assertEqual(contacted_status, 1)

if __name__ == '__main__':
    unittest.main()
