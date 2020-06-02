# -*- coding: UTF-8 -*-
import sys
import os

dir_path = os.path.dirname(os.path.realpath(__file__))
parent_dir_path = os.path.abspath(os.path.join(dir_path, os.pardir))
sys.path.insert(0, parent_dir_path)

from db.SaUsersDB import dbUsersHelper
"""
    Set care catagory list to database
"""

def SetCareCatagory(meta):   
    duh = dbUsersHelper()
    duh.setCareCatagory(meta)    

if __name__ == "__main__":
    if len(sys.argv[1:])>=2:
        print(sys.argv)
        SetCareCatagory((sys.argv[1],sys.argv[2:]))