#!/usr/bin/env python

import configparser
import pickle
import os
import moduleSocial
import moduleBuffer
import moduleCache
import urllib
import logging
import sys
import click
import requests
from bs4 import BeautifulSoup
from bs4 import Tag

from twitter import *
#https://pypi.python.org/pypi/twitter
#http://mike.verdone.ca/twitter/
#https://github.com/sixohsix/twitter/tree
from html.parser import HTMLParser

from configMod import *
from moduleContent import *

class moduleTwitter(Content):

    def __init__(self):
        super().__init__()
        self.user = None
        self.tc = None

    def setClient(self, twitterAC):
        logging.info("     Connecting Twitter")
        try:
            config = configparser.ConfigParser()
            config.read(CONFIGDIR + '/.rssTwitter')

            self.user = twitterAC
            CONSUMER_KEY = config.get("appKeys", "CONSUMER_KEY")
            CONSUMER_SECRET = config.get("appKeys", "CONSUMER_SECRET")
            TOKEN_KEY = config.get(twitterAC, "TOKEN_KEY")
            TOKEN_SECRET = config.get(twitterAC, "TOKEN_SECRET")

            try:
                authentication = OAuth(
                            TOKEN_KEY,
                            TOKEN_SECRET,
                            CONSUMER_KEY,
                            CONSUMER_SECRET)
                t = Twitter(auth=authentication)
            except:
                logging.warning("Twitter authentication failed!")
                logging.warning("Unexpected error:", sys.exc_info()[0])
        except:
            logging.warning("Account not configured")
            t = None

        self.tc = t
 
    def getClient(self):
        return self.tc
 
    def setPosts(self):
        logging.info("  Setting posts")
        self.posts = []
        #tweets = self.tc.statuses.home_timeline()
        try: 
            tweets = self.tc.statuses.user_timeline()
        except:
            tweets = []

        for tweet in tweets:
            self.posts.append(tweet)

        outputData = {}
        serviceName = 'Twitter'
        outputData[serviceName] = {'sent': [], 'pending': []}
        for post in self.getPosts():
            #print(post)
            url = 'https://twitter.com/' + post['user']['screen_name'] + '/status/' + str(post['id'])
            outputData[serviceName]['sent'].append((post['text'], url, 
                    post['user']['screen_name'],     
                    post['created_at'], '','','','',''))

        self.postsFormatted = outputData

    def publishPost(self, post, link='', comment=''):
        logging.debug("     Publishing in Twitter...")
        if comment == None:
            comment = ''
        post = comment + " " + post
        h = HTMLParser()
        post = h.unescape(post)
        res = None
        try:
            logging.info("     Publishing: %s" % post)
            post = post[:(240 - (len(link) + 1))]
            res = self.tc.statuses.update(status=post+" " + link)

            if res: 
                logging.debug("Res: %s" % res)
                urlTw = "https://twitter.com/%s/status/%s" % (self.user, res['id'])
                logging.info("     Link: %s" % urlTw)
                return(urlTw)

        except:        
            return(self.report('Twitter', post, link, sys.exc_info()))

    def getPostTitle(self, post):
        if 'text' in post:
            return(post['text'])
        else:
            return ''

    def search(self, text):
        logging.debug("     Searching in Twitter...")
        try:
            res = self.tc.search.tweets(q=text)

            if res: 
                logging.debug("Res: %s" % res)
                return(res)
        except:        
            return(self.report('Twitter', text, sys.exc_info()))




def main():

    import moduleTwitter

    tw = moduleTwitter.moduleTwitter()

    tw.setClient('fernand0')

    tw.setPosts()
    res = tw.search('url:fernand0')
    for tt in res['statuses']: 
        print(tt)
        print('- @{0} {1} https://twitter.com/{0}/status/{2}'.format(tt['user']['name'], tt['text'], tt['id_str']))
    sys.exit()
    #for tweet in tw.getPosts():
    #    print(tweet)
    #    #print("@%s: %s" %(tweet[2], tweet[0]))

    tw.publishPost("Inscripciones 2019 | Congreso Web", "http://congresoweb.es/cw19/inscripciones/", '')

if __name__ == '__main__':
    main()

