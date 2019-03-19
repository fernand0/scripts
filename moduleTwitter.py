#!/usr/bin/env python

import configparser
import pickle
import os
import moduleSocial
import moduleBuffer
import moduleCache
import urllib
import logging
from slackclient import SlackClient
import sys
import click
import requests
from bs4 import BeautifulSoup
from bs4 import Tag

from twitter import *
#https://pypi.python.org/pypi/twitter
#http://mike.verdone.ca/twitter/
#https://github.com/sixohsix/twitter/tree

from configMod import *
from moduleContent import *

class moduleTwitter(Content):

    def __init__(self):
        super().__init__()

    def setClient(self, twitterAC):
        logging.info("    Connecting Twitter")
        try:
            config = configparser.ConfigParser()
            config.read(CONFIGDIR + '/.rssTwitter')

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
        tweets = self.tc.statuses.home_timeline()
        for tweet in tweets:
            self.posts.append(tweet)

        outputData = {}
        serviceName = 'Twitter'
        outputData[serviceName] = {'sent': [], 'pending': []}
        for post in self.getPosts():
            url = 'https://twitter.com/' + post['user']['screen_name'] + '/status/' + str(post['id'])
            outputData[serviceName]['pending'].append((post['text'], url, 
                    post['user']['screen_name'],     
                    post['created_at'], '','','','',''))

        self.postsFormatted = outputData

def main():

    import moduleTwitter

    tw = moduleTwitter.moduleTwitter()

    tw.setClient('fernand0')

    tw.setPosts()
    print(tw.getPostsFormatted())

if __name__ == '__main__':
    main()

