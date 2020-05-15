# -*- coding: UTF-8 -*-
from datetime import datetime

class DateTimeHelper():
    DATETIME_FORMAT = '%Y:%m:%d %H:%M:%S'
    def timestampToDateTime(self,timestamp):
        try:
            return datetime.fromtimestamp(timestamp)
        except Exception as e:
            print(e)
            return None            

    def dateTimeToTimestamp(self,dt):
        try:
            return datetime.timestamp(dt)
        except Exception as e:
            print(e)
            return None

    def datetimeToStr(self,dt):
        try:
            return dt.strftime(self.DATETIME_FORMAT)
        except Exception as e:
            print(e)
            return None

    def strToDateTime(self,str):
        try:
            return datetime.strptime(str,self.DATETIME_FORMAT)
        except Exception as e:
            print(e)
            return None

    def getYear(self,dt):
        try:
            return dt.year
        except Exception as e:
            print(e)
            return None

    def getMonth(self,dt):
        try:
            return dt.month
        except Exception as e:
            print(e)
            return None

    def getDay(self,dt):
        try:
            return dt.day
        except Exception as e:
            print(e)
            return None       

    def getDateTimeAddYear(self,dt,num):     
        try:
            return datetime(dt.year+num,dt.month,dt.day)
        except Exception as e:
            print(e)
            return None       

    def formatDateTimeToSqliteYMD(self,dt):
        try:
            return dt.strftime('%Y-%m-%d')
        except Exception as e:
            print(e)
            return None

if __name__ == "__main__":
    helper = DateTimeHelper()
    t = helper.timestampToDateTime(1382189138.4196026)
    print(t)

                