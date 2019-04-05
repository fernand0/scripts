#!/usr/bin/env python

import configparser
import os
import telepot

from configMod import *
from moduleContent import *

class moduleTelegram(Content):

    def __init__(self):
        super().__init__()

    def setClient(self, channel):
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
        self.channel = channel

    def getClient(self):
        return self.tc

    def setPosts(self):
        logging.info("  Setting posts")
        self.posts = []
        #tweets = self.tc.statuses.home_timeline()
        posts = self.tc.getUpdates()

        print(posts)

    def publishPost(self, post, link, comment):
        logging.info("    Publishing in Twitter...")
        bot = self.tc
        title = post
        content = comment
        links = ""
        channel = self.channel

        from html.parser import HTMLParser
        h = HTMLParser()
        title = h.unescape(title)
        text = '<a href="'+link+'">'+title+ "</a>\n" + content + '\n\n' + links
        textToPublish2 = ""
        if len(text) < 4090:
            textToPublish = text
            links = ""
        else:
            text = '<a href="'+link+'">'+title + "</a>\n" + content
            textToPublish = text[:4080] + ' ...'
            textToPublish2 = '... '+ text[4081:]

        logging.info("text to "+ textToPublish)
        logging.info("text to 2"+ textToPublish2)

        bot.sendMessage('@'+channel, textToPublish, parse_mode='HTML') 
        if textToPublish2:
            try:
                bot.sendMessage('@'+channel, textToPublish2[:4090], parse_mode='HTML') 
            except:
                bot.sendMessage('@'+channel, "Text is longer", parse_mode='HTML') 
        if links:
            bot.sendMessage('@'+channel, links, parse_mode='HTML') 


def main():
    import moduleTelegram

    config = configparser.ConfigParser()
    config.read(CONFIGDIR + '/.rssBlogs')

    section = 'Blog2'
    url = config.get(section, "url")
    rssFeed = config.get(section, "rssFeed")
    logging.info(" Blog RSS: %s"% rssFeed)
    import moduleRss
    blog = moduleRss.moduleRss()
    # It does not preserve case
    blog.setRssFeed(rssFeed)
    blog.setUrl(url)
    blog.setPosts()
    post = blog.obtainPostData(1)

    tel = moduleTelegram.moduleTelegram()

    tel.setClient('testFernand0')

    tel.setPosts()
    title = post[0]
    link = post[1]
    content = post[7]
    links = post[8]
    tel.publishPost(title,link,content + '\n\n' + links)


if __name__ == '__main__':
    main()

