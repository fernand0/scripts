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

import moduleBlog
# https://github.com/fernand0/scripts/blob/master/moduleBlog.py
import moduleSocial
# https://github.com/fernand0/scripts/blob/master/moduleSocial.py
import moduleCache
# https://github.com/fernand0/scripts/blob/master/moduleCache.py

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
    blog = moduleBlog.moduleBlog()
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
        lastLink = checkLastLink(config.get(section, "rssFeed"))
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
                        level=loggingLevel, format='%(asctime)s %(message)s')

    logging.info("Launched at %s" % time.asctime())

    logging.debug("Parameters %s, %d" % (sys.argv, len(sys.argv)))

    logging.info("Configured blogs:")

    config = configparser.ConfigParser()
    config.read(CONFIGDIR + '/.rssBlogs')

    blogs = []

    for section in config.sections():
        logging.info("\nSection: %s"% section)
        blog = moduleBlog.moduleBlog()
        url = config.get(section, "url")
        print("\nSection: %s %s"% (section, url))
        blog.setUrl(url)

        if ("rssfeed" in config.options(section)):
            # It does not preserve case
            rssFeed = config.get(section, "rssFeed")
            logging.info("Blog RSS: %s"% rssFeed)
            blog.setRssFeed(rssFeed)
            blog.setPostsRss()
        elif blog.getUrl().find('slack')>0:
            logging.info("Blog Slack: %s"% blog.getUrl())
            blog.setPostsSlack()

        if section.find(checkBlog) >= 0:
            # If checkBlog is empty it will add all of them

            blogs.append(blog)

            if ("linksToAvoid" in config.options(section)):
                blog.setLinksToAvoid(config.get(section, "linksToAvoid"))
            if ("time" in config.options(section)):
                blog.setTime(config.get(section, "time"))
            if ('bufferapp' in config.options(section)): 
                blog.setBufferapp(config.get(section, "bufferapp"))
            if ('program' in config.options(section)): 
                blog.setProgram(config.get(section, "program"))

            socialNetworksOpt = ['twitter', 'facebook', 'telegram', 
                    'medium', 'linkedin','pocket'] 
            for option in config.options(section):
                if (option in socialNetworksOpt):
                    nick = config.get(section, option)
                    socialNetwork = (option, nick)
                    blog.addSocialNetwork(socialNetwork)

            logging.info("Looking for pending posts in ...%s"
                    % blog.getSocialNetworks())
            print("    Looking for pending posts ... " )

            bufferMax = 10
            if blog.getBufferapp():
                api = moduleSocial.connectBuffer()
                lenMax, profileList = moduleSocial.checkLimitPosts(api, blog)
                logging.debug("Lenmax %d"% lenMax)

                for profile in profileList:
                    print("        getBuffer %s" % profile['service'])
                    lenMax, profileList = moduleSocial.checkLimitPosts(api, 
                            blog, profile['service'])
                    logging.info("Service %s" 
                            % profile['service'] + blog.getBufferapp())
                    if (profile['service'][0] in blog.getBufferapp()): 
                        lastLink, lastTime = blog.checkLastLink((profile['service'], profile['service_username']))
                        blog.addLastLinkPublished(profile['service'], 
                                lastLink, lastTime) 
                        i = blog.getLinkPosition(lastLink)

                        logging.debug("profile %s"% profile)
                        logging.info("lastLink %s %d"% (lastLink, i))
                        if ((profile['service'] == 'twitter') 
                                or (profile['service'] == 'facebook')):
                            # We should add a configuration option in order
                            # to check which services are the ones with
                            # immediate posting. For now, we know that we are using
                            # Twitter and Facebook We are checking the links tha
                            # have been published with other toolsin order to avoid
                            # duplicates

                            with open(DATADIR + '/.urls.pickle', 'rb') as f:
                                theList = pickle.load(f)
                        else:
                            theList = []

                        num = bufferMax - lenMax
                        logging.info("bufferMax - lenMax = num %d %d %d"%
                                (bufferMax, lenMax, num)) 

                        listPosts = []
                        for j in range(num, 0, -1):
                            logging.info("j %d - %d"% (j,i))
                            if (i <= 0):
                                break
                            i = i - 1
                            post = blog.obtainPostData(i, False)
                            listPosts.append(post)
                            print("          Scheduling post %s\n" % post[0])

                            (title, link, firstLink, image, summary, summaryHtml, summaryLinks, content, links, comment) = (blog.obtainPostData(i, False))
                            moduleSocial.publishBuffer(blog, profile, title, link, firstLink, isDebug, lenMax, blog.getBufferapp())
                            logging.debug("listPosts: %s"% listPosts)
            else:
                for socialNetwork in blog.getSocialNetworks().keys():
                    print("        Not buffer %s" % socialNetwork)
                    logging.info("Social Network %s" % socialNetwork)
                    lastLink, lastTime = blog.checkLastLink((socialNetwork, blog.getSocialNetworks()[socialNetwork]))
                    blog.addLastLinkPublished(socialNetwork, 
                            lastLink, lastTime) 
                    i = blog.getLinkPosition(lastLink) 

                    logging.debug("i, lastLink %d %s"% (i,lastLink))
                    #print("i, lastLink %d %s"% (i,lastLink))
                    if (i > 0):
                        nick = blog.getSocialNetworks()[socialNetwork]
                        (title, link, firstLink, image, summary, summaryHtml, summaryLinks, content , links, comment) = (blog.obtainPostData(i - 1, False))
                        hours = blog.getTime() 
                        if (hours and (((time.time() - lastTime) - int(hours)*60*60) < 0)): 
                            logging.info("Not publishing because time restriction\n") 
                        else:
                            logging.info("Publishing directly\n") 
                            serviceName = socialNetwork.capitalize()
                            publishMethod = getattr(moduleSocial, 
                                    'publish'+ serviceName)
                            publishMethod(nick, title, link, summary, summaryHtml, summaryLinks, image, content, links)
                            logging.info("Updating Link\n") 
                            blog.updateLastLink(link, (socialNetwork, blog.getSocialNetworks()[socialNetwork]))

            if blog.getProgram():
                t = {}
                lenMax = 6
                lenMax, profileList = moduleSocial.checkLimitPosts('', blog)
                logging.debug("Lenmax %d"% lenMax)

                for profile in profileList:
                    lenMax, profileList = moduleSocial.checkLimitPosts('', 
                            blog, profile)
                    if profile[0] in blog.getProgram():
                        print("        getProgram %s" % profile)
                        lastLink, lastTime = blog.checkLastLink((profile, blog.getSocialNetworks()[profile]))
                        blog.addLastLinkPublished(profile, 
                            lastLink, lastTime)
                        i = blog.getLinkPosition(lastLink) 

                        logging.info("lastLink %s %s %d"% (profile, lastLink, i))
                        if ((profile == 'twitter') 
                                or (profile == 'facebook')):
                            # We should add a configuration option in order
                            # to check which services are the ones with
                            # immediate posting. For now, we know that we
                            # are using Twitter and Facebook We are
                            # checking the links tha have been published
                            # with other toolsin order to avoid duplicates

                            with open(DATADIR + '/.urls.pickle', 'rb') as f:
                                theList = pickle.load(f)
                        else:
                            theList = []

                        num = bufferMax - lenMax
                        logging.info("bufferMax - lenMax = num %d %d %d"%
                                (bufferMax, lenMax, num)) 
                        
                        listPosts = []
                        for j in range(num, 0, -1):
                            logging.info("j %d - %d"% (j,i))
                            if (i <= 0):
                                break
                            i = i - 1
                            post = blog.obtainPostData(i, False)
                            listPosts.append(post)
                            print("          Scheduling post %s\n" % post[0])

                        if listPosts:
                            link = listPosts[len(listPosts) - 1][1]
                            logging.debug("link -> %s"% link) 
                        else: 
                            link = ''

                        socialNetwork = (profile,blog.getSocialNetworks()[profile])
                        timeSlots = 60*60 # One hour
                        t[socialNetwork[0]] = threading.Thread(target = moduleSocial.publishDelay, args = (blog, listPosts, socialNetwork, 1, timeSlots))
                        t[socialNetwork[0]].start()

                        if link:
                            logging.info("Updating link %s" % profile)
                            blog.updateLastLink(link, (profile,blog.getSocialNetworks()[profile]))

            time.sleep(2)
        else:
            print("    Skip")

    print("====================================")
    print("Finished at %s" % time.asctime())
    print("====================================")
    logging.info("Finished at %s" % time.asctime())

if __name__ == '__main__':
    main()

