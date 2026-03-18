import unittest
import sqlite3
import os
import tempfile
import collector

class TestDatabase(unittest.TestCase):
    def setUp(self):
        # Create a temporary file database for tests instead of :memory:
        self.fd, self.db_path = tempfile.mkstemp(suffix=".db")
        collector.init_db(self.db_path)

    def tearDown(self):
        os.close(self.fd)
        os.remove(self.db_path)

    def test_init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='leads'")
            self.assertIsNotNone(cursor.fetchone())

    def test_mock_data_and_uncontacted(self):
        collector.generate_mock_leads(self.db_path)
        leads = collector.get_uncontacted_leads(self.db_path)
        self.assertEqual(len(leads), 5)
        # Check that Al-Shifa Clinic is in the list
        names = [lead["business_name"] for lead in leads]
        self.assertIn("Al-Shifa Clinic", names)

    def test_mark_contacted(self):
        collector.generate_mock_leads(self.db_path)
        leads = collector.get_uncontacted_leads(self.db_path)
        lead_id = leads[0]["id"]

        collector.mark_contacted(lead_id, self.db_path)

        uncontacted = collector.get_uncontacted_leads(self.db_path)
        self.assertEqual(len(uncontacted), 4)

    def test_get_stats(self):
        collector.generate_mock_leads(self.db_path)
        stats = collector.get_stats(self.db_path)
        self.assertEqual(stats["Total"], 5)
        self.assertEqual(stats["Contacted"], 0)
        self.assertEqual(stats["New"], 5)

        leads = collector.get_uncontacted_leads(self.db_path)
        collector.mark_contacted(leads[0]["id"], self.db_path)

        stats = collector.get_stats(self.db_path)
        self.assertEqual(stats["Total"], 5)
        self.assertEqual(stats["Contacted"], 1)
        self.assertEqual(stats["New"], 4)

if __name__ == '__main__':
    unittest.main()
