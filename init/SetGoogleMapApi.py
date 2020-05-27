# -*- coding: UTF-8 -*-
import sys
import os

dir_path = os.path.dirname(os.path.realpath(__file__))
parent_dir_path = os.path.abspath(os.path.join(dir_path, os.pardir))
sys.path.insert(0, parent_dir_path)

from db.SaUsersDB import dbUsersHelper

"""
    Set Google Map Api to get Geolocation to database
"""

def SetGoogleMapApi(apiKey):   
    duh = dbUsersHelper()
    duh.setGoogleAPIKey(apiKey)    

if __name__ == "__main__":
    if len(sys.argv[1:])>=1:
        SetGoogleMapApi(sys.argv[1])