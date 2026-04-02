import unittest
import collector
from unittest.mock import patch, MagicMock

class TestCollector(unittest.TestCase):
    @patch('collector.sync_playwright')
    def test_search_duckduckgo_html(self, mock_playwright):
        # Mocking the playwright behavior
        mock_p = MagicMock()
        mock_browser = MagicMock()
        mock_page = MagicMock()

        mock_playwright.return_value.__enter__.return_value = mock_p
        mock_p.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page

        # Mock results
        mock_result1 = MagicMock()
        mock_result1.locator.return_value.count.return_value = 1
        mock_result1.locator.return_value.inner_text.side_effect = ["Mock Clinic", "Some description 0300-1234567"]

        mock_result2 = MagicMock()
        mock_result2.locator.return_value.count.return_value = 1
        mock_result2.locator.return_value.inner_text.side_effect = ["Mock Store", "Has a website.com 0311-1234567"] # Should be filtered

        mock_page.locator.return_value.all.return_value = [mock_result1, mock_result2]

        leads = collector.search_duckduckgo_html("test query")

        # Assertions
        self.assertEqual(len(leads), 1)
        self.assertEqual(leads[0]['business_name'], "Mock Clinic")
        self.assertEqual(leads[0]['phone'], "03001234567")

if __name__ == '__main__':
    unittest.main()
