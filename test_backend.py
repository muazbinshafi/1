import unittest
import json
import database
from run import app

class TestBackend(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()
        database.init_db('test_leads.db')

        # Override the db_file for the app's database calls
        self.original_get_connection = database.get_connection
        database.get_connection = lambda db_file=None: self.original_get_connection('test_leads.db')

        # Clear database
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM leads')
        conn.commit()
        conn.close()

    def tearDown(self):
        database.get_connection = self.original_get_connection

    def test_get_stats(self):
        response = self.app.get('/api/stats')
        data = json.loads(response.data)
        self.assertEqual(data['total'], 0)

    def test_get_leads(self):
        database.add_lead("Test Clinic", "Clinic", "Bahawalpur", "+923000000000")
        response = self.app.get('/api/leads')
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['business_name'], "Test Clinic")

    def test_contact_lead(self):
        database.add_lead("Test Store", "Store", "Bahawalpur", "+923000000001")
        leads = database.get_active_leads()
        lead_id = leads[0]['id']

        response = self.app.post('/api/contact', json={'id': lead_id})
        data = json.loads(response.data)
        self.assertTrue(data['success'])

        stats = database.get_stats()
        self.assertEqual(stats['contacted'], 1)

if __name__ == '__main__':
    unittest.main()