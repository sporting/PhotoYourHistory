#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Signed, expiring thumbnail URLs for LINE image messages."""

import base64
import hashlib
import hmac
import json
import os
import time
from urllib.parse import quote, urlencode, urlparse


class SignedImageDelivery:
    def __init__(self, base_url, signing_secret, allowed_roots, ttl_seconds=172800):
        if not base_url.startswith('https://'):
            raise ValueError('Image delivery base URL must use HTTPS')
        if not signing_secret:
            raise ValueError('Image delivery signing secret is required')
        if not allowed_roots:
            raise ValueError('At least one allowed image root is required')
        self.base_url = base_url.rstrip('/')
        self.signing_secret = signing_secret.encode('utf-8')
        self.allowed_roots = tuple(os.path.realpath(root) for root in allowed_roots)
        self.ttl_seconds = ttl_seconds

    def _is_allowed(self, path):
        real_path = os.path.realpath(path)
        for root in self.allowed_roots:
            try:
                if os.path.commonpath((real_path, root)) == root:
                    return real_path
            except ValueError:
                continue
        return None

    def _encode(self, payload):
        raw = json.dumps(payload, separators=(',', ':'), sort_keys=True).encode('utf-8')
        encoded = base64.urlsafe_b64encode(raw).decode('ascii').rstrip('=')
        signature = hmac.new(self.signing_secret, encoded.encode('ascii'), hashlib.sha256).digest()
        return encoded + '.' + base64.urlsafe_b64encode(signature).decode('ascii').rstrip('=')

    def _decode(self, token):
        try:
            encoded, signature = token.split('.', 1)
            expected = hmac.new(self.signing_secret, encoded.encode('ascii'), hashlib.sha256).digest()
            supplied = base64.urlsafe_b64decode(signature + '=' * (-len(signature) % 4))
            if not hmac.compare_digest(expected, supplied):
                raise ValueError('invalid image signature')
            raw = base64.urlsafe_b64decode(encoded + '=' * (-len(encoded) % 4))
            payload = json.loads(raw.decode('utf-8'))
            path = self._is_allowed(payload['path'])
            if not path or int(payload['exp']) < int(time.time()):
                raise ValueError('image token expired or path is not allowed')
            if not os.path.isfile(path):
                raise OSError('image does not exist')
            return path
        except (KeyError, TypeError, ValueError, UnicodeError) as error:
            raise ValueError(str(error))

    def url_for(self, image_path):
        allowed = self._is_allowed(image_path)
        if not allowed or not os.path.isfile(allowed):
            raise ValueError('image path is outside LINE_IMAGE_ROOTS or missing')
        token = self._encode({'path': allowed, 'exp': int(time.time()) + self.ttl_seconds})
        url = self.base_url + '/line-image?' + urlencode({'token': token}, quote_via=quote)
        if len(url) > 2000:
            raise ValueError('signed image URL exceeds LINE URL length limit')
        return url

    def path_from_token(self, token):
        return self._decode(token)

