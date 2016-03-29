#!/usr/bin/env python
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

import os
import ConfigParser
import feedparser
import logging
import re
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

def selectBlog(sel='a'):
    config = ConfigParser.ConfigParser()
    config.read([os.path.expanduser('~/.rssBlogs')])
 
    print "Configured blogs:"
 
    i = 1
 
    lastPost={}
    for section in config.sections():
       rssFeed = config.get(section, "rssFeed")
       feed = feedparser.parse(rssFeed)
       lastPost[i] = feed.entries[0]
       print str(i), ')', section, config.get(section, "rssFeed"), '(', time.strftime('%Y-%m-%d %H:%M:%SZ', lastPost[i]['published_parsed']), ')'
       if (i == 1) or (recentDate < lastPost[i]['published_parsed']):
          recentDate = lastPost[i]['published_parsed']
          recentIndex = i
          recentPost = lastPost[recentIndex]
       i = i + 1
 
    if (sel == 'm'):
       if (int(i)>1):
          recentIndex = raw_input ('Select one: ')
          recentPost = lastPost[int(recentIndex)]
       else:
          i = 1
 
    i = int(recentIndex)

    if i > 0:
        selectedBlog=config.get("Blog"+str(i), "rssFeed")
        ini=selectedBlog.find('/')+2
        fin=selectedBlog[ini:].find('.')
        identifier=selectedBlog[ini:ini+fin]+"_"+selectedBlog[ini+fin+1:ini+fin+7]
        print "Selected ", selectedBlog
        logging.info("Selected "+ selectedBlog)
    else:
        sys.exit()

    if (config.has_option("Blog"+str(recentIndex), "linksToAvoid")):
        linksToAvoid = config.get("Blog"+str(recentIndex), "linksToAvoid")
    else:
        linksToAvoid = ""

    theTwitter = config.get("Blog"+str(recentIndex), "twitterAC")
    theFbPage = config.get("Blog"+str(recentIndex), "pageFB")


    print "You have chosen " 
    print config.get("Blog"+str(recentIndex), "rssFeed")

    return(selectedBlog, identifier, recentPost)
    #return (selectedBlog, identifier, recentPost, linksToAvoid, theTwitter, theFbPage)


def main():
    PREFIX="rssBuffer_"
    POSFIX="last"

    logging.basicConfig(filename='/home/ftricas/usr/var/' + PREFIX + '.log',
                            level=logging.INFO,format='%(asctime)s %(message)s')

    selectedBlog, identifier, recentPost = selectBlog('m')
    
    feed = feedparser.parse(selectedBlog)
    urlFile = open(os.path.expanduser("~/."+PREFIX+identifier+"."+POSFIX),"r")
    
    linkLast = urlFile.read().rstrip() # Last published
    
    for i in range(len(feed.entries)):
        if (feed.entries[i].link==linkLast):
            break
    
    print "i: ", i
    
    if ((i==0) and (feed.entries[i].link==linkLast)):
        logging.info("No new items")
        sys.exit()
    else:
        if (i == (len(feed.entries)-1)):
            logging.info("All are new")
            logging.info("Please, check manually")
            sys.exit()
            #i = len(feed.entries)-1
        logging.debug("i: "+ str(i))
    
    config.read([os.path.expanduser('~/.rssBuffer')])
    
    clientId = config.get("appKeys", "client_id")
    clientSecret = config.get("appKeys", "client_secret")
    redirectUrl = config.get("appKeys", "redirect_uri")
    accessToken = config.get("appKeys", "access_token")
    
    # instantiate the api object 
    api = API(client_id=clientId,
              client_secret=clientSecret,
              access_token=accessToken)
    
    logging.debug(api.info)
    
    
    # We can put as many items as the service with most items allow
    # The limit is ten.
    # Get all pending updates of a social network profile
    serviceList=['twitter','facebook','linkedin']
    profileList={}
    
    lenMax=0
    logging.info("Checking services...")
    
    for service in serviceList:
        profileList[service] = Profiles(api=api).filter(service=service)[0]
        if (len(profileList[service].updates.pending)>lenMax):
            lenMax=len(profileList[service].updates.pending)
        logging.info("%s ok" % service)
    
    logging.info("There are %d in some buffer, we can put %d", 
                 (lenMax, 10-lenMax))
    logging.info("We have %d items to post" % i)
    
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
                    logging.debug("Una palabra, probamos con el titulo")
                    theTitle = feed.entries[i].title
                if (theLink[:26] == "https://www.instagram.com/") and (theTitle[:17] == "A video posted by"):
                    #exception for Instagram videos
                    theTitle = feed.entries[i].title
                if (theLink[:22] == "https://instagram.com/") and (theTitle.find("(en")>0):
                    theTitle = theTitle[:theTitle.find("(en")-1]
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
            logging.info("I don't know what to do!")
    
        #pageImage = soup.findAll("img")
        theTitle = urllib.quote(theTitle.encode('utf-8'))
    
    
        #print i, ": ", re.sub('\n+',' ', theTitle.encode('iso-8859-1','ignore')) + " " + theLink
        #print len(re.sub('\n+',' ', theTitle.encode('iso-8859-1','ignore')) + " " + theLink)
        
    
        post=re.sub('\n+',' ', theTitle) +" "+theLink
        # Sometimes there are newlines and unnecessary spaces
        #print "post", post
    
        # There are problems with &
        logging.info("Publishing... %s" % post)
        for service in serviceList:
            line = service
            profile=profileList[service]
            try:
                profile.updates.new(post)
                line = line + ' ok'
                time.sleep(3)
            except:
                line = line + ' fail'
                failFile = open(os.path.expanduser("~/."+PREFIX+identifier+".fail"),"w")
                failFile.write(post)
            logging.info("  %s service" % line)
    
    urlFile = open(os.path.expanduser("~/."+PREFIX+identifier+"."+POSFIX),"w")
    urlFile.write(feed.entries[i].link)
    urlFile.close()

if __name__ == '__main__':
    main()
