import unittest
import json
import sqlite3
import os
import time
from run import app
import collector

TEST_DB = 'test_leads.db'

class APITestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

        # use test db
        collector.DB_PATH = TEST_DB
        collector.init_db(TEST_DB)

    def tearDown(self):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

    def test_mock_generation_and_api(self):
        # Generate mock data
        saved = collector.generate_mock_leads(TEST_DB)
        self.assertEqual(saved, 5)

        # Test get leads
        response = self.client.get('/api/leads')
        data = json.loads(response.data)
        self.assertEqual(len(data), 5)

        # Test stats
        response = self.client.get('/api/stats')
        stats = json.loads(response.data)
        self.assertEqual(stats['total'], 5)
        self.assertEqual(stats['contacted'], 0)
        self.assertEqual(stats['new'], 5)

        # Test contact lead
        lead_id = data[0]['id']
        response = self.client.post('/api/contact', json={'id': lead_id})
        self.assertEqual(response.status_code, 200)

        # Verify stats changed
        response = self.client.get('/api/stats')
        stats = json.loads(response.data)
        self.assertEqual(stats['contacted'], 1)
        self.assertEqual(stats['new'], 4)

    def test_phone_cleaner(self):
        self.assertEqual(collector.clean_phone("Call me at 0300-1234567"), "03001234567")
        self.assertEqual(collector.clean_phone("0321 7654321 is the number"), "03217654321")
        self.assertIsNone(collector.clean_phone("No number here"))

    def test_valid_lead(self):
        self.assertTrue(collector.is_valid_lead("A local clinic"))
        self.assertFalse(collector.is_valid_lead("A clinic with website.com"))
        self.assertFalse(collector.is_valid_lead("Visit www.myclinic.pk"))

if __name__ == '__main__':
    unittest.main()
