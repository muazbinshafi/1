import unittest
import os
import sqlite3
from database import init_db, add_lead, get_active_leads, mark_lead_contacted, get_stats

class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.db_path = 'test_leads.db'
        # Ensure fresh start
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        init_db(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_add_and_get_leads(self):
        add_lead(self.db_path, "Test Clinic", "Clinic", "Bahawalpur", "+923001234567")
        leads = get_active_leads(self.db_path)

        self.assertEqual(len(leads), 1)
        self.assertEqual(leads[0]['business_name'], "Test Clinic")
        self.assertEqual(leads[0]['type'], "Clinic")
        self.assertEqual(leads[0]['contacted'], 0)

    def test_mark_contacted(self):
        add_lead(self.db_path, "Test Store", "Store", "Bahawalpur", "+923001234567")
        leads = get_active_leads(self.db_path)
        lead_id = leads[0]['id']

        mark_lead_contacted(self.db_path, lead_id)

        active_leads = get_active_leads(self.db_path)
        self.assertEqual(len(active_leads), 0)

    def test_stats(self):
        add_lead(self.db_path, "Test 1", "Clinic", "Bahawalpur", "+923001234567")
        add_lead(self.db_path, "Test 2", "Store", "Bahawalpur", "+923001234567")
        add_lead(self.db_path, "Test 3", "Service", "Bahawalpur", "+923001234567")

        leads = get_active_leads(self.db_path)
        mark_lead_contacted(self.db_path, leads[0]['id'])

        stats = get_stats(self.db_path)

        self.assertEqual(stats['total_leads'], 3)
        self.assertEqual(stats['contacted_leads'], 1)
        self.assertEqual(stats['new_leads'], 2)

if __name__ == '__main__':
    unittest.main()
