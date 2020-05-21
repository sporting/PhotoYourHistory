# -*- coding: UTF-8 -*-
import os
import fnmatch
from datetime import datetime

"""
    Class logic depends on the synology nas.
"""

class DirectoryHelper:
    def listHasFilesDirectories(self,path):
        """
            List all directories that contain files
            except #eaDir, #recycle, #.thumbnail
        """
        for p,d,f in os.walk(path):
            #for synology nas 
            if p.find('/@eaDir')<0 and p.find('/#recycle')<0 and p.find('/.thumbnail')<0 and (len(f)>0):
                yield p

#mtime modify date
#ctime create date
#atime access date
class ImageFileHelper:
    #windows is case insensitive, windows will run twice *.jpg&*.JPG
    #Linux is case sensitive
    EXTENSIONS = ['*.jpg', '*.jpeg', '*.png','*.JPG','*.JPEG','*.PNG'] 
    def getFiles(self,path,localtimestamp=None,recursive=False):
        """
            List image files
        """
        for dirPath, dirNames, fileNames in os.walk(path):
            for ext in self.EXTENSIONS:
                for filename in fnmatch.filter(fileNames, ext):                    
                    filepath = os.path.join(dirPath, filename)
                    #only find new file by access time (atime)
                    if localtimestamp:
                        atime = os.path.getatime(filepath)
                        if atime>=localtimestamp:
                            yield filepath 
                    else:
                        yield filepath

            if not recursive:
                break

class VideoFileHelper:
    EXTENSIONS = ['*.avi','*.AVI','*.mpg','*.MPG','*.mpeg','*.MPEG','*.mov','*.MOV','*.mp4','*.MP4','*.wmv','*.WMV',
    '*.m2t','*.M2T','*.m2ts','*.M2TS','*.mts','*.MTS','*.asf','*.ASF','*.swf','*.SWF','*.3gp','*.3GP','*.3gp2','*.3GP2','*.rm','*.RM','*.qt','*.QT'] 
    def getFiles(self,path,localtimestamp=None,recursive=False):
        """
            List image files
        """
        for dirPath, dirNames, fileNames in os.walk(path):
            for ext in self.EXTENSIONS:
                for filename in fnmatch.filter(fileNames, ext):                    
                    filepath = os.path.join(dirPath, filename)
                    #only find new file by access time (atime)
                    if localtimestamp:
                        atime = os.path.getatime(filepath)
                        if atime>=localtimestamp:
                            yield filepath 
                    else:
                        yield filepath

            if not recursive:
                break

if __name__ == "__main__":
    helper = ImageHelper()
    d = datetime(2020, 5, 6, 0, 0)
    ts = datetime.timestamp(d)
    ff = helper.getFiles('D:\\private\\WorkArea\\PhotoThisDay\\',ts,recursive=True)
    print(list(ff))
