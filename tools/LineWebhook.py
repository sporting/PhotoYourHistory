#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Signature-checking webhook that records LINE group IDs for allowlisting."""

from __future__ import print_function

import argparse
import base64
import datetime
import hashlib
import hmac
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def verify_signature(channel_secret, body, signature):
    if not channel_secret or not signature:
        return False
    digest = hmac.new(channel_secret.encode('utf-8'), body, hashlib.sha256).digest()
    expected = base64.b64encode(digest).decode('ascii')
    return hmac.compare_digest(expected, signature)


def extract_group_ids(payload):
    result = set()
    for event in payload.get('events', []):
        source = event.get('source') or {}
        if source.get('type') == 'group' and source.get('groupId'):
            result.add(source['groupId'])
    return sorted(result)


class _Handler(BaseHTTPRequestHandler):
    channel_secret = ''
    capture_path = 'line-group-events.jsonl'

    def do_POST(self):
        try:
            length = int(self.headers.get('Content-Length', '0'))
        except ValueError:
            self.send_error(400, 'invalid content length')
            return
        if length > 1024 * 1024:
            self.send_error(413)
            return
        body = self.rfile.read(length)
        signature = self.headers.get('X-Line-Signature', '')
        if not verify_signature(self.channel_secret, body, signature):
            self.send_error(400, 'invalid signature')
            return
        try:
            payload = json.loads(body.decode('utf-8'))
        except (UnicodeDecodeError, ValueError):
            self.send_error(400, 'invalid JSON')
            return
        record = {
            'received_at': datetime.datetime.utcnow().isoformat() + 'Z',
            'group_ids': extract_group_ids(payload),
            'event_count': len(payload.get('events', [])),
        }
        parent = os.path.dirname(os.path.abspath(self.capture_path))
        if parent and not os.path.isdir(parent):
            os.makedirs(parent)
        with open(self.capture_path, 'a', encoding='utf-8') as output:
            output.write(json.dumps(record, sort_keys=True) + '\n')
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK')

    def log_message(self, format_string, *args):
        print('LineWebhook: ' + format_string % args)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--listen', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=18081)
    parser.add_argument('--channel-secret', required=True)
    parser.add_argument('--capture-file', default='line-group-events.jsonl')
    args = parser.parse_args(argv)
    _Handler.channel_secret = args.channel_secret
    _Handler.capture_path = args.capture_file
    server = ThreadingHTTPServer((args.listen, args.port), _Handler)
    print('Listening for LINE webhook events on {0}:{1}'.format(args.listen, args.port))
    server.serve_forever()


if __name__ == '__main__':
    main()

