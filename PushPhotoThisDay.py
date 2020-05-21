# -*- coding: UTF-8 -*-
from datetime import datetime
from db.SaUsersDB import dbUsersHelper
import mysys.PushPhoto as PhotoService

if __name__ == "__main__":
    duh = dbUsersHelper()
    users = duh.getSMSUsers()    
    for user in users:
        PhotoService.Push(user['USER_ID'],datetime.today(),2)            
