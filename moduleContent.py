# This module provides infrastructure for publishing and updating blog posts

# using several generic APIs  (XML-RPC, blogger API, Metaweblog API, ...)

import configparser
import os
import time
import urllib
import requests
import pickle
import logging
from slackclient import SlackClient
from bs4 import BeautifulSoup
from bs4 import Tag
from pdfrw import PdfReader
import moduleCache
import moduleBuffer
# https://github.com/fernand0/scripts/blob/master/moduleCache.py

from configMod import *

class Content:

    def __init__(self):
        self.url = ""
        self.name = ""
        self.Id = 0
        self.socialNetworks = {}
        self.linksToAvoid = ""
        self.posts = None
        self.time = []
        self.bufferapp = None
        self.program = None
        self.buffer = None
        self.cache = None
        self.xmlrpc = None
        self.lastLinkPublished = {}
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

    def getPostsFormatted(self):
        return(self.postsFormatted)

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

    def setBuffer(self, bufferapp):
        self.bufferapp = bufferapp
        self.buffer = moduleBuffer.moduleBuffer(self.bufferapp)
        self.buffer.setBuffer()
        self.buffer.setPosts()
        self.profiles = {}
        for sN in self.buffer.getProfiles():
            serviceName = sN['service']
            nick =  sN['service_username']
            self.profiles[serviceName+'_'+nick] = sN

    def getBufferapp(self):
        return(self.bufferapp)
 
    def setBufferapp(self, bufferapp):
        self.setBuffer(bufferapp)

    def getCache(self):
        return(self.cache)

    def setCache(self):
        self.cache = {}
        for sN in self.getSocialNetworks():
            if sN[0] in self.getProgram():
                cacheAcc = moduleCache.moduleCache(self.getUrl(), 
                        sN, self.getSocialNetworks()[sN]) 
                cacheAcc.setPosts()
                cacheAcc.setPostsFormatted()
                # Maybe adding 'Cache_'?
                self.cache[sN+'_'+self.getSocialNetworks()[sN]] = cacheAcc

    def getProgram(self):
        return(self.program)
 
    def setProgram(self, program):
        self.program = program
        self.setCache()

    def getLinkEntry(self, entry):
        pass

    def getLinkPosition(self, link):
        i = 0
        posts = self.getPosts()
        pos = len(posts) 
        if posts:
            if not link:
                logging.debug(self.getPosts())
                return(len(self.getPosts()))
            for entry in self.getPosts():
                linkS = link.decode()
                url = self.getLinkEntry(entry)
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
        return(self.getPosts().entries[pos]['published_parsed'])

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

    def obtainPostData(self, i, debug=False):
        pass

