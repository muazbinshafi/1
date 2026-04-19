import unittest
import os
import json
import run
import collector

TEST_DB = 'test_leads_api.db'

class TestBackend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        collector.DB_PATH = TEST_DB
        # Override background collect to prevent Playwright/Scheduler issues during tests
        run.background_collect = lambda: None
        if run.scheduler.running:
            run.scheduler.pause()

    @classmethod
    def tearDownClass(cls):
        if run.scheduler.running:
            run.scheduler.shutdown(wait=False)

    def setUp(self):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
        collector.init_db()
        run.app.testing = True
        self.client = run.app.test_client()

    def tearDown(self):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

    def test_get_leads_empty(self):
        response = self.client.get('/api/leads')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), [])

    def test_get_analytics(self):
        with collector.get_db() as conn:
            conn.execute('''
                INSERT INTO leads (name, type, city, phone, contacted)
                VALUES (?, ?, ?, ?, ?)
            ''', ("Clinic 1", "Clinic", "Bahawalpur", "123", 0))
            conn.execute('''
                INSERT INTO leads (name, type, city, phone, contacted)
                VALUES (?, ?, ?, ?, ?)
            ''', ("Clinic 2", "Clinic", "Bahawalpur", "456", 1))

        response = self.client.get('/api/analytics')
        data = json.loads(response.data)
        self.assertEqual(data['total'], 2)
        self.assertEqual(data['contacted'], 1)
        self.assertEqual(data['pending'], 1)

    def test_mark_contacted(self):
        with collector.get_db() as conn:
            conn.execute('''
                INSERT INTO leads (name, type, city, phone)
                VALUES (?, ?, ?, ?)
            ''', ("Clinic 1", "Clinic", "Bahawalpur", "123"))

        response = self.client.post('/api/contact', json={'id': 1})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(json.loads(response.data)['success'])

        with collector.get_db() as conn:
            status = conn.execute("SELECT contacted FROM leads WHERE id = 1").fetchone()[0]
            self.assertEqual(status, 1)

if __name__ == '__main__':
    unittest.main()
