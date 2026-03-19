import unittest
import os
import sqlite3
import collector

class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_leads.db"
        collector.init_db(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_add_and_get_lead(self):
        # Add lead
        added = collector.add_lead("Test Clinic", "Clinic", "Bahawalpur", "12345", self.db_path)
        self.assertTrue(added)

        # Duplicate should return False
        added = collector.add_lead("Test Clinic", "Clinic", "Bahawalpur", "12345", self.db_path)
        self.assertFalse(added)

        leads = collector.get_uncontacted_leads(self.db_path)
        self.assertEqual(len(leads), 1)
        self.assertEqual(leads[0]["business_name"], "Test Clinic")

    def test_mark_contacted_and_stats(self):
        collector.add_lead("Clinic 1", "Clinic", "Bahawalpur", "111", self.db_path)
        collector.add_lead("Store 1", "Store", "Bahawalpur", "222", self.db_path)

        leads = collector.get_uncontacted_leads(self.db_path)
        self.assertEqual(len(leads), 2)

        # Mark one as contacted
        collector.mark_contacted(leads[0]["id"], self.db_path)

        uncontacted = collector.get_uncontacted_leads(self.db_path)
        self.assertEqual(len(uncontacted), 1)

        stats = collector.get_stats(self.db_path)
        self.assertEqual(stats["total"], 2)
        self.assertEqual(stats["contacted"], 1)
        self.assertEqual(stats["new"], 1)

if __name__ == '__main__':
    unittest.main()
