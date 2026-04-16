import unittest
from playwright.sync_api import sync_playwright
import pathlib

class TestIndexHtml(unittest.TestCase):
    def test_index_title(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            file_uri = (pathlib.Path(__file__).parent.parent / 'index.html').absolute().as_uri()
            page.goto(file_uri, wait_until='domcontentloaded')

            title = page.title()
            self.assertIn("MiladiCode", title)
            browser.close()

if __name__ == '__main__':
    unittest.main()