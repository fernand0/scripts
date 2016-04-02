#!/usr/bin/env python
# encoding: utf-8

#
# Very simple Python program to publish the entries of an RSS recentFeed in several
# channels of bufferapp. It uses three configuration files.
# 
# - The first one includes the RSS recentFeed of the blog [~/.rssBlogs]
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
 
 
    feed = []
    # We are caching the feeds in order to use them later

    i = 1

    for section in config.sections():
       rssFeed = config.get(section, "rssFeed")
       feed.append(feedparser.parse(rssFeed))
       lastPost = feed[-1].entries[0]
       print '%s) %s %s (%s)' % (str(i), section, config.get(section, "rssFeed"),  time.strftime('%Y-%m-%d %H:%M:%SZ', lastPost['published_parsed']))
       if (i == 1) or (recentDate < lastPost['published_parsed']):
          recentDate = lastPost['published_parsed']
          recentFeed = feed[-1]
          recentPost = lastPost
       i = i + 1
 
    if (sel == 'm'):
       if (int(i)>1):
          recentIndex = raw_input ('Select one: ')
          i = int(recentIndex)
          recentFeed = feed[i - 1]
       else:
          i = 1
 
    if i > 0:
        ini=recentFeed.feed['title_detail']['base'].find('/')+2
        fin=recentFeed.feed['title_detail']['base'][ini:].find('.')
        identifier=recentFeed.feed['title_detail']['base'][ini:ini+fin]+"_"+recentFeed.feed['title_detail']['base'][ini+fin+1:ini+fin+7]
        print "Selected ", recentFeed.feed['title_detail']['base']
        logging.info("Selected "+ recentFeed.feed['title_detail']['base'])
    else:
        sys.exit()

    selectedBlog = {}
    if (config.has_option("Blog"+str(recentIndex), "linksToAvoid")):
        selectedBlog["linksToAvoid"] = config.get("Blog"+str(recentIndex), "linksToAvoid")
    else:
        selectedBlog["linksToAvoid"] = ""

    selectedBlog["twitterAC"] = config.get("Blog"+str(recentIndex), "twitterAC")
    selectedBlog["pageFB"] = config.get("Blog"+str(recentIndex), "pageFB")
    selectedBlog["identifier"] = identifier


    print "You have chosen " 
    print recentFeed.feed['title_detail']['base']

    return(recentFeed, selectedBlog)
    #return (selectedBlog, identifier, recentPost, linksToAvoid, theTwitter, theFbPage)


def main():
    PREFIX="rssBuffer_"
    POSFIX="last"

    logging.basicConfig(filename='/home/ftricas/usr/var/' + PREFIX + '.log',
                            level=logging.INFO,format='%(asctime)s %(message)s')

    recentFeed, selectedBlog = selectBlog('m')
    
    urlFile = open(os.path.expanduser("~/."+PREFIX+selectedBlog['identifier']+"."+POSFIX),"r")
    
    linkLast = urlFile.read().rstrip() # Last published
    
    for i in range(len(recentFeed.entries)):
        if (recentFeed.entries[i].link==linkLast):
            break
    
    print "i: ", i
    
    if ((i==0) and (recentFeed.entries[i].link==linkLast)):
        logging.info("No new items")
        sys.exit()
    else:
        if (i == (len(recentFeed.entries)-1)):
            logging.info("All are new")
            logging.info("Please, check manually")
            sys.exit()
            #i = len(recentFeed.entries)-1
        logging.debug("i: "+ str(i))
    
    config = ConfigParser.ConfigParser()
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
    
    print (lenMax, 10-lenMax)
    logging.info("There are %d in some buffer, we can put %d" % 
                 (lenMax, 10-lenMax))
    logging.info("We have %d items to post" % i)
    
    for j in range(10-lenMax,0,-1):
    
        if (i==0):
            break
        i = i - 1
        if (recentFeed.feed['title_detail']['base'].find('tumblr') > 0):
            soup = BeautifulSoup(recentFeed.entries[i].summary)
            pageLink  = soup.findAll("a")
            if pageLink:
                theLink  = pageLink[0]["href"]
                theTitle = pageLink[0].get_text()
                if len(re.findall(r'\w+', theTitle)) == 1:
                    logging.debug("Una palabra, probamos con el titulo")
                    theTitle = recentFeed.entries[i].title
                if (theLink[:26] == "https://www.instagram.com/") and (theTitle[:17] == "A video posted by"):
                    #exception for Instagram videos
                    theTitle = recentFeed.entries[i].title
                if (theLink[:22] == "https://instagram.com/") and (theTitle.find("(en")>0):
                    theTitle = theTitle[:theTitle.find("(en")-1]
            else:
                # Some entries do not have a proper link and the rss contains
                # the video, image, ... in the description.
                # In this case we use the title and the link of the entry.
                theLink   = recentFeed.entries[i].link
                theTitle  = recentFeed.entries[i].title.encode('utf-8')
        elif (selectedBlog.find('wordpress') > 0):
            soup = BeautifulSoup(recentFeed.entries[i].content[0].value)
            theTitle = recentFeed.entries[i].title
            theLink  = recentFeed.entries[i].link    
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
                failFile = open(os.path.expanduser("~/."+PREFIX+selectedBlog['identifier']+".fail"),"w")
                failFile.write(post)
            logging.info("  %s service" % line)
    
    urlFile = open(os.path.expanduser("~/."+PREFIX+selectedBlog['identifier']+"."+POSFIX),"w")
    urlFile.write(recentFeed.entries[i].link)
    urlFile.close()

if __name__ == '__main__':
    main()
