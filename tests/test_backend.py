import unittest
import run
import collector
import os

class TestBackendAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        run.app.config['TESTING'] = True
        cls.client = run.app.test_client()
        cls.db_path = 'test_leads_api.db'
        run.DB_PATH = cls.db_path

        # Override background collect to prevent delay
        run.background_collect = lambda: None
        if run.scheduler.running:
            run.scheduler.pause()

    def setUp(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        collector.init_db(self.db_path)
        collector.insert_lead('API Clinic', 'Clinic', 'Bahawalpur', '0300-3333333', self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    @classmethod
    def tearDownClass(cls):
        if run.scheduler.running:
            run.scheduler.shutdown()

    def test_get_leads(self):
        response = self.client.get('/api/leads')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('leads', data)
        self.assertEqual(len(data['leads']), 1)
        self.assertEqual(data['leads'][0]['name'], 'API Clinic')

    def test_contact_lead(self):
        leads = collector.get_uncontacted_leads(self.db_path)
        lead_id = leads[0]['id']

        response = self.client.post('/api/contact', json={'id': lead_id})
        self.assertEqual(response.status_code, 200)

        # Verify database updated
        updated_leads = collector.get_uncontacted_leads(self.db_path)
        self.assertEqual(len(updated_leads), 0)

    def test_get_analytics(self):
        # Insert a second lead and mark it as contacted
        collector.insert_lead('API Store', 'Store', 'Bahawalpur', '0300-4444444', self.db_path)
        leads = collector.get_uncontacted_leads(self.db_path)
        lead_to_contact = [l for l in leads if l['name'] == 'API Store'][0]
        self.client.post('/api/contact', json={'id': lead_to_contact['id']})

        response = self.client.get('/api/analytics')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['total'], 2)
        self.assertEqual(data['contacted'], 1)
        self.assertEqual(data['pending'], 1)

if __name__ == '__main__':
    unittest.main()
