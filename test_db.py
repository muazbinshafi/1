import unittest
import os
import sqlite3
import collector

TEST_DB = 'test_leads.db'

class TestDatabase(unittest.TestCase):
    def setUp(self):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
        collector.init_db(TEST_DB)

    def tearDown(self):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

    def test_schema_creation(self):
        with sqlite3.connect(TEST_DB) as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='leads'")
            self.assertIsNotNone(cursor.fetchone())

    def test_mock_generation(self):
        collector.generate_mock_leads(TEST_DB)
        stats = collector.get_stats(TEST_DB)
        self.assertEqual(stats['total'], 6)
        self.assertEqual(stats['contacted'], 0)
        self.assertEqual(stats['new'], 6)

    def test_mark_contacted(self):
        collector.generate_mock_leads(TEST_DB)
        leads = collector.get_uncontacted_leads(TEST_DB)
        lead_id = leads[0]['id']

        collector.mark_contacted(lead_id, TEST_DB)

        stats = collector.get_stats(TEST_DB)
        self.assertEqual(stats['total'], 6)
        self.assertEqual(stats['contacted'], 1)
        self.assertEqual(stats['new'], 5)

if __name__ == '__main__':
    unittest.main()
