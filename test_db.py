import os
import unittest
import database

class TestDatabase(unittest.TestCase):
    db_file = 'test_leads.db'

    @classmethod
    def setUpClass(cls):
        # Clean up before tests
        if os.path.exists(cls.db_file):
            os.remove(cls.db_file)
        database.init_db(cls.db_file)

    @classmethod
    def tearDownClass(cls):
        # Clean up after tests
        if os.path.exists(cls.db_file):
            os.remove(cls.db_file)

    def setUp(self):
        # Clear data before each test
        conn = database.get_connection(self.db_file)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM leads')
        conn.commit()
        conn.close()

    def test_schema_created(self):
        self.assertTrue(os.path.exists(self.db_file))
        conn = database.get_connection(self.db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='leads'")
        self.assertIsNotNone(cursor.fetchone())
        conn.close()

    def test_add_lead(self):
        result = database.add_lead("Test Clinic", "Clinic", "Bahawalpur", "+923000000000", self.db_file)
        self.assertTrue(result)

        # Test duplicate
        result = database.add_lead("Test Clinic", "Clinic", "Bahawalpur", "+923000000000", self.db_file)
        self.assertFalse(result)

    def test_get_active_leads(self):
        database.add_lead("Test Clinic", "Clinic", "Bahawalpur", "+923000000001", self.db_file)
        database.add_lead("Test Store", "Store", "Bahawalpur", "+923000000002", self.db_file)

        leads = database.get_active_leads(self.db_file)
        self.assertEqual(len(leads), 2)

        # Mark one as contacted
        lead_id = leads[0]['id']
        database.mark_contacted(lead_id, self.db_file)

        leads = database.get_active_leads(self.db_file)
        self.assertEqual(len(leads), 1)

    def test_get_stats(self):
        database.add_lead("Test Clinic", "Clinic", "Bahawalpur", "+923000000001", self.db_file)
        database.add_lead("Test Store", "Store", "Bahawalpur", "+923000000002", self.db_file)

        leads = database.get_active_leads(self.db_file)
        lead_id = leads[0]['id']
        database.mark_contacted(lead_id, self.db_file)

        stats = database.get_stats(self.db_file)
        self.assertEqual(stats['total'], 2)
        self.assertEqual(stats['contacted'], 1)
        self.assertEqual(stats['new'], 1)

if __name__ == '__main__':
    unittest.main()