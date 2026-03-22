import unittest
import os
import sqlite3
import collector

class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.db_path = 'test_leads.db'
        collector.init_db(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_add_and_retrieve_lead(self):
        # Add lead
        added = collector.add_lead("Test Clinic", "Clinic", "Bahawalpur", "+923000000000", self.db_path)
        self.assertTrue(added)

        # Prevent duplicate phone
        added_duplicate = collector.add_lead("Another Clinic", "Clinic", "Bahawalpur", "+923000000000", self.db_path)
        self.assertFalse(added_duplicate)

        # Retrieve lead
        leads = collector.get_uncontacted_leads(self.db_path)
        self.assertEqual(len(leads), 1)
        self.assertEqual(leads[0]['business_name'], "Test Clinic")

    def test_mark_contacted(self):
        collector.add_lead("Test Store", "Store", "Bahawalpur", "+923000000001", self.db_path)
        leads = collector.get_uncontacted_leads(self.db_path)
        lead_id = leads[0]['id']

        collector.mark_lead_contacted(lead_id, self.db_path)

        leads_after = collector.get_uncontacted_leads(self.db_path)
        self.assertEqual(len(leads_after), 0)

    def test_get_stats(self):
        collector.add_lead("Lead 1", "Clinic", "Bahawalpur", "+923000000010", self.db_path)
        collector.add_lead("Lead 2", "Store", "Bahawalpur", "+923000000011", self.db_path)

        leads = collector.get_uncontacted_leads(self.db_path)
        collector.mark_lead_contacted(leads[0]['id'], self.db_path)

        stats = collector.get_stats(self.db_path)
        self.assertEqual(stats['total'], 2)
        self.assertEqual(stats['contacted'], 1)
        self.assertEqual(stats['new'], 1)

if __name__ == '__main__':
    unittest.main()
