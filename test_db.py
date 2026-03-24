import unittest
import os
import db

TEST_DB = 'test_leads.db'

class TestDatabase(unittest.TestCase):
    def setUp(self):
        # Ensure fresh database for each test
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
        db.init_db(TEST_DB)

    def tearDown(self):
        # Clean up
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

    def test_add_lead(self):
        db.add_lead("Test Clinic", "Clinic", "Bahawalpur", "0300-1111111", TEST_DB)
        leads = db.get_uncontacted_leads(TEST_DB)
        self.assertEqual(len(leads), 1)
        self.assertEqual(leads[0]['business_name'], "Test Clinic")

    def test_duplicate_lead_ignored(self):
        db.add_lead("Test Clinic", "Clinic", "Bahawalpur", "0300-1111111", TEST_DB)
        db.add_lead("Test Clinic", "Clinic", "Bahawalpur", "0300-1111111", TEST_DB)
        leads = db.get_uncontacted_leads(TEST_DB)
        self.assertEqual(len(leads), 1)

    def test_mark_contacted(self):
        db.add_lead("Test Clinic", "Clinic", "Bahawalpur", "0300-1111111", TEST_DB)
        leads = db.get_uncontacted_leads(TEST_DB)
        lead_id = leads[0]['id']

        db.mark_lead_contacted(lead_id, TEST_DB)

        # Verify it's removed from uncontacted list
        uncontacted = db.get_uncontacted_leads(TEST_DB)
        self.assertEqual(len(uncontacted), 0)

        # Verify stats
        stats = db.get_stats(TEST_DB)
        self.assertEqual(stats['total_leads'], 1)
        self.assertEqual(stats['contacted_leads'], 1)
        self.assertEqual(stats['new_leads'], 0)

if __name__ == '__main__':
    unittest.main()