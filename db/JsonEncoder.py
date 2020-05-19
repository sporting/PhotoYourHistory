# -*- coding: UTF-8 -*-
import json

class MyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, bytes):
            try:
                return str(obj, encoding='utf-8')
            except:
                return ""

        return json.JSONEncoder.default(self, obj)
