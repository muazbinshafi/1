import unittest
import os
import sqlite3
import collector

class TestDB(unittest.TestCase):
    def setUp(self):
        self.db_path = 'test_leads.db'
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        collector.init_db(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_init_db_creates_table(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='leads'")
            self.assertIsNotNone(cursor.fetchone())

    def test_generate_mock_leads(self):
        collector.generate_mock_leads(self.db_path)
        leads = collector.get_uncontacted_leads(self.db_path)
        self.assertGreater(len(leads), 0)
        self.assertEqual(leads[0]['city'], 'Bahawalpur')

    def test_mark_contacted(self):
        collector.generate_mock_leads(self.db_path)
        leads = collector.get_uncontacted_leads(self.db_path)
        lead_id = leads[0]['id']

        collector.mark_contacted(lead_id, self.db_path)

        updated_leads = collector.get_uncontacted_leads(self.db_path)
        # Should be one less uncontacted lead
        self.assertEqual(len(updated_leads), len(leads) - 1)

        stats = collector.get_stats(self.db_path)
        self.assertEqual(stats['contacted'], 1)

if __name__ == '__main__':
    unittest.main()
