#!/usr/bin/env python

# This module is used as a infrastructure for publishing in several social
# networks using their APIs via different available python modules. 
#
# It uses several configuration files to store credentials such as:
# 
# .rssBlogs
# It can contain as many blogs as desired, with different parameters for each
# one (a blog can have, for example a twtter account, but not Telegram account
# and  so on).  
# The structure for one of these blogs is
# [Blog]
#     url:
#     rssFeed:
#     xmlrpc:
#     twitterAC:
#     pageFB:
#     telegramAC:
#     mediumAC:
#     linksToAvoid:
#      
# .rssTwitter 
# We can store the configuration of the app (CONSUMER_KEY and CONSUMER_SECRET)
# and the configuration for each Twitter account. For just only one Twitter
# account it could be:
# [appKeys]
#CONSUMER_KEY:
#CONSUMER_SECRET:
#[user1]
#TOKEN_KEY:
#TOKEN_SECRET:
# 
# There can be more lines for more Twitter accounts
# We can store the configuration for publishing in a Facebook page.
# 
#
# .rssFacebook
# We can store the configuration of the user. The user has to have permission
# for publishing in the page that will be selected by the program using the
# module. It has been tested with just one user account and several pages. If
# you need more than one user account some changes could be needed.
#[Facebook]
#oauth_access_token:
#
# .rssLinkedin
# We can store the configuration of the user. If you need more than one user
# account some changes could be needed.
# Parameters.
#[Linkedin]
#CONSUMER_KEY:
#CONSUMER_SECRET:
#USER_TOKEN:
#USER_SECRET:
#RETURN_URL:http://localhost:8080/code
# .rssTelegram
# We can store the configuration of the bot. If you need more than one user
# account some changes could be needed.
#[Telegram]
#TOKEN:
#
# .rssMedium
# We can store the configuration of the user. If you need more than one user
# account some changes could be needed.
#[appKeys]
#ClientID:
#ClientSecret:
#access_token:
#
# .rssBuffer
# We can store the configuration of the user. If you need more than one user
# account some changes could be needed.
#[appKeys]
#client_id:
#client_secret:
#redirect_uri:urn:ietf:wg:oauth:2.0:oob
#access_token:
#

import configparser
import os
import sys
import random
import logging
from bs4 import BeautifulSoup
from bs4 import NavigableString
from bs4 import Tag
from bs4 import Doctype
from html.parser import HTMLParser
import facebook
import urllib
import time
from linkedin import linkedin
from tumblpy import Tumblpy
from twitter import *
#https://pypi.python.org/pypi/twitter
#http://mike.verdone.ca/twitter/
#https://github.com/sixohsix/twitter/tree
from html.parser import HTMLParser
import pickle 
import telepot
# sudo pip install buffpy version does not work
# Better use:
# git clone https://github.com/vtemian/buffpy.git
# cd buffpy
# sudo python setup.py install
import buffpy
from buffpy.managers.profiles import Profiles
from buffpy.managers.updates import Update
from medium import Client
from pocket import Pocket, PocketException
import moduleCache
# https://github.com/fernand0/scripts/blob/master/moduleCache.py
import moduleBuffer
# https://github.com/fernand0/scripts/blob/master/moduleBuffer.py

from configMod import *

logger = logging.getLogger(__name__)


def publishMail(channel, title, link, summary, summaryHtml, summaryLinks, image, content = "", links = ""):
    # publishLinkedin("Prueba", "http://fernand0.blogalia.com/", "bla bla bla", "https://scontent-mad1-1.xx.fbcdn.net/v/t1.0-1/31694_125680874118651_1644400_n.jpg")
    logger.info("Publishing in Gmail... ") 
    logger.info("--%s, %s, %s, %s, %s, %s, %s, %s, %s" % (channel, title, link, summary, summaryHtml, summaryLinks, image, content , links))
    if True:
        application = channel.service
        #presentation = 'Publicado! ' + title 
        logger.info("Publishing in Gmail: %s" % title)
        logger.info("Publishing in Gmail: %s" % content)
        logger.info("Publishing in Gmail: %s" % links)
        message = application.users().drafts().send(userId='me', body={ 'id': links}).execute()

    else:
        logger.warning("Gmail posting failed!")
        logger.warning("Unexpected error:", sys.exc_info()[0])
        return("Fail!")

def searchTwitter(search, twitter): 
    t = connectTwitter(twitter)
    return(t.search.tweets(q=search)['statuses'])

def nextPost(blog, socialNetwork):
    cacheName = 'Cache_'+socialNetwork[0]+'_'+socialNetwork[1]
    blog.cache[socialNetwork].setPosts()
    listP = blog.cache[socialNetwork].getPosts()

    if listP: 
        element = listP[0]
        listP = listP[1:] 
    elif type(listP) == type(()):
        element = listP
        listP = [] 
    else:
        logger.warning("This shouldn't happen")
        sys.exit()

    return(element,listP)

def publishDelay(blog, socialNetwork, numPosts, timeSlots): 
    # We allow the rest of the Blogs to start
    time.sleep(2)
    nameCache = 'Cache_'+socialNetwork[0]+'_'+socialNetwork[1]
    #serviceName = blog.cache[nameCache].name

    for j in  range(numPosts): 
        tSleep = random.random()*timeSlots
        tSleep2 = timeSlots - tSleep

        element, listP = nextPost(blog,socialNetwork)

        logger.info("    %s: Waiting ... %.2f minutes" % (socialNetwork[0].capitalize(), tSleep/60))
        logger.info("     I'll publish %s" % element[0])
        print("         [d] %s: waiting... %.2f minutes\n          [d] I'll publish %s"
                % (socialNetwork[0], tSleep/60, element[0]))
        time.sleep(tSleep) 

        # Things can have changed during the waiting
        element, listP = nextPost(blog,socialNetwork)

        (title, link, firstLink, image, summary, summaryHtml, summaryLinks, content, links, comment) = element

        profile = socialNetwork[0]
        nick = socialNetwork[1]

        if (profile == 'twitter') or (profile == 'facebook') or (profile == 'mastodon'): 
            # https://stackoverflow.com/questions/41678073/import-class-from-module-dynamically
            import importlib
            mod = importlib.import_module('module'+profile.capitalize()) 
            cls = getattr(mod, 'module'+profile.capitalize())
            api = cls()
            api.setClient(nick)
            result = api.publishPost(title, link, comment)
            if isinstance(result, str):
                if result[:4]=='Fail':
                    link=''
        else: 
            publishMethod = globals()['publish'+ profile.capitalize()]#()(self, ))
            publishMethod(nick, title, link, summary, summaryHtml, summaryLinks, image, content, links)

        blog.cache[socialNetwork].posts = listP
        blog.cache[socialNetwork].updatePostsCache()
           
        if j+1 < numPosts:
            logger.info("Time: %s Waiting ... %.2f minutes to schedule next post in %s" % (time.asctime(), tSleep2/60, socialNetwork[0]))
            time.sleep(tSleep2) 
    logger.info("   Finished in: %s" % socialNetwork[0].capitalize())
    print("====================================")
    print("Finished in: %s at %s" % (socialNetwork[0].capitalize(), 
        time.asctime()))
    print("====================================")

   
def cleanTags(soup):
    tags = [tag.name for tag in soup.find_all()]
    validtags = ['b', 'strong', 'i', 'em', 'a', 'code', 'pre']

    quotes = soup.find_all('blockquote')
    for quote in quotes:
        quote.insert_before('«')
        quote.insert_after( '»')

    for tag in tags:
        if tag not in validtags:
            for theTag in soup.find_all(tag):
                theTag.unwrap()
        elif (tag == 'strong') or (tag == 'b'):
            # We want to avoid problems with links nested inside these tags.
            for theTag in soup.find_all(tag):
                if theTag.find('a'):
                    theTag.unwrap()

    code = [td.find('code') for td in soup.findAll('pre')]
    # github.io inserts code tags inside pre tags
    for cod in code:
        cod.unwrap()

    tags = soup.findAll(text=lambda text:isinstance(text, Doctype))
    if (len(tags)>0):
        tags[0].extract()
    # <!DOCTYPE html> in github.io


if __name__ == "__main__":

    import moduleSocial
    import moduleRss

    blog = moduleRss.moduleRss()
    url = 'http://fernand0.tumblr.com/'
    rssFeed= 'rss'
    blog.setUrl(url)
    blog.setRssFeed(rssFeed)
    blog.addSocialNetwork(('facebook', 'Fernand0Test'))        
    #blog.addSocialNetwork(('telegram', 'Fernand0Test'))        
    blog.addSocialNetwork(('twitter', 'fernand0Test'))        
    blog.setPostsRss()
    blog.getPostsRss()
    lastLink, lastTime = checkLastLink(blog.url,('twitter', 'fernand0Test'))
    i = blog.getLinkPosition(lastLink) 
    (title, link, firstLink, image, summary, summaryHtml, summaryLinks, content, links, comment) = (blog.obtainPostData(i - 1))
    fbPage = blog.getSocialNetworks()['facebook']
    #telegram = blog.getSocialNetworks()['telegram']
    #medium = blog.getSocialNetworks()['medium']
    num = 4
    listPosts= []
    for j in range(num, 0, -1):
        if (i == 0):
            break
        i = i - 1
        listPosts.append(blog.obtainPostData(i - 1))
        timeSlots = 60*60
    if listPosts:
        moduleSocial.publishDelayTwitter(blog, listPosts ,'fernand0Test', timeSlots)

    #twitter = blog.getSocialNetworks()['twitter']
    #moduleSocial.publishTelegram(telegram, title, link, summary, summaryHtml, summaryLinks, image)
    #moduleSocial.publishMedium(medium, title, link, summary, summaryHtml, summaryLinks, image)

    res = publishTwitter("fernand0Test","Hola ahora devuelve la URL, después de un pequeño fallo", "https://github.com/fernand0/scripts/blob/master/moduleSocial.py", "", "", "", "")
    #print("Published! Text: ", res['text'], " Url: https://twitter.com/fernand0Test/status/%s"%res['id_str'])
    #res = publishFacebook("Hola caracola", "https://github.com/fernand0/scripts/blob/master/moduleSocial.py", "", "", "me")
    #print("Published! Text: %s Url: https://facebook.com/fernando.tricas/posts/%s"% (res[0], res[1]['id'][res[1]['id'].find('_')+1:]))
    #publishLinkedin("Hola caracola", "", "", "")



#def connectTumblr():
#    config = configparser.ConfigParser()
#    config.read(CONFIGDIR + '/.rssTumblr')
#
#    consumer_key = config.get("Buffer1", "consumer_key")
#    consumer_secret = config.get("Buffer1", "consumer_secret")
#    oauth_token = config.get("Buffer1", "oauth_token")
#    oauth_secret = config.get("Buffer1", "oauth_secret")
#
#    client = Tumblpy(consumer_key, consumer_secret, 
#                                       oauth_token, oauth_secret)
#
#    #logger.debug(client.info())
#
#    return(client)
#
#def connectBuffer():
#    logger.info("Connecting Buffer")
#
#    try:
#        # instantiate the api object
#        api = moduleBuffer.API()
#        logger.debug(api.info)
#    except:
#        api = None
#        logger.warning("Buffer authentication failed!")
#        logger.warning("Unexpected error: %s"% sys.exc_info()[0])
#
#    return(api)
#
#def connectTwitter(twitterAC):    
#    logger.info("    Connecting Twitter")
#    # In order to obtain the parameters for a new account, just write twitter
#    # and follow the instructions
#    # The result will be at ~/.twitter_oauth
#    config = configparser.ConfigParser()
#    try:
#        config.read(CONFIGDIR + '/.rssTwitter')
#
#        CONSUMER_KEY = config.get("appKeys", "CONSUMER_KEY")
#        CONSUMER_SECRET = config.get("appKeys", "CONSUMER_SECRET")
#        TOKEN_KEY = config.get(twitterAC, "TOKEN_KEY")
#        TOKEN_SECRET = config.get(twitterAC, "TOKEN_SECRET")
#
#        try:
#            authentication = OAuth(
#                        TOKEN_KEY,
#                        TOKEN_SECRET,
#                        CONSUMER_KEY,
#                        CONSUMER_SECRET)
#            t = Twitter(auth=authentication)
#        except:
#            logger.warning("Twitter authentication failed!")
#            logger.warning("Unexpected error:", sys.exc_info()[0])
#    except:
#        logger.warning("Account not configured")
#        t = None
#
#    return(t)
#
#def connectFacebook(fbPage = 'me'):
#    logger.info("    Connecting Facebook")
#    config = configparser.ConfigParser()
#    config.read(CONFIGDIR + '/.rssFacebook')
#
#    try:
#        oauth_access_token = config.get("Facebook", "oauth_access_token")
#        #client_token = config.get("Facebook", "client_token")
#        #app_token = config.get("Facebook", "app_token")
#
#        graph = facebook.GraphAPI(oauth_access_token, version='3.0')
#        perms = ['publish_actions','manage_pages','publish_pages']
#        pages = graph.get_connections("me", "accounts")
#
#        if (fbPage != 'me'):
#            for i in range(len(pages['data'])):
#                logger.debug("%s %s"% (pages['data'][i]['name'], fbPage))
#                if (pages['data'][i]['name'] == fbPage):
#                    logger.info("    Writing in... %s"% pages['data'][i]['name'])
#                    graph2 = facebook.GraphAPI(pages['data'][i]['access_token'])
#                    # Publishing as the page
#                    return(graph2, pages['data'][i]['id'])
#        else:
#            # Publishing as me
#            return(graph, fbPage)
#    except:
#        logger.warning("Facebook authentication failed!")
#        logger.warning("Unexpected error:", sys.exc_info()[0])
#        print("Fail!")
#
#    return(0,0)
#
#def connectLinkedin():
#    logger.info("Connecting Linkedin")
#    config = configparser.ConfigParser()
#    config.read(CONFIGDIR + '/.rssLinkedin')
#
#    CONSUMER_KEY = config.get("Linkedin", "CONSUMER_KEY")
#    CONSUMER_SECRET = config.get("Linkedin", "CONSUMER_SECRET")
#    USER_TOKEN = config.get("Linkedin", "USER_TOKEN")
#    USER_SECRET = config.get("Linkedin", "USER_SECRET")
#    RETURN_URL = config.get("Linkedin", "RETURN_URL"),
#
#    try:
#        authentication = linkedin.LinkedInDeveloperAuthentication(
#                         CONSUMER_KEY,
#                         CONSUMER_SECRET,
#                         USER_TOKEN,
#                         USER_SECRET,
#                         RETURN_URL,
#                         linkedin.PERMISSIONS.enums.values())
#
#        application = linkedin.LinkedInApplication(authentication)
#
#    except:
#        logger.warning("Linkedin authentication failed!")
#        logger.warning("Unexpected error:", sys.exc_info()[0])
#
#    return(application)
#
#def connectTelegram(channel):
#    logger.info("Connecting Telegram")
#    config = configparser.ConfigParser()
#    config.read(CONFIGDIR + '/.rssTelegram')
#
#    TOKEN = config.get("Telegram", "TOKEN")
#
#    try:
#        bot = telepot.Bot(TOKEN)
#        meMySelf = bot.getMe()
#    except:
#        logger.warning("Telegram authentication failed!")
#        logger.warning("Unexpected error:", sys.exc_info()[0])
#
#    return(bot)
#
#def connectMedium():
#    logger.info("Connecting Medium")
#    config = configparser.ConfigParser()
#    config.read(CONFIGDIR + '/.rssMedium')
#    client = Client(application_id=config.get("appKeys","ClientID"), application_secret=config.get("appKeys","ClientSecret"))
#    try:
#        client.access_token = config.get("appKeys","access_token")
#        # Get profile details of the user identified by the access token.
#        user = client.get_current_user()
#    except:
#        logger.warning("Medium authentication failed!")
#        logger.warning("Unexpected error:", sys.exc_info()[0])
#
#    return(client, user)
#
#def connectPocket():
#    logger.info("    Connecting Pocket")
#
#    config = configparser.ConfigParser()
#    try: 
#        config.read(CONFIGDIR + '/.rssPocket')
#
#        consumer_key = config.get("appKeys", "consumer_key")
#        access_token = config.get("appKeys", "access_token")
#
#        try: 
#            p = Pocket(consumer_key=consumer_key, access_token=access_token)
#        except:
#            logger.warning("Pocket authentication failed!")
#            logger.warning("Unexpected error:", sys.exc_info()[0])
#    except:
#        logger.warning("Account not configured")
#        p = None
#
#    return(p)

## Unused ?
#def publishBuffer(blog, profile, title, link, firstLink, isDebug, lenMax, services='fglt'):
#    prof = blog.profiles[profile]
#    linkPublished = ''
#    if isDebug:
#        profileList = []
#        firstLink = None
#    fail = 'no'
#    line = profile
#
#    if (len(title) > 240):
#        titlePostT = title[:240] 
#    else:
#        titlePostT = ""
#    post = title + " " + link # firstLink
#
#    try:
#        if titlePostT and (profile == 'twitter'):
#            entry = urllib.parse.quote(titlePostT + " " + firstLink)#.encode('utf-8')
#        else:
#            entry = urllib.parse.quote(post)#.encode('utf-8')
#
#        if (profile[0] in services): 
#            blog.profiles[profile].updates.new(entry)
#            linkPublished = link
#
#        line = line + ' ok'
#        time.sleep(2)
#    except:
#        logger.warning("Buffer posting failed!")
#        logger.warning("Entry: %s"% entry)
#        logger.warning("Unexpected error: %s"% sys.exc_info()[0])
#        logger.warning("Unexpected error: %s"% sys.exc_info()[1])
#
#        line = line + ' fail'
#        failFile = open(DATADIR + '/'
#                   + urllib.parse.urlparse(link).netloc
#                   + ".fail", "w")
#        failFile.write(post)
#        fail = 'yes'
#        return(linkPublished)
#
#    logger.info("  Profile %s" % line)
#    return(linkPublished)

#def publishTumblr(channel, title, link, summary, summaryHtml, summaryLinks, image, content = "", links = ""):
#
#    comment = summaryHtml
#    logger.info("Publishing in Tumblr...")
#    import importlib
#    serviceName = 'Tumblr'
#    mod = importlib.import_module('module'+serviceName) 
#    cls = getattr(mod, 'module'+serviceName)
#    api = cls()
#    api.setClient(channel)
#    return(api.publishPost(title, link, comment))
#
#def publishTwitter(channel, title, link, summary, summaryHtml, summaryLinks, image, content = "", links = ""):
#
#    twitter = channel
#    comment = ''
#    logger.info("    Publishing in Twitter...")
#    # https://stackoverflow.com/questions/41678073/import-class-from-module-dynamically
#    import importlib
#    serviceName = 'Twitter'
#    mod = importlib.import_module('module'+serviceName) 
#    cls = getattr(mod, 'module'+serviceName)
#    api = cls()
#    api.setClient(twitter)
#    return(api.publishPost(title, link, comment))
#   
#def publishFacebook(channel, title, link, summary, summaryHtml, summaryLinks, image, content = "", links = ""):
#    fbPage = channel
#    logger.info("   Publishing in Facebook...")
#    textToPublish = ""
#    textToPublish2 = ""
#    try:
#        h = HTMLParser()
#        title = h.unescape(title)
#        logger.info("   Publishing in Facebook page %s" % fbPage)
#        (graph, page) = connectFacebook(fbPage)
#        textToPublish = title + " \n" + summaryLinks
#        logger.info("    Publishing in Facebook: %s" % title)
#        logger.debug("Publishing in Facebook: %s" % textToPublish)
#        if (len(textToPublish) > 9980):
#            textToPublish = textToPublish[:9980]
#            index = textToPublish.rfind(' ')
#            if index > 0:
#                textToPublish = (title + " \n" + summaryLinks)[:index] + ' (sigue ...)'
#                textToPublish2 = '... ' + (title + " \n" + summaryLinks)[index + 1:] + ' (... continuación)'
#        if textToPublish2: 
#            graph.put_object(page,
#                  "feed", message = textToPublish,
#                  link=link) 
#           # , picture=image,
#           #       name=title, caption='',
#           #       description=textToPublish.encode('utf-8'))
#            return (page, graph.put_object(page, 
#                "feed", message = textToPublish2, link=link))
#                          #, picture=image,
#                          
#                          #name=title, caption='',
#                          
#                          #description=textToPublish2.encode('utf-8')))
#        else:
#            return (page, graph.put_object(page, 
#                "feed", message = textToPublish, link=link)) #, picture=image,
#                          #name=title, caption='',
#                          #description=summaryLinks.encode('utf-8')))
#    except:
#        logger.warning("Facebook posting failed!")
#        logger.warning("Unexpected error:", sys.exc_info()[0])
#        return("Fail!")
#
#
#def publishLinkedin(channel, title, link, summary, summaryHtml, summaryLinks, image, content = "", links = ""):
#    # publishLinkedin("Prueba", "http://fernand0.blogalia.com/", "bla bla bla", "https://scontent-mad1-1.xx.fbcdn.net/v/t1.0-1/31694_125680874118651_1644400_n.jpg")
#    logger.info("Publishing in Linkedin...")
#    if True:
#        application = connectLinkedin()
#        presentation = 'Publicado! ' + title 
#        logger.info("Publishing in Linkedin: %s" % title)
#        if link:
#            return(application.submit_share(presentation, summary, link, image))
#        else:
#            return(application.submit_share(comment = title))
#    else:
#        logger.warning("Linkedin posting failed!")
#        logger.warning("Unexpected error:", sys.exc_info()[0])
#        return("Fail!")

#def publishTelegram(channel, title, link, summary, summaryHtml, summaryLinks, image, content = "", links = ""):
#    #publishTelegram("reflexioneseirreflexiones","Canal de Reflexiones e Irreflexiones", "http://fernand0.blogalia.com/", "", "", "", "")
#
#    logger.info("Telegram...%s "%channel)
#
#    import importlib
#    serviceName = 'Telegram'
#    mod = importlib.import_module('module'+serviceName) 
#    cls = getattr(mod, 'module'+serviceName)
#    api = cls()
#    api.setClient(channel)
#    #statusTxt = comment + " " + title + " " + link
#    return(api.publishPost(title, link, content + '\n\n' + links))
#
#def publishMedium(channel, title, link, summary, summaryHtml, summaryLinks, image, content= "", links = ""):
#    logger.info("Medium... %s"%channel)
#    import importlib
#    serviceName = 'Medium'
#    mod = importlib.import_module('module'+serviceName) 
#    cls = getattr(mod, 'module'+serviceName)
#    api = cls()
#    api.setClient(channel)
#    return(api.publishPost(title, link, content))
#
#def publishPocket(channel, title, link, summary, summaryHtml, summaryLinks, image, content= "", links = ""):
#    logger.info("    Publishing in Pocket...%s"%channel)
#    try:
#        pc = connectPocket()
#        logger.info("    Publishing in Pocket: %s" % link)
#        return(pc.add(link))
#    except:
#        logger.warning("Pocket posting failed!")
#        logger.warning("Unexpected error:", sys.exc_info()[0])
#        return("Fail!")


