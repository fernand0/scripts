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
    # In order to obtain the parameters for a new account, just write twitter
    # and follow the instructions
    # The result will be at ~/.twitter_oauth
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

def connectFacebook(fbPage = 'me'):
    config = configparser.ConfigParser()
    config.read([os.path.expanduser('~/.rssFacebook')])

    try:
        oauth_access_token = config.get("Facebook", "oauth_access_token")

        graph = facebook.GraphAPI(oauth_access_token, version='2.7')
        perms = ['manage_pages','publish_pages']
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


def checkLimitPosts(api,services='tfgl'):
    # We can put as many items as the service with most items allow
    # The limit is ten.
    # Get all pending updates of a social network profile

    lenMax = 0
    logging.info("Checking services...")

    profileList = Profiles(api=api).all()
    for profile in profileList:
        if (profile['service'][0] in services): 
            lenProfile = len(profile.updates.pending) 
            if (lenProfile > lenMax): 
                lenMax = lenProfile 
                logging.info("%s ok" % profile['service'])

    logging.info("There are %d in some buffer, we can put %d" %
                 (lenMax, 10-lenMax))

    return(lenMax, profileList)

def publishBuffer(blog, profile, title, link, firstLink, isDebug, lenMax, services='fglt'):
    print("Publishing in Buffer:\n")
    if isDebug:
        profileList = []
        firstLink = None
    fail = 'no'
    line = profile['service']
    print("  %s" % profile['service'])

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
            print("Buffer posting failed!")
            print("Entry: ", entry)
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

    logging.info("  %s service" % line)
    if (fail == 'no' and link):
        blog.updateLastLink(link, 
            (profile['service'], profile['service_username']))
        urlFile = open(os.path.expanduser("~/."
                       + urllib.parse.urlparse(link).netloc
                       + ".last"), "w")
    
        urlFile.write(link)
        urlFile.close()
    print("")

def searchTwitter(search, twitter): 
    t = connectTwitter(twitter)
    return(t.search.tweets(q=search)['statuses'])

def publishDelayTwitter(blog, listPosts, twitter, timeSlots): 
    socialNetwork= ('twitter', twitter)
    listP = blog.listPostsCache(socialNetwork)
    listP = listP + listPosts
    blog.updatePostsCache(listP, socialNetwork)

    numPosts = round((4*60*60)/timeSlots)
    for j in  range(numPosts): 
        tSleep = random.random()*timeSlots
        tSleep2 = timeSlots - tSleep
        listP = blog.listPostsCache(socialNetwork)
        if listP: 
            print("Time: %s Waiting ... %s minutes in Twitter to publish %s" % (time.asctime(), str(tSleep/60), listP[0][0])) 
            time.sleep(tSleep) 
        #print("I'd publish ... %s" % str(listPosts[j]))         
            try:
                (title, link, firstLink, image, summary, summaryHtml, summaryLinks, content, links, comment) = listP[0]
            except:
                # backwards compatibility
                (title, link, firstLink, image, summary, summaryHtml, summaryLinks, comment) = listP[0]
            publishTwitter(twitter, title, firstLink, summary, summaryHtml, summaryLinks, image)
            listP = listP[1:] 

            blog.updatePostsCache(listP, socialNetwork)
               
            print("Time: %s Waiting ... %s minutes in Twitter for scheduling the next post" % (time.asctime(), str(tSleep2/60)))
            time.sleep(tSleep2) 

def publishTwitter(channel, title, link, summary, summaryHtml, summaryLinks, image, content = "", links = ""):

    twitter = channel
    comment = ''
    print("Twitter...\n")
    try:
        t = connectTwitter(twitter)
        statusTxt = comment + " " + title + " " + link
        h = HTMLParser()
        statusTxt = h.unescape(statusTxt)
        return(t.statuses.update(status=statusTxt))
    except:
        print("Twitter posting failed!\n")
        print("Unexpected error:", sys.exc_info()[0])
        return("Fail! %s" % sys.exc_info()[0])


def publishDelayFacebook(blog, listPosts, fbPage, timeSlots): 
    socialNetwork=('facebook',fbPage)
    listP = blog.listPostsCache(socialNetwork)
    listP = listP + listPosts
    blog.updatePostsCache(listP, socialNetwork)

    numPosts = round((4*60*60)/timeSlots)
    for j in range(numPosts): 
        tSleep = random.random()*timeSlots
        tSleep2 = timeSlots - tSleep

        #print("I'd publish ... %s" % str(listPosts[j])) 
        listP = blog.listPostsCache(socialNetwork)
        if listPosts: 
            print("Time: %s Waiting ... %s minutes in Facebook to publish %s" % (time.asctime(), str(tSleep/60), listP[0][0])) 
            time.sleep(tSleep)             
            try: 
                (title, link, firstLink, image, summary, summaryHtml, summaryLinks, content, links, comment) = listP[0] 
            except:
                #backwards compatibility
                (title, link, firstLink, image, summary, summaryHtml, summaryLinks, comment) = listP[0] 
            publishFacebook(fbPage, title, firstLink, summary='', summaryHtml='', summaryLinks='', image='') 
            listP = listP[1:] 
            
            blog.updatePostsCache(listP, socialNetwork)

            print("Time: %s Waiting ... %s minutes to schedule next post in Facebook" % (time.asctime(), str(tSleep2/60))) 
            time.sleep(tSleep2) 
   
def publishFacebook(channel, title, link, summary, summaryHtml, summaryLinks, image, content = "", links = ""):
    fbPage = channel
    print("Facebook...\n")
    textToPublish = ""
    textToPublish2 = ""
    if True:
        h = HTMLParser()
        title = h.unescape(title)
        (graph, page) = connectFacebook(fbPage)
        textToPublish = title + " \n" + summaryLinks
        print(textToPublish)
        if (len(textToPublish) > 9980):
            textToPublish = textToPublish[:9980]
            index = textToPublish.rfind(' ')
            if index > 0:
                textToPublish = (title + " \n" + summaryLinks)[:index] + ' (sigue ...)'
                textToPublish2 = '... ' + (title + " \n" + summaryLinks)[index + 1:] + ' (... continuación)'
        if textToPublish2: 
            graph.put_object(page,
                  "feed", message = textToPublish,
                  link=link, picture=image,
                  name=title, caption='',
                  description=textToPublish.encode('utf-8'))
            return (page, graph.put_object(page,
                          "feed", message = textToPublish2,
                          link=link, picture=image,
                          name=title, caption='',
                          description=textToPublish2.encode('utf-8')))
        else:
            return (page, graph.put_object(page,
                          "feed", message = textToPublish,
                          link=link, picture=image,
                          name=title, caption='',
                          description=summaryLinks.encode('utf-8')))
    else:
        print("Facebook posting failed!\n")
        print("Unexpected error:", sys.exc_info()[0])
        return("Fail!")


def publishLinkedin(channel, title, link, summary, summaryHtml, summaryLinks, image, content = "", links = ""):
    # publishLinkedin("Prueba", "http://fernand0.blogalia.com/", "bla bla bla", "https://scontent-mad1-1.xx.fbcdn.net/v/t1.0-1/31694_125680874118651_1644400_n.jpg")
    print("Linkedin...\n")
    try:
        application = connectLinkedin()
        presentation = 'Publicado! ' + title 
        if link:
            return(application.submit_share(presentation, summary, link, image))
        else:
            return(application.submit_share(comment = title))
    except:
        print("Linkedin posting failed!\n")
        print("Unexpected error:", sys.exc_info()[0])
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

    print("Telegram...%s\n"%channel)

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
        print("text to ", textToPublish)
        print("text to 2", textToPublish2)

        bot.sendMessage('@'+channel, textToPublish, parse_mode='HTML') 
        if textToPublish2:
            try:
                bot.sendMessage('@'+channel, textToPublish2[:4090], parse_mode='HTML') 
            except:
                bot.sendMessage('@'+channel, "Text is longer", parse_mode='HTML') 
        if links:
            bot.sendMessage('@'+channel, links, parse_mode='HTML') 

    else:
        print("Telegram posting failed!\n")
        print("Unexpected error:", sys.exc_info()[0])

def publishMedium(channel, title, link, summary, summaryHtml, summaryLinks, image, content= "", links = ""):
    print("Medium...\n")
    try:
        (client, user) = connectMedium()

        h = HTMLParser()
        title = h.unescape(title)
        textOrig = '\n\nPublicado originalmente en <a href="%s">%s</a>' % (link, title)
        post = client.create_post(user_id=user["id"], title=title,
                content="<h4>"+title+"</h4><br />"+summaryHtml+textOrig, canonical_url = link,
                content_format="html", publish_status="public") #draft")
        print("My new post!", post["url"])
    except:
        print("Medium posting failed!\n")
        print("Unexpected error:", sys.exc_info()[0])


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
