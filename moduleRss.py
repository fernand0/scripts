# This module provides infrastructure for publishing and updating blog posts

# using several generic APIs  (XML-RPC, blogger API, Metaweblog API, ...)

import configparser
import os
import time
import urllib
import requests
import feedparser
import pickle
import logging
from slackclient import SlackClient
from bs4 import BeautifulSoup
from bs4 import Tag
from pdfrw import PdfReader
import moduleCache
# https://github.com/fernand0/scripts/blob/master/moduleCache.py

from configMod import *

class moduleRss():

    def __init__(self):
         self.url = ""
         self.name = ""
         self.rssFeed = ''
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

    def getRssFeed(self):
        return(self.rssFeed)

    def setRssFeed(self, feed):
        self.rssFeed = feed

    def getPosts(self):
        return(self.posts)
 
    def setPosts(self):
        logging.info("  Setting posts")
        if self.rssFeed.find('http')>=0: 
            urlRss = self.rssFeed
        else: 
            urlRss = self.url+self.rssFeed
        logging.debug(urlRss)
        self.posts = feedparser.parse(urlRss)

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
        self.buffer = moduleBuffer.moduleBuffer() 

    def getBufferapp(self):
        return(self.bufferapp)
 
    def setBufferapp(self):
        self.setBuffer()

    def getCache(self):
        return(self.cache)

    def setCache(self):
        self.cache = []
        for sN in self.getSocialNetworks():
            cacheAcc = moduleCache.moduleCache(self.getUrl(), 
                    sN, self.getSocialNetworks()[sN]) 
            cacheAcc.setPosts()
            cacheAcc.listPosts()

    def getProgram(self):
        return(self.program)
 
    def setProgram(self, program):
        self.program = program
        self.setCache()

    def getLinkPosition(self, link):
        i = 0
        if self.getPosts():
            if not link:
                logging.debug(self.getPosts().entries)
                return(len(self.getPosts().entries))
            for entry in self.getPosts().entries:
                linkS = link.decode()
                logging.debug(entry['link'], linkS)
                lenCmp = min(len(entry['link']), len(linkS))
                if entry['link'][:lenCmp] == linkS[:lenCmp]:
                    return i
                i = i + 1
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
        if not self.posts:
            self.setPosts()

        posts = self.getPosts().entries
        if not posts:
            return (None, None, None, None, None, None, None, None, None, None)

        post = posts[i]
        #print(post)

        if 'summary' in post:
            theSummary = post['summary']
            content = theSummary
        if 'content' in post:
            content = post['description']
            if content.startswith('Anuncios'): content = ''
        if 'description' in post:
            theDescription = post['description']
        if 'title' in post:
            theTitle = post['title'].replace('\n', ' ')
        if 'link' in post:
            theLink = post['link']
        if ('comment' in post):
            comment = post['comment']
        else:
            comment = ""

        theSummaryLinks = ""

        soup = BeautifulSoup(theDescription, 'lxml')

        link = soup.a
        if link is None:
           firstLink = theLink 
        else:
           firstLink = link['href']
           pos = firstLink.find('.')
           if firstLink.find('https')>=0:
               lenProt = len('https://')
           else:
               lenProt = len('http://')
           if (firstLink[lenProt:pos] == theTitle[:pos - lenProt]):
               # A way to identify retumblings. They have the name of the
               # tumblr at the beggining of the anchor text
               theTitle = theTitle[pos - lenProt + 1:]

        theSummary = soup.get_text()
        if self.getLinksToAvoid():
            (theContent, theSummaryLinks) = self.extractLinks(soup, self.getLinkstoavoid())
            logging.debug("theC", theContent)
            if theContent.startswith('Anuncios'): 
                theContent = ''
            logging.debug("theC", theContent)
        else:
            (theContent, theSummaryLinks) = self.extractLinks(soup, "") 
            logging.debug("theC", theContent)
            if theContent.startswith('Anuncios'): 
                theContent = ''
            logging.debug("theC", theContent)

        if 'media_content' in posts[i]: 
            theImage = posts[i]['media_content'][0]['url']
        else:
            theImage = self.extractImage(soup)
        logging.debug("theImage", theImage)
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

    import moduleRss
    
    config = configparser.ConfigParser()
    config.read(CONFIGDIR + '/.rssBlogs')

    print("Configured blogs:")

    blogs = []

    for section in config.sections():
        print(section)
        blog = moduleRss.moduleRss()
        url = config.get(section, "url")
        print("Url: %s"% url)
        blog.setUrl(url)
        if 'rssfeed' in config.options(section): 
            rssFeed = config.get(section, "rssFeed")
            print(rssFeed) 
            blog.setRssFeed(rssFeed)
        optFields = ["linksToAvoid", "time", "bufferapp"]
        if ("linksToAvoid" in config.options(section)):
            blog.setLinksToAvoid(config.get(section, "linksToAvoid"))
        if ("time" in config.options(section)):
            blog.setTime(config.get(section, "time"))
        if ("bufferapp" in config.options(section)):
            blog.setBufferapp(config.get(section, "bufferapp"))
        if ("program" in config.options(section)):
            blog.setProgram(config.get(section, "program"))

        blog.setSocialNetworks(config, section)

        print(blog.getSocialNetworks())

        blogs.append(blog)
        print(blog.obtainPostData(0))

    
    #blogs[7].setPosts()
    #print(blogs[7].getPosts().entries)
    blogs[6].setPostsCache()

    print(blogs[6].getPostsCache())
    print(blogs[6].cache.listPosts())
    print(blogs[6].cache.showPost('F1'))
    sys.exit()
    print(blogs[6].cache.editPost('F1', '10 Tricks to Appear Smart During Meetings – The Cooper Review – Medium. ---'))
    print(blogs[6].cache.showPost('F1'))
    sys.exit()

    numPosts = len(blogs[7].getPosts().entries)
    for i in range(numPosts):
        print(blog.obtainPostData(numPosts - 1 - i))


    for blog in blogs:
        print(blog.getUrl())
        print(blog.getRssFeed())
        print(blog.getSocialNetworks())
        if 'twitterac' in blog.getSocialNetworks():
            print(blog.getSocialNetworks()['twitterac'])
        blog.setPosts()
        print(blog.getPosts().entries[0]['link'])
        print(blog.getLinkPosition(blog.getPosts().entries[0]['link']))
        print(time.asctime(blog.datePost(0)))
        print(blog.getLinkPosition(blog.getPosts().entries[5]['link']))
        print(time.asctime(blog.datePost(5)))
        blog.obtainPostData(0)
        if blog.getUrl().find('ando')>0:
            blog.newPost('Prueba %s' % time.asctime(), 'description %s' % 'prueba')
            print(blog.selectPost())

    for blog in blogs:
        import urllib
        urlFile = open(DATADIR + '/' 
              + urllib.parse.urlparse(blog.getUrl()+blog.getRssFeed()).netloc
              + ".last", "r")
        linkLast = urlFile.read().rstrip()  # Last published
        print(blog.getUrl()+blog.getRssFeed(),blog.getLinkPosition(linkLast))
        print("description ->", blog.getPosts().entries[5]['description'])
        for post in posts:
            if "content" in post:
                print(post['content'][:100])

if __name__ == "__main__":
    main()


