# -*- coding: UTF-8 -*-
import requests, os
from im.IMMessage import IMMessage
from im.TelegramMediaType import TelegramMediaType
from im.TelegramBotMedia import TelegramBotMedia
import json

"""
    Telegram Bot API handler
"""

class TelegramBot(IMMessage):
    BaseUrl ='https://api.telegram.org/bot{TOKEN}/' 
    TextApi ='sendMessage'
    PhotoApi = 'sendPhoto'
    VideoApi = 'sendVideo'
    MediaGroupApi = 'sendMediaGroup'
    def __init__(self, token,chatId):
        self.token =token
        self.BaseUrl = self.BaseUrl.replace('{TOKEN}',token)
        self.chatId = chatId

    def sendText(self, msg):
        url = self.BaseUrl+self.TextApi
        payload = {'chat_id':self.chatId,'text':msg}
        r = requests.post(url,params = payload)
        return r

    def sendVideo(self,videoURI,caption="",thumbURI=None):
        url = self.BaseUrl+self.VideoApi
        files = {}
        if os.path.exists(videoURI):          
            payload = {'chat_id':self.chatId,'caption':caption}
            files = {'video': open(videoURI, 'rb')}
        else:
            payload = {'chat_id':self.chatId,'caption':caption,'video':videoURI}

        if thumbURI:
            if os.path.exists(thumbURI):   
                payload.update({'thumb':'attach://media_01'})
                files.update({'media_01':open(thumbURI, 'rb')})
            else:
                payload.update({'thumb':thumbURI})

        r = requests.post(url,params = payload, files = files)
        return r

    def sendPhoto(self,picURI,caption=""):
        url = self.BaseUrl+self.PhotoApi    
        if os.path.exists(picURI):
            payload = {'chat_id':self.chatId,'caption':caption}
            files = {'photo': open(picURI, 'rb')}
            r = requests.post(url,params = payload, files = files)
        else:
            payload = {'chat_id':self.chatId,'caption':caption,'photo':picURI}
            r = requests.post(url,params = payload)
        return r

    def sendMediaGroup(self,botMedias):
        if len(botMedias)<=1:
            raise Exception('Media length must greater than 1')
        
        if not isinstance(botMedias[0],TelegramBotMedia):
            raise Exception('type must be TelegramBotMedia')

        url = self.BaseUrl+self.MediaGroupApi  
        #medias = [{'type':media.mediaType.value,'media':'attach://media_{}'.format(idx),'caption':media.caption} for idx,media in enumerate(botMedias)]
        files = {}
        medias = []
        for idx,media in enumerate(botMedias):
            if os.path.exists(media.uri):
                m={'type':media.mediaType.value,'media':'attach://media_{}'.format(idx),'caption':media.caption}
                files.update({'media_{}'.format(idx):open(media.uri,'rb')})
            else:
                m={'type':media.mediaType.value,'media':media.uri,'caption':media.caption}

            if media.thumbURI:
                if os.path.exists(media.thumbURI):
                    m.update({'thumb':'attach://thumb_{}'.format(idx)})
                    files.update({'thumb_{}'.format(idx):open(media.thumbURI, 'rb')})                    
                else:
                    m.update({'thumb':media.thumbURI})
            #print(m)
            medias.append(m)
        
        payload={'chat_id':self.chatId,'media':json.dumps(medias)}
        #print(files)
        r = requests.post(url,params=payload,files=files) 

        return r

      

