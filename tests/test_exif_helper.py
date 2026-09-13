import sys
import unittest

# test_batch_index installs a lightweight ExifHelper stub for its isolated import.
# Remove the stub so this test exercises the production implementation.
sys.modules.pop('graph.ExifHelper', None)
from graph.ExifHelper import ExifHelper
from PIL.TiffImagePlugin import IFDRational


class ExifHelperTests(unittest.TestCase):
    def test_rational_value_supports_pillow_rational(self):
        self.assertEqual(0.5, ExifHelper._rational_value(IFDRational(1, 2)))

    def test_rational_value_supports_legacy_pair(self):
        self.assertEqual(0.5, ExifHelper._rational_value((1, 2)))


if __name__ == '__main__':
    unittest.main()
