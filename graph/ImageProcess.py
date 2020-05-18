# -*- coding: UTF-8 -*-
import os
from PIL import Image

"""
    class uses to process the image
"""

class ImageProcessHelper:    
    #pic type is string
    #tsize type is tuple (1024,1024)
    #tmpFolder type is string
    def thumbnail(self,pic,tsize,tmpFolder,newName):
        """
            create thumbnail in assigned folder.
        """
        if not os.path.exists(tmpFolder):    
            os.makedirs(tmpFolder, exist_ok=True) 

        #basename = os.path.basename(pic)
        newfilename = os.path.join(tmpFolder,newName)

        im = Image.open(pic)
        im.thumbnail(tsize)
        im.save(newfilename)
        im.close()

        return newfilename

if __name__ == "__main__":
    helper = ImageProcessHelper()
    res = helper.thumbnail('D:/private/workarea/PhotoThisDay/res/IMG_20200330_192704.jpg',(1024,1024),'D:/private/workarea/PhotoThisDay/res/.thumbnail/')
    print(res)
