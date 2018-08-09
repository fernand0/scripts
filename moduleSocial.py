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
from buffpy.api import API
from buffpy.managers.profiles import Profiles
from buffpy.managers.updates import Update
from medium import Client
import moduleCache
# https://github.com/fernand0/scripts/blob/master/moduleCache.py

logger = logging.getLogger(__name__)

def connectTumblr():
    config = configparser.ConfigParser()
    config.read([os.path.expanduser('~/.rssTumblr')])

    consumer_key = config.get("Buffer1", "consumer_key")
    consumer_secret = config.get("Buffer1", "consumer_secret")
    oauth_token = config.get("Buffer1", "oauth_token")
    oauth_secret = config.get("Buffer1", "oauth_secret")

    client = Tumblpy(consumer_key, consumer_secret, 
                                       oauth_token, oauth_secret)

    #logger.debug(client.info())

    return(client)

def connectBuffer():
    logger.info("Connecting Buffer")
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

        logger.debug(api.info)
    except:
        logger.warning("Buffer authentication failed!\n")
        logger.warning("Unexpected error:", sys.exc_info()[0])

    return(api)

def connectTwitter(twitterAC):    
    logger.info("Connecting Twitter")
    # In order to obtain the parameters for a new account, just write twitter
    # and follow the instructions
    # The result will be at ~/.twitter_oauth
    config = configparser.ConfigParser()
    try:
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
            logger.warning("Twitter authentication failed!\n")
            logger.warning("Unexpected error:", sys.exc_info()[0])
    except:
        logger.warning("Account not configured")
        t = None

    return(t)

def connectFacebook(fbPage = 'me'):
    logger.info("Connecting Facebook")
    config = configparser.ConfigParser()
    config.read([os.path.expanduser('~/.rssFacebook')])

    try:
        oauth_access_token = config.get("Facebook", "oauth_access_token")
        #client_token = config.get("Facebook", "client_token")
        #app_token = config.get("Facebook", "app_token")

        graph = facebook.GraphAPI(oauth_access_token, version='3.0')
        perms = ['publish_actions','manage_pages','publish_pages']
        pages = graph.get_connections("me", "accounts")

        if (fbPage != 'me'):
            for i in range(len(pages['data'])):
                if (pages['data'][i]['name'] == fbPage):
                    print("\tWriting in... ", pages['data'][i]['name'], "\n")
                    graph2 = facebook.GraphAPI(pages['data'][i]['access_token'])
                    # Publishing as the page
                    return(graph2, pages['data'][i]['id'])
        else:
            # Publishing as me
            return(graph, fbPage)
    except:
        logger.warning("Facebook authentication failed!\n")
        logger.warning("Unexpected error:", sys.exc_info()[0])

    return(0,0)

def connectLinkedin():
    logger.info("Connecting Linkedin")
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
        logger.warning("Linkedin authentication failed!\n")
        logger.warning("Unexpected error:", sys.exc_info()[0])

    return(application)

def connectTelegram(channel):
    logger.info("Connecting Telegram")
    config = configparser.ConfigParser()
    config.read([os.path.expanduser('~/.rssTelegram')])

    TOKEN = config.get("Telegram", "TOKEN")

    try:
        bot = telepot.Bot(TOKEN)
        meMySelf = bot.getMe()
    except:
        logger.warning("Telegram authentication failed!\n")
        logger.warning("Unexpected error:", sys.exc_info()[0])

    return(bot)

def connectMedium():
    logger.info("Connecting Medium")
    config = configparser.ConfigParser()
    config.read([os.path.expanduser('~/.rssMedium')])
    client = Client(application_id=config.get("appKeys","ClientID"), application_secret=config.get("appKeys","ClientSecret"))
    try:
        client.access_token = config.get("appKeys","access_token")
        # Get profile details of the user identified by the access token.
        user = client.get_current_user()
    except:
        logger.warning("Medium authentication failed!\n")
        logger.warning("Unexpected error:", sys.exc_info()[0])

    return(client, user)


def checkLimitPosts(api, blog):
    # We can put as many items as the service with most items allow
    # The limit is ten.
    # Get all pending updates of a social network profile

    lenMax = 0
    logger.info("Checking services...")
    if api:
        profileList = Profiles(api=api).all()
        for profile in profileList:
            if (profile['service'][0] in blog.getBufferapp()): 
                lenProfile = len(profile.updates.pending) 
                if (lenProfile > lenMax): 
                    lenMax = lenProfile 
                    logger.info("%s ok" % profile['service'])
    elif blog:
        print(blog.getSocialNetworks())
        profileList = blog.getSocialNetworks().keys()
        for profile in blog.getSocialNetworks():
            print("profile", profile)
            if (profile[0] in blog.getProgram()): 
                listP = moduleCache.getPostsCache(blog,
                        (profile, blog.getSocialNetworks()[profile])) 
                lenProfile = len(listP) 
                if (lenProfile > lenMax): 
                    lenMax = lenProfile 
                    logger.info("%s ok" % profile)

    logger.info("There are %d in some buffer, we can put %d" % (lenMax, 10-lenMax))
    print("There are %d in some buffer, we can put %d" % (lenMax, 10-lenMax))
    sys.exit()

    return(lenMax, profileList)

def publishBuffer(blog, profile, title, link, firstLink, isDebug, lenMax, services='fglt'):
    logger.info("Publishing in Buffer:\n")
    if isDebug:
        profileList = []
        firstLink = None
    fail = 'no'
    line = profile['service']
    logger.info("  %s" % profile['service'])

    if (len(title) > 240):
        titlePostT = title[:240] 
    else:
        titlePostT = ""
    post = title + " " + firstLink

    if (profile['service'] == 'twitter') or (profile['service'] == 'facebook'):
        # We should add a configuration option in order to check which
        # services are the ones with immediate posting. For now, we
        # know that we are using Twitter and Facebook
        # We are checking the links tha have been published with other
        # toolsin order to avoid duplicates
        
        path = os.path.expanduser('~')
        with open(path + '/.urls.pickle', 'rb') as f:
            theList = pickle.load(f)
    else:
        theList = []

    if not (firstLink[firstLink.find(':')+2:] in theList):
        # Without the http or https 
        try:
            if titlePostT and (profile['service'] == 'twitter'):
                entry = urllib.parse.quote(titlePostT + " " + firstLink).encode('utf-8')
            else:
                entry = urllib.parse.quote(post).encode('utf-8')

            if (profile['service'][0] in services): 
                profile.updates.new(entry)

            line = line + ' ok'
            time.sleep(2)
        except:
            logger.warning("Buffer posting failed!")
            logger.warning("Entry: ", entry)
            logger.warning("Unexpected error: %s"% sys.exc_info()[0])
            logger.warning("Unexpected error: %s"% sys.exc_info()[1])

            line = line + ' fail'
            failFile = open(os.path.expanduser("~/."
                       + urllib.parse.urlparse(link).netloc
                       + ".fail"), "w")
            failFile.write(post)
            logger.info("  %s service" % line)
            fail = 'yes'

    logger.info("  %s service" % line)
    if (fail == 'no' and link):
        blog.updateLastLink(link, 
            (profile['service'], profile['service_username']))
        fileName = os.path.expanduser("~/."
                       + urllib.parse.urlparse(link).netloc
                       + ".last")
        with open(fileName, "w") as f: 
            f.write(link)

def searchTwitter(search, twitter): 
    t = connectTwitter(twitter)
    return(t.search.tweets(q=search)['statuses'])

def publishDelay(blog, listPosts, socialNetwork, timeSlots): 

    listP = blog.listPostsCache(socialNetwork)
    listP = listP + listPosts
    blog.updatePostsCache(listP, socialNetwork)

    numPosts = round((4*60*60)/timeSlots)

    for j in  range(numPosts): 
        tSleep = random.random()*timeSlots
        tSleep2 = timeSlots - tSleep

        listP = blog.listPostsCache(socialNetwork)

        if listP: 
            element = listP[0]
            listP = listP[1:] 
        elif type(listP) == type(()):
            element = listP
            listP = [] 
        else:
            logger.warning("This shouldn't happen")
            sys.exit()

        logger.info("Time: %s Waiting ... %.2f minutes in %s to publish:\n%s" % (time.asctime(), tSleep/60, socialNetwork[0], element[0]))

        time.sleep(tSleep) 

        (title, link, firstLink, image, summary, summaryHtml, summaryLinks, content, links, comment) = element
        publishMethod = globals()['publish'+ socialNetwork[0].capitalize()]#()(self, ))
        nick = socialNetwork[1]
        publishMethod(nick, title, link, summary, summaryHtml, summaryLinks, image, content, links)

        blog.updatePostsCache(listP, socialNetwork)
           
        logger.info("Time: %s Waiting ... %.2f minutes to schedule next post in %s" % (time.asctime(), tSleep2/60, socialNetwork[0]))
        time.sleep(tSleep2) 
    logger.info("Finished in: %s" % socialNetwork[0])

   
#def publishDelayTwitter(blog, listPosts, twitter, timeSlots): 
#    socialNetwork= ('twitter', twitter)
#    listP = blog.listPostsCache(socialNetwork)
#    listP = listP + listPosts
#    blog.updatePostsCache(listP, socialNetwork)
#
#    numPosts = round((4*60*60)/timeSlots)
#
#    print(socialNetwork, blog.getUrl(), listP)
#    for j in  range(numPosts): 
#        tSleep = random.random()*timeSlots
#        tSleep2 = timeSlots - tSleep
#
#        listP = blog.listPostsCache(socialNetwork)
#
#        if listP: 
#            #print("list")
#            element = listP[0]
#            listP = listP[1:] 
#        elif type(listP) == type(()):
#            #print("tuple")
#            element = listP
#            listP = [] 
#        else:
#            logger.warning("This shouldn't happen")
#            sys.exit()
#
#        logger.info("Time: %s Waiting ... %.2f minutes in %s to publish:\n%s" % (time.asctime(), tSleep/60, socialNetwork[0], element[0]))
#
#        time.sleep(tSleep) 
#
#        (title, link, firstLink, image, summary, summaryHtml, summaryLinks, content, links, comment) = element
#        publishMethod = getattr(moduleSocial, 'publish'+ socialNetwork.capitalize())
#        nick = socialNetwork[1]
#        print(nick, publishMethod)
#        print(nick, title, link, summary, summaryHtml, summaryLinks, image, content, links)
#        sys.exit()
#        publishMethod(nick, title, link, summary, summaryHtml, summaryLinks, image, content, links)
#
#        blog.updatePostsCache(listP, socialNetwork)
#           
#        logger.info("Time: %s Waiting ... %.2f minutes to schedule next post in %s" % (time.asctime(), tSleep2/60, socialNetwork[0]))
#        time.sleep(tSleep2) 

def publishTumblr(channel, title, link, summary, summaryHtml, summaryLinks, image, content = "", links = ""):

    logger.info("Publishing in Tumblr...")
    client = connectTumblr()                    
    
    blog_url = client.post('user/info')['user']['blogs'][0]['url']
    post = client.post('post', blog_url, 
            params={'type':'link', 
                'state':'queue', 
                'title': title, 
                'thumbnail': image, 
                'url': link, 
                'excerpt': summaryHtml, 
                'publisher': ''}) 

    logger.info("Posted!: %s" % post)

    return(post)

def publishTwitter(channel, title, link, summary, summaryHtml, summaryLinks, image, content = "", links = ""):

    twitter = channel
    comment = ''
    logger.info("Publishing in Twitter...")
    try: 
        t = connectTwitter(twitter)
        if t:
            statusTxt = comment + " " + title + " " + link
            h = HTMLParser()
            statusTxt = h.unescape(statusTxt)
            logger.info("Publishing in Twitter:\n%s" % statusTxt)
            return(t.statuses.update(status=statusTxt))
        else:
            logger.warning("You must configure API access for %s" % twitter)
            return("You must configure API access for %s" % twitter)
    except:
        logger.warning("Twitter posting failed!\n")
        logger.warning("Unexpected error:", sys.exc_info()[0])
        return("Fail! %s" % sys.exc_info()[0])

#def publishDelayFacebook(blog, listPosts, fbPage, timeSlots): 
#    socialNetwork=('facebook',fbPage)
#    listP = blog.listPostsCache(socialNetwork)
#    listP = listP + listPosts
#    blog.updatePostsCache(listP, socialNetwork)
#
#    numPosts = round((4*60*60)/timeSlots)
#
#    for j in range(numPosts): 
#        tSleep = random.random()*timeSlots
#        tSleep2 = timeSlots - tSleep
#
#        listP = blog.listPostsCache(socialNetwork)
#
#        if listP: 
#            #print("list")
#            element = listP[0]
#            listP = listP[1:] 
#        elif type(listP) == type(()):
#            #print("tuple")
#            element = listP
#            listP = [] 
#        else:
#            logger.critical("This shouldn't happen")
#            sys.exit()
#
#        logger.info("Time: %s Waiting ... %.2f minutes in %s to publish:\n%s" % (time.asctime(), tSleep/60, socialNetwork[0], element[0])) 
#
#        time.sleep(tSleep)             
#
#        (title, link, firstLink, image, summary, summaryHtml, summaryLinks, content, links, comment) = element 
#        publishFacebook(fbPage, title, firstLink, summary='', summaryHtml='', summaryLinks='', image='') 
#         
#        blog.updatePostsCache(listP, socialNetwork)
#
#        logger.info("Time: %s Waiting ... %.2f minutes to schedule next post in %s" % (time.asctime(), tSleep2/60, socialNetwork[0])) 
#        time.sleep(tSleep2) 
   
def publishFacebook(channel, title, link, summary, summaryHtml, summaryLinks, image, content = "", links = ""):
    fbPage = channel
    logger.info("Publishing in Facebook...")
    textToPublish = ""
    textToPublish2 = ""
    try:
        h = HTMLParser()
        title = h.unescape(title)
        (graph, page) = connectFacebook(fbPage)
        textToPublish = title + " \n" + summaryLinks
        logger.info("Publishing in Facebook:\n%s" % textToPublish)
        if (len(textToPublish) > 9980):
            textToPublish = textToPublish[:9980]
            index = textToPublish.rfind(' ')
            if index > 0:
                textToPublish = (title + " \n" + summaryLinks)[:index] + ' (sigue ...)'
                textToPublish2 = '... ' + (title + " \n" + summaryLinks)[index + 1:] + ' (... continuación)'
        if textToPublish2: 
            graph.put_object(page,
                  "feed", message = textToPublish,
                  link=link) 
           # , picture=image,
           #       name=title, caption='',
           #       description=textToPublish.encode('utf-8'))
            return (page, graph.put_object(page, 
                "feed", message = textToPublish2, link=link))
                          #, picture=image,
                          
                          #name=title, caption='',
                          
                          #description=textToPublish2.encode('utf-8')))
        else:
            return (page, graph.put_object(page, 
                "feed", message = textToPublish, link=link)) #, picture=image,
                          #name=title, caption='',
                          #description=summaryLinks.encode('utf-8')))
    except:
        logger.warning("Facebook posting failed!\n")
        logger.warning("Unexpected error:", sys.exc_info()[0])
        return("Fail!")


def publishLinkedin(channel, title, link, summary, summaryHtml, summaryLinks, image, content = "", links = ""):
    # publishLinkedin("Prueba", "http://fernand0.blogalia.com/", "bla bla bla", "https://scontent-mad1-1.xx.fbcdn.net/v/t1.0-1/31694_125680874118651_1644400_n.jpg")
    logger.info("Publishing in Linkedin...\n")
    if True:
        application = connectLinkedin()
        presentation = 'Publicado! ' + title 
        logger.info("Publishing in Linkedin:\n%s" % title)
        if link:
            return(application.submit_share(presentation, summary, link, image))
        else:
            return(application.submit_share(comment = title))
    else:
        logger.warning("Linkedin posting failed!\n")
        logger.warning("Unexpected error:", sys.exc_info()[0])
        return("Fail!")

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

def publishTelegram(channel, title, link, summary, summaryHtml, summaryLinks, image, content = "", links = ""):
    #publishTelegram("reflexioneseirreflexiones","Canal de Reflexiones e Irreflexiones", "http://fernand0.blogalia.com/", "", "", "", "")

    logger.info("Telegram...%s\n"%channel)

    if True:
        bot = connectTelegram(channel)

        h = HTMLParser()
        title = h.unescape(title)
        htmlText='<a href="'+link+'">'+title + "</a>\n" + summaryHtml
        #soup = BeautifulSoup(htmlText)
        #cleanTags(soup)
        #print(soup)
        text = '<a href="'+link+'">'+title+ "</a>\n" + content + '\n\n' + links
        textToPublish2 = ""
        if len(text) < 4090:
            textToPublish = text
            links = ""
        else:
            text = '<a href="'+link+'">'+title + "</a>\n" + content
            textToPublish = text[:4080] + ' ...'
            textToPublish2 = '... '+ text[4081:]
        logger.info("text to ", textToPublish)
        logger.info("text to 2", textToPublish2)

        bot.sendMessage('@'+channel, textToPublish, parse_mode='HTML') 
        if textToPublish2:
            try:
                bot.sendMessage('@'+channel, textToPublish2[:4090], parse_mode='HTML') 
            except:
                bot.sendMessage('@'+channel, "Text is longer", parse_mode='HTML') 
        if links:
            bot.sendMessage('@'+channel, links, parse_mode='HTML') 

    else:
        logger.warning("Telegram posting failed!\n")
        logger.warning("Unexpected error:", sys.exc_info()[0])
        return("Fail!")

def publishMedium(channel, title, link, summary, summaryHtml, summaryLinks, image, content= "", links = ""):
    logger.info("Medium...%s\n"%channel)
    try:
        (client, user) = connectMedium()

        h = HTMLParser()
        title = h.unescape(title)
        textOrig = '\n\nPublicado originalmente en <a href="%s">%s</a>' % (link, title)
        post = client.create_post(user_id=user["id"], title=title,
                content="<h4>"+title+"</h4><br />"+summaryHtml+textOrig, canonical_url = link,
                content_format="html", publish_status="public") #draft")
        logger.info("My new post!", post["url"])
    except:
        logger.warning("Medium posting failed!\n")
        logger.warning("Unexpected error:", sys.exc_info()[0])
        return("Fail!")


if __name__ == "__main__":

    import moduleSocial
    import moduleBlog

    blog = moduleBlog.moduleBlog()
    url = 'http://fernand0.tumblr.com/'
    rssFeed= 'rss'
    blog.setUrl(url)
    blog.setRssFeed(rssFeed)
    blog.addSocialNetwork(('facebook', 'Fernand0Test'))        
    #blog.addSocialNetwork(('telegram', 'Fernand0Test'))        
    blog.addSocialNetwork(('twitter', 'fernand0Test'))        
    blog.setPostsRss()
    blog.getPostsRss()
    lastLink, lastTime = blog.checkLastLink(('twitter', 'fernand0Test'))
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
