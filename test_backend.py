import unittest
import os
import json
import db
from run import app

class TestBackend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ['DB_PATH'] = 'test_backend.db'
        if os.path.exists('test_backend.db'):
            os.remove('test_backend.db')
        db.init_db()

    @classmethod
    def tearDownClass(cls):
        if os.path.exists('test_backend.db'):
            os.remove('test_backend.db')

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_index_route(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Universal Lead Collector', response.data)

    def test_api_leads(self):
        # Add a lead manually
        db.add_lead("Backend Test Clinic", "Clinic", "Bahawalpur", "03331234567")

        response = self.app.get('/api/leads')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertTrue(isinstance(data, list))

        found = any(l['phone'] == "03331234567" for l in data)
        self.assertTrue(found)

    def test_api_stats(self):
        response = self.app.get('/api/stats')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertIn('total', data)
        self.assertIn('contacted', data)
        self.assertIn('new', data)

    def test_api_contact(self):
        # Add lead and get ID
        db.add_lead("Contact API Test", "Service", "Bahawalpur", "03441234567")
        leads = db.get_uncontacted_leads()
        lead_id = next(l['id'] for l in leads if l['phone'] == "03441234567")

        response = self.app.post('/api/contact',
                                 data=json.dumps({'lead_id': lead_id}),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertTrue(data['success'])

        # Verify it's no longer uncontacted
        updated_leads = db.get_uncontacted_leads()
        found = any(l['id'] == lead_id for l in updated_leads)
        self.assertFalse(found)

if __name__ == '__main__':
    unittest.main()
