# -*- coding: UTF-8 -*-
import urllib.request
from urllib import parse

#url ="http://quickconnect.to/{quickConnectId}/?launchApp=SYNO.SDS.VideoPlayer2.Application&launchParam=ieMode=9&is_drive=false&path={FILE_NAME}&ieMode=9"
url ="http://quickconnect.to/{quickConnectId}/?"

def VideoPlayerLaunch(quickConnectId,fileName):
    actualFileName = fileName.replace('/var/services','')

    params = {"launchApp":"SYNO.SDS.VideoPlayer2.Application","launchParam":"ieMode=9","is_drive":"false","path":actualFileName,"ieMode":"9"}
    res = parse.urlencode(params)
    actualUrl = url.replace('{quickConnectId}',quickConnectId)+res
    #actualUrl = actualUrl.replace('{FILE_NAME}',actualFileName)
    #print(actualUrl)
    shortenUrl = CreateShortUrl(actualUrl)

    return shortenUrl


def CreateShortUrl(url):
    apiurl = "http://tinyurl.com/api-create.php?url="
    tinyurl = urllib.request.urlopen(apiurl + url).read()    
    return tinyurl.decode("utf-8")