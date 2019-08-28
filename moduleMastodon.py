#!/usr/bin/env python

import configparser
import mastodon
import os
import sys

from html.parser import HTMLParser
from configMod import *
from moduleContent import *


class moduleMastodon(Content):


    def __init__(self):
        super().__init__()

    def setClient(self, user):
        logging.info("     Connecting Mastodon")
        if True:
            maCli = mastodon.Mastodon( 
               access_token = CONFIGDIR + '.'+'pytooter_usercred.secret', 
               api_base_url = 'https://mastodon.social'
            )

        else: 
            logging.warning("Mastodon authentication failed!") 
            logging.warning("Unexpected error:", sys.exc_info()[0])

        self.ma = maCli
        self.user = user


    def getClient(self):
        return self.ma

    def setPosts(self):
        logging.info("  Setting posts")
        self.posts = []
        posts = self.getClient().timeline_home()
        for toot in  posts:
            self.posts.append(toot)

    def publishPost(self, post, link, comment):
        logging.debug("    Publishing in Mastodon...")
        if comment == None:
            comment = ''
        title = post
        content = comment
        post = comment + " " + post + " " + link
        h = HTMLParser()
        post = h.unescape(post)
        try:
            logging.info("     Publishing in Mastodon: %s" % post)
            res = self.getClient().toot(post)
            logging.debug("Res: %s" % res)
            if 'uri' in res:
                logging.info("     Toot: %s" % res['uri'])
                return(res['uri'])
            return res
        except:        
            return(self.report('Mastodon', post, link, sys.exc_info()))

    def getPostTitle(self, post):
        if 'content' in post:
            return(post['content'].replace('\n', ' '))

def main():
    import moduleMastodon

    mastodon = moduleMastodon.moduleMastodon()
    mastodon.setClient('fernand0')
    mastodon.setPosts()
    mastodon.publishPost("I'll publish several links each day about technology, social internet, security, ... as in", 'https://twitter.com/fernand0', '')


if __name__ == '__main__':
    main()
