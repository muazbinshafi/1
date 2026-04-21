import unittest
import os
import collector

class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.db_path = 'test_leads.db'
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        collector.init_db(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_insert_lead(self):
        collector.insert_lead('Test Clinic', 'Clinic', 'Bahawalpur', '0300-1111111', self.db_path)
        leads = collector.get_uncontacted_leads(self.db_path)
        self.assertEqual(len(leads), 1)
        self.assertEqual(leads[0]['name'], 'Test Clinic')
        self.assertEqual(leads[0]['type'], 'Clinic')
        self.assertEqual(leads[0]['contacted'], 0)

    def test_unique_phone(self):
        collector.insert_lead('Test 1', 'Clinic', 'Bahawalpur', '0300-2222222', self.db_path)
        collector.insert_lead('Test 2', 'Store', 'Bahawalpur', '0300-2222222', self.db_path)
        leads = collector.get_uncontacted_leads(self.db_path)
        self.assertEqual(len(leads), 1)
        self.assertEqual(leads[0]['name'], 'Test 1')

if __name__ == '__main__':
    unittest.main()
