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


def checkLastLink(rssFeed):
    urlFile = open(os.path.expanduser("~" + "/."  
              + urllib.parse.urlparse(rssFeed).netloc
              + ".last"), "r")
    linkLast = urlFile.read().rstrip()  # Last published
    return(linkLast)

def checkPendingPosts(feed, lastLink):
    posts = []
    for entry in feed.entries:
        lenCmp = min(len(entry['link']), len(lastLink))
        if entry['link'][:lenCmp] == lastLink[:lenCmp]:
            return posts
        posts.append(entry) 

    return posts

def selectBlog(sel='a'):
    config = configparser.ConfigParser()
    config.read([os.path.expanduser('~/.rssBlogs')])
    print("Configured blogs:")

    feed = []
    # We are caching the feeds in order to use them later

    i = 1
    recentPosts = {}

    for section in config.sections():
        rssFeed = config.get(section, "rssFeed")
        if 'time' in config[section].keys():
	# We can put a limit (in hours). If this time has not pased since the
	# last time we posted we will skip this post. 
            filename = os.path.expanduser("~/." + urllib.parse.urlparse(rssFeed).netloc + ".last")
            if ((time.time() - os.path.getmtime(filename))-24*60*60) < 0:
                continue
        feed.append(feedparser.parse(rssFeed))
        lastPost = feed[-1].entries[0]
        print('%s) %s %s (%s)' % (str(i), section,
                                  config.get(section, "rssFeed"),
                                  time.strftime('%Y-%m-%d %H:%M:%SZ',
                                  lastPost['published_parsed'])))
        lastLink = checkLastLink(config.get(section, "rssFeed"))
        lenCmp = min(len(lastLink),len(lastPost['link']))

        if lastLink[:lenCmp] != lastPost['link'][:lenCmp]:
            # There are new posts
            recentPosts[section] = {}
            recentPosts[section]['posts'] = checkPendingPosts(feed[-1], lastLink)
        if (i == 1) or (recentDate < lastPost['published_parsed']):
            recentDate = lastPost['published_parsed']
            recentFeed = feed[-1]
            recentPost = lastPost
            recentIndex = str(i)
        i = i + 1

    if (sel == 'm'):
        if (int(i) > 1):
            recentIndex = input('Select one: ')
            i = int(recentIndex)
            recentFeed = feed[i - 1]
        else:
            i = 1
            recentIndex = '1'

    if i > 1:
        recentFeedBase = recentFeed.feed['title_detail']['base']
        ini = recentFeedBase.find('/')+2
        fin = recentFeedBase[ini:].find('.')
        identifier = recentFeedBase[ini:ini+fin] + "_" + \
            recentFeedBase[ini+fin+1:ini+fin+7]
        #print("Selected ", recentFeedBase)
        logging.info("Selected " + recentFeedBase)
    else:
        sys.exit()

    selectedBlog = {}
    for section in recentPosts.keys():
        for option in config.options(section):
            recentPosts[section][option] = config.get(section, option)
        selectedBlog["identifier"] = identifier

    return(recentFeed, selectedBlog, recentPosts)

def connectBuffer():
    config = configparser.ConfigParser()
    config.read([os.path.expanduser('~/.rssBuffer')])

    clientId = config.get("appKeys", "client_id")
    clientSecret = config.get("appKeys", "client_secret")
    redirectUrl = config.get("appKeys", "redirect_uri")
    accessToken = config.get("appKeys", "access_token")

    try:
        # instantiate the api object
        api = API(client_id=clientId,
                  client_secret=clientSecret,
                  access_token=accessToken)

        logging.debug(api.info)
    except:
        print("Buffer authentication failed!\n")
        print("Unexpected error:", sys.exc_info()[0])

    return(api)

def connectTwitter(twitterAC):    
    config = configparser.ConfigParser()
    config.read([os.path.expanduser('~/.rssTwitter')])

    CONSUMER_KEY = config.get("appKeys", "CONSUMER_KEY")
    CONSUMER_SECRET = config.get("appKeys", "CONSUMER_SECRET")
    TOKEN_KEY = config.get(twitterAC, "TOKEN_KEY")
    TOKEN_SECRET = config.get(twitterAC, "TOKEN_SECRET")

    try:
        authentication = OAuth(
                    TOKEN_KEY,
                    TOKEN_SECRET,
                    CONSUMER_KEY,
                    CONSUMER_SECRET)
        t = Twitter(auth=authentication)
    except:
        print("Twitter authentication failed!\n")
        print("Unexpected error:", sys.exc_info()[0])

    return(t)

def connectFacebook(fbPage):
    config = configparser.ConfigParser()
    config.read([os.path.expanduser('~/.rssFacebook')])

    try:
        oauth_access_token = config.get("Facebook", "oauth_access_token")

        graph = facebook.GraphAPI(oauth_access_token, version='2.7')
        pages = graph.get_connections("me", "accounts")

        for i in range(len(pages['data'])):
            if (pages['data'][i]['name'] == fbPage):
                print("\tWriting in... ", pages['data'][i]['name'], "\n")
                graph2 = facebook.GraphAPI(pages['data'][i]['access_token'])
                return(pages['data'][i]['access_token'], pages['data'][i]['id'])
    except:
        print("Facebook authentication failed!\n")
        print("Unexpected error:", sys.exc_info()[0])

    return(0,0)

def connectLinkedin():
    config = configparser.ConfigParser()
    config.read([os.path.expanduser('~/.rssLinkedin')])

    CONSUMER_KEY = config.get("Linkedin", "CONSUMER_KEY")
    CONSUMER_SECRET = config.get("Linkedin", "CONSUMER_SECRET")
    USER_TOKEN = config.get("Linkedin", "USER_TOKEN")
    USER_SECRET = config.get("Linkedin", "USER_SECRET")
    RETURN_URL = config.get("Linkedin", "RETURN_URL"),

    try:
        authentication = linkedin.LinkedInDeveloperAuthentication(
                         CONSUMER_KEY,
                         CONSUMER_SECRET,
                         USER_TOKEN,
                         USER_SECRET,
                         RETURN_URL,
                         linkedin.PERMISSIONS.enums.values())

        application = linkedin.LinkedInApplication(authentication)

    except:
        print("Linkedin authentication failed!\n")
        print("Unexpected error:", sys.exc_info()[0])

    return(application)

def connectTelegram(channel):
    config = configparser.ConfigParser()
    config.read([os.path.expanduser('~/.rssTelegram')])

    TOKEN = config.get("Telegram", "TOKEN")

    try:
        bot = telepot.Bot(TOKEN)
        meMySelf = bot.getMe()
    except:
        print("Telegram authentication failed!\n")
        print("Unexpected error:", sys.exc_info()[0])

    return(bot)

def connectMedium():
    config = configparser.ConfigParser()
    config.read([os.path.expanduser('~/.rssMedium')])
    client = Client(application_id=config.get("appKeys","ClientID"), application_secret=config.get("appKeys","ClientSecret"))
    try:
        client.access_token = config.get("appKeys","access_token")
        # Get profile details of the user identified by the access token.
        user = client.get_current_user()
    except:
        print("Medium authentication failed!\n")
        print("Unexpected error:", sys.exc_info()[0])

    return(client, user)


def checkLimitPosts(api):
    # We can put as many items as the service with most items allow
    # The limit is ten.
    # Get all pending updates of a social network profile

    lenMax = 0
    logging.info("Checking services...")

    profileList = Profiles(api=api).all()
    for profile in profileList:
        lenProfile = len(profile.updates.pending)
        if (lenProfile > lenMax):
            lenMax = lenProfile
        logging.info("%s ok" % profile['service'])

    logging.info("There are %d in some buffer, we can put %d" %
                 (lenMax, 10-lenMax))

    return(lenMax, profileList)

def publishBuffer(profileList, title, link, firstLink, isDebug, lenMax):
    if isDebug:
        profileList = []
        firstLink = None
    fail = 'no'
    for profile in profileList:
        line = profile['service']
        #print(profile['service'])

        if (len(title) > 140 - 24):
        # We are allowing 24 characters for the (short) link 
            titlePostT = title[:140-24] 
        else:
            titlePostT = ""
        post = title + " " + firstLink

        try:
            if titlePostT and (profile['service'] == 'twitter'):
                profile.updates.new(urllib.parse.quote(titlePostT + " " + firstLink).encode('utf-8'))
            else:
                profile.updates.new(urllib.parse.quote(post).encode('utf-8'))
            line = line + ' ok'
            time.sleep(3)
        except:
            print("Buffer posting failed!")
            print("Unexpected error:", sys.exc_info()[0])
            print("Unexpected error:", sys.exc_info()[1])
            logging.info("Buffer posting failed!")
            logging.info("Unexpected error: %s"% sys.exc_info()[0])
            logging.info("Unexpected error: %s"% sys.exc_info()[1])

            line = line + ' fail'
            failFile = open(os.path.expanduser("~/."
                       + urllib.parse.urlparse(link).netloc
                       + ".fail"), "w")
            failFile.write(post)
            logging.info("  %s service" % line)
            fail = 'yes'
            break

        logging.info("  %s service" % line)
        if (fail == 'no' and link):
            urlFile = open(os.path.expanduser("~/."
                           + urllib.parse.urlparse(link).netloc
                           + ".last"), "w")
    
            urlFile.write(link)
            urlFile.close()

def publishTwitter(title, link, comment, twitter):

    print("Twitter...\n")
    try:
        t = connectTwitter(twitter)
        statusTxt = comment + " " + title + " " + link
        h = HTMLParser()
        statusTxt = h.unescape(statusTxt)
        t.statuses.update(status=statusTxt)
    except:
        print("Twitter posting failed!\n")
        print("Unexpected error:", sys.exc_info()[0])

def publishFacebook(title, link, summaryLinks, image, fbPage):
    #publishFacebook("prueba2", "https://www.facebook.com/reflexioneseirreflexiones/", "b", "https://scontent-mad1-1.xx.fbcdn.net/v/t1.0-9/426052_381657691846622_987775451_n.jpg", "Reflexiones e Irreflexiones")

    print("Facebook...\n")
    try:
        h = HTMLParser()
        title = h.unescape(title)
        (access, page) = connectFacebook(fbPage)
        print(page)
        facebook.GraphAPI(access).put_object(page,
                          "feed", message=title + " \n" + summaryLinks,
                          link=link, picture=image,
                          name=title, caption='',
                          description=summaryLinks.encode('utf-8'))
    except:
        print("Facebook posting failed!\n")
        print("Unexpected error:", sys.exc_info()[0])


def publishLinkedin(title, link, summary, image):
    # publishLinkedin("Prueba", "http://fernand0.blogalia.com/", "bla bla bla", "https://scontent-mad1-1.xx.fbcdn.net/v/t1.0-1/31694_125680874118651_1644400_n.jpg")
    print("Linkedin...\n")
    try:
        application = connectLinkedin()
        presentation = 'Publicado! ' + title 
        application.submit_share(presentation, title, summary, link, image)
    except:
        print("Linkedin posting failed!\n")
        print("Unexpected error:", sys.exc_info()[0])

def cleanTags(soup):
    tags = [tag.name for tag in soup.find_all()]
    validTags = ['b', 'strong', 'i', 'em', 'a', 'code', 'pre']

    quotes = soup.find_all('blockquote')
    for quote in quotes:
        quote.insert_before('«')
        quote.insert_after( '»')

    for tag in tags:
        if tag not in validTags:
            for theTag in soup.find_all(tag):
                theTag.unwrap()

    code = [td.find('code') for td in soup.findAll('pre')]
    # github.io inserts code tags inside pre tags
    for cod in code:
        cod.unwrap()

    tags = soup.findAll(text=lambda text:isinstance(text, Doctype))
    if (len(tags)>0):
        tags[0].extract()
    # <!DOCTYPE html> in github.io

def publishTelegram(channel, title, link, summary, summaryHtml, summaryLinks, image):
    #publishTelegram("reflexioneseirreflexiones","Canal de Reflexiones e Irreflexiones", "http://fernand0.blogalia.com/", "", "", "", "")

    print("Telegram...%s\n"%channel)

    try:
        bot = connectTelegram(channel)

        h = HTMLParser()
        title = h.unescape(title)
        htmlText='<a href="'+link+'">'+title + "</a>\n" + summaryHtml
        soup = BeautifulSoup(htmlText)
        cleanTags(soup)
        #print(soup)
        textToPublish = str(soup)[:4096]
        index = textToPublish.rfind('<')
        index2 = textToPublish.find('>',index)
        if (index2 < 0):
        # unclosed tag
        # Maybe we can still have an unclosed tag
        # Something like: <a href="">< we would 
            textToPublish = str(soup)[:index - 1]+' ...'
        bot.sendMessage('@'+channel, textToPublish, parse_mode='HTML') 
    except:
        print("Telegram posting failed!\n")
        print("Unexpected error:", sys.exc_info()[0])

def publishMedium(channel, title, link, summary, summaryHtml, summaryLinks, image):
    print("Medium...\n")
    try:
        (client, user) = connectMedium()

        post = client.create_post(user_id=user["id"], title=title,
                content=summaryHtml, canonical_url = link,
                content_format="html", publish_status="draft")
        print("My new post!", post["url"])
    except:
        print("Medium posting failed!\n")
        print("Unexpected error:", sys.exc_info()[0])

def test():
    config = configparser.ConfigParser()
    config.read([os.path.expanduser('~/.rssBlogs')])
    blog = moduleBlog.moduleBlog()
    blog.setRssFeed('http://fernand0.blogalia.com/rss20.xml')
    blog.getBlogPosts()
    (title, link, firstLink, image, summary, summaryHtml, summaryLinks, comment) = (blog.obtainPostData(0))
    publishMedium("", title, link, summary, summaryHtml, summaryLinks, image)
    sys.exit()
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
        
        lastLink = checkLastLink(blog.getRssFeed())
        i = blog.getLinkPosition(lastLink)
        print("Position: ", i)
        print("Publishing pending posts\n")

        if ("bufferapp" in config.options(section)):
            blog.setBufferapp(config.get(section, "bufferapp"))
            api = connectBuffer()
            lenMax, profileList = checkLimitPosts(api)
            bufferMax = 10
            for j in range(bufferMax-lenMax, 0, -1):
                if (i == 0):
                    break
                i = i - 1

                (title, link, firstLink, image, summary, summaryHtml, summaryLinks, comment) = (blog.obtainPostData(i))
                publishBuffer(profileList, title, link, firstLink, isDebug, lenMax)
        else:
            if (i > 0):
                (title, link, firstLink, image, summary, summaryHtml, summaryLinks, comment) = (blog.obtainPostData(i - 1))
                if not isDebug:
                    if 'twitterac' in blog.getSocialNetworks():
                        twitter = blog.getSocialNetworks()['twitterac']
                        publishTwitter(title, link, comment, twitter)
                    if 'pagefb' in blog.getSocialNetworks():
                        fbPage = blog.getSocialNetworks()['pagefb']
                        publishFacebook(title, link, summaryLinks, image, fbPage)
                    if 'telegramac' in blog.getSocialNetworks():
                        telegram = blog.getSocialNetworks()['telegramac']
                        publishTelegram(telegram, title, link, summary, summaryHtml, summaryLinks, image)

                    publishLinkedin(title, link, summary, image)

                    if (link):
                        urlFile = open(os.path.expanduser("~/."
                                       + urllib.parse.urlparse(link).netloc
                                       + ".last"), "w")
        
                        urlFile.write(link)
                        urlFile.close()


if __name__ == '__main__':
    test()
    main()
