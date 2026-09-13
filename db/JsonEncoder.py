# -*- coding: UTF-8 -*-
import json
import math
import numbers

try:
    from PIL.TiffImagePlugin import IFDRational
except ImportError:
    IFDRational = ()


class MyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, bytes):
            try:
                return str(obj, encoding='utf-8')
            except:
                return ""

        if ((IFDRational and isinstance(obj, IFDRational))
                or isinstance(obj, numbers.Rational)):
            value = float(obj)
            return value if math.isfinite(value) else None

        return json.JSONEncoder.default(self, obj)
