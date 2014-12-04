#!/usr/bin/python
# encoding: utf-8
#
# Very simple Python program to publish the last RSS entry of a feed in 
# a Twitter account
# 
# It has a configuration file with a number of blogs with:
#	- The RSS feed of the blog
#	- The Twitter account where the news will be published
#	- The Facebook page where the news will be published
# It uses a configuration file that has two sections:
#  	- The appKeys section contains the consumer key and secret for the
#         app.
#	- The other section identifies a twitter account (if we need, we can
#         have more than one account) with the name defined in the previous 
#         config file. It includes the token key and the 
#         token secret.
# 

import ConfigParser, os
from twitter import *
import feedparser
from BeautifulSoup import BeautifulSoup

config = ConfigParser.ConfigParser()

config.read([os.path.expanduser('~/.rssBlogs')])
rssFeed = config.get("Blog1", "rssFeed")
twitterAc = config.get("Blog1", "twitterAc")


config.read([os.path.expanduser('~/.rssTwitter')])
CONSUMER_KEY = config.get("appKeys", "CONSUMER_KEY")
CONSUMER_SECRET = config.get("appKeys", "CONSUMER_SECRET")
TOKEN_KEY = config.get(twitterAc, "TOKEN_KEY")
TOKEN_SECRET = config.get(twitterAc, "TOKEN_SECRET")


print rssFeed

def stripAllTags( html ):
        if html is None:
                return None
        return ''.join( BeautifulSoup( html ).findAll( text = True ) ) 

feed = feedparser.parse(rssFeed)

i = 0 # It will publish the last added item

theTitle = feed.entries[i].title
theLink =  feed.entries[i].link
theSummary =  stripAllTags(feed.entries[i].summary)


statusTxt = theTitle+" "+theLink
print(statusTxt)

t = Twitter(
    auth=OAuth(TOKEN_KEY, TOKEN_SECRET, CONSUMER_KEY, CONSUMER_SECRET))

t.statuses.update(status=statusTxt)
    
