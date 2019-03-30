#!/usr/bin/env python

import configparser
import os
import telepot

from configMod import *
from moduleContent import *

class moduleTelegram(Content):

    def __init__(self):
        super().__init__()

    def setClient(self):
        logging.info("     Connecting Telegram")
        try:
            config = configparser.ConfigParser() 
            config.read(CONFIGDIR + '/.rssTelegram') 
            
            TOKEN = config.get("Telegram", "TOKEN") 
            
            try: 
                bot = telepot.Bot(TOKEN) 
                meMySelf = bot.getMe() 
            except: 
                logging.warning("Telegram authentication failed!") 
                logging.warning("Unexpected error:", sys.exc_info()[0])
        except: 
            logging.warning("Account not configured") 
            bot = None

        self.tc = bot

    def getClient(self):
        return self.tc

    def setPosts(self):
        logging.info("  Setting posts")
        self.posts = []
        #tweets = self.tc.statuses.home_timeline()
        posts = self.tc.getUpdates()

        print(posts)


def main():
    import moduleTelegram

    tel = moduleTelegram.moduleTelegram()

    tel.setClient()

    tel.setPosts()


if __name__ == '__main__':
    main()

