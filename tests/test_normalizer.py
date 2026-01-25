import unittest
import sys
import os
sys.path.append(os.getcwd())
from src.text.urdu_normalizer import UrduNormalizer

class TestUrduNormalizer(unittest.TestCase):
    def setUp(self):
        self.normalizer = UrduNormalizer()

    def test_normalize_spaces(self):
        text = "  یہ   ایک    ٹیسٹ   ہے  "
        expected = "یہ ایک ٹیسٹ ہے"
        self.assertEqual(self.normalizer.normalize(text), expected)

    def test_normalize_unicode(self):
        # Example of different unicode representations if any,
        # but for now just check basic consistency
        text = "پاکستان"
        self.assertEqual(self.normalizer.normalize(text), "پاکستان")

if __name__ == "__main__":
    unittest.main()
