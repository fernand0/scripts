#!/usr/bin/env python
# encoding: utf-8
#
# Very simple Python program to publish the last RSS entry of a feed
# in available social networks.
#
# It shows the blogs available and allows to select one of them.
#
# It has a configuration file with a number of blogs with:
#    - The RSS feed of the blog
#    - The Twitter account where the news will be published
#    - The Facebook page where the news will be published
# It uses a configuration file that has two sections:
#      - The oauth access token
#
# And more thins. To be done.
#
#
#

import BlogData
import configparser
import os
import logging
import feedparser
import facebook
from linkedin import linkedin
from twitter import *
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


def extractImage(soup):
    pageImage = soup.findAll("img")
    #  Only the first one
    if len(pageImage) > 0:
        imageLink = (pageImage[0]["src"])
    else:
        imageLink = ""

    if imageLink.find('?') > 0:
        return imageLink[:imageLink.find('?')]
    else:
        return imageLink

def extractLinks(soup, linksToAvoid=""):
    j = 0
    linksTxt = ""
    links = soup.find_all(["a","iframe"])
    for link in soup.find_all(["a","iframe"]):
        theLink = ""
        if len(link.contents) > 0: 
            if not isinstance(link.contents[0], Tag):
                # We want to avoid embdeded tags (mainly <img ... )
                theLink = link['href']
        else:
            theLink = link['src']

        if ((linksToAvoid == "") or
           (not re.search(linksToAvoid, theLink))):
                if theLink:
                    link.append(" ["+str(j)+"]")
                    linksTxt = linksTxt + "["+str(j)+"] " + \
                        link.contents[0] + "\n"
                    linksTxt = linksTxt + "    " + theLink + "\n"
                    j = j + 1

    if linksTxt != "":
        theSummaryLinks = soup.get_text().strip('\n') + "\n\n" + linksTxt
    else:
        theSummaryLinks = soup.get_text().strip('\n')

    return theSummaryLinks

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

    # instantiate the api object
    api = API(client_id=clientId,
              client_secret=clientSecret,
              access_token=accessToken)

    logging.debug(api.info)

    return(api)

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

def obtainBlogData(postsBlog, lenMax, i):
    posts = postsBlog['posts']
    theSummary = posts[i]['summary']
    theTitle = posts[i]['title']
    tumblrLink = posts[i]['link']
    theSummaryLinks = ""

    soup = BeautifulSoup(posts[i]['summary'], 'lxml')

    link = soup.a
    if link is None:
       theLink = tumblrLink
    else:
       theLink = link['href']
       pos = theLink.find('.')
       lenProt = len('http://')
       if (theLink[lenProt:pos] == theTitle[:pos - lenProt]):
           # A way to identify retumblings. They have the name of the tumblr at
           # the beggining of the anchor text
           logging.debug("It's a retumblr")
           logging.debug(theTitle)
           logging.debug(theTitle[pos - lenProt + 1:])
           theTitle = theTitle[pos - lenProt + 1:]

    if 'content' in posts[i]:
        summaryHtml = posts[i]['content'][0]['value']
    else:    
        summaryHtml = posts[i]['summary']

    soup = BeautifulSoup(summaryHtml, 'lxml')

    theSummary = soup.get_text()
    if "linkstoavoid" in postsBlog:
        theSummaryLinks = extractLinks(soup, postsBlog["linkstoavoid"])
    else:
        theSummaryLinks = extractLinks(soup, "")
    theImage = extractImage(soup)

    return (theTitle, theLink, tumblrLink, theImage, theSummary, summaryHtml ,theSummaryLinks)

def publishBuffer(profileList, posts, isDebug, lenMax, i):
    if isDebug:
        profileList = []
        tumblrLink = None
    fail = 'no'
    for profile in profileList:
        line = profile['service']
        print(profile['service'])

        try:
            if titlePostT and (profile['service'] == 'twitter'):
                profile.updates.new(urllib.parse.quote(titlePostT + " " + link).encode('utf-8'))
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
                       + urllib.parse.urlparse(tumblrLink).netloc
                       + ".fail"), "w")
            failFile.write(post)
            logging.info("  %s service" % line)
            fail = 'yes'
            break

        logging.info("  %s service" % line)
        if (fail == 'no' and tumblrLink):
            urlFile = open(os.path.expanduser("~/."
                           + urllib.parse.urlparse(tumblrLink).netloc
                           + ".last"), "w")
    
            urlFile.write(tumblrLink)
            urlFile.close()

def publishTwitter(title, link, comment, twitter):

    config = configparser.ConfigParser()
    config.read([os.path.expanduser('~/.rssTwitter')])

    statusTxt = comment + " " + title + " " + link
    h = HTMLParser()
    statusTxt = h.unescape(statusTxt)

    CONSUMER_KEY = config.get("appKeys", "CONSUMER_KEY")
    CONSUMER_SECRET = config.get("appKeys", "CONSUMER_SECRET")
    TOKEN_KEY = config.get(twitter, "TOKEN_KEY")
    TOKEN_SECRET = config.get(twitter, "TOKEN_SECRET")

    print("Twitter...\n")

    try:
        authentication = OAuth(
                    TOKEN_KEY,
                    TOKEN_SECRET,
                    CONSUMER_KEY,
                    CONSUMER_SECRET)
        t = Twitter(auth=authentication)
        t.statuses.update(status=statusTxt)
    except:
        print("Twitter posting failed!\n")
        print("Unexpected error:", sys.exc_info()[0])

def publishFacebook(title, link, summaryLinks, image, fbPage):
    config = configparser.ConfigParser()
    config.read([os.path.expanduser('~/.rssFacebook')])

    print("Facebook...\n")
    try:
        oauth_access_token = config.get("Facebook", "oauth_access_token")

        graph = facebook.GraphAPI(oauth_access_token, version='2.7')
        pages = graph.get_connections("me", "accounts")

        for i in range(len(pages['data'])):
            if (pages['data'][i]['name'] == fbPage):
                print("\tWriting in... ", pages['data'][i]['name'], "\n")
                graph2 = facebook.GraphAPI(pages['data'][i]['access_token'])
                h = HTMLParser()
                title = h.unescape(title)
                graph2.put_object(pages['data'][i]['id'],
                                  "feed", message=title + " \n" + summaryLinks,
                                  link=link, picture=image,
                                  name=title, caption='',
                                  description=summaryLinks.encode('utf-8'))
    except:
        print("Facebook posting failed!\n")
        print("Unexpected error:", sys.exc_info()[0])


def publishLinkedin(title, link, summary, image):
    config = configparser.ConfigParser()
    config.read([os.path.expanduser('~/.rssLinkedin')])

    CONSUMER_KEY = config.get("Linkedin", "CONSUMER_KEY")
    CONSUMER_SECRET = config.get("Linkedin", "CONSUMER_SECRET")
    USER_TOKEN = config.get("Linkedin", "USER_TOKEN")
    USER_SECRET = config.get("Linkedin", "USER_SECRET")
    RETURN_URL = config.get("Linkedin", "RETURN_URL"),

    print("Linkedin...\n")
    try:
        authentication = linkedin.LinkedInDeveloperAuthentication(
                    CONSUMER_KEY,
                    CONSUMER_SECRET,
                    USER_TOKEN,
                    USER_SECRET,
                    RETURN_URL,
                    linkedin.PERMISSIONS.enums.values())

        application = linkedin.LinkedInApplication(authentication)

        comment = 'Publicado! ' + title 
        application.submit_share(comment, title, summary, link, image)
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
    config = configparser.ConfigParser()
    config.read([os.path.expanduser('~/.rssTelegram')])

    print("Telegram...%s\n"%channel)

    if True:
        TOKEN = config.get("Telegram", "TOKEN")
        bot = telepot.Bot(TOKEN)
        meMySelf = bot.getMe()

        h = HTMLParser()
        title = h.unescape(title)
        htmlText='<a href="'+link+'">'+title + "</a>\n" + summaryHtml
        soup = BeautifulSoup(htmlText)
        cleanTags(soup)
        print(soup)
        textToPublish = str(soup)[:4096]
        index = textToPublish.rfind('<')
        index2 = textToPublish.find('>',index)
        if (index2 < 0):
        # unclosed tag
        # Maybe we can still have an unclosed tag
        # Something like: <a href="">< we would 
            textToPublish = str(soup)[:index - 1]+' ...'
        bot.sendMessage('@'+channel, textToPublish, parse_mode='HTML') 

def test():
    config = configparser.ConfigParser()
    config.read([os.path.expanduser('~/.rssBlogs')])
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
         theSummaryLinks = extractLinks(soup)
         print("post links",i,theSummaryLinks)

    return recentPosts


def main():

    isDebug = False
    loggingLevel = logging.INFO

    #if len(sys.argv) > 1:
    #    if sys.argv[1] == "-m":
    #        recentFeed, selectedBlog, recentPosts = selectBlog('m')
    #    if sys.argv[1] == "-t":
    #        test()
    #        sys.exit()
    #    if sys.argv[1] == "-d":
    #        print("debug")
    #        recentFeed, selectedBlog, recentPosts = selectBlog()
    #        loggingLevel = logging.DEBUG
    #        isDebug = True
    #else:
    #    recentFeed, selectedBlog, recentPosts = selectBlog()

    config = configparser.ConfigParser()
    config.read([os.path.expanduser('~/.rssBlogs')])

    logging.basicConfig(filename=os.path.expanduser("~") 
                        + "/usr/var/rssSocial_.log",
                        level=loggingLevel, format='%(asctime)s %(message)s')

    print("Configured blogs:")

    blogs = []

    for section in config.sections():
        rssFeed = config.get(section, "rssFeed")
        print(rssFeed)
        blog = BlogData.BlogData()
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
        print(i)
        print("Publishing pending post")

        if ("bufferapp" in config.options(section)):
            blog.setBufferapp(config.get(section, "bufferapp"))
            api = connectBuffer()
            lenMax, profileList = checkLimitPosts(api)
            bufferMax = 10
            for j in range(bufferMax-lenMax, 0, -1):
                if (i == 0):
                    break
                i = i - 1

                (title, link, tumblrLink, image, summary, summaryHtml, summaryLinks) = (
                     blog.obtainPostData(i)
                )
                publishBuffer(profileList, recentPosts[i], isDebug,
                             lenMax, len(recentPosts[i]['posts']))
        else:
            (title, link, tumblrLink, image, summary, summaryHtml, summaryLinks) = (
                 blog.obtainPostData(i)
            )
            continue
    sys.exit()



    for i in recentPosts.keys():
        if 'bufferapp' in recentPosts[i]:
            api = connectBuffer()
            lenMax, profileList = checkLimitPosts(api)

            bufferMax = 10
            for j in range(bufferMax-lenMax, 0, -1):
                if (i == 0):
                    break
                i = i - 1

                titlePost = re.sub('\n+', ' ', title)
                if (len(titlePost) > 140 - 30):
                    # We are allowing 30 characters for the (short) link 
                    titlePostT = titlePost[:140-30] 
                else:
                    titlePostT = ""
                post = titlePost + " " + link
                logging.info("Publishing... %s" % post)

                logging.info("Publishing... %s" % post)

                publishBuffer(profileList, recentPosts[i], isDebug,
                             lenMax, len(recentPosts[i]['posts']))
        else:
            print("Publishing pending post")
            posts = recentPosts[i]
            (title, tumblrLink, link, image, summary, summaryHtml, summaryLinks) = (
                  obtainBlogData(posts, 1, len(recentPosts[i]['posts'])-1)
            )
            tumblrLink = link
            print("title",title, link, tumblrLink, image)
            if ('comment' in recentPosts[i]):
                comment = recentPosts[i]['comment']
            else:
                comment = ""

            if not isDebug:
                if 'twitterac' in recentPosts[i]:
                    twitter = recentPosts[i]['twitterac']
                    publishTwitter(title, link, comment, twitter)
                if 'pagefb' in recentPosts[i]:
                    fbPage = recentPosts[i]['pagefb']
                    publishFacebook(title, link, summaryLinks, image, fbPage)
                if 'telegramac' in recentPosts[i]:
                    telegram = recentPosts[i]['telegramac']
                    publishTelegram(telegram, title,link,summary, summaryHtml, summaryLinks, image)

                publishLinkedin(title, link, summary, image)

                if (tumblrLink):
                    urlFile = open(os.path.expanduser("~/."
                                   + urllib.parse.urlparse(tumblrLink).netloc
                                   + ".last"), "w")
        
                    urlFile.write(tumblrLink)
                    urlFile.close()


if __name__ == '__main__':
    main()
