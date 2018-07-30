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
    loggingLevel = logging.INFO

    config = configparser.ConfigParser()
    config.read([os.path.expanduser('~/.rssBlogs')])

    logging.basicConfig(filename=os.path.expanduser("~") 
                        + "/usr/var/rssSocial_.log",
                        level=loggingLevel, format='%(asctime)s %(message)s')

    logging.info("Launched at %s" % time.asctime())
    logging.debug(sys.argv, len(sys.argv))

    if len(sys.argv)>1:
        print(sys.argv[1])
        checkBlog = sys.argv[1]
    else:
        checkBlog = ""

    logging.info("Configured blogs:")

    blogs = []

    for section in config.sections():
        logging.info("\nSection: ", section)
        blog = moduleBlog.moduleBlog()
        url = config.get(section, "url")
        blog.setUrl(url)
        if ("rssfeed" in config.options(section)):
            # It does not preserve case
            rssFeed = config.get(section, "rssFeed")
            logging.info("Blog: ", url+rssFeed)
            blog.setRssFeed(rssFeed)
            blog.setPostsRss()
        elif blog.getUrl().find('slack')>0:
            blog.setPostsSlack()


        if section.find(checkBlog) >= 0:
            blogs.append(blog)

            optFields = ["linksToAvoid", "time", "bufferapp"]
            if ("linksToAvoid" in config.options(section)):
                blog.setLinksToAvoid(config.get(section, "linksToAvoid"))
            if ("time" in config.options(section)):
                blog.setTime(config.get(section, "time"))

            for option in config.options(section):
                if (option in ['twitter', 'facebook', 'telegram', 
                        'medium', 'linkedin','bufferapp', 'program']):
                    nick = config.get(section, option)
                    socialNetwork = (option, nick)
                    blog.addSocialNetwork(socialNetwork)
                    if option == 'bufferapp': 
                        blog.setBufferapp(config.get(section, "bufferapp"))
                    if option == 'program': 
                        blog.setProgram(config.get(section, "program"))

            logging.info("Looking for pending posts in ...", blog.getSocialNetworks())

            bufferMax = 10
            if ("bufferapp" in config.options(section)):
                api = moduleSocial.connectBuffer()
                lenMax, profileList = moduleSocial.checkLimitPosts(api,'', '', blog.getBufferapp())

                for profile in profileList:
                    logging.info(profile['service'],blog.getBufferapp())
                    if (profile['service'][0] in blog.getBufferapp()): 
                        lastLink, lastTime = blog.checkLastLink((profile['service'], profile['service_username']))
                        blog.addLastLinkPublished((profile['service'], lastLink))
                        i = blog.getLinkPosition(lastLink)
                        logging.debug("i, lastLink", i,lastLink)
                        if ((profile['service'] == 'twitter') 
                           or (profile['service'] == 'facebook')):
                            # We should add a configuration option in order
                            # to check which services are the ones with
                            # immediate posting. For now, we know that we are using
                            # Twitter and Facebook We are checking the links tha
                            # have been published with other toolsin order to avoid
                            # duplicates

                            path = os.path.expanduser('~')
                            with open(path + '/.urls.pickle', 'rb') as f:
                                theList = pickle.load(f)
                        else:
                            theList = []

                        num = bufferMax - lenMax

                        listPosts = []
                        for j in range(num, 0, -1):
                            if (i <= 0):
                                break
                            i = i - 1

                            listPosts.append(blog.obtainPostData(i, False))

                            (title, link, firstLink, image, summary, summaryHtml, summaryLinks, content, links, comment) = (blog.obtainPostData(i, False))
                            moduleSocial.publishBuffer(blog, profile, title, link, firstLink, isDebug, lenMax, blog.getBufferapp())
                            if listPosts:
                                loggint.info("listPosts", listPosts)
            else:
                if not isDebug:
                    for socialNetwork in blog.getSocialNetworks().keys():
                        loggint.info(socialNetwork)
                        lastLink, lastTime = blog.checkLastLink((socialNetwork, blog.getSocialNetworks()[socialNetwork]))
                        blog.addLastLinkPublished((option, lastLink)) 
                        i = blog.getLinkPosition(lastLink) 
                        logging.debug(i)
                        if (i > 0):
                            nick = blog.getSocialNetworks()[socialNetwork]
                            (title, link, firstLink, image, summary, summaryHtml, summaryLinks, content , links, comment) = (blog.obtainPostData(i - 1, False))
                            hours = blog.getTime() 
                            if (hours and (((time.time() - lastTime) - int(hours)*60*60) < 0)): 
                                logging.info("Not publishing because time restriction\n") 
                            else:
                                logging.info("Publishing directly\n") 
                                publishMethod = getattr(moduleSocial, 
                                        'publish'+ socialNetwork.capitalize())
                                publishMethod(nick, title, link, summary, summaryHtml, summaryLinks, image, content, links)
                                logging.info("Updating Link\n") 
                                blog.updateLastLink(link, (socialNetwork, blog.getSocialNetworks()[socialNetwork]))

            if ('program' in config.options(section)):
                blog.setProgram(config.get(section, "program"))
                lenMax = 6
                profileList = blog.getSocialNetworks().keys()
                lenMax, profileList = moduleSocial.checkLimitPosts('', blog.getUrl(), blog.getSocialNetworks(), blog.getProgram())
                logging.debug("Lenmax ", lenMax)

                for profile in profileList:
                    if profile[0] in blog.getProgram():
                        lastLink, lastTime = blog.checkLastLink((profile, blog.getSocialNetworks()[profile]))
                        blog.addLastLinkPublished((profile, lastLink))
                        i = blog.getLinkPosition(lastLink) 
                        logging.info("lastLink", profile, lastLink, "i",i)
                        if ((profile == 'twitter') or (profile == 'facebook')):
                            # We should add a configuration option in order
                            # to check which services are the ones with
                            # immediate posting. For now, we know that we
                            # are using Twitter and Facebook We are
                            # checking the links tha have been published
                            # with other toolsin order to avoid duplicates

                            path = os.path.expanduser('~')
                            with open(path + '/.urls.pickle', 'rb') as f:
                                theList = pickle.load(f)
                        else:
                            theList = []

                        num = bufferMax - lenMax
                        logging.info("bufferMax - lenMax = num", bufferMax, lenMax, num)
                        listPosts = []
                        for j in range(num, 0, -1):
                            if (i <= 0):
                                break
                            i = i - 1
                            (title, link, firstLink, image, summary, summaryHtml, summaryLinks, content, links, comment) = (blog.obtainPostData(i, False))
                            listPosts.append((title, link, firstLink, image, summary, summaryHtml, summaryLinks, content, links, comment))
                            #moduleSocial.publishTumblr("", title, firstLink, summary, summaryHtml, summaryLinks, image, content, links)

                        if listPosts:
                            link = listPosts[len(listPosts) - 1][1]
                            loggign.debug("link ->", link) 
                        else: 
                            link = ''

                        timeSlots = 60*60 # One hour
                        if (profile == 'twitter'): 
                            theNick = blog.getSocialNetworks()['twitter']
                            t = threading.Thread(target=moduleSocial.publishDelayTwitter, args=(blog, listPosts, theNick, timeSlots)) 
                            t.start()
                        if (profile == 'facebook'): 
                            theNick = blog.getSocialNetworks()['facebook']
                            t1 = threading.Thread(target=moduleSocial.publishDelayFacebook, args=(blog, listPosts, theNick, timeSlots)) 
                            t1.start()

                        if link:
                            blog.updateLastLink(link, (profile,blog.getSocialNetworks()[profile]))

            time.sleep(2)

    print("====================================")
    print("Finished at %s" % time.asctime())
    print("====================================")
    logging.info("Finished at %s" % time.asctime())


if __name__ == '__main__':
    main()




