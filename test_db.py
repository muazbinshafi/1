import unittest
import sqlite3
import os
import db

TEST_DB = 'test_leads.db'

class TestDatabase(unittest.TestCase):
    def setUp(self):
        # Initialize test database
        db.init_db(TEST_DB)

    def tearDown(self):
        # Remove test database
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

    def test_insert_and_retrieve_lead(self):
        with db.get_db(TEST_DB) as conn:
            conn.execute('''
                INSERT INTO leads (business_name, type, city, phone)
                VALUES (?, ?, ?, ?)
            ''', ('Test Clinic', 'Clinic', 'Bahawalpur', '03000000000'))

        with db.get_db(TEST_DB) as conn:
            cursor = conn.execute('SELECT * FROM leads WHERE business_name = ?', ('Test Clinic',))
            lead = cursor.fetchone()

        self.assertIsNotNone(lead)
        self.assertEqual(lead['business_name'], 'Test Clinic')
        self.assertEqual(lead['type'], 'Clinic')
        self.assertEqual(lead['city'], 'Bahawalpur')
        self.assertEqual(lead['phone'], '03000000000')
        self.assertEqual(lead['contacted'], 0)

    def test_update_contacted_status(self):
        with db.get_db(TEST_DB) as conn:
            conn.execute('''
                INSERT INTO leads (business_name, type, city, phone)
                VALUES (?, ?, ?, ?)
            ''', ('Test Store', 'Store', 'Bahawalpur', '03111111111'))
            lead_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]

            # Update status
            conn.execute('UPDATE leads SET contacted = 1 WHERE id = ?', (lead_id,))

            # Verify update
            cursor = conn.execute('SELECT contacted FROM leads WHERE id = ?', (lead_id,))
            contacted = cursor.fetchone()[0]

        self.assertEqual(contacted, 1)

if __name__ == '__main__':
    unittest.main()
