# -*- coding: UTF-8 -*-
from synology.FileParser import DirectoryHelper
from db.SaPhotoDB import dbPhotoHelper
import sys

"""
    Insert the root folder to database
"""

def InsertRootDir(folders):   
    dbh = dbPhotoHelper()
    for folder in folders:
        dbh.insertDirIfNotExist((folder,True,False,None))    

if __name__ == "__main__":
    if len(sys.argv[1:])>=1:
        InsertRootDir(sys.argv[1:])