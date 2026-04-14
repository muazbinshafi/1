import unittest
import os
import sqlite3
import collector

class TestDB(unittest.TestCase):
    def setUp(self):
        self.db_path = 'test_leads.db'
        collector.DB_PATH = self.db_path
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_schema_creation(self):
        collector.init_db()
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='leads'")
        self.assertIsNotNone(cur.fetchone())
        conn.close()

    def test_context_manager(self):
        collector.init_db()
        with collector.get_db() as conn:
            conn.execute('INSERT INTO leads (business_name, type, city, phone) VALUES (?, ?, ?, ?)',
                         ('Test', 'Store', 'City', '03001234567'))
            # Check row factory is working
            cur = conn.cursor()
            cur.execute('SELECT * FROM leads LIMIT 1')
            row = cur.fetchone()
            self.assertEqual(row['business_name'], 'Test')

    def test_prevent_duplicate_phones(self):
        collector.init_db()
        with collector.get_db() as conn:
            conn.execute('INSERT INTO leads (business_name, type, city, phone) VALUES (?, ?, ?, ?)',
                         ('Test1', 'Store', 'City', '03001234567'))

        with self.assertRaises(sqlite3.IntegrityError):
            with collector.get_db() as conn:
                conn.execute('INSERT INTO leads (business_name, type, city, phone) VALUES (?, ?, ?, ?)',
                             ('Test2', 'Store', 'City', '03001234567'))

if __name__ == '__main__':
    unittest.main()
