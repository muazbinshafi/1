import unittest
import pathlib
from playwright.sync_api import sync_playwright

class TestPortfolio(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)
        # Point to the static index.html in the root
        cls.file_path = pathlib.Path(__file__).parent.parent / 'index.html'
        cls.file_uri = cls.file_path.absolute().as_uri()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def test_miladicode_title(self):
        page = self.browser.new_page()
        page.goto(self.file_uri, wait_until='domcontentloaded')
        title = page.title()
        self.assertIn("MiladiCode", title)
        page.close()

if __name__ == '__main__':
    unittest.main()
