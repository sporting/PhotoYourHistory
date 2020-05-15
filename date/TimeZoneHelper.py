# -*- coding: UTF-8 -*-
from timezonefinder import TimezoneFinder
from datetime import datetime
from pytz import timezone

class TimeZoneHelper:
    def __init__(self,localTimeZone):
        self.tf = TimezoneFinder()
        self.LocalTimeZone = localTimeZone

    def getTimezone(self,lnglatStr):
        if lnglatStr:            
            t = lnglatStr.split(",")
            if len(t)==2:
                latitude, longitude = float(t[0]), float(t[1])
                return self.tf.timezone_at(lng=longitude, lat=latitude) # returns 'Europe/Berlin'

    #depend on the setting localTimeZone when construct
    #return Local Date Time
    def getLocalTime(self,utcTime):
        return self.zoneUtcToLocalTime(self.LocalTimeZone,utcTime)

    #depend on the setting localTimeZone when construct
    #return UTC Date Time
    def getUTCTime(self,localTime):
        UTC = timezone('UTC')        
        locationZone = timezone(self.LocalTimeZone)
        return locationZone.localize(localTime).astimezone(UTC)

    #gps to local datetime
    def gpsUtcToLocalTime(self,lnglatStr,utcTime):
        zone = self.getTimezone(lnglatStr)
        return self.zoneUtcToLocalTime(zone,utcTime)

    #timezone to local datetime
    def zoneUtcToLocalTime(self,zone,utcTime):
        UTC = timezone('UTC')        
        locationZone = timezone(zone)
        return UTC.localize(utcTime).astimezone(locationZone)

    #timezone to local datetime
    def UtcToUtcTime(self,utcTime):
        UTC = timezone('UTC')        
        locationZone = timezone('UTC')
        return UTC.localize(utcTime).astimezone(locationZone)
if __name__ == "__main__":
    helper = TimeZoneHelper()
    zone = helper.getTimezone('25.088791666666665, 121.46666666666667')
    print(zone)    
    
    t = helper.zoneUtcToLocalTime(zone,datetime.now())
    print(t)
                