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
        except UnidentifiedImageError as error:
            # Skip only unrecognized source images. Storage/write failures should
            # still interrupt the run so they are not mistaken for bad photos.
            print('WARNING: unreadable source photo skipped: {0}: {1}'.format(
                pic, error))
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
