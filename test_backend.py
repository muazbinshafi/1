import unittest
import json
import os
from unittest.mock import patch
from run import app, init_db, get_db

class TestBackend(unittest.TestCase):
    db_path = 'test_leads_api.db'

    @classmethod
    def setUpClass(cls):
        app.config['TESTING'] = True
        cls.client = app.test_client()

    def setUp(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        init_db(self.db_path)

        # Seed DB
        with get_db(self.db_path) as conn:
            conn.execute('''
                INSERT INTO leads (business_name, type, city, phone, contacted)
                VALUES
                ('Lead 1', 'Clinic', 'Bahawalpur', '03001111111', 0),
                ('Lead 2', 'Store', 'Bahawalpur', '03002222222', 1)
            ''')

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    @patch('run.get_db')
    def test_stats_endpoint(self, mock_get_db):
        # We need to mock get_db correctly or redirect DB_PATH
        # An easier way is to patch the module-level DB_PATH or use app context.
        pass # we will rewrite this to avoid patching get_db directly to avoid recursion issues

class TestBackendProper(unittest.TestCase):
    db_path = 'test_leads_api.db'

    @classmethod
    def setUpClass(cls):
        app.config['TESTING'] = True
        cls.client = app.test_client()

    def setUp(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        init_db(self.db_path)

        with get_db(self.db_path) as conn:
            conn.execute('''
                INSERT INTO leads (business_name, type, city, phone, contacted)
                VALUES
                ('Lead 1', 'Clinic', 'Bahawalpur', '03001111111', 0),
                ('Lead 2', 'Store', 'Bahawalpur', '03002222222', 1)
            ''')

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_stats_route(self):
        # We will use patching to mock the DB retrieval to use our test DB path
        import run
        original_get_uncontacted_leads = run.get_uncontacted_leads

        def mocked_get_uncontacted_leads():
            return original_get_uncontacted_leads(self.db_path)

        with patch('run.DB_PATH', self.db_path):
            response = self.client.get('/api/stats')
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertEqual(data['total'], 2)
            self.assertEqual(data['contacted'], 1)
            self.assertEqual(data['new_leads'], 1)

    def test_leads_route(self):
        with patch('run.DB_PATH', self.db_path):
            import run
            # need to patch get_uncontacted_leads explicitly since it uses default argument
            original_func = run.get_uncontacted_leads
            def mocked_func(db_path=self.db_path):
                return original_func(self.db_path)

            with patch('run.get_uncontacted_leads', side_effect=mocked_func):
                response = self.client.get('/api/leads')
                self.assertEqual(response.status_code, 200)
                data = json.loads(response.data)
                self.assertEqual(len(data), 1)
                self.assertEqual(data[0]['business_name'], 'Lead 1')

    def test_contact_route(self):
        with patch('run.DB_PATH', self.db_path):
            # get ID of Lead 1
            with get_db(self.db_path) as conn:
                lead_id = conn.execute("SELECT id FROM leads WHERE business_name='Lead 1'").fetchone()['id']

            # Prevent background collection trigger during test
            with patch('run.scheduler.add_job'):
                response = self.client.post('/api/contact', json={'id': lead_id})
                self.assertEqual(response.status_code, 200)
                data = json.loads(response.data)
                self.assertTrue(data['success'])

            with get_db(self.db_path) as conn:
                contacted = conn.execute("SELECT contacted FROM leads WHERE id=?", (lead_id,)).fetchone()['contacted']
                self.assertEqual(contacted, 1)

if __name__ == '__main__':
    unittest.main()
