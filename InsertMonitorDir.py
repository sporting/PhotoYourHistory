# -*- coding: UTF-8 -*-
import sys
from db.SaPhotoDB import dbPhotoHelper

"""
    Insert the monitor folder to database
"""

def InsertMonitorDir(folders):   
    dbh = dbPhotoHelper()
    for folder in folders:
        dbh.insertDir((folder,False,None))    

if __name__ == "__main__":
    if len(sys.argv[1:])>=1:
        InsertMonitorDir(sys.argv[1:])

