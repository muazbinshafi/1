import unittest
import os
import sqlite3
import database

class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.db_file = 'test_leads.db'
        database.init_db(self.db_file)

    def tearDown(self):
        if os.path.exists(self.db_file):
            os.remove(self.db_file)

    def test_add_lead(self):
        database.add_lead('Test Clinic', 'Clinic', 'Bahawalpur', '+923000000000', db_file=self.db_file)
        leads = database.get_active_leads(db_file=self.db_file)
        self.assertEqual(len(leads), 1)
        self.assertEqual(leads[0]['business_name'], 'Test Clinic')

    def test_get_active_leads(self):
        database.add_lead('Clinic 1', 'Clinic', 'City', '123', db_file=self.db_file)
        database.add_lead('Store 1', 'Store', 'City', '456', db_file=self.db_file)
        leads = database.get_active_leads(db_file=self.db_file)
        self.assertEqual(len(leads), 2)

    def test_mark_lead_contacted(self):
        database.add_lead('Service 1', 'Service', 'City', '789', db_file=self.db_file)
        leads = database.get_active_leads(db_file=self.db_file)
        lead_id = leads[0]['id']
        database.mark_lead_contacted(lead_id, db_file=self.db_file)

        active_leads = database.get_active_leads(db_file=self.db_file)
        self.assertEqual(len(active_leads), 0)

    def test_get_stats(self):
        database.add_lead('C1', 'Clinic', 'C', '1', db_file=self.db_file)
        database.add_lead('S1', 'Store', 'C', '2', db_file=self.db_file)

        leads = database.get_active_leads(db_file=self.db_file)
        database.mark_lead_contacted(leads[0]['id'], db_file=self.db_file)

        stats = database.get_stats(db_file=self.db_file)
        self.assertEqual(stats['total'], 2)
        self.assertEqual(stats['contacted'], 1)
        self.assertEqual(stats['new'], 1)

if __name__ == '__main__':
    unittest.main()
