import unittest
import os
import sqlite3
import collector

class TestDB(unittest.TestCase):
    def setUp(self):
        self.test_db = 'test_leads.db'
        collector.DB_PATH = self.test_db
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def tearDown(self):
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_setup_db(self):
        collector.setup_db()
        self.assertTrue(os.path.exists(self.test_db))

        with sqlite3.connect(self.test_db) as conn:
            cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='leads'")
            self.assertIsNotNone(cur.fetchone())

    def test_generate_mock_leads(self):
        collector.generate_mock_leads()

        with sqlite3.connect(self.test_db) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute("SELECT * FROM leads")
            leads = cur.fetchall()

            self.assertGreater(len(leads), 0)

            # Check if fields are correct
            for lead in leads:
                self.assertIn(lead['type'], ['Clinic', 'Retail Store', 'Service Provider'])
                self.assertEqual(lead['city'], 'Bahawalpur')
                self.assertTrue(lead['phone'].startswith('03'))
                self.assertEqual(lead['contacted'], 0)

if __name__ == '__main__':
    unittest.main()