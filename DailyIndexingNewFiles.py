# -*- coding: UTF-8 -*-
import os
from datetime import datetime
from db.SaPhotoDB import dbPhotoHelper
from date.TimeZoneHelper import TimeZoneHelper
from date.DateTimeHelper import DateTimeHelper
from graph.ExifHelper import ExifHelper
from synology.FileParser import ImageFileHelper
from synology.FileParser import VideoFileHelper

from db.MyCatalogEncoder import MyCatalogEncoder
"""
    Parse all the photos from your monitor folders in database.
    Extract every photo information and exif, then store in database.
"""

DefaultTimeZone = 'Asia/Taipei'
dbh = dbPhotoHelper()
tzh = TimeZoneHelper(DefaultTimeZone)
dth = DateTimeHelper()
dirs = dbh.getMonitorDirs()

def VideoProcess(DIR,BatchProcessDateTime,recursiveFalg):
    videofh = VideoFileHelper()

    i = 0
    j = 0
    files = videofh.getFiles(DIR,None,recursiveFalg)
    for f in files:
        dd = os.path.dirname(f)
        fname = os.path.basename(f)   
        ext = os.path.splitext(fname)[1]         

        if not dbh.videoExists(dd,fname):
            i = i + 1
            print(str(i)+': Insert:'+os.path.join(dd,fname))           

            cdate = os.path.getmtime(f)
            cLocalDT = dth.timestampToDateTime(cdate)
            createDT = tzh.getUTCTime(cLocalDT)
            tz = DefaultTimeZone            
            size_b=os.stat(f).st_size
            log = (fname,DIR,dd,createDT,tz,BatchProcessDateTime,ext,size_b)
            dbh.insertVideo(log,cls=MyCatalogEncoder)    
        else:
            j = j + 1
            print(str(j)+': Update:'+os.path.join(dd,fname))   
            dbh.updateVideo(dd,fname,BatchProcessDateTime)        

def ImagesProcess(DIR,BatchProcessDateTime,recursiveFalg):
    imgfh = ImageFileHelper()
    exifh = ExifHelper()
    i = 0
    j = 0
    files = list(imgfh.getFiles(DIR,None,recursiveFalg))
    for f in files:
        dd = os.path.dirname(f)
        fname = os.path.basename(f)   
        ext = os.path.splitext(fname)[1]         
        ts = None
        if not dbh.photoExists(dd,fname):
            i = i + 1
            print(str(i)+': Insert:'+os.path.join(dd,fname))           
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
            log = (fname,DIR,dd,meta,ts,photoUtcDT,createDT,tz,gps,BatchProcessDateTime,'',ext,'',size_b)
            dbh.insertPhoto(log,cls=MyCatalogEncoder)
            #dbh.insertPhoto(log)
        else:
            j = j + 1
            print(str(j)+': Update:'+os.path.join(dd,fname))   
            dbh.updatePhoto(dd,fname,BatchProcessDateTime)

def DailyIndexingNewImageFile():   
    """
        Monitor the changed photos from the last parser time.
    """
    currentDT = tzh.getUTCTime(datetime.now())
    for d in dirs:
        lastParserUtc = d['PARSER_UTC_DATE']
        recursiveFalg = d['RECURSIVE'] == True
        lastParserLocalTimestamp=None
        if lastParserUtc:
            if not os.path.exists(d['DIR']):
                print(str(d['DIR'])+' folder is not exists')
                continue            
            dirTimestamp =  os.path.getmtime(d['DIR'])
            dirTime = dth.timestampToDateTime(dirTimestamp)
            dirUtcTime = tzh.getUTCTime(dirTime)
            dirUtcTimestamp = dth.dateTimeToTimestamp(dirUtcTime)
            lastParserUtcTimestamp = dth.dateTimeToTimestamp(dth.strToDateTime2(lastParserUtc))
            #print('Compare(DIR_DT,PARSER_DT): ('+str(dirUtcTime)+','+str(lastParserUtc)+')')
            #print('CompareTS(DIR_DT,PARSER_DT): ('+str(dirUtcTimestamp)+','+str(lastParserUtcTimestamp)+')')
            if not (dirUtcTimestamp>= lastParserUtcTimestamp):
                print(d['DIR']+' pass!')
                continue

        ImagesProcess(d['DIR'],currentDT,recursiveFalg)
        VideoProcess(d['DIR'],currentDT,recursiveFalg)

        #update the last index utc datetime 
        dbh.updateDir(currentDT,d['DIR'])

        dbh.obseletePhoto(d['DIR'],currentDT)
        dbh.obseleteVideo(d['DIR'],currentDT)

if __name__ == "__main__":
    DailyIndexingNewImageFile()

