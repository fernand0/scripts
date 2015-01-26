#!/usr/bin/python
# encoding: utf-8

#
# Very simple Python program to publish the entries of an RSS feed in several
# channels of bufferapp. It uses three configuration files.
# 
# - The first one includes the RSS feed of the blog [~/.rssBlogs]
# [Blog3]
# rssFeed:http://fernand0.tumblr.com/rss
#
# There can exist several blogs, and more parameters if needed for other things
# the program will ask which one we want to publish.
#
# - The second one includes the secret data of the buffer app [~/.rssBuffer]
# [appKeys]
# client_id:XXXXXXXXXXXXXXXXXXXXXXXX
# client_secret:XXXXXXXXXXXXXXXXXXXXXXXXXXXxXXXX
# redirect_uri:XXXXXXXXXXXXXXXXXXXXXXXXX
# access_token:XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
# 
# These data can be obtained registering an app in the bufferapp site.
# Follow instructions at:
# https://bufferapp.com/developers/api
# 
# - The third one contains the last published URL [~/.rssBuffer.last]
# It contains just an URL which is the last one published. 
# At this moment it only considers one blog

import ConfigParser, os
import feedparser, re
from bs4 import BeautifulSoup

# sudo pip install buffpy version does not work
# Better use:
# git clone https://github.com/vtemian/buffpy.git
# cd buffpy
# sudo python setup.py install
from colorama import Fore
from buffpy.api import API
from buffpy.managers.profiles import Profiles
from buffpy.managers.updates import Update

import time, sys
import urllib
reload(sys)
sys.setdefaultencoding("UTF-8")
config = ConfigParser.ConfigParser()
config.read([os.path.expanduser('~/.rssBlogs')])

i=1
for section in config.sections():
	print str(i), ')', section, config.get(section, "rssFeed")
	i = i + 1

if (int(i)>0):
	i = raw_input ('Select one: ')


if i>0:
	print "Selected ", config.get("Blog"+str(i), "rssFeed")
else:
	sys.exit()


feed = feedparser.parse(config.get("Blog"+str(i), "rssFeed"))
urlFile = open(os.path.expanduser("~/.rssBuffer.last"),"r")

linkLast = urlFile.read().rstrip() # Last published

for i in range(len(feed.entries)-1,-1, -1):
	if (feed.entries[i].link==linkLast):
		break

if (i==0):
	print "No new items"
	sys.exit()


config.read([os.path.expanduser('~/.rssBuffer')])

clientId = config.get("appKeys", "client_id")
clientSecret = config.get("appKeys", "client_secret")
redirectUrl = config.get("appKeys", "redirect_uri")
accessToken = config.get("appKeys", "access_token")

# instantiate the api object 
api = API(client_id=clientId,
          client_secret=clientSecret,
          access_token=accessToken)

#print api.info


# We can put as many items as the service with most items allow
# The limit is ten.
# Get all pending updates of a social network profile
serviceList=['twitter','facebook','linkedin']
profileList={}

lenMax=0
print "Checking services..."

for service in serviceList:
	print "  %s"%service,
	profileList[service] = Profiles(api=api).filter(service=service)[0]
	if (len(profileList[service].updates.pending)>lenMax):
		lenMax=len(profileList[service].updates.pending)
	print "  ok"

print "There are", lenMax, "in some buffer, we can put", 10-lenMax

print "i", i

if (i > 10 - lenMax):
	iFin = i - (10 - lenMax)
else:
	iFin = -1

for j in range(i-1,iFin, -1):

	soup = BeautifulSoup(feed.entries[j].summary)

	pageImage = soup.findAll("img")
	pageLink  = soup.findAll("a")

	if pageLink:
		theLink  = pageLink[0]["href"]
		theTitle = pageLink[0].get_text()
		if len(re.findall(r'\w+', theTitle)) == 1:
			print "Una palabra, probamos con el titulo"
			theTitle = feed.entries[j].title
	else:
		# Some entries do not have a proper link and the rss contains
		# the video, image, ... in the description.
		# In this case we use the title and the link of the entry.
		theLink   = feed.entries[j].link
		theTitle  = feed.entries[j].title

	
	print j, ": ", re.sub('\n+',' ', theTitle) + " " + theLink
	print len(re.sub('\n+',' ', theTitle) + " " + theLink)
	

	
	post=re.sub('\n+',' ', theTitle) +" "+theLink
	# Sometimes there are newlines and unnecessary spaces
	#print "post", post
	print "Publishing..."
	for service in serviceList:
		print "  %s service"%service,
		profile=profileList[service]
		profile.updates.new(post)
		print "  ok"
		time.sleep(3)

if (i>=1):
	urlFile = open(os.path.expanduser("~/.rssBuffer.last"),"w")
	urlFile.write(feed.entries[j].link)
	urlFile.close()
