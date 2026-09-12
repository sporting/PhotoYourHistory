# -*- coding: UTF-8 -*-
import sys
import os

dir_path = os.path.dirname(os.path.realpath(__file__))
parent_dir_path = os.path.abspath(os.path.join(dir_path, os.pardir))
sys.path.insert(0, parent_dir_path)

from db.SaUsersDB import dbUsersHelper
"""
    Set synology nas host ip and port to database
"""

def SetNasHostIPPort(ip,port):   
    duh = dbUsersHelper()
    duh.setNasHostIPPort(ip,port)    

if __name__ == "__main__":
    if len(sys.argv[1:])>=2:
        SetNasHostIPPort(sys.argv[1],sys.argv[2])