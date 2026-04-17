import unittest
import os
import json
import sqlite3
import run
import collector

class TestBackend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Override background task to prevent timeouts
        collector.collect_leads = lambda: None
        if run.scheduler.running:
            run.scheduler.pause()

        # Setup test db path
        collector.DB_PATH = 'test_leads_api.db'
        if os.path.exists(collector.DB_PATH):
            os.remove(collector.DB_PATH)

        collector.init_db()

        # Insert test data
        with collector.get_db() as conn:
            conn.execute("INSERT INTO leads (business_name, type, city, phone) VALUES ('Test Clinic', 'Clinic', 'Bahawalpur', '123')")
            conn.execute("INSERT INTO leads (business_name, type, city, phone, contacted) VALUES ('Test Store', 'Retail', 'Bahawalpur', '456', 1)")

        cls.app = run.app.test_client()

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(collector.DB_PATH):
            os.remove(collector.DB_PATH)

    def setUp(self):
        # Recreate tables before each test to ensure state is clean
        if os.path.exists(collector.DB_PATH):
            os.remove(collector.DB_PATH)
        collector.init_db()
        with collector.get_db() as conn:
            conn.execute("INSERT INTO leads (business_name, type, city, phone) VALUES ('Test Clinic', 'Clinic', 'Bahawalpur', '123')")
            conn.execute("INSERT INTO leads (business_name, type, city, phone, contacted) VALUES ('Test Store', 'Retail', 'Bahawalpur', '456', 1)")

    def test_api_leads(self):
        response = self.app.get('/api/leads')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['business_name'], 'Test Clinic')

    def test_api_analytics(self):
        response = self.app.get('/api/analytics')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['total'], 2)
        self.assertEqual(data['contacted'], 1)

    def test_api_contact(self):
        with collector.get_db() as conn:
            lead = conn.execute("SELECT id FROM leads WHERE phone = '123'").fetchone()
            lead_id = lead['id']

        response = self.app.post('/api/contact', json={'id': lead_id})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])

        with collector.get_db() as conn:
            lead_after = conn.execute("SELECT contacted FROM leads WHERE id = ?", (lead_id,)).fetchone()
            self.assertEqual(lead_after['contacted'], 1)
