# -*- coding: UTF-8 -*-
import os
from PIL import Image


class SourcePhotoDecodeError(Exception):
    """Known malformed image data; never used for filesystem failures."""


_DECODE_ERROR_PREFIXES = (
    'Truncated File Read',
    'image file is truncated',
    'broken data stream when reading image file',
)


def _is_corrupt_image(error):
    # Decode errors emitted by Pillow lack an OS errno. Do not hide genuine
    # storage, permission, or NAS read errors, even during image decoding.
    return (error.errno is None and
            str(error).startswith(_DECODE_ERROR_PREFIXES))


class ImageProcessHelper:
    def thumbnail(self, pic, tsize, tmpFolder, newName):
        """Create a derived thumbnail; never modify the source photo."""
        try:
            image = Image.open(pic)
        except OSError as error:
            if _is_corrupt_image(error):
                raise SourcePhotoDecodeError(str(error)) from error
            raise

        with image:
            try:
                image.thumbnail(tsize)
                # Decode completely before creating a folder or writing output.
                image.load()
            except OSError as error:
                if _is_corrupt_image(error):
                    raise SourcePhotoDecodeError(str(error)) from error
                raise

            os.makedirs(tmpFolder, exist_ok=True)
            newfilename = os.path.join(tmpFolder, newName)
            image.save(newfilename)

        return newfilename


if __name__ == '__main__':
    helper = ImageProcessHelper()
    res = helper.thumbnail('D:/private/workarea/PhotoThisDay/res/IMG_20200330_192704.jpg',
                           (1024, 1024), 'D:/private/workarea/PhotoThisDay/res/.thumbnail/',
                           'SYNOPHOTO_THUMB_XL.jpg')
    print(res)
