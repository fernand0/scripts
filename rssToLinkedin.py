#!/usr/bin/python
# encoding: utf-8
#
# Very simple Python program to publish a notification with the last RSS entry
# of a feed in a Linkedin Page. It shows the blogs available and allows to
# select one of them.
# 
# It has a configuration file with a number of blogs with:
#	- The RSS feed of the blog
#	- The Twitter account where the news will be published
#	- The Facebook page where the news will be published
# It uses a configuration file that has one section with the authentication
# tokens provided by Linkedin.
#


import ConfigParser, os, re, sys
import feedparser
from bs4 import BeautifulSoup
from bs4 import NavigableString
from bs4 import Tag
from linkedin import linkedin

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

i = 0


soup = BeautifulSoup(feed.entries[i].title)
theTitle = soup.get_text()
theLink =  feed.entries[i].link

soup = BeautifulSoup(feed.entries[i].summary)

theSummary = soup.get_text()

print theSummary.encode('utf-8')[0:693].rsplit(' ', 1)[0]+" [...]"

pageImage = soup.findAll("img")
#  Only the first one
if len(pageImage) > 0:
	imageLink = (pageImage[0]["src"])
else:
	imageLine = None

config = ConfigParser.ConfigParser()
config.read([os.path.expanduser('~/.rssLinkedin')])

authentication = linkedin.LinkedInDeveloperAuthentication(
			config.get("Linkedin", "CONSUMER_KEY"), 
			config.get("Linkedin", "CONSUMER_SECRET"), 
			config.get("Linkedin", "USER_TOKEN"), 
			config.get("Linkedin", "USER_SECRET"),
			config.get("Linkedin", "RETURN_URL"), 
			linkedin.PERMISSIONS.enums.values())
application = linkedin.LinkedInApplication(authentication)

comment='Publicado!'

application.submit_share(comment, theTitle, theSummary, theLink, imageLink)


