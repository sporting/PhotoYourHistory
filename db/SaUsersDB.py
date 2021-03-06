# -*- coding: UTF-8 -*-
import sqlite3
import json
from db.JsonEncoder import MyEncoder

""" 
    system table
"""

class dbUsersHelper:
    def __init__(self):
        self.conn = None
        try:
            self.conn = sqlite3.connect('SaUsers.db')
            self.conn.row_factory = sqlite3.Row
            #self.conn.text_factory = str
            #self.conn.text_factory =  sqlite3.OptimizedUnicode
            self.create()
        except Exception as e:
            print(e)

    def create(self):
        #photo meta data 
        try:
            cur = self.conn.cursor()            
#            cur.execute('''CREATE TABLE IF NOT EXISTS GROUPS
#            (ID  INTEGER PRIMARY KEY AUTOINCREMENT,
#            NAME      TEXT    NOT NULL,
#            USERS_ID        TEXT    NOT NULL,
#            DESC      TEXT
#            );''')

            cur.execute('''CREATE TABLE IF NOT EXISTS USERS
            (ID  INTEGER PRIMARY KEY AUTOINCREMENT,
            USER_ID       TEXT    NOT NULL,
            SMS_TYPE      TEXT    NOT NULL,
            SMS_ID        TEXT    NOT NULL,
            NAME          TEXT    NOT NULL
            );''')

            cur.execute('''CREATE INDEX IF NOT EXISTS USERS_TYPE_ID_IDX ON USERS ( SMS_TYPE,SMS_ID );''')
            cur.execute('''CREATE INDEX IF NOT EXISTS USERS_ID_IDX ON USERS ( USER_ID );''')

            cur.execute('''CREATE TABLE IF NOT EXISTS USER_NOTICE
            (ID  INTEGER PRIMARY KEY AUTOINCREMENT,
            USER_ID       TEXT    NOT NULL,
            NOTICE_USER_ID TEXT    NOT NULL
            );''')

            cur.execute('''CREATE TABLE IF NOT EXISTS SYSPARAM
            (ID INTEGER PRIMARY KEY AUTOINCREMENT, 
            KEY             TEXT,
            VALUE           TEXT,
            DESC            TEXT
            );''')      

            cur.execute('''CREATE INDEX IF NOT EXISTS SYSPARAM_KEY_IDX ON SYSPARAM ( KEY );''')          

        except Exception as e:
            print(e)

#    def insertGroup(self,meta):
#        try:
#            cur = self.conn.cursor()
#            cur.execute('''INSERT INTO GROUPS (NAME,USERS_ID,DESC) VALUES (?,?,?);''',(meta[0],meta[1],meta[2]))
#            self.conn.commit()
#        except Exception as e:
#            self.conn.rollback()
#            print("insertGroup:"+str(e))
#
#    def deleteGroup(self,groupName,usersId):
#        try:
#            cur = self.conn.cursor()
#            cur.execute('''DELETE FROM GROUPS WHERE NAME=? AND USERS_ID=?;''',(groupName,usersId))
#            self.conn.commit()
#        except Exception as e:
#            self.conn.rollback()
#            print("deleteGroup:"+str(e))  

    def setUserData(self,meta):        
        try:
            self.deleteUser(meta)      
            self.insertUser(meta)
        except Exception as e:
            self.conn.rollback()
            return False            
            print("setUserData:"+str(e)) 

    def insertUser(self,meta):        
        try:
            cur = self.conn.cursor()
            cur.execute('''INSERT INTO USERS (USER_ID,SMS_TYPE,SMS_ID,NAME) VALUES (?,?,?,?);''',(meta[0],meta[1],meta[2],meta[3]))
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            print("insertUser:"+str(e))            
            return False

    def deleteUser(self,meta):        
        try:
            cur = self.conn.cursor()
            cur.execute('''DELETE FROM USERS WHERE USER_ID=? AND SMS_TYPE=? ;''',(meta[0],meta[1]))
            self.conn.commit()
            return True            
        except Exception as e:
            self.conn.rollback()
            print("deleteUser:"+str(e))              
            return False                              

    def getSMSUsers(self):      
        try:
            cur = self.conn.cursor()
            cur.execute('''SELECT USER_ID,SMS_TYPE,SMS_ID,NAME FROM USERS WHERE SMS_ID <>'' ;''')
            rows = cur.fetchall()
            return rows
        except Exception as e:
            print("getSMSUsers:"+str(e))     

    def getSMSUser(self,userId):      
        try:
            cur = self.conn.cursor()
            cur.execute('''SELECT USER_ID,SMS_TYPE,SMS_ID,NAME FROM USERS WHERE SMS_ID <>'' AND USER_ID=? ;''',(userId,))
            rows = cur.fetchall()
            return rows
        except Exception as e:
            print("getSMSUser:"+str(e))   

    def getUserNotice(self,userId):        
        try:
            cur = self.conn.cursor()
            cur.execute(''' SELECT USER_ID,NOTICE_USER_ID FROM USER_NOTICE WHERE USER_ID=?; ''',(userId,))
            rows = cur.fetchall()
            return rows
        except Exception as e:
            print("getUserNotice:"+str(e))          

    def setGoogleAPIKey(self,value):        
        try:
            cur = self.conn.cursor()
            cur.execute('''DELETE FROM SYSPARAM WHERE KEY=? ;''',('GOOGLE_MAP_API_KEY',))            
            cur.execute('''INSERT INTO SYSPARAM (KEY,VALUE,DESC) VALUES (?,?,?);''',('GOOGLE_MAP_API_KEY',value,''))
            self.conn.commit()
            return True            
        except Exception as e:
            self.conn.rollback()
            print("setGoogleAPIKey:"+str(e))             
            return False            

    def getGoogleAPIKey(self):        
        try:
            cur = self.conn.cursor()
            cur.execute(''' SELECT value from SYSPARAM where key='GOOGLE_MAP_API_KEY' ''')
            one = cur.fetchone()
            return one['value']
        except Exception as e:
            print("getGoogleAPIKey:"+str(e))    

    def setQuickConnectID(self,value):        
        try:
            cur = self.conn.cursor()
            cur.execute('''DELETE FROM SYSPARAM WHERE KEY=? ;''',('QUICKCONNECT_ID',))            
            cur.execute('''INSERT INTO SYSPARAM (KEY,VALUE,DESC) VALUES (?,?,?);''',('QUICKCONNECT_ID',value,''))
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            print("setQuickConnectID:"+str(e))             
            return False

    def getQuickConnectID(self):
        try:
            cur = self.conn.cursor()
            cur.execute(''' SELECT value from SYSPARAM where key='QUICKCONNECT_ID' ''')
            one = cur.fetchone()
            return one['value']
        except Exception as e:
            print("getQuickConnectID:"+str(e))

    def setNasHostIPPort(self,ip,port):
        try:
            cur = self.conn.cursor()
            cur.execute('''DELETE FROM SYSPARAM WHERE KEY=? ;''',('SYNOLOGY_HOST_IP',))            
            cur.execute('''INSERT INTO SYSPARAM (KEY,VALUE,DESC) VALUES (?,?,?);''',('SYNOLOGY_HOST_IP',ip,''))

            cur.execute('''DELETE FROM SYSPARAM WHERE KEY=? ;''',('SYNOLOGY_HOST_PORT',))            
            cur.execute('''INSERT INTO SYSPARAM (KEY,VALUE,DESC) VALUES (?,?,?);''',('SYNOLOGY_HOST_PORT',port,''))            
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            print("setNasHostIPPort:"+str(e))            
            return False

    def getNasHostIPPort(self):
        try:
            cur = self.conn.cursor()
            cur.execute(''' SELECT value from SYSPARAM where key='SYNOLOGY_HOST_IP' ''')
            one = cur.fetchone()
            ip = one['value']

            cur.execute(''' SELECT value from SYSPARAM where key='SYNOLOGY_HOST_PORT' ''')
            one = cur.fetchone()
            port = one['value']

            return ip,port
        except Exception as e:
            print("getNasHostIPPort:"+str(e))

    def setNasLoginAccountPwd(self,account,pwd):
        try:
            cur = self.conn.cursor()
            cur.execute('''DELETE FROM SYSPARAM WHERE KEY=? ;''',('SYNOLOGY_LOGIN_ACCOUNT',))            
            cur.execute('''INSERT INTO SYSPARAM (KEY,VALUE,DESC) VALUES (?,?,?);''',('SYNOLOGY_LOGIN_ACCOUNT',account,''))

            cur.execute('''DELETE FROM SYSPARAM WHERE KEY=? ;''',('SYNOLOGY_LOGIN_PWD',))            
            cur.execute('''INSERT INTO SYSPARAM (KEY,VALUE,DESC) VALUES (?,?,?);''',('SYNOLOGY_LOGIN_PWD',pwd,''))            
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            print("setNasLoginAccountPwd:"+str(e))            
            return False

    def getNasLoginAccountPwd(self):
        try:
            cur = self.conn.cursor()
            cur.execute(''' SELECT value from SYSPARAM where key='SYNOLOGY_LOGIN_ACCOUNT' ''')
            one = cur.fetchone()
            ip = one['value']

            cur.execute(''' SELECT value from SYSPARAM where key='SYNOLOGY_LOGIN_PWD' ''')
            one = cur.fetchone()
            port = one['value']

            return ip,port
        except Exception as e:
            print("getNasLoginAccountPwd:"+str(e))
       
    def setTelegramBotAccessToken(self,token):
        try:
            cur = self.conn.cursor()
            cur.execute('''DELETE FROM SYSPARAM WHERE KEY=? ;''',('TELEGRAM_BOT_TOKEN',))            
            cur.execute('''INSERT INTO SYSPARAM (KEY,VALUE,DESC) VALUES (?,?,?);''',('TELEGRAM_BOT_TOKEN',token,''))
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            print("setTelegramBotAccessToken:"+str(e))            
            return False

    def getTelegramBotAccessToken(self):
        try:
            cur = self.conn.cursor()
            cur.execute(''' SELECT value from SYSPARAM where key='TELEGRAM_BOT_TOKEN' ''')
            one = cur.fetchone()

            return one['value']
        except Exception as e:
            print("getTelegramBotAccessToken:"+str(e))       

    def setCareCatagory(self,who,carelist):
        try:
            cur = self.conn.cursor()
            cur.execute('''DELETE FROM USER_NOTICE WHERE USER_ID=? ;''',(who,))            
            for care in carelist:
                cur.execute('''INSERT INTO USER_NOTICE (USER_ID,NOTICE_USER_ID) VALUES (?,?);''',(who,care))
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            print("setCareCatagory:"+str(e))            
            return False
