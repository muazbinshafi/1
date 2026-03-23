import run
import collector
from unittest.mock import patch

TEST_DB = 'test_leads_backend.db'
collector.init_db(TEST_DB)
collector.generate_mock_leads(TEST_DB)

with patch('run.collector.get_uncontacted_leads', lambda *args, **kwargs: collector.get_uncontacted_leads(TEST_DB)):
    with patch('run.collector.get_stats', lambda *args, **kwargs: collector.get_stats(TEST_DB)):
        client = run.app.test_client()
        res = client.get('/api/leads')
        print(res.status_code, res.data)
