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
from moduleContent import *

class moduleRss(Content):

    def __init__(self):
        super().__init__()
        self.rssFeed = ''
 
    def getRssFeed(self):
        return(self.rssFeed)

    def setRssFeed(self, feed):
        self.rssFeed = feed

    def setPosts(self):
        logging.info("  Setting posts")
        if self.rssFeed.find('http')>=0: 
            urlRss = self.getRssFeed()
        else: 
            urlRss = self.url+self.getRssFeed()
        logging.debug(urlRss)
        self.posts = feedparser.parse(urlRss).entries

        outputData = {}
        serviceName = 'Rss'
        outputData[serviceName] = {'sent': [], 'pending': []}
        for i in range(len(self.getPosts())):
            outputData[serviceName]['pending'].append(self.obtainPostData(i))
        self.postsFormatted = outputData
 
    def getLinkEntry(self, entry):
        return(entry['link'])

    def obtainPostData(self, i, debug=False):
        if not self.posts:
            self.setPosts()

        posts = self.getPosts()
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
            logging.debug("theC %s" % theContent)
            if theContent.startswith('Anuncios'): 
                theContent = ''
            logging.debug("theC %s"% theContent)
        else:
            (theContent, theSummaryLinks) = self.extractLinks(soup, "") 
            logging.debug("theC %s"% theContent)
            if theContent.startswith('Anuncios'): 
                theContent = ''
            logging.debug("theC %s"% theContent)

        if 'media_content' in posts[i]: 
            theImage = ''
            for media in posts[i]['media_content']:
                if media['url'].find('avatar')<0: 
                    theImage = media['url']
        else:
            theImage = self.extractImage(soup)
        logging.debug("theImage %s"% theImage)
        theLinks = theSummaryLinks
        theSummaryLinks = theContent + theLinks
            
        logging.debug("=========")
        logging.debug("Results: ")
        logging.debug("=========")
        logging.debug("Title:      %s"% theTitle)
        logging.debug("Link:       %s"% theLink)
        logging.debug("First Link: %s"% firstLink)
        logging.debug("Summary:    %s"% content[:200])
        logging.debug("Sum links:  %s"% theSummaryLinks)
        logging.debug("the Links   %s"% theLinks)
        logging.debug("Comment:    %s"% comment)
        logging.debug("Image;      %s"% theImage)
        logging.debug("Post        %s"% theTitle + " " + theLink)
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
        blog.setCache()

        blogs.append(blog)

    


    for blog in blogs:
        print(blog.getUrl())
        print(blog.getRssFeed())
        print(blog.getSocialNetworks())
        if 'twitterac' in blog.getSocialNetworks():
            print(blog.getSocialNetworks()['twitterac'])
        blog.setPosts()
        if blog.getPosts():
            print(blog.getPosts()[0]['link'])
            print(blog.getLinkPosition(blog.getPosts()[0]['link']))
            print(time.asctime(blog.datePost(0)))
            print(blog.getLinkPosition(blog.getPosts()[5]['link']))
            print(time.asctime(blog.datePost(5)))
            blog.obtainPostData(0)
        #    blog.newPost('Prueba %s' % time.asctime(), 'description %s' % 'prueba')
        #    print(blog.selectPost())

    for blog in blogs:
        for service in blog.getSocialNetworks():
            socialNetwork = (service, blog.getSocialNetworks()[service])
            
        linkLast = checkLastLink(blog.getUrl(), socialNetwork)
        print(blog.getUrl()+blog.getRssFeed(),blog.getLinkPosition(linkLast))
        if blog.getPosts(): 
            print("description ->", blog.getPosts()[5]['description'])
        for post in blog.getPosts():
            if "content" in post:
                print(post['content'][:100])

if __name__ == "__main__":
    main()


