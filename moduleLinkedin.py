#!/usr/bin/env python

import configparser
import pickle
import os
import logging
import sys
import requests

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

            #self.CONSUMER_KEY = config.get("Linkedin", "CONSUMER_KEY") 
            #self.CONSUMER_SECRET = config.get("Linkedin", "CONSUMER_SECRET") 
            #self.USER_TOKEN = config.get("Linkedin", "USER_TOKEN") 
            #self.USER_SECRET = config.get("Linkedin", "USER_SECRET") 
            #self.RETURN_URL = config.get("Linkedin", "RETURN_URL")
            self.ACCESS_TOKEN = config.get("Linkedin", "ACCESS_TOKEN")
            self.URN = config.get("Linkedin", "URN")
        except:
            logging.warning("Account not configured")

 
    def getClient(self):
        return None
 
    def setPosts(self):
        logging.info("  Setting posts")
        self.posts = []

    def publishPost(self, post, link, comment):
        # Based on https://github.com/gutsytechster/linkedin-post
        access_token = self.ACCESS_TOKEN
        urn = self.URN

        author = f"urn:li:person:{urn}"

        headers = {'X-Restli-Protocol-Version': '2.0.0',
           'Content-Type': 'application/json',
           'Authorization': f'Bearer {access_token}'}

        api_url_base = 'https://api.linkedin.com/v2/'
        api_url = f'{api_url_base}ugcPosts'
    
        logging.info("    Publishing in LinkedIn...")
        if comment == None:
            comment = ''
        postC = comment + " " + post + " " + link
        h = HTMLParser()
        postC = h.unescape(post)
        try:
            logging.info("    Publishing in Linkedin: %s" % post)
            if link: 
                post_data = {
                    "author": author,
                    "lifecycleState": "PUBLISHED",
                    "specificContent": {
                        "com.linkedin.ugc.ShareContent": {
                            "shareCommentary": {
                                "text": comment
                            },
                            "shareMediaCategory": "ARTICLE",
                            "media": [
                                { "status": "READY",
                                    #"description": {
                                    #    "text": "El mundo es imperfecto"
                                    #    },
                                    "originalUrl": link,
                                    "title": {
                                        "text": post
                                    }
                               }
                            ]
                        },
                    },
                    "visibility": {
                        "com.linkedin.ugc.MemberNetworkVisibility": "CONNECTIONS"
                    },
                }
            else: 
                post_data = {
                     "author": author,
                     "lifecycleState": "PUBLISHED",
                     "specificContent": {
                         "com.linkedin.ugc.ShareContent": {
                             "shareCommentary": {
                                 "text": post
                             },
                             "shareMediaCategory": "NONE"
                         },
                     },
                     "visibility": {
                         "com.linkedin.ugc.MemberNetworkVisibility": "CONNECTIONS"
                     },
                }

            res = requests.post(api_url, headers=headers, json=post_data)
            logging.info("Res: %s" % res)
            if res.status_code == 201: 
                return("Success ") 
            else: 
                return(res.content)
        except:        
            return(self.report('LinkedIn', post, link, sys.exc_info()))


def main():

    import moduleLinkedin

    ln = moduleLinkedin.moduleLinkedin()

    ln.setClient('fernand0')

    print(ln.publishPost("Probando á é í ó ú — ",'',''))
    print(ln.publishPost("El mundo es Imperfecto",'http://elmundoesimperfecto.com/',''))

if __name__ == '__main__':
    main()

