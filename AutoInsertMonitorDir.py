# -*- coding: UTF-8 -*-
from synology.FileParser import DirectoryHelper
from db.SaPhotoDB import dbPhotoHelper
import sys

"""
    Prepare your photo database.
    List photo folders that you want to monitor in nas.
"""

def autoInsertMonitorDir(rootdir):
    """
        Search sub folder in the root folder that contains some files.
        Maintain the database.
    """
    dbh = dbPhotoHelper()
    fdh = DirectoryHelper()
    folders = fdh.listHasFilesDirectories(rootdir)  
    
    for folder in folders:
        print(folder)
        dbh.insertDir((folder,False,None))    

if __name__ == "__main__":
    if len(sys.argv[1:])>=1:
        ps = sys.argv[1:]
        for p in ps:
            autoInsertMonitorDir(p)
