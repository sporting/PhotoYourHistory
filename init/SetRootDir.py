# -*- coding: UTF-8 -*-
import sys
import os

dir_path = os.path.dirname(os.path.realpath(__file__))
parent_dir_path = os.path.abspath(os.path.join(dir_path, os.pardir))
sys.path.insert(0, parent_dir_path)

from synology.FileParser import DirectoryHelper
from db.SaPhotoDB import dbPhotoHelper

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