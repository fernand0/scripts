#!/usr/bin/python
# encoding: utf-8
#
# Very simple Python program to publish the last RSS entry of a feed
# in a Twitter account. It shows the blogs available and allows to
# select one of them.
# 
# It has a configuration file with a number of blogs with:
#	- The RSS feed of the blog
#	- The Twitter account where the news will be published
#	- The Facebook page where the news will be published
# It uses a configuration file that has two sections:
#  	- The appKeys section contains the consumer key and secret
#  	for the app.
#	- The other section identifies a twitter account (if we need,
#	we can have more than one account) with the name defined in
#	the previous config file. It includes the token key and the
#	token secret.
# 

import ConfigParser, os
import re, sys
import feedparser
from twitter import *
from bs4 import BeautifulSoup
from bs4 import BeautifulStoneSoup


reload(sys)
sys.setdefaultencoding("UTF-8")

config = ConfigParser.ConfigParser()
config.read([os.path.expanduser('~/.rssBlogs')])

print "Configured blogs:"

i=1
for section in config.sections():
	print str(i), ')', section, config.get(section, "rssFeed")
	i = i + 1

if (int(i)>1):
	i = raw_input ('Select one: ')
else:
	i = 1

print "You have chosen ", config.get("Blog"+str(i), "rssFeed")

rssFeed = config.get("Blog"+str(i), "rssFeed")
feed = feedparser.parse(rssFeed)

i = 0 # It will publish the last added item

soup = BeautifulSoup(feed.entries[i].title)
theTitle = soup.get_text()
theLink =  feed.entries[i].link
comment='Publicado!'


statusTxt = comment+" "+theTitle.contents[0].get_text()+" "+theLink


twitterAc = config.get("Blog"+str(i), "twitterAC")







config.read([os.path.expanduser('~/.rssTwitter')])

CONSUMER_KEY = config.get("appKeys", "CONSUMER_KEY")
CONSUMER_SECRET = config.get("appKeys", "CONSUMER_SECRET")
TOKEN_KEY = config.get(twitterAc, "TOKEN_KEY")
TOKEN_SECRET = config.get(twitterAc, "TOKEN_SECRET")


authentication  = OAuth(
			TOKEN_KEY, 
			TOKEN_SECRET, 
			CONSUMER_KEY, 
			CONSUMER_SECRET)



t = Twitter(auth=authentication)

t.statuses.update(status=statusTxt)
