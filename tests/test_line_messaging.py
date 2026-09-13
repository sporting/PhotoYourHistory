import hashlib
import hmac
import json
import os
import tempfile
import unittest

from im.LineConfig import LineConfig
from im.LineMessagingApi import LineMessagingApi
from tools.LineImageDelivery import SignedImageDelivery
from tools.LineWebhook import extract_group_ids, verify_signature


class _Response:
    status_code = 200

    def raise_for_status(self):
        return None


class _Session:
    def __init__(self):
        self.calls = []

    def post(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return _Response()


class LineMessagingTests(unittest.TestCase):
    def test_push_batches_use_at_most_five_objects_and_whitelist_is_required(self):
        with tempfile.TemporaryDirectory() as temp:
            image = os.path.join(temp, 'thumb.jpg')
            with open(image, 'wb') as output:
                output.write(b'jpeg')
            values = {
                'LINE_CHANNEL_ACCESS_TOKEN': 'token',
                'LINE_GROUP_WHITELIST': 'group-1',
                'LINE_IMAGE_BASE_URL': 'https://photos.example.com',
                'LINE_IMAGE_SIGNING_SECRET': 'secret',
                'LINE_IMAGE_ROOTS': temp,
                'LINE_USAGE_LOG_PATH': os.path.join(temp, 'usage.jsonl'),
                'LINE_MAX_MESSAGE_OBJECTS_PER_DAY': '20',
            }
            config = LineConfig(values)
            config.require_destination('group-1')
            with self.assertRaises(PermissionError):
                config.require_destination('group-2')
            session = _Session()
            delivery = SignedImageDelivery(config.image_base_url,
                                           config.image_signing_secret,
                                           config.image_roots)
            api = LineMessagingApi(config.channel_access_token, session)
            api.push_selected(
                'group-1',
                [{'uri': image, 'msg': str(index)} for index in range(6)],
                delivery,
                config,
            )
            self.assertEqual(2, len(session.calls))
            self.assertTrue(all(len(call[1]['json']['messages']) <= 5
                                for call in session.calls))

    def test_webhook_signature_uses_raw_body_and_extracts_group_id(self):
        body = b'{"events":[{"source":{"type":"group","groupId":"C123"}}]}'
        signature = hmac.new(b'secret', body, hashlib.sha256).digest()
        import base64
        signature = base64.b64encode(signature).decode('ascii')
        self.assertTrue(verify_signature('secret', body, signature))
        self.assertFalse(verify_signature('secret', body + b' ', signature))
        self.assertEqual(['C123'], extract_group_ids(json.loads(body.decode('utf-8'))))


if __name__ == '__main__':
    unittest.main()

