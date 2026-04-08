import unittest
import os
import sqlite3
import collector

class TestDBOperations(unittest.TestCase):
    db_path = 'test_leads.db'

    def setUp(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        collector.init_db(db_path=self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='leads';")
            self.assertIsNotNone(cursor.fetchone())

    def test_insert_and_contact_lead(self):
        with collector.get_db(self.db_path) as conn:
            conn.execute(
                'INSERT INTO leads (business_name, type, city, phone) VALUES (?, ?, ?, ?)',
                ('Test Clinic', 'Clinic', 'Bahawalpur', '03001234567')
            )

            cursor = conn.cursor()
            cursor.execute('SELECT * FROM leads WHERE business_name = "Test Clinic"')
            lead = cursor.fetchone()
            self.assertIsNotNone(lead)
            self.assertEqual(lead['contacted'], 0)

            # Update
            conn.execute('UPDATE leads SET contacted = 1 WHERE id = ?', (lead['id'],))

            cursor.execute('SELECT * FROM leads WHERE id = ?', (lead['id'],))
            updated_lead = cursor.fetchone()
            self.assertEqual(updated_lead['contacted'], 1)

if __name__ == '__main__':
    unittest.main()
