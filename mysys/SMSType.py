# -*- coding: UTF-8 -*-
from enum import Enum


class SMSType(Enum):
    LineNotify = 'LINE NOTIFY'
    LineMessagingApi = 'LINE MESSAGING API'
    TelegramBot = 'TELEGRAM BOT'

