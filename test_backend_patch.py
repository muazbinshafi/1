import unittest
import json
import os
from unittest.mock import patch
import run
import collector

TEST_DB = 'test_leads_backend.db'

class TestBackend(unittest.TestCase):
    def setUp(self):
        run.app.config['TESTING'] = True
        self.client = run.app.test_client()

        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
        collector.init_db(TEST_DB)
        collector.generate_mock_leads(TEST_DB)

        # Patch the base get_db instead to ensure all functions use TEST_DB properly.
        # But actually wait, the get_db is a context manager. Patching run.collector functions should work.
        # Why is it returning 500? Oh, wait, in debug test it returns 200, so my patch must be failing.
