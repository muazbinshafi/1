import unittest
import json
import run
import db
import os
import sqlite3
import time

class TestBackendAPI(unittest.TestCase):
    def setUp(self):
        run.app.config['TESTING'] = True
        self.app = run.app.test_client()
        self.db_path = 'test_leads_api.db'

        if os.path.exists(self.db_path):
            os.remove(self.db_path)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    business_name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    city TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    contacted BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

        # Monkeypatch db.DATABASE for the routes
        self.original_get_uncontacted = db.get_uncontacted_leads
        self.original_get_stats = db.get_stats
        self.original_mark_contacted = db.mark_contacted

        run.db.get_uncontacted_leads = lambda db_path=self.db_path: self.original_get_uncontacted(db_path)
        run.db.get_stats = lambda db_path=self.db_path: self.original_get_stats(db_path)
        run.db.mark_contacted = lambda x, db_path=self.db_path: self.original_mark_contacted(x, db_path)

        # Add some mock leads
        db.add_lead("Lead 1", "Clinic", "Bahawalpur", "03001112222", self.db_path)
        time.sleep(1) # Ensure timestamps are different for order tests. SQLite TIMESTAMP default CURRENT_TIMESTAMP usually has 1s precision
        db.add_lead("Lead 2", "Store", "Bahawalpur", "03003334444", self.db_path)

    def tearDown(self):
        run.db.get_uncontacted_leads = self.original_get_uncontacted
        run.db.get_stats = self.original_get_stats
        run.db.mark_contacted = self.original_mark_contacted

        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_get_leads(self):
        response = self.app.get('/api/leads')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 2)
        # Should be Lead 2 then Lead 1
        self.assertEqual(data[0]['business_name'], 'Lead 2')
        self.assertEqual(data[1]['business_name'], 'Lead 1')

    def test_get_stats(self):
        response = self.app.get('/api/stats')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['total'], 2)
        self.assertEqual(data['contacted'], 0)
        self.assertEqual(data['new'], 2)

    def test_mark_contacted(self):
        # Find first lead id
        leads = db.get_uncontacted_leads(self.db_path)
        lead_id = leads[0]['id']

        response = self.app.post('/api/contact', json={'id': lead_id})
        self.assertEqual(response.status_code, 200)

        stats = db.get_stats(self.db_path)
        self.assertEqual(stats['contacted'], 1)

if __name__ == '__main__':
    unittest.main()
