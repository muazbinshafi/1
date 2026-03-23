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

    def test_insert_and_get_uncontacted(self):
        collector.generate_mock_leads(TEST_DB)
        leads = collector.get_uncontacted_leads(TEST_DB)
        self.assertEqual(len(leads), 6)

    def test_mark_contacted(self):
        collector.generate_mock_leads(TEST_DB)
        leads = collector.get_uncontacted_leads(TEST_DB)
        first_id = leads[0]['id']

        collector.mark_contacted(first_id, TEST_DB)

        uncontacted = collector.get_uncontacted_leads(TEST_DB)
        self.assertEqual(len(uncontacted), 5)

        stats = collector.get_stats(TEST_DB)
        self.assertEqual(stats['contacted'], 1)

if __name__ == '__main__':
    unittest.main()
