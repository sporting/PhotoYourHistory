# -*- coding: UTF-8 -*-
import os
from datetime import datetime
from db.SaPhotoDB import dbPhotoHelper
from date.TimeZoneHelper import TimeZoneHelper
from date.DateTimeHelper import DateTimeHelper
from graph.ExifHelper import ExifHelper
from synology.FileParser import ImageFileHelper

DefaultTimeZone = 'Asia/Taipei'

def IndexingNewImageFile(forcedAll=False):   
    dbh = dbPhotoHelper()
    tzh = TimeZoneHelper(DefaultTimeZone)
    dth = DateTimeHelper()
    exifh = ExifHelper()
    imgfh = ImageFileHelper()

    #default monitor folder
    #dirs = dbh.getDirs()
    #if len(dirs)<=0:
    #    dbh.insertDir((DefaultMonitorDir,True,None))
    dirs = dbh.getDirs()

    i = 0
    currentDT = tzh.getUTCTime(datetime.now())
    for d in dirs:
        lastParserUtc = d['PARSER_UTC_DATE']
        recursiveFalg = d['RECURSIVE'] == True
        lastParserLocalTimestamp=None
        #if lastParserUtc:
        #    lastParserUtcDT = dth.strToDateTime(lastParserUtc)
        #    lt = tzh.getLocalTime(lastParserUtcDT) 
        #    lastParserLocalTimestamp = dth.dateTimeToTimestamp(lt)
        if not forcedAll and lastParserUtc:
            continue

        files = imgfh.getFiles(d['DIR'],lastParserLocalTimestamp,recursiveFalg)
        for f in files:
            dd = os.path.dirname(f)
            fname = os.path.basename(f)   
            ext = os.path.splitext(fname)[1]         
            i = i + 1
            print(str(i)+': '+os.path.join(dd,fname))

            if not dbh.photoExists(dd,fname):
                meta = exifh.getExif(f)

                #there is no Exif information
                #if not meta:
                    #continue

                photoUtcDT = exifh.getGPSDateTime(meta)

                if photoUtcDT:
                    photoUtcDT = dth.strToDateTime(photoUtcDT)  
                    photoUtcDT = None if not photoUtcDT else tzh.UtcToUtcTime(photoUtcDT)                  
                else:
                    photoUtcDT = exifh.getDateTimeDigitizedDateTime(meta)
                    photoUtcDT = None if not photoUtcDT else dth.strToDateTime(photoUtcDT)                    
                    if not photoUtcDT:
                        photoUtcDT = exifh.getDateTimeOriginal(meta)
                        photoUtcDT = None if not photoUtcDT else dth.strToDateTime(photoUtcDT)
                        if not photoUtcDT:
                            photoUtcDT = exifh.getDateTime(meta)
                            photoUtcDT = None if not photoUtcDT else dth.strToDateTime(photoUtcDT) 
                    if photoUtcDT:
                        photoUtcDT = tzh.getUTCTime(photoUtcDT)

                ts = dth.dateTimeToTimestamp(photoUtcDT)

                cdate = os.path.getmtime(f)
                cLocalDT = dth.timestampToDateTime(cdate)
                createDT = tzh.getUTCTime(cLocalDT)

                gps = exifh.getGPS(meta)
                tz = DefaultTimeZone            
                if gps:
                    tz = tzh.getTimezone(gps)
            
                size_b=os.stat(f).st_size

                log = (fname,d['DIR'],dd,meta,ts,photoUtcDT,createDT,tz,gps,currentDT,'',ext,'','',size_b)
                dbh.insertPhoto(log)
            else:
                dbh.updatePhoto(dd,fname,currentDT)
        #update the last index utc datetime
        ct = tzh.getUTCTime(datetime.now())        
        dbh.updateDir(dth.datetimeToStr(ct),d['DIR'])
        dbh.obseletePhoto(d['DIR'],currentDT)

if __name__ == "__main__":
    IndexingNewImageFile()

