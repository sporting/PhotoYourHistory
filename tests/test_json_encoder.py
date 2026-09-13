import json
import sys
import unittest
from fractions import Fraction

# test_batch_index installs lightweight dependency modules for its isolated import.
# Remove its JSON encoder stub so this test exercises the production implementation.
sys.modules.pop('db.JsonEncoder', None)
from db.JsonEncoder import MyEncoder

try:
    from PIL.TiffImagePlugin import IFDRational
except ImportError:
    IFDRational = None


class JsonEncoderTests(unittest.TestCase):
    def test_encodes_ifd_rational_as_json_number(self):
        if IFDRational is None:
            self.skipTest('Pillow is not installed')
        payload = json.dumps({'ratio': IFDRational(1, 3)}, cls=MyEncoder)
        self.assertEqual(1.0 / 3.0, json.loads(payload)['ratio'])

    def test_encodes_standard_rational_as_json_number(self):
        payload = json.dumps({'ratio': Fraction(1, 3)}, cls=MyEncoder)
        self.assertEqual(1.0 / 3.0, json.loads(payload)['ratio'])

    def test_encodes_zero_denominator_ifd_rational_as_null(self):
        if IFDRational is None:
            self.skipTest('Pillow is not installed')
        payload = json.dumps({'ratio': IFDRational(0, 0)}, cls=MyEncoder)
        self.assertIsNone(json.loads(payload)['ratio'])


if __name__ == '__main__':
    unittest.main()
