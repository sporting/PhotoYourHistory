# -*- coding: UTF-8 -*-
import os
from datetime import datetime
from datetime import timedelta  
from db.SaPhotoDB import dbPhotoHelper
from db.SaUsersDB import dbUsersHelper
from date.TimeZoneHelper import TimeZoneHelper
from date.DateTimeHelper import DateTimeHelper
from synology.ImageGetter import ImageThumbnailGetter
from im.LineNotify import LineNotify
from google.geoapi import GeoHelper
from mysys.EvaluateTime import EvaluateTimeHelper

DefaultTimeZone = 'Asia/Taipei'
timeHelper = EvaluateTimeHelper()

def GetManyYearPhotoDates(currentLocalDT,catalogs):
    dbh = dbPhotoHelper()
    tzh = TimeZoneHelper(DefaultTimeZone)
    dth = DateTimeHelper()

    ts = dbh.getMinPhotoUtcTSByCatalog(catalogs)
    if not ts:
        return

    localUtcDateTime = dth.timestampToDateTime(ts)
    localDateTime = tzh.getLocalTime(localUtcDateTime)
    nowMonth = currentLocalDT.month
    nowDay = currentLocalDT.day

    for y in range(localDateTime.year,currentLocalDT.year+1):
        #print(datetime(y,nowMonth,nowDay))    
        yield datetime(y,nowMonth,nowDay)

def GetPhotosByPhotoDates(photoDates,catalogs):
    dbh = dbPhotoHelper()
    dth = DateTimeHelper()   
    tzh = TimeZoneHelper(DefaultTimeZone) 
    for dt in photoDates:
        timeHelper.start('GetPhotosByPhotoDates')
        #ymd = dth.formatDateTimeToSqliteYMD(dt)
        ymdtsStart = dth.dateTimeToTimestamp(tzh.getUTCTime(dt))
        ymdtsEnd = dth.dateTimeToTimestamp(tzh.getUTCTime(dt+ timedelta(days=1)))
        dataRows = dbh.getRandomThisDayByCatalog(ymdtsStart,ymdtsEnd,2,catalogs)
        timeHelper.stop()
        yield (dt,map(lambda row: {'DIR':row['DIR'],'FILE_NAME':row['FILE_NAME'],'GPS':row['GPS']},dataRows))

def GetPhotoThumbnail(photoFileNames):
    thumbnailGetter = ImageThumbnailGetter()
    for yearData in photoFileNames:
        #adata=list(yearData[1])
        timeHelper.start('GetPhotoThumbnail')  
        yield (yearData[0],map(lambda data:{'DIR':data['DIR'],'FILE_NAME':data['FILE_NAME'],'GPS':data['GPS'],'THUMBNAIL': thumbnailGetter.thumbnail(os.path.join(data['DIR'],data['FILE_NAME'])) },yearData[1]))  
        timeHelper.stop()

def MainProcessSengMsg():
    memoryDate = datetime.today()

    duh = dbUsersHelper()
    users = duh.getSMSUsers()
    noticeUsers = map(lambda user: (user,duh.getUserNotice(user['USER_ID'])),users)

    apiKey =duh.getGoogleAPIKey()

    geoh = GeoHelper(apiKey)

    for noticeUser in noticeUsers:
        catalogs = list(map(lambda data: data['NOTICE_USER_ID'], noticeUser[1]))
        user = noticeUser[0]
        photoDates = GetManyYearPhotoDates(memoryDate,catalogs)
        photoFileNames = GetPhotosByPhotoDates(photoDates,catalogs)
        photoThumbnails = GetPhotoThumbnail(photoFileNames)
        print(user['USER_ID'])
        print(catalogs)
        if user['SMS_TYPE']=='LINE NOTIFY':
            token = user['SMS_ID']
            
            line = LineNotify(token)
            for data in photoThumbnails:
                for obj in data[1]:
                    by =datetime.now().year-data[0].year
                    msg = "\n"+str(by)+' years ago' if by>1 else "\n"+str(by)+' year ago'
                    picURI = obj['THUMBNAIL']
                    basename = os.path.basename(obj['DIR'])
                    msg = msg+"\n"+basename
                    gps = obj['GPS']
                    if gps:
                        address =geoh.getNearAddress(gps)
                        if address:
                            msg = msg+ "\n"+address
                    print(picURI)
                    line.send(str(msg),picURI)

if __name__ == "__main__":
    MainProcessSengMsg()