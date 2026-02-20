import unittest
import sys
import os
import json

# Add parent directory to path to import app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lead_collector.app import app, db, Lead

class LeadCollectorTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app = app.test_client()

        with app.app_context():
            db.create_all()

            # Add a test lead
            lead = Lead(
                name="Test Clinic",
                type="Clinic",
                city="Bahawalpur",
                phone="03001234567",
                website=None,
                status="new"
            )
            db.session.add(lead)
            db.session.commit()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_dashboard(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Universal Lead Collector', response.data)

    def test_get_leads(self):
        response = self.app.get('/api/leads')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], "Test Clinic")

    def test_mark_contacted(self):
        # Get lead id
        with app.app_context():
            lead_id = Lead.query.first().id

        response = self.app.post(f'/api/leads/{lead_id}/contacted')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])

        # Verify status changed
        with app.app_context():
            lead = Lead.query.get(lead_id)
            self.assertEqual(lead.status, 'contacted')

    def test_collection_trigger(self):
        # This calls the real collector which might scrape or generate mock data.
        # We should probably mock collector.collect_leads but for now let's see if it runs.
        # Since we have mock fallback, it should work.
        response = self.app.post('/api/collect')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])

if __name__ == '__main__':
    unittest.main()
