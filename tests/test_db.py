import unittest
import os
import sqlite3
import collector

class TestDBOperations(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Use temporary DB file to persist across connections
        collector.DB_PATH = 'test_leads.db'

    def setUp(self):
        # Fresh db for every test
        if os.path.exists(collector.DB_PATH):
            os.remove(collector.DB_PATH)
        collector.init_db()

    def tearDown(self):
        if os.path.exists(collector.DB_PATH):
            os.remove(collector.DB_PATH)

    def test_init_db(self):
        with collector.get_db() as conn:
            cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='leads'")
            self.assertIsNotNone(cur.fetchone())

    def test_generate_mock_leads(self):
        collector.generate_mock_leads()
        with collector.get_db() as conn:
            cur = conn.execute("SELECT COUNT(*) FROM leads")
            count = cur.fetchone()[0]
            self.assertGreater(count, 0)

    def test_duplicate_mock_leads(self):
        collector.generate_mock_leads()
        collector.generate_mock_leads() # should not add duplicates
        with collector.get_db() as conn:
            cur = conn.execute("SELECT COUNT(*) FROM leads")
            count = cur.fetchone()[0]
            self.assertEqual(count, 5) # 5 mock leads initially

if __name__ == '__main__':
    unittest.main()