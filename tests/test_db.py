import unittest
import os
import collector

class TestDB(unittest.TestCase):
    def setUp(self):
        self.db_path = 'test_leads.db'
        collector.DB_PATH = self.db_path
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_init_and_mock(self):
        collector.init_db()
        collector.generate_mock_leads()
        with collector.get_db(self.db_path) as db:
            count = db.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
            self.assertGreater(count, 0)

    def test_parse_phone(self):
        self.assertEqual(collector.parse_phone("Call 0300-1234567 today"), "0300-1234567")
        self.assertEqual(collector.parse_phone("No number here"), None)

if __name__ == '__main__':
    unittest.main()