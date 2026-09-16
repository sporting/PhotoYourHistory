# -*- coding: UTF-8 -*-

import os
from PIL import UnidentifiedImageError
from graph.ImageProcess import ImageProcessHelper

"""
    Get the photo thumbnail.
    If Synology already has one, use it; otherwise create one.
"""

class ImageThumbnailGetter:
    ImageHelper = ImageProcessHelper()

    def thumbnail(self, pic):
        if not os.path.exists(pic):
            return None

        dd = os.path.dirname(pic)
        fname = os.path.basename(pic)
        f = os.path.join(dd, '@eaDir', fname, 'SYNOPHOTO_THUMB_XL.jpg')
        if os.path.exists(f):
            return f

        print('Thumbnail missing; generating: {0}'.format(pic))
        thumbnailFolder = os.path.join(dd, '@eaDir', fname)
        try:
            return self.ImageHelper.thumbnail(pic, (1024, 1024), thumbnailFolder,
                                              'SYNOPHOTO_THUMB_XL.jpg')
        except (UnidentifiedImageError, OSError, ValueError) as error:
            # A damaged or unsupported source must not abort other photos/users.
            # Only source-image decoding failures should be skipped. Output write
            # failures must still propagate so operators can address storage issues.
            if os.path.exists(f):
                raise
            print('WARNING: thumbnail unavailable for {0}: {1}: {2}'.format(
                pic, type(error).__name__, error))
            return None

    def getThumbnail(self, pic):
        if os.path.exists(pic):
            dd = os.path.dirname(pic)
            fname = os.path.basename(pic)
            f = os.path.join(dd, '@eaDir', fname, 'SYNOPHOTO_THUMB_XL.jpg')
            if os.path.exists(f):
                return f
        return None

if __name__ == "__main__":
    helper = ImageThumbnailGetter()
    res = helper.thumbnail('D:/private/workarea/PhotoThisDay/res/IMG_20200330_192704.jpg')
