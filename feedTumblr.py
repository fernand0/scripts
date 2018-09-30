#!/usr/bin/env python
# encoding: utf-8

import os
import sys
import configparser
import re
import logging
import time
import moduleSocial
#import pytumblr
from tumblpy import Tumblpy
# https://github.com/michaelhelmick/python-tumblpy
import urllib
from feedgen.feed import FeedGenerator
#https://github.com/lkiesow/python-feedgen

# This program gets the posts from a tumblr blog using the API and constructs a
# minimal RSS feed in order to avoid the problem with GDPR limitations with the
# official RSS feed.

def main():

    client = moduleSocial.connectTumblr()

    posts = client.posts('fernand0')
    
    fg = FeedGenerator()
    fg.id(posts['blog']['url'])
    fg.title(posts['blog']['title'])
    fg.author( {'name':posts['blog']['name'],'email':'fernand0@elmundoesimperfecto.com'} )
    fg.link( href=posts['blog']['url'], rel='alternate' )
    fg.subtitle('Alternate feed due to Tumblr GDPR restrictions')
    fg.language('en')

    print(len(posts['posts']))
    for i in range(len(posts['posts'])):
        fe = fg.add_entry()
        print(posts['posts'][i]['post_url'])
        if 'title' in posts['posts'][i]:
            title = posts['posts'][i]['title']
            print('T', posts['posts'][i]['title'])
        else:
            title = posts['posts'][i]['summary'].split('\n')[0]
            print('S', posts['posts'][i]['summary'].split('\n')[0])
        fe.title(title)
        fe.link(href=posts['posts'][i]['post_url'])
        fe.id(posts['posts'][i]['post_url'])

    print(fg.atom_file('/var/www/html/elmundoesimperfecto/tumblr.xml'))

    sys.exit()
