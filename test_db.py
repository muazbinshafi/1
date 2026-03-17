import unittest
import os
import sqlite3
import collector

class TestDB(unittest.TestCase):
    def setUp(self):
        self.db_path = 'test_leads.db'
        collector.init_db(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_insert_and_get_uncontacted(self):
        collector.insert_lead("Test Business", "Clinic", "Bahawalpur", "+923001234567", self.db_path)
        leads = collector.get_uncontacted_leads(self.db_path)
        self.assertEqual(len(leads), 1)
        self.assertEqual(leads[0]['business_name'], "Test Business")

    def test_mark_contacted(self):
        collector.insert_lead("Test Business 2", "Store", "Bahawalpur", "03001234568", self.db_path)
        leads = collector.get_uncontacted_leads(self.db_path)
        lead_id = leads[0]['id']

        collector.mark_contacted(lead_id, self.db_path)
        leads_after = collector.get_uncontacted_leads(self.db_path)
        self.assertEqual(len(leads_after), 0)

    def test_get_stats(self):
        collector.insert_lead("Test 1", "Clinic", "Bahawalpur", "1", self.db_path)
        collector.insert_lead("Test 2", "Store", "Bahawalpur", "2", self.db_path)
        leads = collector.get_uncontacted_leads(self.db_path)
        collector.mark_contacted(leads[0]['id'], self.db_path)

        stats = collector.get_stats(self.db_path)
        self.assertEqual(stats['total'], 2)
        self.assertEqual(stats['contacted'], 1)
        self.assertEqual(stats['new'], 1)

if __name__ == '__main__':
    unittest.main()
