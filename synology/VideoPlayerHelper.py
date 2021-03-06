# -*- coding: UTF-8 -*-
import re
import os
import urllib.request
import ssl
import json
from urllib import parse
from pathlib import Path

ssl._create_default_https_context = ssl._create_unverified_context

class VideoPlayerHelper:
    loginUrl = '''https://{SYNOLOGY_HOST_IP}:{SYNOLOGY_HOST_PORT}/webapi/auth.cgi?api=SYNO.API.Auth&version=6&method=login&account={account}&passwd={password}&session=FileStation&format=cookie'''
    url = '''https://{SYNOLOGY_HOST_IP}:{SYNOLOGY_HOST_PORT}/fbdownload/{fileName}?'''

    def __init__(self,hostIP,hostPort,account,password):
        self.hostIP = hostIP
        self.hostPort = hostPort
        self.account = account
        self.password = password
        self.SID = self.loginSynology()

    def utfencode(self,s):
        a=''
        for c in s:
            e = ord(c)
            if e<128:
                a = a + chr(e)
            else:
                if e>127 and e<2048:
                    a = a + chr((e>>6) | 192)
                    a = a + chr((e&63) | 128)
                else:
                    a = a + chr((e>>12) | 224)
                    a = a + chr(((e>>6) & 63) | 128)
                    a = a + chr((e&63) | 128)
        return a	
		
    def bin2hex(self,t):
        t=self.utfencode(t)
        n = []
        for c in t:
            e = ord(str(c))
            n.append(re.sub(r'/^([\da-f])$/','0$1',format(e,'x')))
        return ''.join(n)     
    
    def loginSynology(self):
        if not (self.hostIP and self.hostPort and self.account and self.password):
            return None

        url = self.loginUrl
        url = url.replace('{SYNOLOGY_HOST_IP}',self.hostIP)
        url = url.replace('{SYNOLOGY_HOST_PORT}',self.hostPort)
        
        url = url.replace('{account}',self.account)
        url = url.replace('{password}',self.password)
        try:
            js = urllib.request.urlopen(url).read() 
            js = js.decode('utf-8')
            jsObj = json.loads(js)
            if jsObj['success']==True:
                return jsObj['data']['sid']
        except Exception as e:
            print(e)

    def getVideoViewUrl(self,dir,fileName,shortenFalg=True):
        if not self.SID:
            return None
            
        fullPath = os.path.join(dir,fileName)
        fullPath = fullPath.replace('/var/services','')

        dLink = self.bin2hex(fullPath)
        ext = Path(fileName).suffix
        url = self.url
        url = url.replace('{SYNOLOGY_HOST_IP}',self.hostIP)
        url = url.replace('{SYNOLOGY_HOST_PORT}',self.hostPort)        
        #url = url.replace('{fileName}',fileName)
        url = url.replace('{fileName}','memory'+ext)

        params = {"dlink":dLink,"_sid":self.SID,"mode":"open"}
        encodeParams = parse.urlencode(params)

        url=url+encodeParams

        #url = url.replace('{dLink}',dLink)
        #url = url.replace('{SID}',self.SID)

        return self.CreateShortUrl(url) if shortenFalg else url

    def CreateShortUrl(self,url):
        apiurl = "http://tinyurl.com/api-create.php?url="
        tinyurl = urllib.request.urlopen(apiurl + url).read()    
        return tinyurl.decode("utf-8")        
        