# This module provides infrastructure for reading content from different places
# It stores in a convenient and consistent way the content in order to be used
# in other programs

import configparser
import os
import logging
from bs4 import Tag

from configMod import *

class Content:

    def __init__(self):
        self.url = ""
        self.name = ""
        self.Id = 0
        self.socialNetworks = {}
        self.linksToAvoid = ""
        self.posts = None
        self.postsFormatted = None
        self.time = []
        self.bufferapp = None
        self.program = None
        self.buffer = None
        self.cache = None
        self.xmlrpc = None
        self.api = {}
        self.lastLinkPublished = {}
 
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

    def getSocialNetworksAPI(self):
        return(self.api)

    def setSocialNetworks(self, config, section):
        socialNetworksOpt = ['twitter', 'facebook', 'telegram', 
                'medium', 'linkedin','pocket', 'mastodon','instagram'] 
        for option in config.options(section):
            if (option in socialNetworksOpt):
                nick = config.get(section, option)
                socialNetwork = (option, nick)
                self.addSocialNetwork(socialNetwork)

    def addSocialNetworkAPI(self, socialNetwork):
        sN = socialNetwork[0]
        nick = socialNetwork[1]
        #if sN == 'twitter':
        #    self.api[socialNetwork] = moduleTwitter.moduleTwitter()
        #    self.api[socialNetwork].setClient(nick)
        
    def addSocialNetwork(self, socialNetwork):
        self.socialNetworks[socialNetwork[0]] = socialNetwork[1]

    #def getPostsFormatted(self):
    #    return(self.postsFormatted)

    def getPosts(self):
        return(self.posts)
 
    def setPosts(self):
        pass 

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

    def getBuffer(self):
        return(self.buffer)

    def setBuffer(self): 
        import moduleBuffer 
        # https://github.com/fernand0/scripts/blob/master/moduleBuffer.py
        self.buffer = {}
        for service in self.getSocialNetworks():
            if service[0] in self.getBufferapp():
                nick = self.getSocialNetworks()[service]
                buf = moduleBuffer.moduleBuffer() 
                buf.setClient(self.url, (service, nick))
                buf.setPosts()
                self.buffer[(service, nick)] = buf

    def getBufferapp(self):
        return(self.bufferapp)
 
    def setBufferapp(self, bufferapp):
        self.bufferapp = bufferapp
        self.setBuffer()

    def getCache(self):
        return(self.cache)

    def setCache(self): 
        import moduleCache 
        # https://github.com/fernand0/scripts/blob/master/moduleCache.py
        self.cache = {}
        for service in self.getSocialNetworks():
            if self.getProgram():
                if service[0] in self.getProgram():
                    nick = self.getSocialNetworks()[service]
                    cache = moduleCache.moduleCache() 
                    param = (self.url, (service, nick))
                    cache.setClient(param)
                    cache.setPosts()
                    self.cache[(service, nick)] = cache

    def getProgram(self):
        return(self.program)
 
    def setProgram(self, program):
        self.program = program
        self.setCache()

    def len(self, profile):
        service = profile
        nick = self.getSocialNetworks()[profile]
        print("Profile %s, Nick %s" % (service, nick))
        if self.cache and (service, nick) in self.cache:
            if self.cache[(service, nick)].getPosts(): 
                return(len(self.cache[(service, nick)].getPosts()))
            else:
                return(0)
        elif self.buffer and (service, nick) in self.buffer:
            if self.buffer[(service, nick)].getPosts(): 
                return(len(self.buffer[(service, nick)].getPosts()))
            else:
                return(0)

    def getLinkPosition(self, link):
        i = 0
        posts = self.getPosts()
        pos = len(posts) 
        if posts:
            if not link:
                logging.debug(self.getPosts())
                return(len(self.getPosts()))
            for entry in posts:
                linkS = link
                if isinstance(link, bytes):
                    linkS = linkS.decode()
                url = self.getPostLink(entry)
                logging.debug(url, linkS)
                lenCmp = min(len(url), len(linkS))
                if url[:lenCmp] == linkS[:lenCmp]:
                    # When there are duplicates (there shouldn't be) it returns
                    # the last one
                    pos = i
                i = i + 1
            return(pos)
        return(i)

    def datePost(self, pos):
        print(self.getPosts())
        if 'entries' in self.getPosts():
            return(self.getPosts().entries[pos]['published_parsed'])
        else:
            return(self.getPosts()[pos]['published_parsed'])

    def extractImage(self, soup):
        #This should go to the moduleHtml
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

    def extractLinks(self, soup, linksToAvoid=""):
        #This should go to the moduleHtml
        j = 0
        linksTxt = ""
        links = soup.find_all(["a","iframe"])
        for link in soup.find_all(["a","iframe"]):
            theLink = ""
            if len(link.contents) > 0: 
                if not isinstance(link.contents[0], Tag):
                    # We want to avoid embdeded tags (mainly <img ... )
                    if link.has_attr('href'):
                        theLink = link['href']
                    else:
                        if 'src' in link: 
                            theLink = link['src']
                        else:
                            continue
            else:
                if 'src' in link: 
                    theLink = link['src']
                else:
                    continue
    
            if ((linksToAvoid == "") or
               (not re.search(linksToAvoid, theLink))):
                    if theLink:
                        link.append(" ["+str(j)+"]")
                        linksTxt = linksTxt + "["+str(j)+"] " + \
                            link.contents[0] + "\n"
                        linksTxt = linksTxt + "    " + theLink + "\n"
                        j = j + 1
    
        if linksTxt != "":
            theSummaryLinks = linksTxt
        else:
            theSummaryLinks = ""
    
        return (soup.get_text().strip('\n'), theSummaryLinks)

    def report(self, profile, post, link, data): 
        logging.warning("%s posting failed!" % profile) 
        logging.warning("Post %s %s" % (post,link)) 
        logging.warning("Unexpected error: %s"% data[0]) 
        logging.warning("Unexpected error: %s"% data[1]) 
        print("%s posting failed!" % profile) 
        print("Post %s %s" % (post,link)) 
        print("Unexpected error: %s"% data[0]) 
        print("Unexpected error: %s"% data[1]) 
        return("Fail! %s" % data[1])
        #print("----Unexpected error: %s"% data[2]) 


    def getPostTitle(self, post):
        return str(post)
    
    def getPostLink(self, post):
        return ''
