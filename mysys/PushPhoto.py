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
from im.TelegramBot import TelegramBot
from im.TelegramBotMedia import TelegramBotMedia
from im.TelegramMediaType import TelegramMediaType
from google.geoapi import GeoHelper
from mysys.EvaluateTime import EvaluateTimeHelper
from synology.VideoPlayerHelper import VideoPlayerHelper
from mysys.SMSType import SMSType
from itertools import groupby

"""
    Search photos in this date on the past several years
    and Line the random photos to someone who cares about this photo.
"""

DefaultTimeZone = 'Asia/Taipei'
timeHelper = EvaluateTimeHelper()

def GetManyYearPhotoDates(currentLocalDT):
    """
        From users care lists, to find out the past date.
        2020-05-20, 2019-05-20, 2018-05-20, 2017-05-20, 2016-05-20...etc
    """
    dbh = dbPhotoHelper()
    tzh = TimeZoneHelper(DefaultTimeZone)
    dth = DateTimeHelper()

    ts = dbh.getMinPhotoUtcTS()
    if not ts:
        return

    localUtcDateTime = dth.timestampToDateTime(ts)
    localDateTime = tzh.getLocalTime(localUtcDateTime)
    nowMonth = currentLocalDT.month
    nowDay = currentLocalDT.day

    for y in range(localDateTime.year,currentLocalDT.year+1):
        yield datetime(y,nowMonth,nowDay)

def GetVideosByVideoDates(videoDates,catalogs,randomVideosNumber):
    """
        Get the random video path in your video database.
    """    
    dbh = dbPhotoHelper()
    dth = DateTimeHelper()   
    tzh = TimeZoneHelper(DefaultTimeZone) 
    for dt in videoDates:
        #timeHelper.start('GetVideosByVideoDates')
        #ymd = dth.formatDateTimeToSqliteYMD(dt)
        ymdStart = tzh.getUTCTime(dt)
        ymdEnd = tzh.getUTCTime(dt+ timedelta(days=1))
        dataRows = dbh.getRandomVideoThisDayByCatalog(ymdStart,ymdEnd,randomVideosNumber,catalogs)
        #timeHelper.stop()
        yield (dt,map(lambda row: {'DIR':row['DIR'],'FILE_NAME':row['FILE_NAME']},dataRows))

def GetVideosThumbnail(videoFileNames):
    """
        Create and get your video thumbnail path.
    """
    thumbnailGetter = ImageThumbnailGetter()
    for yearData in videoFileNames:
        #adata=list(yearData[1])
        #timeHelper.start('GetPhotoThumbnail')  
        yield (yearData[0],map(lambda data:{'DIR':data['DIR'],'FILE_NAME':data['FILE_NAME'],'THUMBNAIL': thumbnailGetter.getThumbnail(os.path.join(data['DIR'],data['FILE_NAME'])) },yearData[1]))  
        #timeHelper.stop()

def GetPhotosByPhotoDates(photoDates,catalogs,randomPhotosNumber):
    """
        Get the random photo path in your photo database.
    """
    dbh = dbPhotoHelper()
    dth = DateTimeHelper()   
    tzh = TimeZoneHelper(DefaultTimeZone) 
    for dt in photoDates:
        #timeHelper.start('GetPhotosByPhotoDates')
        #ymd = dth.formatDateTimeToSqliteYMD(dt)
        ymdtsStart = dth.dateTimeToTimestamp(tzh.getUTCTime(dt))
        ymdtsEnd = dth.dateTimeToTimestamp(tzh.getUTCTime(dt+ timedelta(days=1)))
        dataRows = dbh.getRandomThisDayByCatalog(ymdtsStart,ymdtsEnd,randomPhotosNumber,catalogs)
        #timeHelper.stop()
        yield (dt,map(lambda row: {'DIR':row['DIR'],'FILE_NAME':row['FILE_NAME'],'GPS':row['GPS'],'GPS_ADDRESS':row['GPS_ADDRESS']},dataRows))

def GetPhotosThumbnail(photoFileNames):
    """
        Create and get your photo thumbnail path.
    """
    thumbnailGetter = ImageThumbnailGetter()
    for yearData in photoFileNames:
        #adata=list(yearData[1])
        #timeHelper.start('GetPhotoThumbnail')          
        yield (yearData[0],map(lambda data:{'DIR':data['DIR'],'FILE_NAME':data['FILE_NAME'],'GPS':data['GPS'],'GPS_ADDRESS':data['GPS_ADDRESS'],'THUMBNAIL': thumbnailGetter.thumbnail(os.path.join(data['DIR'],data['FILE_NAME'])) },yearData[1]))  
        #timeHelper.stop()

def CreateVideoMessage(oriYear,obj):
    duh = dbUsersHelper()
    ip,port = duh.getNasHostIPPort()
    account,pwd = duh.getNasLoginAccountPwd()

    by =datetime.now().year-oriYear
    msg = str(by)+' years ago' if by>1 else str(by)+' year ago'
    #picURI = obj['THUMBNAIL']
    basename = os.path.basename(obj['DIR'])
    msg = msg+"\n"+basename+"/"+obj['FILE_NAME']

    if ip and port and account and pwd:
        vph = VideoPlayerHelper(ip,port,account,pwd)        
        url = vph.getVideoViewUrl(obj['DIR'],obj['FILE_NAME'])
        #print(url)
        msg = msg+"\n\n 影片: "+url

    return msg

def CreatePhotoMessage(oriYear,obj):
    dbh = dbPhotoHelper()    
    duh = dbUsersHelper()
    apiKey =duh.getGoogleAPIKey()
    geoh = None
    if apiKey:
        geoh = GeoHelper(apiKey)

    by =datetime.now().year-oriYear
    msg = str(by)+' years ago' if by>1 else str(by)+' year ago'
    #picURI = obj['THUMBNAIL']
    basename = os.path.basename(obj['DIR'])
    msg = msg+"\n"+basename+"/"+obj['FILE_NAME']
    gps_address = obj['GPS_ADDRESS']
    gps = obj['GPS']
    if gps_address:
        msg = msg+ "\n"+gps_address
    elif gps:    
        if geoh:
            address =geoh.getNearAddress(gps)
            if address:
                msg = msg+ "\n"+address
                dbh.UpdateGeoAddress(obj['FILE_NAME'],obj['DIR'],address)
    return msg

def Push(users,memoryDate,randomPhotoNumbers):
    """
        Integrate all the processes.
        1. Get care list.
        2. GetManyYearPhotoDates
        3. GetPhotosByPhotoDates
        4. GetPhotoThumbnail
        5. Use google map api to find address which the photo taken with the data from photo exif gps information
        6. Use Line notify to remind you and enjoy it.
    """

    #memoryDate = datetime.today()
    duh = dbUsersHelper()
    #users = duh.getSMSUsers()
    #users = duh.getSMSUser(userId)
    noticeUsers = map(lambda user: (user,duh.getUserNotice(user['USER_ID'])),users)
    print(memoryDate)
    photoDates = list(GetManyYearPhotoDates(memoryDate))

    for noticeUser in noticeUsers:
        catalogs = list(map(lambda data: data['NOTICE_USER_ID'], noticeUser[1]))
        user = noticeUser[0]

        #photoFileNames=[]
        #photoThumbnails=[]
        #photoDates = GetManyYearPhotoDates(memoryDate,catalogs)
        photoFileNames = (GetPhotosByPhotoDates(photoDates,catalogs,randomPhotoNumbers))
        photoThumbnails = (GetPhotosThumbnail(photoFileNames))

        videoFileNames = GetVideosByVideoDates(photoDates,catalogs,randomPhotoNumbers)
        videoThumbnails = (GetVideosThumbnail(videoFileNames))

        print(user['USER_ID']+' '+user['SMS_TYPE'])
        print(catalogs)

        PhotoMessage = []
        VideoMessage = []

        for data in photoThumbnails:
            for obj in data[1]:
                photoMsg = CreatePhotoMessage(data[0].year,obj)
                picURI = obj['THUMBNAIL']
                if picURI:
                    print(picURI)
                    PhotoMessage.append({'year':data[0].year,'msg':str(photoMsg),'uri':picURI})
                    #statusCode = line.send(str(photoMsg),picURI)
                    #print(statusCode)
        for data in videoThumbnails:
            for obj in data[1]:
                videoMsg = CreateVideoMessage(data[0].year,obj)
                picURI = obj['THUMBNAIL']
                if picURI:
                    print(picURI)
                    VideoMessage.append({'year':data[0].year,'msg':str(videoMsg),'uri':picURI})
                    #statusCode = line.send(str(videoMsg),picURI)
                    #print(statusCode)

        token = user['SMS_ID']        
        if user['SMS_TYPE']==SMSType.LineNotify.value:
            line = LineNotify(token)
            for p in PhotoMessage:
                line.send(p['msg'],p['uri'])
            for v in VideoMessage:
                line.send(v['msg'],v['uri'])
        elif user['SMS_TYPE']==SMSType.TelegramBot.value:
            botToken = duh.getTelegramBotAccessToken()
            if not botToken:
                print('Must set telegram bot access token. Please type \'python SetBotToken.py [ACCESS_TOKEN]\'')
                continue
            bot = TelegramBot(botToken,token)

            for key, groups in groupby(PhotoMessage, lambda photo : photo['year']):
                gPhoto = list(groups)
                if len(gPhoto)<=1:
                    bot.sendPhoto(gPhoto[0]['uri'],gPhoto[0]['msg'])
                else:
                    gPhotos = []
                    for g in gPhoto:
                        gPhotos.append(TelegramBotMedia(TelegramMediaType.Photo,g['uri'],g['msg']))
                    r=bot.sendMediaGroup(gPhotos)
                    #print(r)

            for v in VideoMessage:
                #bot.sendText(v['msg'])
                bot.sendPhoto(v['uri'],v['msg'])


if __name__ == "__main__":
    MainProcessSengMsg()