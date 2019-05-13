#!/usr/bin/env python

import configparser
import pickle
import os
import urllib
import logging
from pdfrw import PdfReader
from slackclient import SlackClient
import sys
import click
import requests
from bs4 import BeautifulSoup
from bs4 import Tag

from moduleContent import *

class moduleSlack(Content):

    def __init__(self):
        super().__init__()
        self.sc = None
        self.keys = []

    def setSlackClient(self, slackCredentials):
        config = configparser.ConfigParser()
        config.read(slackCredentials)
    
        slack_token = config["Slack"].get('api-key')
        
        self.sc = SlackClient(slack_token)
 
    def getSlackClient(self):
        return self.sc
 
    def setPosts(self, channel='links'):
        logging.info("  Setting posts")
        self.posts = []
        theChannel = self.getChanId(channel)
        history = self.sc.api_call( "channels.history", count=1000, channel=theChannel)
        if 'messages' in history:
            self.posts = history['messages']
        else:
            self.posts = []

        #outputData = {}
        #serviceName = 'Slack'
        #outputData[serviceName] = {'sent': [], 'pending': []}
        #for post in self.getPosts():
        #    if 'attachments' in post:
        #        outputData[serviceName]['pending'].append(
        #            (post['text'][1:-1], post['attachments'][0]['title'], '', '', '', '', '', '', post['ts'], ''))
        #    else:
        #        #print(post)
        #        outputData[serviceName]['pending'].append(
        #            (post['text'][1:-1], '', '', '', '', '', '', '', post['ts'], ''))
        #self.postsFormatted = outputData

    def getTitle(self, i):
        post = self.getPosts()[i]
        return(self.getPostTitle(post))

    def getLink(self, i):
        post = self.getPosts()[i]
        return(self.getPostLink(post))

    def getPostTitle(self, post):
        if 'attachments' in post:
            return(post['attachments'][0]['title'])
        else:
            text = post['text']
            if text.startswith('<'): 
                title = post['text'][1:-1]
            else:
                pos = text.find('<')
                title=text[:pos]
            return(title)                

    def getPostLink(self, post):
        if 'attachments' in post:
            return(post['attachments'][0]['original_url'])
        else:
            text = post['text']
            if text.startswith('<'): 
                url = post['text'][1:-1]
            else:
                pos = text.find('<')
                url=text[pos+1:-1]
            return(url) 

    def getId(self, i):
        post = self.getPosts()[i]
        return(post['ts'])

    def getKeys(self):
        return(self.keys)
    
    def setKeys(self, keys):
        self.keys = keys

    def deletePost(self, idPost, theChannel): 
        #theChannel or the name of the channel?
        logging.info("Deleting id %s" % idPost)
            
        result = self.sc.api_call("chat.delete", channel=theChannel, ts=idPost)
    
        logging.info(result)
        return(result)
    
    def getChanId(self, name):
        chanList = self.sc.api_call("channels.list")['channels']
        for channel in chanList:
            if channel['name_normalized'] == name:
                return(channel['id'])
        return(None)

    def obtainPostData(self, i, debug=False):
        if not self.posts:
            self.setPosts()

        posts = self.getPosts()
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

        theTitle = self.getTitle(i)
        theLink = self.getLink(i)
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
        #elif 'text' in post:
        #    if post['text'].startswith('<h'):
        #        # It's an url
        #        url = post['text'][1:-1]
        #        req = requests.get(url)
        #            
        #        if req.text.find('403 Forbidden')>=0:
        #            theTitle = url
        #            theSummary = url
        #            content = url
        #            theDescription = url
        #        else:
        #            if url.lower().endswith('pdf'):
        #                nameFile = '/tmp/kkkkk.pdf'
        #                with open(nameFile,'wb') as f:
        #                    f.write(req.content)
        #                theTitle = PdfReader(nameFile).Info.Title
        #                if theTitle:
        #                    theTitle = theTitle[1:-1]
        #                else:
        #                    theTitle = url
        #                theUrl = url
        #                theSummary = ''
        #                content = theSummary
        #                theDescription = theSummary
        #            else:
        #                soup = BeautifulSoup(req.text, 'lxml')
        #                #print("soup", soup)
        #                theTitle = soup.title
        #                if theTitle:
        #                    theTitle = str(theTitle.string)
        #                else:
        #                    # The last part of the path, without the dot part, and
        #                    # capitized
        #                    urlP = urllib.parse.urlparse(url)
        #                    theTitle = os.path.basename(urlP.path).split('.')[0].capitalize()
        #                theSummary = str(soup.body)
        #                content = theSummary
        #                theDescription = theSummary
        #    else:
        #        theSummary = post['text']
        #        content = post['text']
        #        theDescription = post['text']
        #        theTitle = post['text']
        #else:
        #    theSummary = post['title']
        #    content = post['title']
        #    theDescription = post['title']

        if 'original_url' in post: 
            theLink = post['original_url']
        elif url: 
            theLink = url
        else:
            theLink = self.getPostLink(post)

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

    def publishPost(self, chan, msg):
        theChan = self.getChanId(chan)
        logging.info("Publishing %s" % msg)
        result = self.sc.api_call("chat.postMessage", 
                channel = theChan, text = msg)
        logging.info(result)
        return(result)

def main():
    CHANNEL = 'tavern-of-the-bots' 

    import moduleTumblr
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
    site.setPosts('links')

    site.setSocialNetworks(config, section)

    if ('bufferapp' in config.options(section)): 
        site.setBufferapp(config.get(section, "bufferapp"))

    if ('program' in config.options(section)): 
        site.setProgram(config.get(section, "program"))

    theChannel = site.getChanId("links")  

    i = 0
    listLinks = ""

    lastUrl = ''
    for i, post in enumerate(site.getPosts()):
        url = site.getLink(i)
        if urllib.parse.urlparse(url).netloc == lastUrl: 
            listLinks = listLinks + "%d>> %s\n" % (i, url)
        else:
            listLinks = listLinks + "%d) %s\n" % (i, url)
        lastUrl = urllib.parse.urlparse(url).netloc
        print(site.getTitle(i))
        print(site.getLink(i))
        print(site.getPostTitle(post))
        print(site.getPostLink(post))
        i = i + 1

    numEntries = i
    click.echo_via_pager(listLinks)
    i = input("Which one? [x] to exit ")
    if i == 'x':
        sys.exit()

    elem = int(i)
    print(site.getPosts()[elem])

    action = input("Delete [d], publish [p], exit [x] ")

    if action == 'x':
        sys.exit()
    elif action == 'p':
        if site.getBufferapp():
            for profile in site.getSocialNetworks():
                if profile[0] in site.getBufferapp():
                    lenMax = site.len(profile)
                    print("   getBuffer %s" % profile)
                    socialNetwork = (profile,site.getSocialNetworks()[profile])
                    title = site.getTitle(elem)
                    url = site.getLink(elem)
                    listPosts = []
                    listPosts.append((title, url))
                    site.buffer[socialNetwork].addPosts(listPosts)

        if site.getProgram():
            for profile in site.getSocialNetworks():
                if profile[0] in site.getProgram():
                    lenMax = site.len(profile)
                    print("   getProgram %s" % profile)
 
                    socialNetwork = (profile,site.getSocialNetworks()[profile])

                    listP = site.cache[socialNetwork].getPosts()
                    #site.cache[socialNetwork].posts = site.cache[socialNetwork].posts[:8]  
                    #listP = site.cache[socialNetwork].getPosts()
                    #for i,l in enumerate(listP):
                    #    print(i, l)
                    #site.cache[socialNetwork].updatePostsCache()
                    listPsts = site.obtainPostData(elem)
                    listP = listP + [listPsts]
                    #for i,l in enumerate(listP):
                    #    print(i, l)
                    #sys.exit()
                    site.cache[socialNetwork].posts = listP
                    site.cache[socialNetwork].updatePostsCache()
        t = moduleTumblr.moduleTumblr()
        t.setClient('fernand0')
        # We need to publish it in the Tumblr blog since we won't publish it by
        # usuarl means (it is deleted from queue).
        t.publishPost(title, url, '')

    site.deletePost(site.getId(elem), theChannel)
    #print(outputData['Slack']['pending'][elem][8])


if __name__ == '__main__':
    main()
