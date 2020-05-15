# -*- coding: UTF-8 -*-
import os
from datetime import datetime
from SaPhotoDB import dbPhotoHelper
from TimeZoneHelper import TimeZoneHelper
from DateTimeHelper import DateTimeHelper
from ExifHelper import ExifHelper
from FileParser import ImageFileHelper

exifh=ExifHelper()
dth=DateTimeHelper()
tzh=TimeZoneHelper('Asia/Taipei')
dbh=dbPhotoHelper()

cur = dbh.conn.cursor()
cur.execute('''select * from photos where photo_utc_date is null''')
rows=cur.fetchall()

for row in rows:
    id=row['ID']
    f=os.path.join(row['DIR'],row['FILE_NAME'])
    print(f)
    meta = exifh.getExif(f)
    if not meta:
        continue
    photoUtcDT=exifh.getGPSDateTime(meta)
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

    cdate = os.path.getmtime(f)
    cLocalDT = dth.timestampToDateTime(cdate)
    createDT = tzh.getUTCTime(cLocalDT)
    gps = exifh.getGPS(meta)
    tz = 'Asia/Taipei'
    if gps:
        tz = tzh.getTimezone(gps)

    cur.execute('''update photos set photo_utc_date=?,GPS=?,TIME_ZONE=? where id=?''',(photoUtcDT,gps,tz,id))    
    dbh.conn.commit()


