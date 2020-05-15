# -*- coding: UTF-8 -*-
import os
import fnmatch
from datetime import datetime

class DirectoryHelper:
    #list all directories contain files
    def listHasFilesDirectories(self,path):
        for p,d,f in os.walk(path):
            #for synology nas 
            if p.find('/@eaDir')<0 and p.find('/#recycle')<0 and p.find('/.thumbnail')<0 and (len(f)>0):
                yield p


#mtime modify date
#ctime create date
#atime access date
class ImageFileHelper:
    EXTENSIONS = ['*.jpg', '*.jpeg', '*.png'] 
    def getFiles(self,path,localtimestamp=None,recursive=False):
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
