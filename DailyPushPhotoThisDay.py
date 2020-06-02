# -*- coding: UTF-8 -*-
from datetime import datetime
from db.SaUsersDB import dbUsersHelper
import mysys.PushPhoto as PhotoService

if __name__ == "__main__":    
    duh = dbUsersHelper()
    users = duh.getSMSUsers()    
    PhotoService.Push(users,datetime.today(),3)
