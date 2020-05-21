# -*- coding: UTF-8 -*-
import os
from datetime import datetime
from db.SaPhotoDB import dbPhotoHelper
from date.TimeZoneHelper import TimeZoneHelper
from date.DateTimeHelper import DateTimeHelper
from synology.FileParser import VideoFileHelper
from db.MyCatalogEncoder import MyCatalogEncoder

"""
    Parse all the photos from your monitor folders in database.
    Extract every video information, then store in database.
"""

DefaultTimeZone = 'Asia/Taipei'

def IndexingAllVideos():   
    """
        Monitor the changed photos from the last parser time.
    """
    dbh = dbPhotoHelper()
    tzh = TimeZoneHelper(DefaultTimeZone)
    dth = DateTimeHelper()
    videofh = VideoFileHelper()

    dirs = dbh.getMonitorDirs()

    i = 0
    j = 0
    currentDT = tzh.getUTCTime(datetime.now())
    for d in dirs:
        files = videofh.getFiles(d['DIR'],None,False)
        for f in files:
            dd = os.path.dirname(f)
            fname = os.path.basename(f)   
            ext = os.path.splitext(fname)[1]         

            i = i + 1
            print(str(i)+': Insert:'+os.path.join(dd,fname))           

            cdate = os.path.getmtime(f)
            cLocalDT = dth.timestampToDateTime(cdate)
            createDT = tzh.getUTCTime(cLocalDT)
            tz = DefaultTimeZone            
            size_b=os.stat(f).st_size
            log = (fname,d['DIR'],dd,createDT,tz,currentDT,ext,size_b)
            dbh.insertVideoIfNotExist(log,cls=MyCatalogEncoder)

if __name__ == "__main__":
    IndexingAllVideos()

