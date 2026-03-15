import unittest
import sqlite3
import os
from run import init_db, get_db

class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.db_path = 'test_leads.db'
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        init_db(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_insert_and_fetch_lead(self):
        conn = get_db(self.db_path)
        c = conn.cursor()
        c.execute('''
            INSERT INTO leads (business_name, type, city, phone)
            VALUES (?, ?, ?, ?)
        ''', ("Test Clinic", "Clinic", "Bahawalpur", "03001234567"))
        conn.commit()

        c.execute('SELECT * FROM leads WHERE business_name = ?', ("Test Clinic",))
        lead = c.fetchone()
        conn.close()

        self.assertIsNotNone(lead)
        self.assertEqual(lead['type'], "Clinic")
        self.assertEqual(lead['contacted'], 0)

    def test_unique_constraint(self):
        conn = get_db(self.db_path)
        c = conn.cursor()
        c.execute('''
            INSERT INTO leads (business_name, type, city, phone)
            VALUES (?, ?, ?, ?)
        ''', ("Dup Clinic", "Clinic", "Bahawalpur", "03001234567"))
        conn.commit()

        with self.assertRaises(sqlite3.IntegrityError):
            c.execute('''
                INSERT INTO leads (business_name, type, city, phone)
                VALUES (?, ?, ?, ?)
            ''', ("Dup Clinic", "Clinic", "Bahawalpur", "03007654321"))
            conn.commit()
        conn.close()

if __name__ == '__main__':
    unittest.main()
