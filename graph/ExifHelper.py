# -*- coding: UTF-8 -*-
from PIL import Image, ExifTags
from PIL.ExifTags import TAGS, GPSTAGS
from datetime import datetime
from pytz import timezone

"""
    class uses to fetch and process the image exif information
"""

class ExifHelper:
    DATETIME_FORMAT = '%Y:%m:%d %H:%M:%S' # YYYY-MM-DD HH:MM:SS
    TAG_SKIP_MARKERNOTE='MakerNote'
    TAG_GPSDATESTAMP = 'GPSDateStamp'
    TAG_GPSTIMESTAMP = 'GPSTimeStamp'
    TAG_GPS_LATITUDE_REF = 'GPSLatitudeRef'
    TAG_GPS_LONGTITUDE_REF = 'GPSLongitudeRef'
    TAG_GPS_LATITUDE = 'GPSLatitude'
    TAG_GPS_LONGTITUDE = 'GPSLongitude'
    TAG_GPS_INFO = 'GPSInfo'
    KEY_GPSDT = 'GpsDateTime'    
    KEY_GPS = 'GPSGeo'
    KEY_DateTimeDigitized = 'DateTimeDigitized'
    KEY_DateTimeOriginal = 'DateTimeOriginal'
    KEY_DateTime = 'DateTime'
    UTC = timezone('UTC')

    def getExif(self,filename):
        try:
            img = Image.open(filename)
            exif_info = img._getexif()
        except Exception as e:
            print('getExif:'+str(e))
            return

        res = {}
        gps_date = None
        gps_time = None
        exif_date = None
        gps_E = None
        gps_N = None
        gps_Long = None
        gps_Lat = None 
        if not exif_info:
            return

        for tag, val in exif_info.items():
            try:
                key = TAGS.get(tag)
                if key and key!=self.TAG_SKIP_MARKERNOTE:
                    res[key]=val
                    if key == self.TAG_GPS_INFO:
                        for t in val:
                            sub_decoded = GPSTAGS.get(t, t)
                            
                            if sub_decoded == self.TAG_GPSTIMESTAMP:
                                gs = val[t]
                                gps_time = ':'.join(map('{0:0>2}'.format, # Convert tuple to padded zero str
                                    (int(gs[0][0]/gs[0][1]), 
                                    int(gs[1][0]/gs[1][1]), 
                                    int(gs[2][0]/gs[2][1]))))
                            elif sub_decoded == self.TAG_GPSDATESTAMP:
                                gps_date = val[t]
                            elif sub_decoded == self.TAG_GPS_LONGTITUDE_REF:
                                gps_E = 1 if val[t] =='E' else -1
                            elif sub_decoded == self.TAG_GPS_LONGTITUDE:
                                gsLong = val[t]
                                gps_Long = (gsLong[0][0]/gsLong[0][1])+(gsLong[1][0]/gsLong[1][1])/60+((gsLong[2][0]/gsLong[2][1])/60)/60
                            elif sub_decoded == self.TAG_GPS_LATITUDE_REF:
                                gps_N = 1 if val[t] =='N' else -1
                            elif sub_decoded == self.TAG_GPS_LATITUDE:
                                gsLat = val[t]
                                gps_Lat = (gsLat[0][0]/gsLat[0][1])+(gsLat[1][0]/gsLat[1][1])/60+((gsLat[2][0]/gsLat[2][1])/60)/60
                        if gps_date and gps_time:
                            dt = datetime.strptime(gps_date + ' ' + gps_time, self.DATETIME_FORMAT).replace(tzinfo=self.UTC)
                            res[self.KEY_GPSDT] = dt.strftime(self.DATETIME_FORMAT)
                        if gps_E and gps_N and gps_Long and gps_Lat:
                            res[self.KEY_GPS] = str(gps_N*gps_Lat)+', '+str(gps_E*gps_Long)
            except Exception as e:
                print(e)
        return res        
    
    def getGPSDateTime(self,exif):
        try:
            return exif[self.KEY_GPSDT]
        except:
            return None        

    def getDateTimeDigitizedDateTime(self,exif):
        try:
            return exif[self.KEY_DateTimeDigitized]
        except:
            return None       
    
    def getDateTimeOriginal(self,exif):
        try:
            return exif[self.KEY_DateTimeOriginal]
        except:
            return None                     

    def getDateTime(self,exif):
        try:
            return exif[self.KEY_DateTime]
        except Exception as e:
            return None

    def getGPS(self,exif):
        try:
            return exif[self.KEY_GPS]
        except:
            return None        

if __name__ == "__main__":
    helper = ExifHelper()
    res = helper.getExif('D:/private/workarea/PhotoThisDay/res/P_20200216_173159.jpg')
    print(res)
