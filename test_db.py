import unittest
import os
import sqlite3
import collector

class TestDB(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_leads.db"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        collector.init_db(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_save_and_retrieve_lead(self):
        saved = collector.save_lead("Test Clinic", "Clinic", "Bahawalpur", "03001234567", self.db_path)
        self.assertTrue(saved)

        leads = collector.get_uncontacted_leads(self.db_path)
        self.assertEqual(len(leads), 1)
        self.assertEqual(leads[0]["business_name"], "Test Clinic")

    def test_duplicate_lead(self):
        collector.save_lead("Test Store", "Store", "Bahawalpur", "03001234567", self.db_path)
        saved = collector.save_lead("Test Store", "Store", "Bahawalpur", "03001234567", self.db_path)
        self.assertFalse(saved)

        leads = collector.get_uncontacted_leads(self.db_path)
        self.assertEqual(len(leads), 1)

    def test_mark_contacted(self):
        collector.save_lead("Test Service", "Service", "Bahawalpur", "03001234567", self.db_path)
        leads = collector.get_uncontacted_leads(self.db_path)
        lead_id = leads[0]["id"]

        collector.mark_contacted(lead_id, self.db_path)
        leads_after = collector.get_uncontacted_leads(self.db_path)
        self.assertEqual(len(leads_after), 0)

    def test_stats(self):
        collector.save_lead("L1", "Clinic", "Bahawalpur", "111", self.db_path)
        collector.save_lead("L2", "Store", "Bahawalpur", "222", self.db_path)
        collector.save_lead("L3", "Service", "Bahawalpur", "333", self.db_path)

        leads = collector.get_uncontacted_leads(self.db_path)
        collector.mark_contacted(leads[0]["id"], self.db_path)

        stats = collector.get_stats(self.db_path)
        self.assertEqual(stats["total"], 3)
        self.assertEqual(stats["contacted"], 1)
        self.assertEqual(stats["new"], 2)

if __name__ == '__main__':
    unittest.main()
