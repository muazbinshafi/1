import unittest
import os
import db

class TestDB(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Setup temporary database
        os.environ['DB_PATH'] = 'test_leads.db'
        if os.path.exists('test_leads.db'):
            os.remove('test_leads.db')
        db.init_db()

    @classmethod
    def tearDownClass(cls):
        if os.path.exists('test_leads.db'):
            os.remove('test_leads.db')

    def test_add_lead(self):
        # Clear db for this test manually if needed, but we rely on unique phones
        res = db.add_lead("Test Business", "Clinic", "Bahawalpur", "03001234567")
        self.assertTrue(res)

        # Adding same phone should fail
        res2 = db.add_lead("Another Business", "Store", "Bahawalpur", "03001234567")
        self.assertFalse(res2)

    def test_get_uncontacted_leads(self):
        db.add_lead("Test Uncontacted", "Service", "Bahawalpur", "03111234567")
        leads = db.get_uncontacted_leads()

        found = any(l['phone'] == "03111234567" for l in leads)
        self.assertTrue(found)

    def test_mark_contacted(self):
        db.add_lead("Contact Test", "Store", "Bahawalpur", "03221234567")
        leads = db.get_uncontacted_leads()
        target_lead = next((l for l in leads if l['phone'] == "03221234567"), None)
        self.assertIsNotNone(target_lead)

        db.mark_contacted(target_lead['id'])

        # Verify it's gone from uncontacted
        updated_leads = db.get_uncontacted_leads()
        found = any(l['phone'] == "03221234567" for l in updated_leads)
        self.assertFalse(found)

    def test_get_stats(self):
        stats = db.get_stats()
        self.assertIn('total', stats)
        self.assertIn('contacted', stats)
        self.assertIn('new', stats)
        self.assertTrue(stats['total'] >= 0)

if __name__ == '__main__':
    unittest.main()
