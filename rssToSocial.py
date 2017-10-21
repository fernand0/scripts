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
import moduleSocial

import configparser
import os
import logging
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
    blog.getBlogPosts()
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

    isDebug = False
    loggingLevel = logging.INFO

    config = configparser.ConfigParser()
    config.read([os.path.expanduser('~/.rssBlogs')])

    logging.basicConfig(filename=os.path.expanduser("~") 
                        + "/usr/var/rssSocial_.log",
                        level=loggingLevel, format='%(asctime)s %(message)s')

    print("Configured blogs:")

    blogs = []

    for section in config.sections():
        rssFeed = config.get(section, "rssFeed")
        print("Blog: ", rssFeed)
        blog = moduleBlog.moduleBlog()
        blog.setRssFeed(rssFeed)

        optFields = ["linksToAvoid", "time", "bufferapp"]
        if ("linksToAvoid" in config.options(section)):
            blog.setLinksToAvoid(config.get(section, "linksToAvoid"))
        if ("time" in config.options(section)):
            blog.setTime(config.get(section, "time"))

        for option in config.options(section):
            if ('ac' in option) or ('fb' in option):
                blog.addSocialNetwork((option, config.get(section, option)))

        blog.getBlogPosts()
        blogs.append(blog)
        
        lastLink = blog.checkLastLink()
        i = blog.getLinkPosition(lastLink)
        print("Position: ", i)
        print("Publishing pending posts\n")

        if ("bufferapp" in config.options(section)):
            blog.setBufferapp(config.get(section, "bufferapp"))
            api = moduleSocial.connectBuffer()
            lenMax, profileList = moduleSocial.checkLimitPosts(api)
            bufferMax = 10
            for j in range(bufferMax-lenMax, 0, -1):
                if (i == 0):
                    break
                i = i - 1

                (title, link, firstLink, image, summary, summaryHtml, summaryLinks, comment) = (blog.obtainPostData(i))
                moduleSocial.publishBuffer(profileList, title, link, firstLink, isDebug, lenMax)
        else:
            if (i > 0):
                (title, link, firstLink, image, summary, summaryHtml, summaryLinks, comment) = (blog.obtainPostData(i - 1))
                if not isDebug:
                    if 'twitterac' in blog.getSocialNetworks():
                        twitter = blog.getSocialNetworks()['twitterac']
                        moduleSocial.publishTwitter(title, link, comment, twitter)
                    if 'pagefb' in blog.getSocialNetworks():
                        fbPage = blog.getSocialNetworks()['pagefb']
                        moduleSocial.publishFacebook(title, link, summaryLinks, image, fbPage)
                    if 'telegramac' in blog.getSocialNetworks():
                        telegram = blog.getSocialNetworks()['telegramac']
                        moduleSocial.publishTelegram(telegram, title, link, summary, summaryHtml, summaryLinks, image)
                    if 'mediumac' in blog.getSocialNetworks():
                        medium = blog.getSocialNetworks()['mediumac']
                        moduleSocial.publishMedium(medium, title, link, summary, summaryHtml, summaryLinks, image)

                    moduleSocial.publishLinkedin(title, link, summary, image)

                    if (link):
                        urlFile = open(os.path.expanduser("~/."
                                       + urllib.parse.urlparse(link).netloc
                                       + ".last"), "w")
        
                        urlFile.write(link)
                        urlFile.close()


if __name__ == '__main__':
    main()


# Not used
#def checkPendingPosts(feed, lastLink):
#    posts = []
#    for entry in feed.entries:
#        lenCmp = min(len(entry['link']), len(lastLink))
#        if entry['link'][:lenCmp] == lastLink[:lenCmp]:
#            return posts
#        posts.append(entry) 
#
#    return posts

# Not used
#def selectBlog(sel='a'):
#    config = configparser.ConfigParser()
#    config.read([os.path.expanduser('~/.rssBlogs')])
#    print("Configured blogs:")
#
#    feed = []
#    # We are caching the feeds in order to use them later
#
#    i = 1
#    recentPosts = {}
#
#    for section in config.sections():
#        rssFeed = config.get(section, "rssFeed")
#        if 'time' in config[section].keys():
#	# We can put a limit (in hours). If this time has not pased since the
#	# last time we posted we will skip this post. 
#            filename = os.path.expanduser("~/." + urllib.parse.urlparse(rssFeed).netloc + ".last")
#            if ((time.time() - os.path.getmtime(filename))-24*60*60) < 0:
#                continue
#        feed.append(feedparser.parse(rssFeed))
#        lastPost = feed[-1].entries[0]
#        print('%s) %s %s (%s)' % (str(i), section,
#                                  config.get(section, "rssFeed"),
#                                  time.strftime('%Y-%m-%d %H:%M:%SZ',
#                                  lastPost['published_parsed'])))
#        lastLink = checkLastLink(config.get(section, "rssFeed"))
#        lenCmp = min(len(lastLink),len(lastPost['link']))
#
#        if lastLink[:lenCmp] != lastPost['link'][:lenCmp]:
#            # There are new posts
#            recentPosts[section] = {}
#            recentPosts[section]['posts'] = checkPendingPosts(feed[-1], lastLink)
#        if (i == 1) or (recentDate < lastPost['published_parsed']):
#            recentDate = lastPost['published_parsed']
#            recentFeed = feed[-1]
#            recentPost = lastPost
#            recentIndex = str(i)
#        i = i + 1
#
#    if (sel == 'm'):
#        if (int(i) > 1):
#            recentIndex = input('Select one: ')
#            i = int(recentIndex)
#            recentFeed = feed[i - 1]
#        else:
#            i = 1
#            recentIndex = '1'
#
#    if i > 1:
#        recentFeedBase = recentFeed.feed['title_detail']['base']
#        ini = recentFeedBase.find('/')+2
#        fin = recentFeedBase[ini:].find('.')
#        identifier = recentFeedBase[ini:ini+fin] + "_" + \
#            recentFeedBase[ini+fin+1:ini+fin+7]
#        #print("Selected ", recentFeedBase)
#        logging.info("Selected " + recentFeedBase)
#    else:
#        sys.exit()
#
#    selectedBlog = {}
#    for section in recentPosts.keys():
#        for option in config.options(section):
#            recentPosts[section][option] = config.get(section, option)
#        selectedBlog["identifier"] = identifier
#
#    return(recentFeed, selectedBlog, recentPosts)


