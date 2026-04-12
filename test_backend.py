import unittest
import os
import json
import run
import collector

class TestBackendAPI(unittest.TestCase):
    def setUp(self):
        self.db_path = 'test_leads_api.db'
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

        collector.init_db(self.db_path)
        collector.DB_PATH = self.db_path

        # Populate test data
        with collector.get_db(self.db_path) as conn:
            conn.execute('INSERT INTO leads (business_name, type, city, phone) VALUES (?, ?, ?, ?)', ('API Clinic', 'Clinic', 'Bahawalpur', '03009999999'))

        self.app = run.app.test_client()
        self.app.testing = True

    def tearDown(self):
        if run.scheduler.running:
            run.scheduler.shutdown()

        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except Exception:
                pass

    def test_get_leads(self):
        response = self.app.get('/api/leads')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['business_name'], 'API Clinic')

    def test_mark_contacted(self):
        # get lead id
        with collector.get_db(self.db_path) as conn:
            lead = conn.execute('SELECT id FROM leads WHERE phone = ?', ('03009999999',)).fetchone()
            lead_id = lead['id']

        response = self.app.post('/api/contact', json={'id': lead_id})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])

        # verify updated
        with collector.get_db(self.db_path) as conn:
            updated_lead = conn.execute('SELECT contacted FROM leads WHERE id = ?', (lead_id,)).fetchone()
            self.assertEqual(updated_lead['contacted'], 1)

if __name__ == '__main__':
    unittest.main()
