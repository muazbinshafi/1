import unittest
from collector import collect_leads

class TestCollector(unittest.TestCase):
    def test_collect_leads_structure(self):
        leads = collect_leads()
        self.assertIsInstance(leads, list)
        self.assertTrue(len(leads) > 0, "Should return at least one lead (mock or real)")

        first_lead = leads[0]
        expected_keys = {'name', 'type', 'city', 'phone'}
        self.assertTrue(expected_keys.issubset(first_lead.keys()), f"Lead missing keys: {expected_keys - first_lead.keys()}")
        self.assertEqual(first_lead['city'], 'Bahawalpur')
        self.assertIn(first_lead['type'], ['Clinic', 'Store', 'Service'])

if __name__ == '__main__':
    unittest.main()
