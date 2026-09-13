# -*- coding: UTF-8 -*-
"""Environment-backed configuration for LINE Messaging API delivery."""

import os


def _integer(value, name, default, minimum=0):
    if value in (None, ''):
        return default
    try:
        parsed = int(value)
    except ValueError:
        raise ValueError('{0} must be an integer'.format(name))
    if parsed < minimum:
        raise ValueError('{0} must be at least {1}'.format(name, minimum))
    return parsed


class LineConfig:
    def __init__(self, values=None):
        values = values or os.environ
        self.channel_access_token = values.get('LINE_CHANNEL_ACCESS_TOKEN', '').strip()
        self.channel_secret = values.get('LINE_CHANNEL_SECRET', '').strip()
        self.group_whitelist = frozenset(
            value.strip() for value in values.get('LINE_GROUP_WHITELIST', '').split(',')
            if value.strip()
        )
        self.image_base_url = values.get('LINE_IMAGE_BASE_URL', '').strip().rstrip('/')
        self.image_signing_secret = values.get('LINE_IMAGE_SIGNING_SECRET', '').strip()
        self.image_roots = tuple(
            value.strip() for value in values.get('LINE_IMAGE_ROOTS', '').split(',')
            if value.strip()
        )
        self.image_ttl_seconds = _integer(
            values.get('LINE_IMAGE_TTL_SECONDS'), 'LINE_IMAGE_TTL_SECONDS', 172800, 60)
        self.max_images = _integer(values.get('LINE_MAX_IMAGES'), 'LINE_MAX_IMAGES', 0)
        self.max_message_objects_per_day = _integer(
            values.get('LINE_MAX_MESSAGE_OBJECTS_PER_DAY'),
            'LINE_MAX_MESSAGE_OBJECTS_PER_DAY', 20, 1)
        self.usage_log_path = values.get(
            'LINE_USAGE_LOG_PATH', '.line-message-usage.jsonl').strip()

    @classmethod
    def from_environment(cls):
        return cls(os.environ)

    def require_destination(self, destination):
        if not self.channel_access_token:
            raise ValueError('LINE_CHANNEL_ACCESS_TOKEN is not configured')
        if not self.group_whitelist:
            raise ValueError('LINE_GROUP_WHITELIST is empty; refusing to send')
        if destination not in self.group_whitelist:
            raise PermissionError('LINE destination is not in LINE_GROUP_WHITELIST')
        if not self.image_base_url.startswith('https://'):
            raise ValueError('LINE_IMAGE_BASE_URL must be an https:// URL')
        if not self.image_signing_secret:
            raise ValueError('LINE_IMAGE_SIGNING_SECRET is not configured')
        if not self.image_roots:
            raise ValueError('LINE_IMAGE_ROOTS is empty; refusing to expose files')

