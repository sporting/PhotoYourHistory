# -*- coding: UTF-8 -*-
"""LINE Messaging API push transport."""

import requests

from im.LineUsage import LineUsageLedger


class LineMessagingApi:
    PushUrl = 'https://api.line.me/v2/bot/message/push'
    MAX_MESSAGE_OBJECTS = 5

    def __init__(self, channel_access_token, request_session=None):
        self.channel_access_token = channel_access_token
        self.session = request_session or requests

    @staticmethod
    def text_message(text):
        return {'type': 'text', 'text': text[:5000]}

    @staticmethod
    def image_message(image_url, preview_url=None):
        preview_url = preview_url or image_url
        return {
            'type': 'image',
            'originalContentUrl': image_url,
            'previewImageUrl': preview_url,
        }

    def push(self, destination, messages):
        if not messages or len(messages) > self.MAX_MESSAGE_OBJECTS:
            raise ValueError('LINE push must contain 1 to 5 message objects')
        response = self.session.post(
            self.PushUrl,
            headers={
                'Authorization': 'Bearer ' + self.channel_access_token,
                'Content-Type': 'application/json',
            },
            json={'to': destination, 'messages': messages},
            timeout=30,
        )
        response.raise_for_status()
        return response

    def push_selected(self, destination, selected_items, delivery, config):
        """Push selected thumbnails in compact batches and record usage.

        Each batch uses one text summary plus up to four image objects.  The
        selector remains in ``mysys.PushPhoto``; this method only transports
        its selected items.
        """
        ledger = LineUsageLedger(config.usage_log_path)
        items = list(selected_items)
        if config.max_images:
            items = items[:config.max_images]
        delivered = []
        for item in items:
            try:
                url = delivery.url_for(item['uri'])
            except (OSError, ValueError, PermissionError) as error:
                print('LINE image skipped: {0}'.format(error))
                continue
            delivered.append({'msg': str(item.get('msg', '')), 'url': url})

        request_count = 0
        message_objects = 0
        for start in range(0, len(delivered), 4):
            batch = delivered[start:start + 4]
            summary = '\n'.join(item['msg'] for item in batch)
            messages = [self.text_message(summary)]
            messages.extend(self.image_message(item['url']) for item in batch)
            if not ledger.can_send(len(messages), config.max_message_objects_per_day):
                print('LINE daily message-object limit reached; remaining items skipped')
                break
            response = self.push(destination, messages)
            ledger.record(destination, len(messages), response.status_code)
            request_count += 1
            message_objects += len(messages)
        return {'request_count': request_count, 'message_objects': message_objects}

