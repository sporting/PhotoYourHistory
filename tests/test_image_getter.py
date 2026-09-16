import errno
import hashlib
import os
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image
from synology.ImageGetter import ImageThumbnailGetter


class ImageThumbnailGetterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = os.path.join(self.temp.name, 'photo.JPG')
        self.getter = ImageThumbnailGetter()

    def _save_source(self, path=None):
        path = path or self.path
        Image.new('RGB', (1200, 800)).save(path, 'JPEG')
        return path

    def _thumbnail_folder(self, path=None):
        path = path or self.path
        return os.path.join(os.path.dirname(path), '@eaDir',
                            os.path.basename(path))

    def test_unrecognized_source_returns_none_without_deleting_original(self):
        contents = b'not actually a JPEG'
        with open(self.path, 'wb') as stream:
            stream.write(contents)
        self.assertIsNone(self.getter.thumbnail(self.path))
        with open(self.path, 'rb') as stream:
            self.assertEqual(contents, stream.read())
        self.assertFalse(os.path.exists(self._thumbnail_folder()))

    def test_truncated_jpeg_skipped_and_original_unchanged(self):
        self._save_source()
        with open(self.path, 'rb') as stream:
            contents = stream.read()[:128]
        with open(self.path, 'wb') as stream:
            stream.write(contents)
        before = hashlib.sha256(contents).hexdigest()
        self.assertIsNone(self.getter.thumbnail(self.path))
        with open(self.path, 'rb') as stream:
            self.assertEqual(before, hashlib.sha256(stream.read()).hexdigest())
        self.assertFalse(os.path.exists(self._thumbnail_folder()))

    def test_valid_source_generates_thumbnail(self):
        self._save_source()
        thumbnail = self.getter.thumbnail(self.path)
        self.assertTrue(os.path.isfile(thumbnail))
        with Image.open(thumbnail) as image:
            self.assertLessEqual(max(image.size), 1024)

    def test_existing_thumbnail_is_reused(self):
        thumb = os.path.join(self._thumbnail_folder(), 'SYNOPHOTO_THUMB_XL.jpg')
        os.makedirs(os.path.dirname(thumb))
        with open(self.path, 'wb') as stream:
            stream.write(b'bad source')
        with open(thumb, 'wb') as stream:
            stream.write(b'existing thumbnail')
        self.assertEqual(thumb, self.getter.thumbnail(self.path))

    def test_missing_source_returns_none(self):
        self.assertIsNone(self.getter.thumbnail(self.path))

    def test_source_os_error_with_errno_propagates(self):
        self._save_source()
        with patch('graph.ImageProcess.Image.open',
                   side_effect=OSError(errno.EIO, 'NAS read failed')):
            with self.assertRaises(OSError) as raised:
                self.getter.thumbnail(self.path)
        self.assertEqual(errno.EIO, raised.exception.errno)
        self.assertFalse(os.path.exists(self._thumbnail_folder()))

    def test_source_permission_error_propagates(self):
        self._save_source()
        with patch('graph.ImageProcess.Image.open',
                   side_effect=PermissionError(errno.EACCES, 'access denied')):
            with self.assertRaises(PermissionError):
                self.getter.thumbnail(self.path)

    def test_decode_stage_nas_io_error_propagates(self):
        self._save_source()
        with patch.object(Image.Image, 'thumbnail',
                          side_effect=OSError(errno.EIO, 'NAS read failed')):
            with self.assertRaises(OSError):
                self.getter.thumbnail(self.path)
        self.assertFalse(os.path.exists(self._thumbnail_folder()))

    def test_unknown_os_error_propagates(self):
        self._save_source()
        with patch.object(Image.Image, 'thumbnail',
                          side_effect=OSError('unexpected decoding error')):
            with self.assertRaises(OSError):
                self.getter.thumbnail(self.path)

    def test_storage_failure_is_not_silenced(self):
        self._save_source()
        with patch.object(Image.Image, 'save',
                          side_effect=PermissionError(errno.EACCES, 'write denied')):
            with self.assertRaises(PermissionError):
                self.getter.thumbnail(self.path)

    def test_disk_full_is_not_silenced(self):
        self._save_source()
        with patch.object(Image.Image, 'save',
                          side_effect=OSError(errno.ENOSPC, 'disk full')):
            with self.assertRaises(OSError) as raised:
                self.getter.thumbnail(self.path)
        self.assertEqual(errno.ENOSPC, raised.exception.errno)

    def test_corrupt_then_valid_across_two_recipients(self):
        bad = self.path
        self._save_source()
        with open(bad, 'rb') as stream:
            contents = stream.read()[:128]
        with open(bad, 'wb') as stream:
            stream.write(contents)
        good = self._save_source(os.path.join(self.temp.name, 'good.JPG'))
        second = self._save_source(os.path.join(self.temp.name, 'second.JPG'))
        delivered = []
        for recipient, photos in [('first', [bad, good]), ('second', [second])]:
            for photo in photos:
                thumb = self.getter.thumbnail(photo)
                if thumb:
                    delivered.append((recipient, thumb))
        self.assertEqual(['first', 'second'], [item[0] for item in delivered])
        self.assertTrue(all(os.path.isfile(item[1]) for item in delivered))
        with open(bad, 'rb') as stream:
            self.assertEqual(contents, stream.read())


if __name__ == '__main__':
    unittest.main()
