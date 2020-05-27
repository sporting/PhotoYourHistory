# -*- coding: UTF-8 -*-
import sys
import os

dir_path = os.path.dirname(os.path.realpath(__file__))
parent_dir_path = os.path.abspath(os.path.join(dir_path, os.pardir))
sys.path.insert(0, parent_dir_path)

from db.SaUsersDB import dbUsersHelper
import sys

"""
    Set synology QuickConnect ID to database
"""

def SetQuickConnectID(qid):   
    duh = dbUsersHelper()
    duh.setQuickConnectID(qid)    

if __name__ == "__main__":
    if len(sys.argv[1:])>=1:
        SetQuickConnectID(sys.argv[1])