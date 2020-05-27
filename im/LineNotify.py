# -*- coding: UTF-8 -*-
import requests, os

"""
    Line Notify API handler
"""

class LineNotify():
    def __init__(self, token):
        self.token = token

    def send(self, msg, picURI=None):
        url = "https://notify-api.line.me/api/notify"
        headers = {
            "Authorization": "Bearer " + self.token
        }
   
        payload = {'message': msg}
        files = {'imageFile': open(picURI, 'rb')}
        r = requests.post(url, headers = headers, params = payload, files = files)
        return r.status_code
