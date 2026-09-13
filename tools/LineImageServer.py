#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Serve only signed JPEG/PNG thumbnails behind a Synology HTTPS proxy."""

from __future__ import print_function

import argparse
import mimetypes
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from tools.LineImageDelivery import SignedImageDelivery


class _Handler(BaseHTTPRequestHandler):
    delivery = None

    def do_GET(self):
        if urlparse(self.path).path != '/line-image':
            self.send_error(404)
            return
        token = parse_qs(urlparse(self.path).query).get('token', [None])[0]
        try:
            path = self.delivery.path_from_token(token or '')
            content_type = mimetypes.guess_type(path)[0]
            if content_type not in ('image/jpeg', 'image/png'):
                raise ValueError('only JPEG and PNG thumbnails are allowed')
            size = os.path.getsize(path)
            # The same signed thumbnail URL is used for both LINE fields, so
            # enforce the stricter preview limit rather than risk a rejected
            # image message because previewImageUrl is too large.
            if size > 1 * 1024 * 1024:
                raise ValueError('thumbnail is larger than LINE preview image limit')
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(size))
            self.send_header('Cache-Control', 'private, max-age=60')
            self.end_headers()
            with open(path, 'rb') as source:
                while True:
                    chunk = source.read(1024 * 1024)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
        except (OSError, ValueError):
            self.send_error(404)

    def log_message(self, format_string, *args):
        print('LineImageServer: ' + format_string % args)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--listen', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=18080)
    parser.add_argument('--base-url', required=True)
    parser.add_argument('--secret', required=True)
    parser.add_argument('--root', action='append', required=True)
    parser.add_argument('--ttl-seconds', type=int, default=172800)
    args = parser.parse_args(argv)
    roots = []
    for value in args.root:
        roots.extend(item.strip() for item in value.split(',') if item.strip())
    _Handler.delivery = SignedImageDelivery(
        args.base_url, args.secret, roots, args.ttl_seconds)
    server = ThreadingHTTPServer((args.listen, args.port), _Handler)
    print('Serving signed LINE thumbnails on {0}:{1}'.format(args.listen, args.port))
    server.serve_forever()


if __name__ == '__main__':
    main()

