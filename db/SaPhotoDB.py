# -*- coding: UTF-8 -*-
import sqlite3
import json
from db.JsonEncoder import MyEncoder
from db.CatalogEncoder import CatalogEncoder

""" 
    Initial the sqlite3 database and create tables, indexes.
    To store monitor folders and all the photo information.
"""

class dbPhotoHelper:
    def __init__(self):
        self.conn = None
        try:
            self.conn = sqlite3.connect('SaPhoto.db')
            self.conn.row_factory = sqlite3.Row
            #self.conn.text_factory = str
            self.create()
        except Exception as e:
            print(e)

    def create(self):
        #photo meta data 
        cur = self.conn.cursor()
        try:
            #face_recognition store face location
            #FILE_TYPE store file extension, ex avi,mov,jpg,png,mpg,mpeg
            cur.execute('''CREATE TABLE IF NOT EXISTS PHOTOS
            (ID  INTEGER PRIMARY KEY AUTOINCREMENT,
            FILE_NAME      TEXT    NOT NULL,
            ROOT_DIR       TEXT    NOT NULL,
            DIR            TEXT    NOT NULL,
            META           JSON,
            PHOTO_UTC_TS   INTEGER,
            PHOTO_UTC_DATE DATETIME,
            CREATE_UTC_DATE DATETIME,
            TIME_ZONE      TEXT,
            GPS            TEXT,
            BATCH_UTC_DATE DATETIME,
            FACE_RECOGNITION TEXT, 
            FILE_TYPE      TEXT,
            SCENE          TEXT,
            CATALOG        TEXT,
            SIZE_B         INTEGER,
            GPS_ADDRESS    TEXT
            );''')

            cur.execute('''CREATE INDEX IF NOT EXISTS PHOTOS_TS_IDX ON PHOTOS ( PHOTO_UTC_TS );''')
            cur.execute('''CREATE INDEX IF NOT EXISTS PHOTOS_DATE_IDX ON PHOTOS ( PHOTO_UTC_DATE );''')
            cur.execute('''CREATE INDEX IF NOT EXISTS PHOTOS_CDATE_IDX ON PHOTOS ( CREATE_UTC_DATE );''')
            cur.execute('''CREATE INDEX IF NOT EXISTS PHOTOS_ROOT_DIR_IDX ON PHOTOS ( ROOT_DIR );''')
            cur.execute('''CREATE INDEX IF NOT EXISTS PHOTOS_CATALOG_IDX ON PHOTOS ( CATALOG );''')
            cur.execute('''CREATE INDEX IF NOT EXISTS PHOTOS_DIR_FILE_IDX ON PHOTOS ( FILE_NAME,DIR );''')

            # Indexing Directory
            cur.execute('''CREATE TABLE IF NOT EXISTS PARSER_DIRECTORY
            (ID INTEGER PRIMARY KEY AUTOINCREMENT, 
            DIR             TEXT,
            ROOT_DIR        INTEGER DEFAULT 0,            
            RECURSIVE       INTEGER DEFAULT 0,
            PARSER_UTC_DATE      DATETIME,
            MONITOR         INTEGER DEFAULT 1
            );''')

            cur.execute('''CREATE INDEX IF NOT EXISTS PHOTOS_DATE_IDX ON PARSER_DIRECTORY ( DIR,PARSER_UTC_DATE );''')

            cur.execute('''CREATE TABLE IF NOT EXISTS VIDEOS
            (ID  INTEGER PRIMARY KEY AUTOINCREMENT,
            FILE_NAME      TEXT    NOT NULL,
            ROOT_DIR       TEXT    NOT NULL,
            DIR            TEXT    NOT NULL,
            CREATE_UTC_DATE DATETIME,
            TIME_ZONE      TEXT,
            BATCH_UTC_DATE DATETIME,
            FILE_TYPE      TEXT,
            CATALOG        TEXT,
            SIZE_B         INTEGER
            );''')

            cur.execute('''CREATE INDEX IF NOT EXISTS VIDEOS_CDATE_IDX ON VIDEOS ( CREATE_UTC_DATE );''')
            cur.execute('''CREATE INDEX IF NOT EXISTS VIDEOS_ROOT_DIR_IDX ON VIDEOS ( ROOT_DIR );''')
            cur.execute('''CREATE INDEX IF NOT EXISTS VIDEOS_CATALOG_IDX ON VIDEOS ( CATALOG );''')
            cur.execute('''CREATE INDEX IF NOT EXISTS VIDEOS_DIR_FILE_IDX ON VIDEOS ( FILE_NAME,DIR );''')

        except Exception as e:
            print(e)

    def UpdateGeoAddress(self,fileName,dirName,address):
        cur = self.conn.cursor()
        try:
            cur.execute('''UPDATE PHOTOS SET GPS_ADDRESS=? WHERE FILE_NAME=? AND DIR=?;''',(address,fileName,dirName))
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            return False            
            print("UpdateGeoAddress:"+str(e))   

    def insertVideo(self,meta,cls=CatalogEncoder):
        cur = self.conn.cursor()
        try:
            catalog = cls().default(meta[2])
            cur.execute('''INSERT INTO VIDEOS (FILE_NAME,ROOT_DIR,DIR,CREATE_UTC_DATE,TIME_ZONE,BATCH_UTC_DATE,FILE_TYPE,CATALOG,SIZE_B) VALUES (?,?,?,?,?,?,?,?,?);''',(meta[0],meta[1],meta[2],meta[3],meta[4],meta[5],meta[6],catalog,meta[7]))
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            return False            
            print("insertVideo:"+str(e))

    def insertVideoIfNotExist(self,meta,cls=CatalogEncoder):
        cur = self.conn.cursor()
        try:
            catalog = cls().default(meta[2])
            cur.execute('''SELECT * FROM VIDEOS WHERE FILE_NAME=? AND DIR=?''',(meta[0],meta[2]))
            r = cur.fetchone()
            if not r:
                cur.execute('''INSERT INTO VIDEOS (FILE_NAME,ROOT_DIR,DIR,CREATE_UTC_DATE,TIME_ZONE,BATCH_UTC_DATE,FILE_TYPE,CATALOG,SIZE_B) VALUES (?,?,?,?,?,?,?,?,?);''',(meta[0],meta[1],meta[2],meta[3],meta[4],meta[5],meta[6],catalog,meta[7]))
                self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            return False            
            print("insertVideoIfNotExist:"+str(e))

    def updateVideo(self,directory,filename,batchDT):
        cur = self.conn.cursor()
        try:
            cur.execute('''UPDATE VIDEOS SET BATCH_UTC_DATE=? WHERE DIR=? AND FILE_NAME=? ''',(batchDT,directory,filename))
            self.conn.commit()            
            return True
        except Exception as e:
            self.conn.rollback()
            return False            
            print("updateVideo:"+str(e)) 
    def videoExists(self,directory,filename):
        cur = self.conn.cursor()
        try:
            cur.execute('''SELECT * FROM VIDEOS WHERE DIR=? AND FILE_NAME=? ''',(directory,filename))
            r = cur.fetchone()
            return True if r else False
            
        except Exception as e:
            print("photoExists:"+str(e))   
            
    def obseleteVideo(self,rootDir,batchDT):
        cur = self.conn.cursor()
        try:
            cur.execute('''DELETE FROM VIDEOS WHERE ROOT_DIR=? AND BATCH_UTC_DATE<>?''',(rootDir,batchDT))
            print('obseleteVideo: '+str(cur.rowcount))
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            return False            
            print("obseleteVideo:"+str(e))

    def insertPhoto(self,meta,cls=CatalogEncoder):
        #log = [('2006-03-28', 'BUY', 'IBM', 1000, 45.00),
        #     ('2006-04-05', 'BUY', 'MSFT', 1000, 72.00),
        #     ('2006-04-06', 'SELL', 'IBM', 500, 53.00),
        #    ]
        cur = self.conn.cursor()
        try:
            m3 = json.dumps(meta[3],cls=MyEncoder,indent=4)
            catalog = cls().default(meta[2])
            cur.execute('''INSERT INTO PHOTOS (FILE_NAME,ROOT_DIR,DIR,META,PHOTO_UTC_TS,PHOTO_UTC_DATE,CREATE_UTC_DATE,TIME_ZONE,GPS,BATCH_UTC_DATE,FACE_RECOGNITION,FILE_TYPE,SCENE,CATALOG,SIZE_B) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);''',(meta[0],meta[1],meta[2],m3,meta[4],meta[5],meta[6],meta[7],meta[8],meta[9],meta[10],meta[11],meta[12],catalog,meta[13]))
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            return False            
            print("insertPhoto:"+str(e))

    def obseletePhoto(self,rootDir,batchDT):
        cur = self.conn.cursor()
        try:
            cur.execute('''DELETE FROM PHOTOS WHERE ROOT_DIR=? AND BATCH_UTC_DATE<>?''',(rootDir,batchDT))
            print('obseletePhoto: '+str(cur.rowcount))
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            return False
            print("obseletePhoto:"+str(e))        

    def photoExists(self,directory,filename):
        cur = self.conn.cursor()
        try:
            cur.execute('''SELECT * FROM PHOTOS WHERE DIR=? AND FILE_NAME=? ''',(directory,filename))
            r = cur.fetchone()
            return True if r else False
            
        except Exception as e:
            print("photoExists:"+str(e))       

    def updatePhoto(self,directory,filename,batchDT):
        cur = self.conn.cursor()
        try:
            cur.execute('''UPDATE PHOTOS SET BATCH_UTC_DATE=? WHERE DIR=? AND FILE_NAME=? ''',(batchDT,directory,filename))
            self.conn.commit()      
            return True      
        except Exception as e:
            self.conn.rollback()
            return False            
            print("updatePhoto:"+str(e)) 

    def insertPhotoIfNotExist(self,meta,cls=CatalogEncoder):
        cur = self.conn.cursor()
        try:
            cur.execute('''SELECT * FROM PHOTOS WHERE FILE_NAME=? AND DIR=?''',(meta[0],meta[2]))
            r = cur.fetchone()
            if not r:
                catalog = cls().default(meta[2])
                cur.execute('''INSERT INTO PHOTOS (FILE_NAME,ROOT_DIR,DIR,META,PHOTO_UTC_TS,PHOTO_UTC_DATE,CREATE_UTC_DATE,TIME_ZONE,GPS,BATCH_UTC_DATE,FACE_RECOGNITION,FILE_TYPE,SCENE,CATALOG,SIZE_B) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?);''',(meta[0],meta[1],meta[2],m3,meta[4],meta[5],meta[6],meta[7],meta[8],meta[9],meta[10],meta[11],meta[12],catalog,meta[13]))
                self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            return False
            print("insertPhotoIfNotExist:"+str(e))

    def insertDirIfNotExist(self,log):
        #log = [('2006-03-28', 'BUY', 'IBM', 1000, 45.00),
        #     ('2006-04-05', 'BUY', 'MSFT', 1000, 72.00),
        #     ('2006-04-06', 'SELL', 'IBM', 500, 53.00),
        #    ]
        cur = self.conn.cursor()
        try:
            cur.execute('''SELECT * FROM PARSER_DIRECTORY WHERE DIR=? ''',(log[0],))
            r = cur.fetchone()
            if not r:
                print('new dir = '+log[0])
                cur.execute('''INSERT INTO PARSER_DIRECTORY (DIR, ROOT_DIR, RECURSIVE, PARSER_UTC_DATE,MONITOR) VALUES (?,?,?,?,1);''',log)
                self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            return False            
            print("insertDirIfNotExist:"+str(e))

    def clearDirs(self):
        cur = self.conn.cursor()
        try:
            cur.execute('''update parser_directory set parser_utc_date=null''')
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            return False            
            print("clearDirs:"+str(e))

    def clearDir(self,log):
        cur = self.conn.cursor()
        try:
            cur.execute('''update parser_directory set parser_utc_date=null where dir=?''',(log,))
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            return False            
            print("clearDir:"+str(e))

    def insertDirs(self,logs):
        #log = [('2006-03-28', 'BUY', 'IBM', 1000, 45.00),
        #     ('2006-04-05', 'BUY', 'MSFT', 1000, 72.00),
        #     ('2006-04-06', 'SELL', 'IBM', 500, 53.00),
        #    ]
        cur = self.conn.cursor()
        try:
            cur.executemany('''INSERT INTO PARSER_DIRECTORY (DIR, ROOT_DIR, RECURSIVE, PARSER_UTC_DATE) VALUES (?,?,?,?);''',logs)
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            return False            
            print("insertDirs:"+str(e))

    def updateDir(self,utcDate,directory):
        #log = [('2006-03-28', 'BUY', 'IBM', 1000, 45.00),
        #     ('2006-04-05', 'BUY', 'MSFT', 1000, 72.00),
        #     ('2006-04-06', 'SELL', 'IBM', 500, 53.00),
        #    ]
        cur = self.conn.cursor()
        try:
            cur.execute('''UPDATE PARSER_DIRECTORY SET PARSER_UTC_DATE=? WHERE DIR=?;''',(utcDate,directory))
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            return False            
            print("updateDir:"+str(e))

    def getRootDirs(self):        
        try:
            cur = self.conn.cursor()        
            cur.execute('''SELECT * FROM PARSER_DIRECTORY WHERE ROOT_DIR=1''')
            rows = cur.fetchall()

            return rows
        except Exception as e:
            print("getRootDirs:"+str(e))

    def getMonitorDirs(self):        
        try:
            cur = self.conn.cursor()        
            cur.execute('''SELECT * FROM PARSER_DIRECTORY WHERE MONITOR=1''')
            rows = cur.fetchall()

            return rows
        except Exception as e:
            print("getMonitorDirs:"+str(e))

    def getDir(self,dir):        
        try:
            cur = self.conn.cursor()        
            cur.execute('''SELECT * FROM PARSER_DIRECTORY WHERE MONITOR=1 AND DIR=?''',(dir,))
            rows = cur.fetchall()

            return rows
        except Exception as e:
            print("getDir:"+str(e))

    def getMinPhotoUtcTS(self):
        try:
            cur = self.conn.cursor()
            cur.execute('''SELECT min(photo_utc_ts) min_photo_utc_ts from PHOTOS a WHERE PHOTO_UTC_TS IS NOT NULL''')
            one = cur.fetchone()
            if one:
                return one['min_photo_utc_ts']            
        except Exception as e:
            print("getMinPhotoUtcTS"+str(e))

    def getMinPhotoUtcTS(self):
        try:           
            cur = self.conn.cursor()
            cur.execute('SELECT min(photo_utc_ts) min_photo_utc_ts from PHOTOS a WHERE PHOTO_UTC_TS IS NOT NULL')
            one = cur.fetchone()
            if one:
                return one['min_photo_utc_ts']            
        except Exception as e:
            print("getMinPhotoUtcTS"+str(e))

    def getMinPhotoUtcTSByCatalog(self,catalogs):
        try:
            s = ' 1=0 '
            for cata in catalogs:
                s = s + ' OR CATALOG LIKE ("%'+cata+'%")'

            s = '('+s+')'
            
            cur = self.conn.cursor()
            cur.execute('SELECT min(photo_utc_ts) min_photo_utc_ts from PHOTOS a WHERE '+s+' AND PHOTO_UTC_TS IS NOT NULL')
            one = cur.fetchone()
            if one:
                return one['min_photo_utc_ts']            
        except Exception as e:
            print("getMinPhotoUtcTSByCatalog"+str(e))        
    
    def getRandomThisDay(self,utcTimestampStart,utcTimestampEnd,num):
        try:
            cur = self.conn.cursor()
            cur.execute('''SELECT a.* from PHOTOS a
                        'where PHOTO_UTC_TS >=?  and PHOTO_UTC_TS<=? '+
                        ORDER BY RANDOM() LIMIT ?
                        ''',(utcTimestampStart,utcTimestampEnd,num))
            rows = cur.fetchall()

            return rows
        except Exception as e:
            print("getRandomThisDay:"+str(e))        

    def getRandomThisDayByCatalog(self,utcTimestampStart,utcTimestampEnd,num,catalogs):
        try:
            #s = 'CATALOG=""'
            s = '1=0' #default new image can't push to anyone
            for cata in catalogs:
                s = s + ' OR CATALOG LIKE ("%'+cata+'%")'

            s = '('+s+')'

            #print('getRandomThisDayByCatalog:'+str(s))
            cur = self.conn.cursor()
            cur.execute('SELECT a.* from PHOTOS a '+
                        'where PHOTO_UTC_TS >=?  and PHOTO_UTC_TS<=? '+
                        ' AND '+ s +
                        'ORDER BY RANDOM() LIMIT ?'
                        ,(utcTimestampStart,utcTimestampEnd,num))
            rows = cur.fetchall()

            return rows
        except Exception as e:
            print("getRandomThisDayByCatalog:"+str(e)) 

    def getRandomVideoThisDayByCatalog(self,utcDTStart,utcDTEnd,num,catalogs):
        try:
            #s = 'CATALOG=""'
            s = '1=0' #default new image can't push to anyone
            for cata in catalogs:
                s = s + ' OR CATALOG LIKE ("%'+cata+'%")'

            s = '('+s+')'

            #print('getRandomThisDayByCatalog:'+str(s))
            cur = self.conn.cursor()
            cur.execute('SELECT a.* from VIDEOS a '+
                        'where CREATE_UTC_DATE >=?  and CREATE_UTC_DATE<=? '+
                        ' AND '+ s +
                        'ORDER BY RANDOM() LIMIT ?'
                        ,(utcDTStart,utcDTEnd,num))
            rows = cur.fetchall()

            return rows
        except Exception as e:
            print("getRandomVideoThisDayByCatalog:"+str(e)) 

    def getPhoto(self,dir,fileName):
        try:
            cur = self.conn.cursor()
            cur.execute('SELECT a.* from PHOTOS a where DIR=? AND FILE_NAME=? ',(dir,fileName))
            rows = cur.fetchall()

            return rows
        except Exception as e:
            print("getPhoto:"+str(e)) 
if __name__ == "__main__":
    helper = dbHelper()
    helper.create()
