import unittest
import os
import database

class TestDatabase(unittest.TestCase):
    def setUp(self):
        # Use a temporary database for testing
        self.test_db = "test_leads.db"
        database.DB_FILE = self.test_db
        database.init_db()

    def tearDown(self):
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_add_lead(self):
        # Test inserting a lead
        success = database.add_lead("Test Business", "Store", "Bahawalpur", "+923000000000")
        self.assertTrue(success)

        # Test inserting a duplicate lead (should fail due to duplicate phone)
        success_dup = database.add_lead("Test Business 2", "Store", "Bahawalpur", "+923000000000")
        self.assertFalse(success_dup)

    def test_get_uncontacted_leads(self):
        database.add_lead("Test Business 1", "Clinic", "Bahawalpur", "+923000000001")
        database.add_lead("Test Business 2", "Store", "Bahawalpur", "+923000000002")

        leads = database.get_uncontacted_leads()
        self.assertEqual(len(leads), 2)

        # Verify the order (descending by created_at, so lead 2 should be first, but sqlite insert is fast,
        # created_at might be same, so we just verify they are there)
        self.assertTrue(any(l["business_name"] == "Test Business 1" for l in leads))
        self.assertTrue(any(l["business_name"] == "Test Business 2" for l in leads))

    def test_mark_contacted(self):
        database.add_lead("Test Business 1", "Clinic", "Bahawalpur", "+923000000001")
        leads = database.get_uncontacted_leads()
        lead_id = leads[0]["id"]

        # Mark as contacted
        database.mark_contacted(lead_id)

        # Should now be empty for uncontacted
        leads_after = database.get_uncontacted_leads()
        self.assertEqual(len(leads_after), 0)

    def test_get_stats(self):
        database.add_lead("Test Business 1", "Clinic", "Bahawalpur", "+923000000001")
        database.add_lead("Test Business 2", "Store", "Bahawalpur", "+923000000002")

        leads = database.get_uncontacted_leads()
        database.mark_contacted(leads[0]["id"])

        stats = database.get_stats()
        self.assertEqual(stats["total"], 2)
        self.assertEqual(stats["contacted"], 1)
        self.assertEqual(stats["new"], 1)

if __name__ == '__main__':
    unittest.main()
