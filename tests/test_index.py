import unittest
import run

class TestIndexRoute(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import collector
        cls.original_collect = collector.collect_leads
        collector.collect_leads = lambda: None

    @classmethod
    def tearDownClass(cls):
        import collector
        collector.collect_leads = cls.original_collect

    def setUp(self):
        run.app.config['TESTING'] = True
        self.client = run.app.test_client()

        if run.scheduler.running:
            run.scheduler.pause()

    def tearDown(self):
        run.is_collecting = True
        if run.scheduler.running:
            run.scheduler.shutdown(wait=False)

    def test_index_route(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Universal Lead Collector Dashboard', response.data)

if __name__ == '__main__':
    unittest.main()
