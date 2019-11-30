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
        logging.info("     Connecting Facebook")
        try:
            config = configparser.ConfigParser()
            config.read(CONFIGDIR + '/.rssFacebook')

            self.user = facebookAC
            try:
                oauth_access_token = config.get("Facebook", "oauth_access_token")
                graph = facebook.GraphAPI(oauth_access_token, version='3.0') 
                self.fc = graph
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
        self.pages = pages

        if (facebookAC != 'me'): 
            for i in range(len(pages['data'])): 
                logging.debug("%s %s"% (pages['data'][i]['name'], facebookAC)) 
                if (pages['data'][i]['name'] == facebookAC): 
                    logging.info("     Writing in... %s"% pages['data'][i]['name']) 
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
            if 'message' in post:
                self.posts.append(post)

        outputData = {}
        serviceName = 'Facebook'
        outputData[serviceName] = {'sent': [], 'pending': []}
        for post in self.getPosts():
            (page, idPost) = post['id'].split('_')
            url = 'https://facebook.com/' + page + '/posts/' + idPost
            outputData[serviceName]['sent'].append((post['message'], url, 
                    '', post['created_time'], '','','','',''))

        self.postsFormatted = outputData

    def publishPost(self, post, link='', comment=''):
        logging.debug("    Publishing in Facebook...")
        if comment == None:
            comment = ''
        post = comment + " " + post
        h = HTMLParser()
        post = h.unescape(post)
        res = None
        try:
            logging.info("     Publishing: %s" % post)
            res = self.page.put_object('me', "feed", message=post, link=link)
            #res = self.page.put_object(self.fc.get_object('me')['id'], "feed", message=post, link=link)
            if res:
                logging.debug("Res: %s" % res)
                if 'id' in res:
                    urlFb = 'https://www.facebook.com/%s' % res['id']
                    logging.info("     Link: %s" % urlFb)
                    return(urlFb)

                return(res)
        except:        
            return(self.report('Facebook', post, link, sys.exc_info()))

    def getPostTitle(self, post):
        if 'message' in post:
            return(post['message'].replace('\n', ' '))

def main():

    import moduleFacebook

    fc = moduleFacebook.moduleFacebook()

    fc.setClient('Enlaces de fernand0')
    print(fc.user)
    print(fc.fc.get_object(id='me'))
    sys.exit()
    fc.setPage()

    for page in fc.pages['data']:
        print(page['name'], page)
        if page['name'] == 'F.T.G.':
            idPage = page['id']
            tokenPage = page['access_token']

    link= "https://graph.facebook.com/v5.0/%s?fields=instagram_business_account&access_token={%s}"%(idPage,tokenPage)
    print(link)
    sys.exit()


    fc.setPosts()
    posts = fc.getPosts()
    for post in posts:
        print(post)
        #print("%s: %s" %(post[0], post[1]))

    #fc.publishPost("Prueba")

if __name__ == '__main__':
    main()

