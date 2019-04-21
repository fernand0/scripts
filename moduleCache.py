#!/usr/bin/env python
# encoding: utf-8

# Queue [cache] files name is composed of a dot, followed by the path of the
# URL, followed by the name of the social network and the name of the user for
# posting there.
# The filename ends in .queue
# For example:
#    .my.blog.com_twitter_myUser.queue
# This file stores a list of pending posts stored as an array of posts as
# returned by moduleRss
# (https://github.com/fernand0/scripts/blob/master/moduleRss
#  obtainPostData method.

import configparser, os
import pickle
import logging
import sys
import importlib
importlib.reload(sys)
#sys.setdefaultencoding("UTF-8")

from configMod import *
from moduleQueue import *

class moduleCache(Queue):
    
    def __init__(self):
        super().__init__()
        self.service = None
        self.nick = None
        #self.url = url
        #self.socialNetwork = (socialNetwork, nick)

    def setClient(self, url, socialNetwork):
        self.url = url
        self.service = socialNetwork[0]
        self.nick = socialNetwork[1]

    def getSocialNetwork(self):
        return (self.service, self.nick)

    def getService(self):
        return(self.service)

    def setPosts(self):        
        fileNameQ = fileNamePath(self.url, 
                (self.service, self.nick)) + ".queue"
        try:
            with open(fileNameQ,'rb') as f: 
                try: 
                    listP = pickle.load(f) 
                except: 
                    listP = [] 
        except:
            listP = []

        self.posts = listP

    def addPosts(self, listPosts):
        self.posts = self.posts + listPosts
        self.updatePostsCache()

    def updatePostsCache(self):
        fileNameQ = fileNamePath(self.url, (self.service, self.nick)) + ".queue"

        with open(fileNameQ, 'wb') as f:
            pickle.dump(self.posts, f)
        logging.debug("Writing in %s" % fileNameQ)

    def extractDataMessage(self, i):
        logging.info("Service %s"% self.service)
        messageRaw = self.getPosts()[i]

        theTitle = messageRaw[0]
        theLink = messageRaw[1]

        theLinks = None
        content = messageRaw[4]
        theContent = None
        firstLink = theLink
        theImage = messageRaw[3]
        theSummary = content

        theSummaryLinks = content
        comment = None

        return (theTitle, theLink, firstLink, theImage, theSummary, content, theSummaryLinks, theContent, theLinks, comment)

    def getTitle(self, i):
        if i < len(self.getPosts()): 
            post = self.getPosts()[i]
            title = post[0]
            return (title)
        return(None)

    def getLink(self, i):
        if i < len(self.getPosts()): 
            post = self.getPosts()[i]
            link = post[1]
            return (link)
        return(None) 
    
    def getPostTitle(self, post):
        logging.info(post)
        if post:
            title = post[0]
            return (title)
        return(None)

    def getPostLink(self, post):
        if post:
            link = post[0]
            return (link)
        return(None)

    def isForMe(self, args):
        return ((self.service[0].capitalize() in args.split()[0])
                or (args[0] == '*'))

    def edit(self, j, newTitle):
        logging.info("New title %s", newTitle)
        thePost = self.obtainPostData(j)
        oldTitle = thePost[0]
        thePost = thePost[1:]
        thePost = (newTitle,) + thePost
        self.posts[j] = thePost
        logging.info("Service Name %s" % self.name)
        self.updatePostsCache()
        update = "Changed "+oldTitle+" with "+newTitle
        return(update)

    def publish(self, j):
        logging.info("Publishing %d"% j)
        post = self.obtainPostData(j)
        logging.info("Publishing %s"% post[0])
        import importlib
        serviceName = self.service.capitalize()
        mod = importlib.import_module('module' + serviceName) 
        cls = getattr(mod, 'module' + serviceName)
        api = cls()
        api.setClient(self.nick)
        comment = ''
        title = post[0]
        link = post[1]
        comment = ''
        update = api.publishPost(title, link, comment)
        logging.info("Publishing title: %s" % title)
        logging.info("Social network: %s Nick: %s" % (self.service, self.nick))
        if not isinstance(update, str) or (isinstance(update, str) and update[:4] != "Fail"):
            self.posts = self.posts[:j] + self.posts[j+1:]
            logging.debug("Updating %s" % self.posts)
            self.updatePostsCache()
            logging.info("Update ... %s" % str(update))
            if 'text' in update:
                update = update['text']
            if type(update) == tuple:
                update = update[1]['id']
                # link: https://www.facebook.com/[name]/posts/[second part of id]
        logging.info("Update before return %s"% update)
        return(update)
    
    def delete(self, j):
        logging.info("Deleting %d"% j)
        post = self.obtainPostData(j)
        logging.info("Deleting %s"% post[0])
        self.posts = self.posts[:j] + self.posts[j+1:]
        self.updatePostsCache()

        logging.info("Deleted %s"% post[0])
        return("Deleted %s"% post[0])
 
def main():
    import moduleCache
    import moduleSlack

    cache = moduleCache.moduleCache()
    cache.setClient('http://fernand0-errbot.slack.com/', 
            ('twitter', 'fernand0'))
    cache.setPosts()
    print(cache.getPosts())
    print(cache.getPosts()[0])
    print(len(cache.getPosts()[0]))
    # It has 10 elements
    print(cache.obtainPostData(0))
    print(cache.selectAndExecute('show', 'T0'))
    print(cache.selectAndExecute('show', 'M0'))
    print(cache.selectAndExecute('show', 'F1'))
    print(cache.selectAndExecute('show', '*2'))
    print(cache.selectAndExecute('show', 'TM3'))
    print(cache.selectAndExecute('show', 'TM6'))
    #print(cache.selectAndExecute('delete', 'F7'))
    #print(cache.selectAndExecute('edit', 'M0 Why Blockchain is Hard.'))
    #print(cache.selectAndExecute('publish', 'T1'))
    sys.exit()

    blog.cache.setPosts()
    print('T0', blog.cache.selectAndExecute('show', 'T0'))
    print('T3', blog.cache.selectAndExecute('show', 'T3'))
    print('TF2', blog.cache.selectAndExecute('show', 'TF2'))
    print('F4', blog.cache.selectAndExecute('show', 'F4'))
    print('*3', blog.cache.selectAndExecute('show', '*3'))
    #print('F0', blog.cache.selectAndExecute('delete', 'F0'))
    #print('edit F0', blog.cache.selectAndExecute('edit', 'F0'+' '+'LLVM 8.0.0 Release.'))
    #print('edit F0', blog.cache.editPost('F0', 'Así es Guestboard, un "Slack" para la organización de eventos.'))
    #print('publish T0', blog.cache.publishPost('T0'))
    #ca.movePost('T4 T3')
    #ca.editPost('T4', "My Stepdad's Huge Dataset.") 
    #ca.editPost('F5', "¡Sumate al datatón y a WiDS 2019! - lanacion.com")
    sys.exit()
    print(ca.editPost('F1', 'Alternative Names for the Tampon Tax - The Belladonna Comedy'))
    sys.exit()
    print(cache.editPost(postsP, 'F1', '10 Tricks to Appear Smart During Meetings – The Cooper Review – Medium...'))
    sys.exit()

    publishPost(api, profiles, ('F',1))

    posts.update(postsP)
    print("-> Posts",posts)
    #print("Posts",profiles)
    print("Keys",posts.keys())
    print("Pending",type(profiles))
    profiles = listSentPosts(api, "")
    print("Sent",type(profiles))


    if profiles:
       toPublish, toWhere = input("Which one do you want to publish? ").split(' ')
       #publishPost(api, profiles, toPublish)


if __name__ == '__main__':
    main()
