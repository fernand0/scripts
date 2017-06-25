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
from colorama import Fore
from buffpy.api import API
from buffpy.managers.profiles import Profiles
from buffpy.managers.updates import Update


#importlib.reload(sys)
#sys.setdefaultencoding("UTF-8")


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
    print("ll",links)
    for link in soup.find_all(["a","iframe"]):
        print("link", link)
        print("link cont", link.contents, type(link.contents))
        theLink = ""
        if len(link.contents) > 0: 
            if not isinstance(link.contents[0], Tag):
                # We want to avoid embdeded tags (mainly <img ... )
                theLink = link['href']
        else:
            theLink = link['src']
        #print(linksToAvoid)
        #print(re.escape(linksToAvoid))
        #print(str(link['href']))
        #print(re.search(linksToAvoid, link['href']))
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
    urlFile = open(os.path.expanduser("~/." 
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
                print("no")
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
           print("si")
           print(theTitle)
           print(theTitle[pos - lenProt + 1:])
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
    sys.exit()
    if posts['posts'][i]['type'] == 'photo':
        print('photo')
        soup = BeautifulSoup(posts['posts'][i]['caption'], 'lxml')
        link = soup.a
        if link:
            theLink = link['href']
            theTitle = link.get_text()
        elif 'post_url' in posts['posts'][i]:
            # Tumblr photo
            theLink = posts['posts'][i]['post_url']
            theTitle = soup.get_text()
        else:
            from pprint import pprint 
            pprint (posts['posts'][i])
            theLink = posts['posts'][i]['link_url']
            theTitle = soup.get_text()
    elif posts['posts'][i]['type'] == 'link':
        print('link')
        #print(posts['posts'][i])
        theLink = posts['posts'][i]['url']
        theTitle = posts['posts'][i]['title']
    elif 'post_url' in posts['posts'][i]:
        print('post_url')
        print(posts['posts'][i])
        theLink = posts['posts'][i]['post_url']
        theTitle = posts['posts'][i]['summary']
    elif 'caption' in posts['posts'][i]:
        #soup = BeautifulSoup(posts['posts'][i]['caption'],'lxml')
        #print "Content: "+ soup.get_text()
        #print posts['posts'][i]['trail'][0].keys()
        soup = BeautifulSoup(posts['posts'][i]['trail'][0]['content'], 'lxml')
        sys.exit()
        if 'source_url' in posts['posts'][i]:
            #print('posts',posts['posts'][i])
            theLink = posts['posts'][i]['source_url']
            theTitle = soup.findAll("a")[0].get_text()
            if len(re.findall(r'\w+', theTitle)) == 1:
                #reTumblr
                logging.debug("Una palabra, probamos con el titulo")
                #print(posts['posts'][i]['summary'])
                theTitle = posts['posts'][i]['summary']
            if (theLink[:26] == "https://www.instagram.com/") and \
               (theTitle[:17] == "A video posted by"):
                # exception for Instagram videos
                theTitle = posts['posts'][i]['summary']
            if (theLink[:22] == "https://instagram.com/") and \
               (theTitle.find("(en") > 0):
                theTitle = theTitle[:theTitle.find("(en")-1]
        else:
            #print('no source_url')
            # Some entries do not have a proper link and the rss contains
            # the video, image, ... in the description.
            # In this case we use the title and the link of the entry.
            theLink = posts['posts'][i]['post_url']
            theTitle = posts['posts'][i]['summary']


    else:
        #print "s "+ posts['posts'][i]['summary']
        theLink = posts['posts'][i]['post_url']
        theTitle = posts['posts'][i]['summary']

    #print("Link: "+ theLink)
    #print("Title: "+ theTitle)
    if theTitle is None:
        theTitle = ""
    if theLink is None:
        theLink = ""
    theTitle = urllib.quote(theTitle.encode('utf-8'))
    tumblrLink = posts['posts'][i]['post_url']

    return (theTitle, theLink, tumblrLink)


def publishBuffer(profileList, posts, isDebug, lenMax, i):
    tumblrLink = ""

    bufferMax = 10
    for j in range(bufferMax-lenMax, 0, -1):
        if (i == 0):
            break
        i = i - 1
        #print(i)
        #if 'blog' in posts:
        (title, link, tumblrLink, image, summary, summaryHtml, summaryLinks) = (
             obtainBlogData(posts, lenMax, i)
        )
        #else:
        #    title, link = obtainBlogData(posts, lenMax, i)
        #print("title",title, link, tumblrLink)

        titlePost = re.sub('\n+', ' ', title)
        if (len(titlePost) > 140 - 30):
            # We are allowing 30 characters for the (short) link 
            titlePostT = titlePost[:140-30] 
        else:
            titlePostT = ""
        post = titlePost + " " + link
        logging.info("Publishing... %s" % post)
        print("============================================================\n")
        print("Results: \n")
        print("============================================================\n")
        print("Title:     ", title)
        print("Link:      ", link)
        print("tumb Link: ", tumblrLink)
        print("Summary:   ", summary)
        print("Sum links: ", summaryLinks)
        print("Image;     ", image)
        print("Post       ", post)
        print("============================================================\n")

        #print(type(post))
        if isDebug:
            profileList = []
            tumblrLink = None
        fail = 'no'
        for profile in profileList:
            line = profile['service']
            print(profile['service'])
            #from pprint import pprint 
            #pprint (profile)
            #pprint (post)
            #print("type", type(post))
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
                #pprint (vars(sys.exc_info()[1]))
                #pprint (sys.exc_info()[1].__str__())

                #sys.exit()
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

def cleanTags(soup):
    tags = [tag.name for tag in soup.find_all()]
    validTags = ['b', 'strong', 'i', 'em', 'a', 'code', 'pre']

    if soup.blockquote:
        soup.blockquote.insert_before('«')
        soup.blockquote.insert_after( '»')

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
        #bot.sendMessage('@'+channel,'<a href="'+link+'">'+title + "</a>\n"
        #            #+ "\nEnlace: " + link
        #            #+ "\nEscribí: \n"
        #            + summaryHtml, parse_mode='HTML') 
    #except:
    #    print("Telegram posting failed!\n")
    #    print("Unexpected error:", sys.exc_info()[0])

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

    if len(sys.argv) > 1:
        if sys.argv[1] == "-m":
            recentFeed, selectedBlog, recentPosts = selectBlog('m')
        if sys.argv[1] == "-t":
            test()
            sys.exit()
        if sys.argv[1] == "-d":
            print("debug")
            recentFeed, selectedBlog, recentPosts = selectBlog()
            loggingLevel = logging.DEBUG
            isDebug = True
    else:
        recentFeed, selectedBlog, recentPosts = selectBlog()

    logging.basicConfig(filename='/home/ftricas/usr/var/rssSocial_.log',
                        level=loggingLevel, format='%(asctime)s %(message)s')

    #print(recentPosts.keys())
    for i in recentPosts.keys():
        if 'bufferapp' in recentPosts[i]:
            print("Bufferapp")
            api = connectBuffer()
            lenMax, profileList = checkLimitPosts(api)
            publishBuffer(profileList, recentPosts[i], isDebug,
                         lenMax, len(recentPosts[i]['posts']))
        else:
            print("Publishing pending post")
            #print("Hay ", len(recentPosts[i]['posts']))
            #print(recentPosts[i]['posts'][len(recentPosts[i]['posts'])-1])
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

    #title, link, summary, comment, summaryLinks, image, twitter, fbPage, telegram, bufferapp = \
    #    getBlogData(recentFeed, selectedBlog)

            #isDebug = True
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

# Not in use
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


