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

from linkedin import linkedin
from html.parser import HTMLParser

from configMod import *
from moduleContent import *

class moduleLinkedin(Content):

    def __init__(self):
        super().__init__()
        self.user = None
        self.ln = None

    def setClient(self, linkedinAC=""):
        logging.info("    Connecting Linkedin")
        try:
            config = configparser.ConfigParser()
            config.read(CONFIGDIR + '/.rssLinkedin')

            self.user = linkedinAC    

            CONSUMER_KEY = config.get("Linkedin", "CONSUMER_KEY") 
            CONSUMER_SECRET = config.get("Linkedin", "CONSUMER_SECRET") 
            USER_TOKEN = config.get("Linkedin", "USER_TOKEN") 
            USER_SECRET = config.get("Linkedin", "USER_SECRET") 
            RETURN_URL = config.get("Linkedin", "RETURN_URL"),

            try: 
                authentication = linkedin.LinkedInDeveloperAuthentication(
                         CONSUMER_KEY,
                         CONSUMER_SECRET,
                         USER_TOKEN,
                         USER_SECRET,
                         RETURN_URL,
                         linkedin.PERMISSIONS.enums.values())

                l = linkedin.LinkedInApplication(authentication)
            except:
                logging.warning("LinkedIn authentication failed!")
                logging.warning("Unexpected error:", sys.exc_info()[0])
        except:
            logging.warning("Account not configured")
            l = None

        self.ln = l
 
    def getClient(self):
        return self.ln
 
    def setPosts(self):
        logging.info("  Setting posts")
        self.posts = []

        outputData = {}
        serviceName = 'Linkedin'
        outputData[serviceName] = {'sent': [], 'pending': []}
        for post in self.getPosts():
            #print(post)
            #url = 'https://twitter.com/' + post['user']['screen_name'] + '/status/' + str(post['id'])
            outputData[serviceName]['sent'].append((post['text'], url, 
                    post['user']['screen_name'],     
                    post['created_at'], '','','','',''))

        self.postsFormatted = outputData

    def publishPost(self, post, link, comment):
        logging.info("    Publishing in LinkedIn...")
        if comment == None:
            comment = ''
        postC = comment + " " + post + " " + link
        h = HTMLParser()
        postC = h.unescape(post)
        try:
            logging.info("    Publishing in Linkedin: %s" % post)
            if link: 
                res = self.ln.submit_share(post, link, '') 
            else: 
                res = self.ln.submit_share(comment = postC)
            logging.info("Res: %s" % res)
            return res
        except:        
            return(self.report('LinkedIn', post, link, sys.exc_info()))


def main():

    import moduleLinkedin

    ln = moduleLinkedin.moduleLinkedin()

    ln.setClient('fernand0')

    ln.setPosts()
    for tweet in ln.getPostsFormatted()['Linkedin']['pending']:
        print("@%s: %s" %(tweet[2], tweet[0]))

    ln.publishPost("Prueba",'','')

if __name__ == '__main__':
    main()

