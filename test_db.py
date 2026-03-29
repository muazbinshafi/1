import unittest
import os
import sqlite3
import collector

class TestDatabaseFunctions(unittest.TestCase):
    def setUp(self):
        self.db_path = 'test_leads.db'
        # Ensure db is clean before each test
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        collector.init_db(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_add_lead(self):
        result = collector.add_lead('Test Clinic', 'Clinic', 'Bahawalpur', '+923001234567', self.db_path)
        self.assertTrue(result)

        # Test duplicate phone
        result_dup = collector.add_lead('Test Store', 'Store', 'Bahawalpur', '+923001234567', self.db_path)
        self.assertFalse(result_dup)

    def test_get_uncontacted_leads(self):
        collector.add_lead('Clinic A', 'Clinic', 'Bahawalpur', '111', self.db_path)
        collector.add_lead('Store B', 'Store', 'Bahawalpur', '222', self.db_path)

        leads = collector.get_uncontacted_leads(self.db_path)
        self.assertEqual(len(leads), 2)

        # Mark one as contacted
        collector.mark_contacted(leads[0]['id'], self.db_path)

        leads_after = collector.get_uncontacted_leads(self.db_path)
        self.assertEqual(len(leads_after), 1)

    def test_get_stats(self):
        collector.add_lead('A', 'Type1', 'City', '1', self.db_path)
        collector.add_lead('B', 'Type1', 'City', '2', self.db_path)
        collector.add_lead('C', 'Type1', 'City', '3', self.db_path)

        leads = collector.get_uncontacted_leads(self.db_path)
        collector.mark_contacted(leads[0]['id'], self.db_path)

        stats = collector.get_stats(self.db_path)
        self.assertEqual(stats['total'], 3)
        self.assertEqual(stats['contacted'], 1)
        self.assertEqual(stats['new'], 2)

if __name__ == '__main__':
    unittest.main()
