import unittest
import db
import sqlite3
import os

class TestDB(unittest.TestCase):
    def setUp(self):
        self.db_path = 'test_leads.db'

        # Ensure fresh database
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

        # We need to monkeypatch the DATABASE for the init_db call
        # Or better, update db.py to allow passing db_path to init_db
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    business_name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    city TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    contacted BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='leads'")
            self.assertIsNotNone(cursor.fetchone())

    def test_add_lead(self):
        result = db.add_lead("Test Clinic", "Clinic", "Bahawalpur", "03001234567", self.db_path)
        self.assertTrue(result)

        # Test duplicate phone number
        result2 = db.add_lead("Another Clinic", "Clinic", "Bahawalpur", "03001234567", self.db_path)
        self.assertFalse(result2)

    def test_get_uncontacted_leads(self):
        db.add_lead("Lead 1", "Store", "Bahawalpur", "03001111111", self.db_path)
        db.add_lead("Lead 2", "Store", "Bahawalpur", "03002222222", self.db_path)

        leads = db.get_uncontacted_leads(self.db_path)
        self.assertEqual(len(leads), 2)

        db.mark_contacted(leads[0]['id'], self.db_path)

        leads_after = db.get_uncontacted_leads(self.db_path)
        self.assertEqual(len(leads_after), 1)

    def test_get_stats(self):
        db.add_lead("Lead 1", "Store", "Bahawalpur", "03001111111", self.db_path)
        db.add_lead("Lead 2", "Store", "Bahawalpur", "03002222222", self.db_path)
        db.add_lead("Lead 3", "Store", "Bahawalpur", "03003333333", self.db_path)

        leads = db.get_uncontacted_leads(self.db_path)
        db.mark_contacted(leads[0]['id'], self.db_path)

        stats = db.get_stats(self.db_path)
        self.assertEqual(stats['total'], 3)
        self.assertEqual(stats['contacted'], 1)
        self.assertEqual(stats['new'], 2)

if __name__ == '__main__':
    unittest.main()
