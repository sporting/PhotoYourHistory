# -*- coding: UTF-8 -*-
import sys
import os

dir_path = os.path.dirname(os.path.realpath(__file__))
parent_dir_path = os.path.abspath(os.path.join(dir_path, os.pardir))
sys.path.insert(0, parent_dir_path)

from db.SaUsersDB import dbUsersHelper
"""
    Set notify user to database
"""

def SetUserData(meta):   
    duh = dbUsersHelper()
    duh.setUserData(meta)    

if __name__ == "__main__":
    if len(sys.argv[1:])>=4:
        #USER_ID,SMS_TYPE,SMS_ID,NAME
        #SMS_TYPE in 'LINE NOTIFY', 'TELEGRAM BOT'
        print(sys.argv)
        SetUserData((sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4]))