# -*- coding: UTF-8 -*-
import sqlite3
import json
from db.JsonEncoder import MyEncoder

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

    def insertUser(self,meta):        
        try:
            cur = self.conn.cursor()
            cur.execute('''INSERT INTO USERS (USER_ID,SMS_TYPE,SMS_ID,NAME) VALUES (?,?,?);''',(meta[0],meta[1],meta[2],meta[3]))
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print("insertUser:"+str(e))

    def deleteUser(self,userId,smsType,smsId):        
        try:
            cur = self.conn.cursor()
            cur.execute('''DELETE FROM USERS WHERE USER_ID=? AND SMS_TYPE=? AND SMS_ID=?;''',(userId,smsType,smsId))
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print("deleteUser:"+str(e))            

    def getSMSUsers(self):      
        try:
            cur = self.conn.cursor()
            cur.execute('''SELECT USER_ID,SMS_TYPE,SMS_ID,NAME FROM USERS WHERE SMS_ID <>'' ;''')
            rows = cur.fetchall()
            return rows
        except Exception as e:
            self.conn.rollback()
            print("getSMSUsers:"+str(e))     

    def getUserNotice(self,userId):        
        try:
            cur = self.conn.cursor()
            cur.execute(''' SELECT USER_ID,NOTICE_USER_ID FROM USER_NOTICE WHERE USER_ID=?; ''',(userId,))
            rows = cur.fetchall()
            return rows
        except Exception as e:
            self.conn.rollback()
            print("getUserNotice:"+str(e))          

    def getGoogleAPIKey(self):        
        try:
            cur = self.conn.cursor()
            cur.execute(''' SELECT value from SYSPARAM where key='GOOGLE_MAP_API_KEY' ''')
            one = cur.fetchone()
            return one['value']
        except Exception as e:
            self.conn.rollback()
            print("getGoogleAPIKey:"+str(e))                 

if __name__ == "__main__":
    helper = dbUsersHelper()
    helper.create()
    helper.deleteUser('ERIC','LINE NOTIFY','BSwQXMJoXQvABhIdiTyLIDbe1cWL8DxlpFEaUcCZZWA')
    helper.insertUser(('ERIC','LINE NOTIFY','BSwQXMJoXQvABhIdiTyLIDbe1cWL8DxlpFEaUcCZZWA','ERIC SHIH'))
