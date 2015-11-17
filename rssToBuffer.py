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
	selectedBlog=config.get("Blog"+str(i), "rssFeed")
	ini=selectedBlog.find('/')+2
	fin=selectedBlog[ini:].find('.')
	identifier=selectedBlog[ini:ini+fin]+"_"+selectedBlog[ini+fin+1:ini+fin+7]
	print "Selected ", selectedBlog
else:
	sys.exit()

PREFIX=".rssBuffer_"
POSFIX=".last"

feed = feedparser.parse(selectedBlog)
urlFile = open(os.path.expanduser("~/"+PREFIX+identifier+POSFIX),"r")

linkLast = urlFile.read().rstrip() # Last published


for i in range(len(feed.entries)):
	if (feed.entries[i].link==linkLast):
		break

if ((i==0) and (feed.entries[i].link==linkLast)):
	print "No new items"
	sys.exit()
else:
	if (i==0):
		print "All are new"
		i = len(feed.entries)-1

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
print "We have", i, "items to post"

for j in range(10-lenMax,0,-1):

	if (i==0):
		break
	i = i - 1
	if (selectedBlog.find('tumblr') > 0):
		soup = BeautifulSoup(feed.entries[i].summary)
		pageLink  = soup.findAll("a")
		if pageLink:
			theLink  = pageLink[0]["href"]
			theTitle = pageLink[0].get_text()
			if len(re.findall(r'\w+', theTitle)) == 1:
				print "Una palabra, probamos con el titulo"
				theTitle = feed.entries[i].title
			if (theLink[:22] == "https://instagram.com/") and (theTitle[:17] == "A video posted by"):
				#exception for Instagram videos
				theTitle = feed.entries[i].title
			if (theLink[:22] == "https://instagram.com/") and (theTitle.find("(en")>0):
				theTitle = theTitle[:theTitle.find("(3n")-1]
		else:
			# Some entries do not have a proper link and the rss contains
			# the video, image, ... in the description.
			# In this case we use the title and the link of the entry.
			theLink   = feed.entries[i].link
			theTitle  = feed.entries[i].title.encode('utf-8')
	elif (selectedBlog.find('wordpress') > 0):
		soup = BeautifulSoup(feed.entries[i].content[0].value)
		theTitle = feed.entries[i].title	
		theLink  = feed.entries[i].link	
	else:
		print "I don't know what to do!"

	#pageImage = soup.findAll("img")


	
	print i, ": ", re.sub('\n+',' ', theTitle) + " " + theLink
	print len(re.sub('\n+',' ', theTitle) + " " + theLink)
	
	post=re.sub('\n+',' ', theTitle) +" "+theLink
	# Sometimes there are newlines and unnecessary spaces
	#print "post", post
	print "Publishing..."
	for service in serviceList:
		print "  %s service"%service,
		profile=profileList[service]
		try:
			profile.updates.new(post)
			print "  ok"
			time.sleep(3)
		except:
			failFile = open(os.path.expanduser("~/"+PREFIX+identifier+".fail"),"w")
			failFile.write(post)

urlFile = open(os.path.expanduser("~/"+PREFIX+identifier+POSFIX),"w")
urlFile.write(feed.entries[i].link)
urlFile.close()
