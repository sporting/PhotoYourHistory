# -*- coding: UTF-8 -*-
"""Small append-only usage ledger for LINE push requests."""

import datetime
import json
import os


class LineUsageLedger:
    def __init__(self, path):
        self.path = path

    @staticmethod
    def today():
        return datetime.datetime.now().date().isoformat()

    def used_message_objects_today(self):
        if not self.path or not os.path.isfile(self.path):
            return 0
        total = 0
        with open(self.path, encoding='utf-8') as source:
            for line in source:
                try:
                    record = json.loads(line)
                except ValueError:
                    continue
                if record.get('date') == self.today():
                    total += int(record.get('message_objects', 0))
        return total

    def can_send(self, message_objects, daily_limit):
        return self.used_message_objects_today() + message_objects <= daily_limit

    def record(self, destination, message_objects, status_code, request_count=1):
        parent = os.path.dirname(os.path.abspath(self.path))
        if parent and not os.path.isdir(parent):
            os.makedirs(parent)
        record = {
            'date': self.today(),
            'timestamp': datetime.datetime.utcnow().isoformat() + 'Z',
            'destination': destination,
            'message_objects': message_objects,
            'request_count': request_count,
            'status_code': status_code,
        }
        with open(self.path, 'a', encoding='utf-8') as output:
            output.write(json.dumps(record, sort_keys=True) + '\n')

