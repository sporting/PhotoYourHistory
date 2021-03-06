# -*- coding: UTF-8 -*-
from synology.FileParser import DirectoryHelper
from db.SaPhotoDB import dbPhotoHelper
from mysys.EvaluateTime import EvaluateTimeHelper
import sys

"""
    Daily monitor the new folder in monitored dirs.
"""

def maintainMonitorDir():
    """
        Search sub folder from the root dir in the database.
        Maintain the database.
    """
    print('maintainMonitorDir:')
    
    evalh = EvaluateTimeHelper()

    dbh = dbPhotoHelper()
    fdh = DirectoryHelper()
    rootdirs = dbh.getRootDirs()
    i = 0
    for rootdir in rootdirs:
        evalh.start(rootdir['DIR'])        
        folders = fdh.listHasFilesDirectories(rootdir['DIR'])     
        for folder in folders:
            i = i+1
            #print(str(i)+'. '+rootdir['DIR']+' : '+folder)                  
            dbh.insertDirIfNotExist((folder,False,False,None))    
        evalh.stop()

if __name__ == "__main__":
    maintainMonitorDir()
