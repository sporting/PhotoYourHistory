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

    def test_unrecognized_source_returns_none_without_deleting_original(self):
        contents = b'not actually a JPEG'
        with open(self.path, 'wb') as stream:
            stream.write(contents)
        self.assertIsNone(self.getter.thumbnail(self.path))
        with open(self.path, 'rb') as stream:
            self.assertEqual(contents, stream.read())

    def test_valid_source_generates_thumbnail(self):
        Image.new('RGB', (1200, 800)).save(self.path, 'JPEG')
        thumbnail = self.getter.thumbnail(self.path)
        self.assertTrue(os.path.isfile(thumbnail))
        with Image.open(thumbnail) as image:
            self.assertLessEqual(max(image.size), 1024)

    def test_existing_thumbnail_is_reused(self):
        thumb = os.path.join(self.temp.name, '@eaDir', 'photo.JPG',
                             'SYNOPHOTO_THUMB_XL.jpg')
        os.makedirs(os.path.dirname(thumb))
        with open(self.path, 'wb') as stream:
            stream.write(b'bad source')
        with open(thumb, 'wb') as stream:
            stream.write(b'existing thumbnail')
        self.assertEqual(thumb, self.getter.thumbnail(self.path))

    def test_missing_source_returns_none(self):
        self.assertIsNone(self.getter.thumbnail(self.path))

    def test_storage_failure_is_not_silenced(self):
        with open(self.path, 'wb') as stream:
            stream.write(b'source')
        with patch.object(self.getter.ImageHelper, 'thumbnail',
                          side_effect=PermissionError('write denied')):
            with self.assertRaises(PermissionError):
                self.getter.thumbnail(self.path)


if __name__ == '__main__':
    unittest.main()
