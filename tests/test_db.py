import unittest
import os
import sqlite3
import collector

class TestDBFunctions(unittest.TestCase):
    def setUp(self):
        self.db_path = 'test_leads_temp.db'
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('''
                CREATE TABLE leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    business_name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    city TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    contacted BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_get_uncontacted_leads(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT INTO leads (business_name, type, city, phone, contacted) VALUES ('Test Clinic', 'Clinic', 'Bahawalpur', '+923001234567', FALSE)")
            conn.execute("INSERT INTO leads (business_name, type, city, phone, contacted) VALUES ('Test Store', 'Store', 'Bahawalpur', '+923001234568', TRUE)")

        leads = collector.get_uncontacted_leads(self.db_path)
        self.assertEqual(len(leads), 1)
        self.assertEqual(leads[0]['business_name'], 'Test Clinic')

    def test_get_stats(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT INTO leads (business_name, type, city, phone, contacted) VALUES ('Test Clinic', 'Clinic', 'Bahawalpur', '+923001234567', FALSE)")
            conn.execute("INSERT INTO leads (business_name, type, city, phone, contacted) VALUES ('Test Store', 'Store', 'Bahawalpur', '+923001234568', TRUE)")

        stats = collector.get_stats(self.db_path)
        self.assertEqual(stats['total'], 2)
        self.assertEqual(stats['contacted'], 1)
        self.assertEqual(stats['new'], 1)

    def test_mark_lead_contacted(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("INSERT INTO leads (business_name, type, city, phone, contacted) VALUES ('Test Clinic', 'Clinic', 'Bahawalpur', '+923001234567', FALSE)")
            lead_id = cursor.lastrowid

        collector.mark_lead_contacted(lead_id, self.db_path)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT contacted FROM leads WHERE id = ?", (lead_id,))
            contacted = cursor.fetchone()[0]
            self.assertTrue(contacted)

if __name__ == '__main__':
    unittest.main()
