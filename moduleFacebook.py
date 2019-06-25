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

import facebook
from html.parser import HTMLParser

from configMod import *
from moduleContent import *

class moduleFacebook(Content):

    def __init__(self):
        super().__init__()
        self.user = None
        self.fc = None

    def setClient(self, facebookAC='me'):
        logging.info("    Connecting Facebook")
        try:
            config = configparser.ConfigParser()
            config.read(CONFIGDIR + '/.rssFacebook')

            self.user = facebookAC
            try:
                oauth_access_token = config.get("Facebook", "oauth_access_token")
                graph = facebook.GraphAPI(oauth_access_token, version='3.0') 
                self.fc =graph
                self.setPage(facebookAC)
            except: 
                logging.warning("Facebook authentication failed!") 
                logging.warning("Unexpected error:", sys.exc_info()[0]) 
                print("Fail!")
        except:
            logging.warning("Facebook authentication failed!")
            logging.warning("Unexpected error:", sys.exc_info()[0])
            print("Fail!")

    def setPage(self, facebookAC='me'):
        perms = ['publish_actions','manage_pages','publish_pages'] 
        pages = self.fc.get_connections("me", "accounts") 
        
        if (facebookAC != 'me'): 
            for i in range(len(pages['data'])): 
                logging.debug("%s %s"% (pages['data'][i]['name'], facebookAC)) 
                if (pages['data'][i]['name'] == facebookAC): 
                    logging.info("    Writing in... %s"% pages['data'][i]['name']) 
                    graph2 = facebook.GraphAPI(pages['data'][i]['access_token']) 
                    self.page = graph2
                    self.pageId = pages['data'][i]['id']
                    break
                else: 
                    # Publishing as me 
                    self.page = facebookAC 


    def getClient(self):
        return self.fc
 
    def setPosts(self):
        logging.info("  Setting posts")
        self.posts = []
        count = 5
        posts = self.page.get_connections(self.pageId, connection_name='posts') 

        for post in posts['data']:
            self.posts.append(post)

        outputData = {}
        serviceName = 'Facebook'
        outputData[serviceName] = {'sent': [], 'pending': []}
        for post in self.getPosts():
            (page, idPost) = post['id'].split('_')
            url = 'https://facebook.com/' + page + '/posts/' + idPost
            outputData[serviceName]['sent'].append((post['message'], url, 
                    '',     
                    post['created_time'], '','','','',''))

        self.postsFormatted = outputData

    def publishPost(self, post, link='', comment=''):
        logging.info("    Publishing in Facebook...")
        h = HTMLParser()
        post = h.unescape(post)
        try:
            logging.info("    Publishing in Facebook: %s" % post)
            res = self.page.put_object(self.pageId, "feed", message=post, link=link)
            logging.debug("Res: %s" % res)
            if 'id' in res:
                #id2, id1 = res['id'].split('_')
                #urlFb = 'https://www.facebook.com/permalink.php?story_fbid=%s&id=%s'%(id1, id2)
                urlFb = 'https://www.facebook.com/%s/posts/%s' % (self.user,res['id'].split('_')[1])
                logging.info("Post: %s" % urlFb)
                return(urlFb)

            return(res)
        except:        
            return(self.report('Facebook', post, link, sys.exc_info()))

def main():

    import moduleFacebook

    fc = moduleFacebook.moduleFacebook()

    fc.setClient('Enlaces de fernand0')

    fc.setPosts()
    for post in fc.getPostsFormatted()['Facebook']['sent']:
        print("%s: %s" %(post[0], post[1]))

    fc.publishPost("Prueba")

if __name__ == '__main__':
    main()

