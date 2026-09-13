import unittest

from graph.ExifHelper import ExifHelper
from PIL.TiffImagePlugin import IFDRational


class ExifHelperTests(unittest.TestCase):
    def test_rational_value_supports_pillow_rational(self):
        self.assertEqual(0.5, ExifHelper._rational_value(IFDRational(1, 2)))

    def test_rational_value_supports_legacy_pair(self):
        self.assertEqual(0.5, ExifHelper._rational_value((1, 2)))


if __name__ == '__main__':
    unittest.main()
