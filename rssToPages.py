#!/usr/bin/python
# encoding: utf-8
#
# Very simple Python program to publish the last RSS entry of a feed in 
# a Facebook Page. It shows the blogs available and allows to select 
# one of them.
# 
# It has a configuration file with a number of blogs with:
#	- The RSS feed of the blog
#	- The Twitter account where the news will be published
#	- The Facebook page where the news will be published
# It uses a configuration file that has two sections:
#  	- The oauth access token
#

import ConfigParser, os, re
import pprint
import feedparser
from bs4 import BeautifulSoup
from bs4 import NavigableString
from bs4 import Tag
import facebook
import sys


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
pageFB = config.get("Blog"+str(i), "pageFB")
if (config.has_option("Blog"+str(i), "linksToAvoid")):
	linksToAvoid = config.get("Blog"+str(i), "linksToAvoid")
else:
	linksToAvoid = ""



feed = feedparser.parse(rssFeed)

i = 0


soup = BeautifulSoup(feed.entries[i].title)
theTitle = soup.get_text()
theLink =  feed.entries[i].link

soup = BeautifulSoup(feed.entries[i].summary)

# Now the links

j = 0
linksTxt = ""
for link in soup("a"):
	if not isinstance(link.contents[0], Tag):
		# We want to avoid embdeded tags (mainly <img ... )
		
		print linksToAvoid
		print re.escape(linksToAvoid)
		print str(link['href'])
		print re.search(linksToAvoid, link['href'])
		if ((linksToAvoid =="") 
			or (not re.search(linksToAvoid, link['href']))):
			link.append(" ["+str(j)+"]")
			linksTxt = linksTxt + "["+str(j)+"] " + link.contents[0] + "\n"
			linksTxt = linksTxt + "    " + link['href'] + "\n"
			j =  j + 1


#theSummary = theTitle+"\n"
theSummary = soup.get_text()
theSummary = theSummary+"\n\n"

if linksTxt != "":
	theSummary = theSummary + linksTxt
theSummary = theSummary+"\n\n"

print theSummary.encode('utf-8')

pageImage = soup.findAll("img")
#  Only the first one
if len(pageImage) > 0:
	imageLink = (pageImage[0]["src"])
else:
	imageLink = ""

config.read([os.path.expanduser('~/.rssFacebook')])
oauth_access_token= config.get("Facebook", "oauth_access_token")

graph = facebook.GraphAPI(oauth_access_token)
pages = graph.get_connections("me", "accounts")

for i in range(len(pages['data'])):
	if (pages['data'][i]['name'] == pageFB):
		print "Writing in... ", pages['data'][i]['name']
		graph2 = facebook.GraphAPI(pages['data'][i]['access_token'])
		graph2.put_object(pages['data'][i]['id'], 
			"feed", message = theSummary, link=theLink, 
			picture = imageLink, 
			name=theTitle, caption='',
			description=theSummary.encode('utf-8'))

