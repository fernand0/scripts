#!/usr/bin/env python

import configparser
import pickle
import os
import moduleSocial
import moduleBuffer
import moduleCache
import urllib
import logging
from slackclient import SlackClient
import sys
import click
import requests
from bs4 import BeautifulSoup
from bs4 import Tag

from configMod import *

class moduleSlack():

    def __init__(self):
         self.url = ""
         self.name = ""
         self.sc = None
         self.socialNetworks = {}
         self.linksToAvoid = ""
         self.posts = None
         self.postsCache = None
         self.time = []
         self.bufferapp = None
         self.program = None
         self.buffer = None
         self.cache = None
         self.lastLinkPublished = {}
         self.keys = []
         #self.logger = logging.getLogger(__name__)

    def getUrl(self):
        return(self.url)

    def setUrl(self, url):
        self.url = url

    def getName(self):
        return(self.name)

    def setName(self, name):
        self.name = name

    def getSocialNetworks(self):
        return(self.socialNetworks)

    def setSocialNetworks(self, config, section):
        socialNetworksOpt = ['twitter', 'facebook', 'telegram', 
                'medium', 'linkedin','pocket'] 
        for option in config.options(section):
            if (option in socialNetworksOpt):
                nick = config.get(section, option)
                socialNetwork = (option, nick)
                self.addSocialNetwork(socialNetwork)
 
    def addSocialNetwork(self, socialNetwork):
        self.socialNetworks[socialNetwork[0]] = socialNetwork[1]

    def setSlackClient(self, slackCredentials):
        config = configparser.ConfigParser()
        config.read(slackCredentials)
    
        slack_token = config["Slack"].get('api-key')
        
        self.sc = SlackClient(slack_token)
 
    def getSlackClient(self):
        return self.sc
 
    def addLastLinkPublished(self, socialNetwork, lastLink, lastTime):
        self.lastLinkPublished[socialNetwork] = (lastLink, lastTime)

    def getLastLinkPublished(self):
        return(self.lastLinkPublished)
 
    def getLinksToAvoid(self):
        return(self.linksToAvoid)
 
    def setLinksToAvoid(self,linksToAvoid):
        self.linksToAvoid = linksToAvoid
 
    def getTime(self):
        return(self.time)
 
    def setTime(self, time):
        self.time = time

    def getBufferapp(self):
        return(self.bufferapp)
 
    def setBufferapp(self, bufferapp):
        self.bufferapp = bufferapp
        self.setBuffer()

    def getProgram(self):
        return(self.program)
 
    def setProgram(self, program):
        self.program = program
        self.setCache()

    def setPostsSlack(self, channel='links'):
        if self.posts is None:
            self.posts = []
            theChannel = self.getChanId(channel)
            history = self.sc.api_call( "channels.history", count=1000, channel=theChannel)
            logging.debug(history)
            for msg in history['messages']:
                self.posts.append(msg)

    def getPostsSlack(self):
        logging.debug("# posts", len(self.posts))
        logging.debug(self.posts)
        return(self.posts)

    def getBuffer(self):
        return(self.buffer)

    def setBuffer(self):
        self.buffer = moduleBuffer.moduleBuffer() 

    def getCache(self):
        return(self.cache)

    def setCache(self):
        self.cache = []
        for sN in self.getSocialNetworks():
            cacheAcc = moduleCache.moduleCache(self.getUrl(), 
                    sN, self.getSocialNetworks()[sN]) 
            self.cache.append(cacheAcc)

    def getPostsCache(self):
        return(self.cache.posts)

    def setPostsCache(self):
        self.setCache() 
        for ca in self.getCache():
            postsP, profiles = ca.listPosts()
            print(postsP)
            sys.exit()
            self.cache.posts = postsP

    def getKeys(self):
        return(self.keys)
    
    def setKeys(self, keys):
        self.keys = keys

    #def checkLimitPosts(self, myServices, service=''):
    #    profileList = self.getSocialNetworks().keys()
    #    if service: 
    #        self.setPostsCache() 
    #        listP = self.getPostsCache() 
    #        lenProfile = len(listP) 
    #        #print(lenProfile)
    #        lenMax = lenProfile
    #        listProfiles = []
    #    else:
    #        for profile in self.getSocialNetworks():
    #            print("-->",profile, myServices)
    #            if (profile[0] in myServices): 
    #                print("Profile %s" %profile)
    #                print("Profile program %s" % myServices)
    #                listP = self.getPostsCache((profile, 
    #                    self.getSocialNetworks()[profile])) 
    #                print(listP)
    #                lenProfile = len(listP) 
    #                if (lenProfile > lenMax): 
    #                    lenMax = lenProfile 
    #                    logger.info("%s ok" % profile)

    #    logging.info("There are %d in some buffer, we can put %d" % (lenMax, 10-lenMax))

    #    return(lenMax, profileList)


    def getLinkPosition(self, link):
        i = 0
        if self.getPostsSlack():
            if not link:
                logging.debug(self.getPostsSlack())
                return(len(self.getPostsSlack()))
            for entry in self.getPostsSlack():
                linkS = link.decode()
                if 'original_url' in entry: 
                    url = entry['original_url']
                else:
                    url = entry['text'][1:-1]
                #print(url, link)
                lenCmp = min(len(url), len(linkS))
                if url[:lenCmp] == linkS[:lenCmp]:
                    return i
                i = i + 1
        return(i)

    def deletePost(self, idPost, theChannel): 
        logging.info("Deleting id %s" % idPost)
        # Needs improvement
            
        result = self.sc.api_call("chat.delete", channel=theChannel, ts=idPost)
    
        logging.info(result)
        return(result)
    
    def listPosts(api, service=""):
        outputData = {}
    
        serviceName = 'Slack'
        outputData[serviceName] = {'sent': [], 'pending': []}
        posts = api.getPostsSlack()
        for post in posts:
            if 'attachments' in post:
                outputData[serviceName]['pending'].append(
                    (post['text'][1:-1], post['attachments'][0]['title'], '', '', '', '', '', '', post['ts'], ''))
            else:
                #print(post)
                outputData[serviceName]['pending'].append(
                    (post['text'][1:-1], '', '', '', '', '', '', '', post['ts'], ''))
        return(outputData, posts)

    def getChanId(self, name):
        chanList = self.sc.api_call("channels.list")['channels']
        for channel in chanList:
            if channel['name_normalized'] == name:
                return(channel['id'])
        return(None)

    def obtainPostData(self, i, debug=False):
        if not self.posts:
            self.setPostsSlack()

        posts = self.getPostsSlack()
        if not posts:
            return (None, None, None, None, None, None, None, None, None, None)

        post = posts[i]
        if 'attachments' in post:
            post = post['attachments'][0]

        theContent = ''
        url = ''
        firstLink = ''
        logging.debug("i %d", i)
        logging.debug("post %s", post)

        if 'title' in post:
            theTitle = post['title']
            theLink = post['title_link']
            if theLink.find('tumblr')>0:
                theTitle = post['text']
            firstLink = theLink
            if 'text' in post: 
                content = post['text']
            else:
                content = theLink
            theSummary = content
            theSummaryLinks = content
            if 'image_url' in post:
                theImage = post['image_url']
            elif 'thumb_url' in post:
                theImage = post['thumb_url']
            else:
                logging.info("Fail image")
                logging.info("Fail image %s", post)
                theImage = ''
        elif 'text' in post:
            if post['text'].startswith('<h'):
                # It's an url
                url = post['text'][1:-1]
                req = requests.get(url)
                    
                if req.text.find('403 Forbidden')>=0:
                    theTitle = url
                    theSummary = url
                    content = url
                    theDescription = url
                else:
                    if url.lower().endswith('pdf'):
                        nameFile = '/tmp/kkkkk.pdf'
                        with open(nameFile,'wb') as f:
                            f.write(req.content)
                        theTitle = PdfReader(nameFile).Info.Title
                        if theTitle:
                            theTitle = theTitle[1:-1]
                        else:
                            theTitle = url
                        theUrl = url
                        theSummary = ''
                        content = theSummary
                        theDescription = theSummary
                    else:
                        soup = BeautifulSoup(req.text, 'lxml')
                        #print("soup", soup)
                        theTitle = soup.title
                        if theTitle:
                            theTitle = str(theTitle.string)
                        else:
                            # The last part of the path, without the dot part, and
                            # capitized
                            urlP = urllib.parse.urlparse(url)
                            theTitle = os.path.basename(urlP.path).split('.')[0].capitalize()
                        theSummary = str(soup.body)
                        content = theSummary
                        theDescription = theSummary
            else:
                theSummary = post['text']
                content = post['text']
                theDescription = post['text']
                theTitle = post['text']
        else:
            theSummary = post['title']
            content = post['title']
            theDescription = post['title']

        if 'original_url' in post: 
            theLink = post['original_url']
        elif url: 
            theLink = url
        else:
            theLink = post['text']

        if ('comment' in post):
            comment = post['comment']
        else:
            comment = ""

        #print("content", content)
        theSummaryLinks = ""

        soup = BeautifulSoup(content, 'lxml')
        if not content.startswith('http'):
            link = soup.a
            if link: 
                firstLink = link.get('href')
                if firstLink:
                    if firstLink[0] != 'h': 
                        firstLink = theLink

        if not firstLink: 
            firstLink = theLink

        if 'image_url' in post:
            theImage = post['image_url']
        else:
            theImage = None
        theLinks = theSummaryLinks
        theSummaryLinks = theContent + theLinks
        
        theContent = ""
        theSummaryLinks = ""
        #if self.getLinksToAvoid():
        #    (theContent, theSummaryLinks) = self.extractLinks(soup, self.getLinkstoavoid())
        #else:
        #    (theContent, theSummaryLinks) = self.extractLinks(soup, "") 
            
        if 'image_url' in post:
            theImage = post['image_url']
        else:
            theImage = None
        theLinks = theSummaryLinks
        theSummaryLinks = theContent + theLinks


        logging.debug("=========")
        logging.debug("Results: ")
        logging.debug("=========")
        logging.debug("Title:     ", theTitle)
        logging.debug("Link:      ", theLink)
        logging.debug("First Link:", firstLink)
        logging.debug("Summary:   ", content[:200])
        logging.debug("Sum links: ", theSummaryLinks)
        logging.debug("the Links"  , theLinks)
        logging.debug("Comment:   ", comment)
        logging.debug("Image;     ", theImage)
        logging.debug("Post       ", theTitle + " " + theLink)
        logging.debug("==============================================")
        logging.debug("")


        return (theTitle, theLink, firstLink, theImage, theSummary, content, theSummaryLinks, theContent, theLinks, comment)

def main():
    CHANNEL = 'tavern-of-the-bots' 

    import moduleSlack

    config = configparser.ConfigParser()
    config.read(CONFIGDIR + '/.rssBlogs')

    site = moduleSlack.moduleSlack()
    section = "Blog7"

    url = config.get(section, "url")
    site.setUrl(url)

    SLACKCREDENTIALS = os.path.expanduser(CONFIGDIR + '/.rssSlack')
    site.setSlackClient(SLACKCREDENTIALS)

    theChannel = site.getChanId(CHANNEL)  
    site.setPostsSlack('links')
    site.getPostsSlack()
    
    if ('bufferapp' in config.options(section)): 
        site.setBufferapp(config.get(section, "bufferapp"))
    if ('program' in config.options(section)): 
        site.setProgram(config.get(section, "program"))

    site.setSocialNetworks(config, section)
    site.setCache()

    outputData, posts = site.listPosts()
    site.setPostsCache()
    site.getPostsCache()
    theChannel = site.getChanId("links")  
    # We should check for consistency 

    i = 0
    listLinks = ""

    lastUrl = ''
    for line in outputData['Slack']['pending']:
        if urllib.parse.urlparse(line[0]).netloc == lastUrl: 
            listLinks = listLinks + "%d>> %s\n" % (i, line[0])
        else:
            listLinks = listLinks + "%d) %s\n" % (i, line[0])
        lastUrl = urllib.parse.urlparse(line[0]).netloc
        i = i + 1

    numEntries = i
    click.echo_via_pager(listLinks)
    i = input("Which one? [x] to exit ")
    if i == 'x':
        sys.exit()

    elem = int(i)
    print(outputData['Slack']['pending'][elem])

    action = input("Delete [d], publish [p], exit [x] ")

    (title, link, firstLink, image, summary, summaryHtml, summaryLinks, content, links, comment) = (site.obtainPostData(elem, False))
    if action == 'x':
        sys.exit()
    elif action == 'p':
        if site.getBufferapp():
            #api = moduleSocial.connectBuffer()

            site.buffer.API()
            lenMax, profileList = site.buffer.checkLimitPosts(site.getBufferapp())

            for profile in profileList:

                if profile['service'][0] in site.getBufferapp():
                    print("      getBuffer %s" % profile['service'])
                    (title, link, firstLink, image, summary, summaryHtml, summaryLinks, content, links, comment) = (site.obtainPostData(elem, False))
                    # In order to avoid saving the link as the last one

                    isDebug = False
                    moduleSocial.publishBuffer(site, profile, title, link, firstLink, isDebug, lenMax, site.getBufferapp())

        if site.getProgram():

            lenMax, profileList = site.cache.checkLimitPosts(site.getProgram())

            site.cache.getProfiles()
            site.cache.listPosts()

            for profile in profileList:
                lenMax = site.cache.lenMax[profile]
                if profile[0] in site.getProgram():
                    print("        getProgram %s" % profile)

 
                socialNetwork = (profile,site.getSocialNetworks()[profile])

                import moduleCache
                listP = site.cache.listPostsCache(socialNetwork)
                listPsts = [(title, link, firstLink, image, summary, summaryHtml, summaryLinks, content, links, comment)]
                listP = listP + listPsts
                serviceName = socialNetwork[0].capitalize()
                site.cache.posts[serviceName]['pending'] = listP
                site.cache.updatePostsCache(socialNetwork)


    site.deletePost(outputData['Slack']['pending'][elem][8], theChannel)

    client = moduleSocial.connectTumblr()
    # We need to publish it in the Tumblr blog since we won't publish it by
    # usuarl means (it is deleted from queue).
    moduleSocial.publishTumblr('fernand0', title, link, summary, summaryHtml,
            summaryLinks, image, content, links)


if __name__ == '__main__':
    main()
