# -*- coding: UTF-8 -*-
from im.TelegramMediaType import TelegramMediaType

class TelegramBotMedia():
    def __init__(self,mediaType,uri,caption,thumbURI=''):
        if not isinstance(mediaType,TelegramMediaType):
            raise Exception('type must be TelegramMediaType')

        self.mediaType = mediaType
        self.caption = caption
        self.uri = uri
        self.thumbURI = thumbURI