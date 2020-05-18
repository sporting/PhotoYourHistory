# -*- coding: UTF-8 -*-
import sqlite3
import json
from db.JsonEncoder import MyEncoder

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
            SIZE_B         INTEGER
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
            RECURSIVE       INTEGER DEFAULT 0,
            PARSER_UTC_DATE      DATETIME
            );''')

            cur.execute('''CREATE INDEX IF NOT EXISTS PHOTOS_DATE_IDX ON PARSER_DIRECTORY ( DIR,PARSER_UTC_DATE );''')

            cur.execute('''CREATE TABLE IF NOT EXISTS SYSPARAM
            (ID INTEGER PRIMARY KEY AUTOINCREMENT, 
            KEY             TEXT,
            VALUE           TEXT,
            DESC            TEXT
            );''')            
        except Exception as e:
            print(e)

    def insertPhoto(self,meta):
        #log = [('2006-03-28', 'BUY', 'IBM', 1000, 45.00),
        #     ('2006-04-05', 'BUY', 'MSFT', 1000, 72.00),
        #     ('2006-04-06', 'SELL', 'IBM', 500, 53.00),
        #    ]
        cur = self.conn.cursor()
        try:
            m3 = json.dumps(meta[3],cls=MyEncoder,indent=4)
            cur.execute('''INSERT INTO PHOTOS (FILE_NAME,ROOT_DIR,DIR,META,PHOTO_UTC_TS,PHOTO_UTC_DATE,CREATE_UTC_DATE,TIME_ZONE,GPS,BATCH_UTC_DATE,FACE_RECOGNITION,FILE_TYPE,SCENE,CATALOG,SIZE_B) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);''',(meta[0],meta[1],meta[2],m3,meta[4],meta[5],meta[6],meta[7],meta[8],meta[9],meta[10],meta[11],meta[12],meta[13],meta[14]))
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print("insertPhoto:"+str(e))

    def obseletePhoto(self,rootDir,batchDT):
        cur = self.conn.cursor()
        try:
            cur.execute('''DELETE FROM PHOTOS WHERE ROOT_DIR=? AND BATCH_UTC_DATE<>?''',(rootDir,batchDT))
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
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
        except Exception as e:
            self.conn.rollback()
            print("updatePhoto:"+str(e)) 

    def insertPhotoIfNotExist(self,meta):
        cur = self.conn.cursor()
        try:
            m3 = json.dumps(meta[3],cls=MyEncoder,indent=4)
            cur.execute('''SELECT * FROM PHOTOS WHERE FILE_NAME=? AND DIR=? AND META=?''',(meta[0],meta[1],m3))
            r = cur.fetchone()
            if not r:
                cur.execute('''INSERT INTO PHOTOS (FILE_NAME,ROOT_DIR,DIR,META,PHOTO_UTC_TS,PHOTO_UTC_DATE,CREATE_UTC_DATE,TIME_ZONE,GPS,BATCH_UTC_DATE,FACE_RECOGNITION,FILE_TYPE,SCENE,CATALOG,SIZE_B) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?);''',(meta[0],meta[1],meta[2],m3,meta[4],meta[5],meta[6],meta[7],meta[8],meta[9],meta[10],meta[11],meta[12],meta[13],meta[14]))
                self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print("insertPhotoIfNotExist:"+str(e))

    def insertDir(self,log):
        #log = [('2006-03-28', 'BUY', 'IBM', 1000, 45.00),
        #     ('2006-04-05', 'BUY', 'MSFT', 1000, 72.00),
        #     ('2006-04-06', 'SELL', 'IBM', 500, 53.00),
        #    ]
        cur = self.conn.cursor()
        try:
            d = log[0]
            cur.execute('''DELETE FROM PARSER_DIRECTORY WHERE DIR=? ;''',[(d)])
            cur.execute('''INSERT INTO PARSER_DIRECTORY (DIR, RECURSIVE, PARSER_UTC_DATE) VALUES (?,?,?);''',log)
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print("insertDir:"+str(e))

    def insertDirs(self,logs):
        #log = [('2006-03-28', 'BUY', 'IBM', 1000, 45.00),
        #     ('2006-04-05', 'BUY', 'MSFT', 1000, 72.00),
        #     ('2006-04-06', 'SELL', 'IBM', 500, 53.00),
        #    ]
        cur = self.conn.cursor()
        try:
            cur.executemany('''INSERT INTO PARSER_DIRECTORY (DIR, RECURSIVE, PARSER_UTC_DATE) VALUES (?,?,?);''',logs)
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
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
        except Exception as e:
            self.conn.rollback()
            print("updateDir:"+str(e))


    def getDirs(self):        
        try:
            cur = self.conn.cursor()
            cur.execute('''SELECT * FROM PARSER_DIRECTORY''')
            rows = cur.fetchall()

            return rows
        except Exception as e:
            print("getDirs:"+str(e))

    def getMinPhotoUtcTS(self):
        try:
            cur = self.conn.cursor()
            cur.execute('''SELECT min(photo_utc_ts) min_photo_utc_ts from PHOTOS a WHERE PHOTO_UTC_TS IS NOT NULL''')
            one = cur.fetchone()
            if one:
                return one['min_photo_utc_ts']            
        except Exception as e:
            print("getMinPhotoUtcTS"+str(e))

    def getMinPhotoUtcTSByCatalog(self,catalogs):
        try:
            s = 'CATALOG==""'
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
            s = 'CATALOG==""'
            for cata in catalogs:
                s = s + ' OR CATALOG LIKE ("%'+cata+'%")'

            s = '('+s+')'


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

if __name__ == "__main__":
    helper = dbHelper()
    helper.create()
