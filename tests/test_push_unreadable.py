"""Exercise PushPhoto.Push with mocked databases and Telegram transport."""
import datetime
import os
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image
from mysys import PushPhoto as service


class PushUnreadableTests(unittest.TestCase):
    def test_bad_then_good_photo_and_next_recipient_are_sent(self):
        with tempfile.TemporaryDirectory() as folder:
            bad = os.path.join(folder, 'broken.JPG')
            first_good = os.path.join(folder, 'first-good.JPG')
            second_good = os.path.join(folder, 'second-good.JPG')
            for photo in (bad, first_good, second_good):
                Image.new('RGB', (1200, 800)).save(photo, 'JPEG')
            with open(bad, 'rb') as stream:
                original = stream.read()[:128]
            with open(bad, 'wb') as stream:
                stream.write(original)

            users = [{'USER_ID': 'first', 'SMS_TYPE': service.SMSType.TelegramBot.value,
                      'SMS_ID': 'first-id'},
                     {'USER_ID': 'second', 'SMS_TYPE': service.SMSType.TelegramBot.value,
                      'SMS_ID': 'second-id'}]
            dates = [datetime.datetime(2012, 9, 16)]

            def photos(_, catalogs, __):
                selected = [bad, first_good] if catalogs == ['first'] else [second_good]
                yield (dates[0], ({'DIR': os.path.dirname(path),
                                   'FILE_NAME': os.path.basename(path),
                                   'GPS': None, 'GPS_ADDRESS': None}
                                  for path in selected))

            with patch.object(service, 'dbUsersHelper') as users_db, \
                 patch.object(service, 'GetManyYearPhotoDates', return_value=dates), \
                 patch.object(service, 'GetPhotosByPhotoDates', side_effect=photos), \
                 patch.object(service, 'GetVideosByVideoDates', return_value=iter(())), \
                 patch.object(service, 'CreatePhotoMessage', return_value='test photo'), \
                 patch.object(service, 'TelegramBot') as telegram:
                users_db.return_value.getUserNotice.side_effect = lambda uid: [
                    {'NOTICE_USER_ID': uid}]
                users_db.return_value.getTelegramBotAccessToken.return_value = 'fake-token'
                service.Push(users, datetime.datetime(2026, 9, 16), 3)

            self.assertEqual(2, telegram.call_count)
            self.assertEqual(['first-id', 'second-id'],
                             [call.args[1] for call in telegram.call_args_list])
            self.assertEqual(2, telegram.return_value.sendPhoto.call_count)
            sent_paths = [call.args[0]
                          for call in telegram.return_value.sendPhoto.call_args_list]
            self.assertIn('first-good.JPG', sent_paths[0])
            self.assertIn('second-good.JPG', sent_paths[1])
            self.assertFalse(any('broken.JPG' in path for path in sent_paths))
            with open(bad, 'rb') as stream:
                self.assertEqual(original, stream.read())
            self.assertFalse(os.path.exists(os.path.join(
                folder, '@eaDir', 'broken.JPG')))


if __name__ == '__main__':
    unittest.main()
