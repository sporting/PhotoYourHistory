# -*- coding: UTF-8 -*-

url ="http://quickconnect.to/{quickConnectId}}/?launchApp=SYNO.SDS.VideoPlayer2.Application&launchParam=ieMode=9&is_drive=false&path={FILE_NAME}}&ieMode=9"

def VideoPlayerLaunch(quickConnectId,fileName):
    actualFileName = fileName.replace('/var/services','')
    actualUrl = url.replace('{quickConnectId}',quickConnectId)
    actualUrl = actualUrl.replace('{FILE_NAME}',actualFileName)

    return actualUrl
