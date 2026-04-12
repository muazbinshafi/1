import unittest
import os
import sqlite3
import collector

class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.db_path = 'test_leads.db'
        # ensure clean state
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        collector.init_db(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_insert_and_retrieve_lead(self):
        with collector.get_db(self.db_path) as conn:
            conn.execute(
                'INSERT INTO leads (business_name, type, city, phone) VALUES (?, ?, ?, ?)',
                ('Test Clinic', 'Clinic', 'Bahawalpur', '03001234567')
            )

            lead = conn.execute('SELECT * FROM leads WHERE phone = ?', ('03001234567',)).fetchone()
            self.assertIsNotNone(lead)
            self.assertEqual(lead['business_name'], 'Test Clinic')
            self.assertEqual(lead['contacted'], 0)

    def test_uncontacted_leads(self):
        with collector.get_db(self.db_path) as conn:
            conn.execute('INSERT INTO leads (business_name, type, city, phone) VALUES (?, ?, ?, ?)', ('L1', 'Store', 'BWP', '03001111111'))
            conn.execute('INSERT INTO leads (business_name, type, city, phone, contacted) VALUES (?, ?, ?, ?, ?)', ('L2', 'Store', 'BWP', '03002222222', 1))

            uncontacted = conn.execute('SELECT * FROM leads WHERE contacted = 0').fetchall()
            self.assertEqual(len(uncontacted), 1)
            self.assertEqual(uncontacted[0]['business_name'], 'L1')

if __name__ == '__main__':
    unittest.main()
