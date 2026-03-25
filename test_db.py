import unittest
import os
import sqlite3
from run import get_db, init_db, insert_leads, get_uncontacted_leads, get_stats

TEST_DB = 'test_leads.db'

class TestDatabase(unittest.TestCase):
    def setUp(self):
        # Ensure we start with a clean db
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
        init_db(TEST_DB)

    def tearDown(self):
        # Cleanup after tests
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

    def test_insert_leads(self):
        mock_leads = [
            {"business_name": "Test Clinic", "type": "Clinic", "city": "Bahawalpur", "phone": "03001234567"}
        ]
        insert_leads(mock_leads, db_path=TEST_DB)

        with get_db(TEST_DB) as db:
            cursor = db.execute("SELECT * FROM leads")
            rows = cursor.fetchall()
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]['business_name'], "Test Clinic")

    def test_duplicate_leads_ignored(self):
        mock_leads = [
            {"business_name": "Test Clinic", "type": "Clinic", "city": "Bahawalpur", "phone": "03001234567"}
        ]
        insert_leads(mock_leads, db_path=TEST_DB)
        insert_leads(mock_leads, db_path=TEST_DB) # Should be ignored

        with get_db(TEST_DB) as db:
            cursor = db.execute("SELECT * FROM leads")
            rows = cursor.fetchall()
            self.assertEqual(len(rows), 1)

    def test_get_uncontacted_leads(self):
        mock_leads = [
            {"business_name": "Test Clinic", "type": "Clinic", "city": "Bahawalpur", "phone": "03001234567"}
        ]
        insert_leads(mock_leads, db_path=TEST_DB)

        leads = get_uncontacted_leads(db_path=TEST_DB)
        self.assertEqual(len(leads), 1)
        self.assertEqual(leads[0]['contacted'], 0)

    def test_get_stats(self):
        mock_leads = [
            {"business_name": "Test Clinic 1", "type": "Clinic", "city": "Bahawalpur", "phone": "03001234567"},
            {"business_name": "Test Clinic 2", "type": "Clinic", "city": "Bahawalpur", "phone": "03001234568"}
        ]
        insert_leads(mock_leads, db_path=TEST_DB)

        stats = get_stats(db_path=TEST_DB)
        self.assertEqual(stats['total'], 2)
        self.assertEqual(stats['new'], 2)
        self.assertEqual(stats['contacted'], 0)

if __name__ == '__main__':
    unittest.main()
