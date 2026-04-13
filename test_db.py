import unittest
import os
import sqlite3
from collector import get_db, init_db

class TestDatabase(unittest.TestCase):
    db_path = 'test_leads.db'

    def setUp(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        init_db(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_get_db_context_manager(self):
        with get_db(self.db_path) as db:
            db.execute('INSERT INTO leads (business_name, type, city, phone) VALUES (?, ?, ?, ?)',
                       ("Test Clinic", "Clinic", "Bahawalpur", "0312-3456789"))

        # Verify it committed
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.execute('SELECT * FROM leads WHERE phone=?', ("0312-3456789",))
        row = cur.fetchone()
        conn.close()

        self.assertIsNotNone(row)
        self.assertEqual(row['business_name'], "Test Clinic")
        self.assertEqual(row['type'], "Clinic")

if __name__ == '__main__':
    unittest.main()
