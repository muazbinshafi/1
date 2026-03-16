import unittest
import database
import os

class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.db_path = 'test_leads.db'
        database.init_db(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_add_lead(self):
        database.add_lead("Test Business", "Clinic", "Bahawalpur", "03000000000", self.db_path)
        leads = database.get_uncontacted_leads(self.db_path)
        self.assertEqual(len(leads), 1)
        self.assertEqual(leads[0]['business_name'], "Test Business")
        self.assertEqual(leads[0]['contacted'], 0)

    def test_mark_contacted(self):
        database.add_lead("Test Business 2", "Store", "Bahawalpur", "03000000001", self.db_path)
        leads = database.get_uncontacted_leads(self.db_path)
        lead_id = leads[0]['id']

        database.mark_contacted(lead_id, self.db_path)

        updated_leads = database.get_uncontacted_leads(self.db_path)
        self.assertEqual(len(updated_leads), 0)

        stats = database.get_stats(self.db_path)
        self.assertEqual(stats['contacted'], 1)
        self.assertEqual(stats['new'], 0)
        self.assertEqual(stats['total'], 1)

if __name__ == '__main__':
    unittest.main()
