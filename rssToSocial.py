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

import configparser
import os
import logging
import feedparser
import facebook
from linkedin import linkedin
from twitter import *
import telepot
import re
import sys
import time
import datetime
from bs4 import BeautifulSoup
from bs4 import NavigableString
from bs4 import Tag
import importlib
import urllib.parse
# sudo pip install buffpy version does not work
# Better use:
# git clone https://github.com/vtemian/buffpy.git
# cd buffpy
# sudo python setup.py install
from colorama import Fore
from buffpy.api import API
from buffpy.managers.profiles import Profiles
from buffpy.managers.updates import Update


importlib.reload(sys)
#sys.setdefaultencoding("UTF-8")


def extractImage(soup):
    pageImage = soup.findAll("img")
    #  Only the first one
    if len(pageImage) > 0:
        imageLink = (pageImage[0]["src"])
    else:
        imageLink = ""

    return imageLink


def extractLinks(soup, linksToAvoid=""):
    j = 0
    linksTxt = ""
    for link in soup("a"):
        if not isinstance(link.contents[0], Tag):
            # We want to avoid embdeded tags (mainly <img ... )

            print(linksToAvoid)
            print(re.escape(linksToAvoid))
            print(str(link['href']))
            print(re.search(linksToAvoid, link['href']))
            if ((linksToAvoid == "") or
               (not re.search(linksToAvoid, link['href']))):
                    link.append(" ["+str(j)+"]")
                    linksTxt = linksTxt + "["+str(j)+"] " + \
                        link.contents[0] + "\n"
                    linksTxt = linksTxt + "    " + link['href'] + "\n"
                    j = j + 1
    if linksTxt != "":
        theSummaryLinks = soup.get_text() + "\n\n" + linksTxt
    else:
        theSummaryLinks = soup.get_text()

    return theSummaryLinks

def checkLastLink(rssFeed):
    urlFile = open(os.path.expanduser("~/." 
              + urllib.parse.urlparse(rssFeed).netloc
              + ".last"), "r")
    linkLast = urlFile.read().rstrip()  # Last published
    return(linkLast)

def checkPendingPosts(feed, lastLink):
    posts = []
    for entry in feed.entries:
        if entry['link'] == lastLink:
            break
        posts.append(feed) 

    return posts

def selectBlog(sel='a'):
    config = configparser.ConfigParser()
    config.read([os.path.expanduser('~/.rssBlogs')])
    print("Configured blogs:")

    feed = []
    # We are caching the feeds in order to use them later

    i = 1

    for section in config.sections():
        rssFeed = config.get(section, "rssFeed")
        feed.append(feedparser.parse(rssFeed))
        lastPost = feed[-1].entries[0]
        print('%s) %s %s (%s)' % (str(i), section,
                                  config.get(section, "rssFeed"),
                                  time.strftime('%Y-%m-%d %H:%M:%SZ',
                                  lastPost['published_parsed'])))
        lastLink = checkLastLink(config.get(section, "rssFeed"))
        if lastLink != lastPost['link']:
            posts = checkPendingPosts(feed[-1], lastLink)
            print(posts)
            print(len(posts))
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

    if i > 0:
        recentFeedBase = recentFeed.feed['title_detail']['base']
        ini = recentFeedBase.find('/')+2
        fin = recentFeedBase[ini:].find('.')
        identifier = recentFeedBase[ini:ini+fin] + "_" + \
            recentFeedBase[ini+fin+1:ini+fin+7]
        print("Selected ", recentFeedBase)
        logging.info("Selected " + recentFeedBase)
    else:
        sys.exit()

    selectedBlog = {}
    if (config.has_option("Blog"+str(recentIndex), "linksToAvoid")):
        selectedBlog["linksToAvoid"] = config.get("Blog" + str(recentIndex),
                                                  "linksToAvoid")
    else:
        selectedBlog["linksToAvoid"] = ""

    if (config.has_option("Blog"+str(recentIndex), "comment")):
        selectedBlog["comment"] = config.get("Blog" + str(recentIndex),
                                                  "comment")

    if (config.has_option("Blog"+str(recentIndex), "twitterAC")):
        selectedBlog["twitterAC"] = config.get("Blog" + str(recentIndex),
                                           "twitterAC")
    else:
        selectedBlog["twitterAC"] = ""
    if (config.has_option("Blog"+str(recentIndex), "pageFB")):
        selectedBlog["pageFB"] = config.get("Blog" + str(recentIndex),
                                        "pageFB")
    else:
        selectedBlog["pageFB"] = ""
    if (config.has_option("Blog"+str(recentIndex), "telegramAC")):
        selectedBlog["telegramAC"] = config.get("Blog" + str(recentIndex),
                                           "telegramAC")
    else:
        selectedBlog["telegramAC"] = ""
    if (config.has_option("Blog"+str(recentIndex), "bufferapp")):
        selectedBlog["bufferapp"] = config.get("Blog" + str(recentIndex),
                                           "bufferapp")
    else:
        selectedBlog["bufferapp"] = ""

    selectedBlog["identifier"] = identifier

    print("You have chosen ")
    print(recentFeedBase)

    return(recentFeed, selectedBlog)


def getBlogData(recentFeed, selectedBlog):
    i = 0  # It will publish the last added item

    soup = BeautifulSoup(recentFeed.entries[0].title)
    theTitle = soup.get_text()
    theLink = recentFeed.entries[0].link

    soup = BeautifulSoup(recentFeed.entries[0].summary)
    theSummary = soup.get_text()

    theSummaryLinks = extractLinks(soup, selectedBlog["linksToAvoid"])
    if 'comment' in selectedBlog:
        theComment = extractLinks(soup, selectedBlog["comment"])
    else: 
        theComment = "Publicado!"
    theImage = extractImage(soup)
    theTwitter = selectedBlog["twitterAC"]
    theFbPage = selectedBlog["pageFB"]
    theTelegram = selectedBlog["telegramAC"]
    theBuffer = selectedBlog["bufferapp"]

    print("============================================================\n")
    print("Results: \n")
    print("============================================================\n")
    print("Title:     ", theTitle.encode('utf-8'))
    print("Link:      ", theLink)
    print("Summary:   ", theSummary.encode('utf-8'))
    print("Sum links: ", theSummaryLinks.encode('utf-8'))
    print("Image;     ", theImage)
    print("Comment:   ", theComment)
    print("Twitter:   ", theTwitter)
    print("Facebook:  ", theFbPage)
    print("Telegram:  ", theTelegram)
    print("Buffer:    ", theBuffer)
    print("============================================================\n")

    return (theTitle, theLink, theSummary, theComment, theSummaryLinks,
            theImage, theTwitter, theFbPage, theTelegram, theBuffer)

def publishBuffer(title, link, comment, twitter):
    sys.exit()
def publishBuffer(selectedBlog, profileList, posts, lenMax, i):
    tumblrLink = ""

    bufferMax = 10
    for j in range(bufferMax-lenMax, 0, -1):
        if (i == 0):
            break
        i = i - 1
        if 'blog' in posts:
            (title, link, tumblrLink) = obtainTumblrData(posts, lenMax, i)
        else:
            title, link = obtainBlogData(posts, lenMax, i)

        post = re.sub('\n+', ' ', title) + " " + link
        logging.info("Publishing... %s" % post)

        #print("res", post, tumblrLink)
        for profile in profileList:
            line = profile['service']
            #from pprint import pprint 
            #pprint (profile)
            #pprint (post)
            try:
                profile.updates.new(post)
                line = line + ' ok'
                time.sleep(3)
            except:
                #print "Unexpected error:", sys.exc_info()[0]
                #print "Unexpected error:", sys.exc_info()[1]
                #pprint (vars(sys.exc_info()[1]))
                #pprint (sys.exc_info()[1].__str__())

                #sys.exit()
                line = line + ' fail'
                logging.info(line)
                failFile = open(os.path.expanduser("~/." +
                        PREFIX+selectedBlog['identifier'] +
                        ".fail"), "w")
                failFile.write(post.encode('utf-8', 'ignore'))
                logging.info("  %s service" % line)
    if (tumblrLink):
        urlFile = open(os.path.expanduser("~/." +
               PREFIX + selectedBlog['identifier'] +
               "." + POSFIX), "w")

        urlFile.write(tumblrLink.encode('utf-8'))
        urlFile.close()

def publishTwitter(title, link, comment, twitter):

    config = configparser.ConfigParser()
    config.read([os.path.expanduser('~/.rssTwitter')])

    statusTxt = comment + " " + title + " " + link

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

        graph = facebook.GraphAPI(oauth_access_token)
        pages = graph.get_connections("me", "accounts")

        for i in range(len(pages['data'])):
            if (pages['data'][i]['name'] == fbPage):
                print("\tWriting in... ", pages['data'][i]['name'], "\n")
                graph2 = facebook.GraphAPI(pages['data'][i]['access_token'])
                graph2.put_object(pages['data'][i]['id'],
                                  "feed", message=title + " \n" + summaryLinks,
                                  link=link, picture=image,
                                  name=title, caption='',
                                  description=summaryLinks.encode('utf-8'))
                # graph2.put_object(pages['data'][2]['id'], "instant_articles", html_source=html, development_mode = True)
                # facebook.GraphAPIError: (#200) Requires pages_manage_instant_articles permission to manage the object
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

def publishTelegram(channel, title, link, summary, image):
    config = configparser.ConfigParser()
    config.read([os.path.expanduser('~/.rssTelegram')])

    print("Telegram...\n")

    try:
        TOKEN = config.get("Telegram", "TOKEN")
        bot = telepot.Bot(TOKEN)
        meMySelf = bot.getMe()

        bot.sendMessage('@'+channel,title + " "
                        + summary + " "
                        + "\nEnlace: " + link + " "
                        + image) 
    except:
        print("Telegram posting failed!\n")
        print("Unexpected error:", sys.exc_info()[0])

def main():

    logging.basicConfig(filename='/home/ftricas/usr/var/rssSocial_.log',
                        level=logging.INFO, format='%(asctime)s %(message)s')

    if len(sys.argv) > 1:
        if sys.argv[1] == "-m":
            recentFeed, selectedBlog = selectBlog('m')
    else:
        recentFeed, selectedBlog = selectBlog()
    sys.exit()

    title, link, summary, comment, summaryLinks, image, twitter, fbPage, telegram, bufferapp = \
        getBlogData(recentFeed, selectedBlog)

    if bufferapp:
        sys.exit()
        publishBuffer(title, link, comment, twitter)
    if twitter:
        publishTwitter(title, link, comment, twitter)
    if fbPage:
        publishFacebook(title, link, summaryLinks, image, fbPage)
    if telegram:
        publishTelegram(telegram, title,link,summary,image)

    publishLinkedin(title, link, summary, image)

    # Now we can publish it in some social network

if __name__ == '__main__':
    main()
