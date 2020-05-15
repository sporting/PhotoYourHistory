# -*- coding: UTF-8 -*-

import os
from graph.ImageProcess import ImageProcessHelper

class ImageThumbnailGetter:
    ImageHelper = ImageProcessHelper()
    def thumbnail(self,pic):                      
        print(pic)
        if os.path.exists(pic):
            dd = os.path.dirname(pic)
            fname = os.path.basename(pic)   
            f = os.path.join(dd,'@eaDir',fname,'SYNOPHOTO_THUMB_XL.jpg')
            if  os.path.exists(f):
                return f
            else:
                print(fname+" not exist")
                thumbnailFolder = os.path.join(dd,'@eaDir',fname)
                return self.ImageHelper.thumbnail(pic,(1024,1024),thumbnailFolder,'SYNOPHOTO_THUMB_XL.jpg')
        return None

if __name__ == "__main__":
    helper = ImageThumbnailGetter()
    res = helper.thumbnail('D:/private/workarea/PhotoThisDay/res/IMG_20200330_192704.jpg')
    print(res)