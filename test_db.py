import unittest
import sqlite3
import os
import run

class TestDatabaseFunctions(unittest.TestCase):
    def setUp(self):
        # Create a temporary file database
        self.db_path = 'test_leads.db'
        run.init_db(self.db_path)

    def tearDown(self):
        # Remove the temporary database after test
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='leads'")
        self.assertIsNotNone(c.fetchone())
        conn.close()

    def test_save_leads(self):
        mock_leads = [
            {"business_name": "Test Clinic", "type": "Clinic", "city": "Bahawalpur", "phone": "+923001234567"}
        ]
        run.save_leads(mock_leads, self.db_path)

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT * FROM leads WHERE business_name='Test Clinic'")
        result = c.fetchone()
        self.assertIsNotNone(result)
        self.assertEqual(result[1], "Test Clinic") # index 1 is business_name
        self.assertEqual(result[2], "Clinic")      # index 2 is type
        self.assertEqual(result[4], "+923001234567") # index 4 is phone
        self.assertEqual(result[5], 0)             # index 5 is contacted
        conn.close()

if __name__ == '__main__':
    unittest.main()
