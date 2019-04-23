#!/usr/bin/env python
# encoding: utf-8
#
# Very simple Python program to publish RSS entries of a set of feeds
# in available social networks.
#
# It has a configuration file with a number of blogs with:
#    - The RSS feed of the blog
#    - The Twitter account where the news will be published
#    - The Facebook page where the news will be published
#    - Other social networks
# It uses a configuration file that has two sections:
#      - The oauth access token
#
# And more thins. To be done.
#

import moduleRss
# https://github.com/fernand0/scripts/blob/master/moduleRss.py
import moduleXmlrpc
# https://github.com/fernand0/scripts/blob/master/moduleXmlrpc.py
import moduleSocial
# https://github.com/fernand0/scripts/blob/master/moduleSocial.py
import moduleCache
# https://github.com/fernand0/scripts/blob/master/moduleCache.py
import moduleBuffer
# https://github.com/fernand0/scripts/blob/master/moduleBuffer.py
import moduleSlack
# https://github.com/fernand0/scripts/blob/master/moduleSlack.py

import configparser
import os
import logging
import random
import threading
import feedparser
import facebook
from linkedin import linkedin
from twitter import *
from medium import Client
from html.parser import HTMLParser
import telepot
import re
import sys
import time
import datetime
import pickle
from bs4 import BeautifulSoup
from bs4 import NavigableString
from bs4 import Tag
from bs4 import Doctype
import importlib
import urllib.parse
# sudo pip install buffpy version does not work
# Better use:
# git clone https://github.com/vtemian/buffpy.git
# cd buffpy
# sudo python setup.py install
from buffpy.api import API
from buffpy.managers.profiles import Profiles
from buffpy.managers.updates import Update

from configMod import *

def test():
    config = configparser.ConfigParser()
    config.read([os.path.expanduser('~/.rssBlogs')])

    # We can publish the last entry of a blog in Medium as a draft
    blog = moduleRss.moduleRss()
    blog.setRssFeed('http://fernand0.blogalia.com/rss20.xml')
    blog.getBlogPostsRss()
    (title, link, firstLink, image, summary, summaryHtml, summaryLinks, comment) = (blog.obtainPostData(0))
    publishMedium("", title, link, summary, summaryHtml, summaryLinks, image)


    print("Configured blogs:")

    feed = []
    # We are caching the feeds in order to use them later

    i = 1
    recentPosts = {}

    for section in config.sections():
        rssFeed = config.get(section, "rssFeed")
        feed.append(feedparser.parse(rssFeed))
        lastPost = feed[-1].entries[0]
        print('%s) %s %s (%s)' % (str(i), section,
                                  config.get(section, "rssFeed"),
                                  time.strftime('%Y-%m-%d %H:%M:%SZ',
                                  lastPost['published_parsed'])))
        lastLink = checkLastLink(self.url, config.get(section, "rssFeed"))
        print(lastLink)
        sys.exit()
        lenCmp = min(len(lastLink),len(lastPost['link']))

        recentPosts[section] = {}
        recentPosts[section]['posts'] = feed[-1].entries[0]

    for i in recentPosts.keys():
         print("post",i,recentPosts[i]['posts']['title'])
         print("post",i,recentPosts[i]['posts']['link'])
         if 'content' in recentPosts[i]['posts']:
             content = recentPosts[i]['posts']['content'][0]['value']
         else:
             content = recentPosts[i]['posts']['summary']
         print("post content",i,content)
         soup = BeautifulSoup(content)
         theSummary = soup.get_text()
         theSummaryLinks = blog.extractLinks(soup)
         print("post links",i,theSummaryLinks)

    return recentPosts

def main():

    print("====================================")
    print("Launched at %s" % time.asctime())
    print("====================================")
    print("")
        
    isDebug = False

    if len(sys.argv)>1:
        print(sys.argv[1])
        checkBlog = sys.argv[1]
    else:
        checkBlog = ""

    loggingLevel = logging.INFO
    logging.basicConfig(filename = LOGDIR + "/rssSocial_.log", 
            level=loggingLevel, 
            format='%(asctime)s [%(filename).12s] %(message)s', 
            datefmt='%Y-%m-%d %H:%M')

    logging.info("Launched at %s" % time.asctime())
    logging.debug("Parameters %s, %d" % (sys.argv, len(sys.argv)))
    logging.info("Configured blogs:")

    config = configparser.ConfigParser()
    config.read(CONFIGDIR + '/.rssBlogs')

    blogs = []

    for section in config.sections():
        blog = None
        logging.info("Section: %s"% section)
        url = config.get(section, "url")
        print("Section: %s %s"% (section, url))
        if ("rssfeed" in config.options(section)):
            rssFeed = config.get(section, "rssFeed")
            logging.info(" Blog RSS: %s"% rssFeed)
            blog = moduleRss.moduleRss()
            # It does not preserve case
            blog.setRssFeed(rssFeed)
        elif url.find('slack')>0:
            logging.info(" Blog Slack: %s"% url)
            blog = moduleSlack.moduleSlack()
            blog.setSlackClient(os.path.expanduser('~/.mySocial/config/.rssSlack'))
        blog.setUrl(url)
        blog.setPosts()

        if section.find(checkBlog) >= 0:
            # If checkBlog is empty it will add all of them
            if ("linksToAvoid" in config.options(section)):
                blog.setLinksToAvoid(config.get(section, "linksToAvoid"))
            if ("time" in config.options(section)):
                blog.setTime(config.get(section, "time"))

            blog.setSocialNetworks(config, section)


            if ('bufferapp' in config.options(section)): 
                blog.setBufferapp(config.get(section, "bufferapp")) 

            if ('program' in config.options(section)): 
                blog.setProgram(config.get(section, "program"))

            logging.info(" Looking for pending posts") # in ...%s"
                    #% blog.getSocialNetworks())
            print("   Looking for pending posts ... " )

            bufferMax = 9
            t = {}

            #print(blog.getSocialNetworks())
            #blog.socialNetworks = {'linkedin':'Fernando Tricas'}
            for profile in blog.getSocialNetworks():
                lenMax = 9
                link= ""

                nick = blog.getSocialNetworks()[profile]
                socialNetwork = (profile, nick)
                nameProfile = profile + '_' + nick

                if ((blog.getBufferapp() 
                        and (profile[0] in blog.getBufferapp())) 
                        or (blog.getProgram() 
                            and (profile[0] in blog.getProgram()))): 
                    print(profile)
                    lenMax = blog.len(profile)

                logging.info("  Service %s Lenmax %d" % (profile, lenMax))

                num = bufferMax - lenMax

                listPosts = []
                if (num > 0) or not (blog.getBufferapp() or blog.getProgram()):
                    lastLink, lastTime = checkLastLink(url, socialNetwork)
                    i = blog.getLinkPosition(lastLink)

                    logging.info("   Profile %s"% profile)
                    print("    Profile %s"% profile)
                    logging.info("    Last link %s %s %d"% 
                            (time.strftime('%Y-%m-%d %H:%M:%S', 
                                time.localtime(lastTime)), lastLink, i))
                    print("     Last link %s Pos: %d" %
                            (time.strftime('%Y-%m-%d %H:%M:%S', 
                                time.localtime(lastTime)), i))
                    if isinstance(lastLink, bytes): 
                        print("      %s"% lastLink.decode())
                    else:
                        print("      %s"% lastLink)
                    logging.debug("bufferMax - lenMax = num %d %d %d"%
                            (bufferMax, lenMax, num)) 

                    link = ""
                    for j in range(num, 0, -1):
                        logging.debug("j, i %d - %d"% (j,i))
                        if (i < 0):
                            break
                        i = i - 1
                        post = blog.obtainPostData(i, False)
                        listPosts.append(post)
                        print("      Scheduling post %s" % post[0])
                        logging.info("    Scheduling post %s" % post[0])

                    if listPosts:
                        link = listPosts[len(listPosts) - 1][1]
                        logging.debug("link -> %s"% link)


                if blog.getBufferapp() and (profile[0] in blog.getBufferapp()): 
                    link = blog.buffer[socialNetwork].addPosts(listPosts)

                if blog.getProgram() and (profile[0] in blog.getProgram()):
                    blog.cache[socialNetwork].addPosts(listPosts)
                    time.sleep(1)
                    timeSlots = 5*60 # One hour
                    t[nameProfile] = threading.Thread(target = moduleSocial.publishDelay, args = (blog, socialNetwork, 1, timeSlots))
                    t[nameProfile].start() 

                if not (blog.getBufferapp() or blog.getProgram()):
                    if (i > 0):
                        hours = blog.getTime() 
                        if (hours and (((time.time() - lastTime) - int(hours)*60*60) < 0)): 
                            logging.info("  Not publishing because time restriction") 
                        else:
                            (title, link, firstLink, image, summary, summaryHtml, summaryLinks, content , links, comment) = (blog.obtainPostData(i - 1, False))
                            logging.info("  Publishing directly\n") 
                            serviceName = profile.capitalize()
                            print("   Publishing in %s %s" % (serviceName, title))
                            if (profile == 'twitter') or (profile == 'facebook') or (profile=='telegram') or (profile=='mastodon') or (profile=='linkedin') or (profile == 'pocket'): 
                                # https://stackoverflow.com/questions/41678073/import-class-from-module-dynamically
                                import importlib
                                mod = importlib.import_module('module'+serviceName) 
                                cls = getattr(mod, 'module'+serviceName)
                                api = cls()
                                api.setClient(nick)
                                result = api.publishPost(title, link, comment)
                                #print(result)
                                if isinstance(result, str):
                                    if result[:4]=='Fail':
                                        link=''
                            else:
                                publishMethod = getattr(moduleSocial, 
                                    'publish'+ serviceName)
                                result = publishMethod(nick, title, link, summary, summaryHtml, summaryLinks, image, content, links)

                if link:
                     logging.info("  Updating link %s" % profile)
                     updateLastLink(blog.url, link, socialNetwork) 
                     #       if result != "Fail!":
                     logging.debug("listPosts: %s"% listPosts)

            time.sleep(2)
        else:
            print("    Skip")

    print("====================================")
    print("Finished at %s" % time.asctime())
    print("====================================")
    logging.info("Finished at %s" % time.asctime())

if __name__ == '__main__':
    main()

