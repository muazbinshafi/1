import unittest
import sqlite3
import os
from db import init_db, add_lead, get_uncontacted_leads, mark_lead_contacted, get_stats

class TestDB(unittest.TestCase):
    db_file = "test_leads.db"

    def setUp(self):
        # Create a fresh database before each test
        if os.path.exists(self.db_file):
            os.remove(self.db_file)
        init_db(self.db_file)

    def tearDown(self):
        # Clean up database after each test
        if os.path.exists(self.db_file):
            os.remove(self.db_file)

    def test_init_db(self):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='leads';")
        self.assertIsNotNone(cursor.fetchone())
        conn.close()

    def test_add_lead(self):
        success = add_lead("Test Clinic", "Clinic", "Bahawalpur", "+923001234567", self.db_file)
        self.assertTrue(success)

        # Test duplicate insertion prevention
        success_dup = add_lead("Test Clinic", "Clinic", "Bahawalpur", "+923001234567", self.db_file)
        self.assertFalse(success_dup)

    def test_get_uncontacted_leads(self):
        add_lead("Test Store 1", "Store", "Bahawalpur", "111", self.db_file)
        add_lead("Test Store 2", "Store", "Bahawalpur", "222", self.db_file)

        leads = get_uncontacted_leads(self.db_file)
        self.assertEqual(len(leads), 2)

        # Verify order
        # Since they are added instantly, timestamp might be identical, sorting by ID fallback
        names = [lead["business_name"] for lead in leads]
        self.assertIn("Test Store 1", names)
        self.assertIn("Test Store 2", names)

    def test_mark_lead_contacted(self):
        add_lead("Test Service", "Service", "Bahawalpur", "333", self.db_file)

        # Need to fetch the lead to get its ID
        leads = get_uncontacted_leads(self.db_file)
        lead_id = leads[0]["id"]

        success = mark_lead_contacted(lead_id, self.db_file)
        self.assertTrue(success)

        # Verify it's no longer in uncontacted
        uncontacted = get_uncontacted_leads(self.db_file)
        self.assertEqual(len(uncontacted), 0)

    def test_get_stats(self):
        add_lead("Clinic A", "Clinic", "Bahawalpur", "1", self.db_file)
        add_lead("Store B", "Store", "Bahawalpur", "2", self.db_file)
        add_lead("Service C", "Service", "Bahawalpur", "3", self.db_file)

        leads = get_uncontacted_leads(self.db_file)

        # Mark one as contacted
        mark_lead_contacted(leads[0]["id"], self.db_file)

        stats = get_stats(self.db_file)

        self.assertEqual(stats["total"], 3)
        self.assertEqual(stats["contacted"], 1)
        self.assertEqual(stats["new"], 2)

if __name__ == '__main__':
    unittest.main()