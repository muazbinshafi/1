import unittest
import json
import os
from run import app
from db import init_db, DB_FILE

class TestBackend(unittest.TestCase):
    def setUp(self):
        # Setup Flask test client
        self.app = app.test_client()
        self.app.testing = True

        # Use test database
        app.config['TESTING'] = True

        # Ensure db exists
        if not os.path.exists(DB_FILE):
             init_db()

    def test_dashboard(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)

    def test_get_leads_api(self):
        response = self.app.get('/api/leads')
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["status"], "success")
        self.assertIsInstance(data["data"], list)

    def test_get_stats_api(self):
        response = self.app.get('/api/stats')
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["status"], "success")
        self.assertIn("total", data["data"])
        self.assertIn("contacted", data["data"])
        self.assertIn("new", data["data"])

    def test_contact_lead_api(self):
         # Create a test lead first
         from db import add_lead, get_uncontacted_leads, get_connection, DB_FILE
         import time
         unique_name = f"API Test Lead {int(time.time())}"
         add_lead(unique_name, "Store", "Bahawalpur", "+92000000000")

         leads = get_uncontacted_leads()
         # Find the lead we just created
         lead_id = next((lead["id"] for lead in leads if lead["business_name"] == unique_name), None)

         if lead_id:
             response = self.app.post('/api/contact',
                                      data=json.dumps({'lead_id': lead_id}),
                                      content_type='application/json')
             data = json.loads(response.data)
             self.assertEqual(response.status_code, 200)
             self.assertEqual(data["status"], "success")
         else:
             self.fail("Could not find test lead")

         # Test invalid lead id
         response_invalid = self.app.post('/api/contact',
                                      data=json.dumps({'lead_id': 99999}),
                                      content_type='application/json')
         data_invalid = json.loads(response_invalid.data)
         self.assertEqual(response_invalid.status_code, 404)

         # Test missing lead id
         response_missing = self.app.post('/api/contact',
                                      data=json.dumps({}),
                                      content_type='application/json')
         data_missing = json.loads(response_missing.data)
         self.assertEqual(response_missing.status_code, 400)

if __name__ == '__main__':
    unittest.main()