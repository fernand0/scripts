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
from bs4 import BeautifulSoup
import logging
import time
import sys
import urllib
import importlib
importlib.reload(sys)
#sys.setdefaultencoding("UTF-8")
import moduleRss
import moduleSocial

from configMod import *

class moduleCache():
    
    def __init__(self, url, socialNetwork, nick):
        self.service = None
        self.profiles = None
        self.posts = None
        self.postsFormatted = None
        self.name = "Cache_"+socialNetwork+"_"+nick
        self.url = url
        self.socialNetwork = (socialNetwork, nick)
        self.lenMax = -1

    def setPosts(self):        
        fileNameQ = fileNamePath(self.url, self.socialNetwork) + ".queue" 
        with open(fileNameQ,'rb') as f: 
            try: 
                listP = pickle.load(f) 
            except: 
                listP = [] 
        self.posts = listP
        self.lenMax= len(self.posts)

    def getPosts(self):        
        return(self.posts)

    def getPostsFormatted(self):    
        return(self.postsFormatted)

    def setPostsFormatted(self):    
        outputData = {}
        files = []
    
        serviceName = self.name.capitalize()
        logging.info("Service %s" % serviceName)
    
        outputData[serviceName] = {'sent': [], 'pending': []}
        listP = self.getPosts()

        logging.debug("-Posts %s"% listP)
    
        if listP and len(listP) > 0: 
            for element in listP: 
                outputData[serviceName]['pending'].append(element) 
    
        self.postsFormatted = outputData
    
    def updatePostsCache(self):
        fileNameQ = fileNamePath(self.url, self.socialNetwork) + ".queue" 
    
        serviceName = self.name.capitalize()
        with open(fileNameQ, 'wb') as f:
            pickle.dump(self.postsFormatted[serviceName]['pending'], f)
        logging.info("Writing in %s" % fileNameQ)
    
    def isForMe(self, args):
        serviceName =  self.socialNetwork[0].capitalize()
        if (serviceName[0] in args) or ('*' in args): 
           return True
        return False
    
    def showPost(self, args):
        #return(self.interpretAndExecute(args,'show'))
        logging.info("To show %s" % args)
    
        if self.isForMe(args):
            j = int(args[-1])
            serviceName = self.name.capitalize()
            (title, link, firstLink, image, summary, summaryHtml, summaryLinks, content, links, comment) = (self.postsFormatted[serviceName]['pending'][j])
                        
            if title:
                return(title+' '+link)
            else:
                return(None)
    
    def publishPost(self, args):
        #return(self.interpretAndExecute(args,'publish'))
        logging.info("To publish %s" % args)
    
        udpate = None
        if self.isForMe(args):
            j = int(args[-1])
            nick = profile['socialNetwork'][1]
            (title, link, firstLink, image, summary, summaryHtml, summaryLinks, content, links, comment) = (self.postsFormatted[serviceName]['pending'][j])
            publishMethod = getattr(moduleSocial, 
                    'publish'+ serviceName)
            logging.info("Publishing title: %s" % title)
            logging.info("Social network: %s Nick: %s" % (serviceName, nick))
            update = publishMethod(nick, title, link, summary, summaryHtml, summaryLinks, image, content, links)
            if not isinstance(update, str) or (isinstance(update, str) and update[:4] != "Fail"):
                self.posts[serviceName]['pending'] = self.posts[serviceName]['pending'][:j] + self.posts[serviceName]['pending'][j+1:]
                logging.debug("Updating %s" % self.posts)
                #logging.info("Blog %s" % cache['blog'])
                self.updatePostsCache(profile['socialNetwork'])
                if 'text' in update:
                    update = update['text']
    
        return(update)
    
    def deletePost(self, args):
        #return(self.interpretAndExecute(args,'delete'))
        logging.info("To Delete %s" % args)
    
        udpate = None
        if self.isForMe(args):
            j = int(args[-1])
            serviceName = self.name.capitalize()
            (title, link, firstLink, image, summary, summaryHtml, summaryLinks, content, links, comment) = (self.posts[serviceName]['pending'][j])
            update = "Deleted: "+ title
            logging.debug("Posts %s" % self.postsFormatted[serviceName]['pending'])
            self.postsFormatted[serviceName]['pending'] = self.postsFormatted[serviceName]['pending'][:j] + self.postsFormatted[serviceName]['pending'][j+1:]
            logging.debug("-Posts %s" % self.postsFormatted[serviceName]['pending'])
            logging.info("social network %s - %s" 
                    % (self.socialNetwork[0], self.socialNetwork[1]))
    
        return(update)
    
    def editPost(self, args, newTitle):
        #return(self.interpretAndExecute(args,'edit', newTitle))
        logging.info("To edit %s" % args)
        logging.info("New title %s", newTitle)
    
        udpate = None
        if self.isForMe(args):
            j = int(args[-1])
            serviceName = self.name.capitalize()
            (title, link, firstLink, image, summary, summaryHtml, summaryLinks, content, links, comment) = (self.postsFormatted[serviceName]['pending'][j])
            self.postsFormatted[serviceName]['pending'][j] = (newTitle, link, firstLink, image, summary, summaryHtml, summaryLinks, content, links, comment) 
            self.updatePostsCache()
            update = "Changed "+title+" with "+newTitle
        else:
            update = None

        return(update)
    
   
    
    #######################################################
    # These need work
    #######################################################
    
    def movePost(self, cache, posts, toMove, toWhere):
        # Moving posts, we identify the profile by the first letter. We can use
        # several letters and if we put a '*' we'll move the posts in all the
        # social networks
        logging.info("To move %s to %s" % (toMove,toWhere))
    
        i = 0
        profMov = ""
        while toMove[i].isalpha():
            profMov = profMov + toMove[i]
            i = i + 1
    
        profiles = cache['profiles']
        for profile in profiles: 
            logging.info("Social Network %s" % profile)
            logging.info("profMov %s", profMov)
            if 'socialNetwork' in profile:
                logging.info("socialNetwork %s", profile['socialNetwork'])
    
                serviceName = profile['socialNetwork'][0].capitalize()
                nick = profile['socialNetwork'][1]
                if (serviceName[0] in profMov) or toMove[0]=='*': 
                    logging.info("to Move %s to %s" % (toMove, toWhere))
                    j = int(toMove[-1])
                    k = int(toWhere[-1])
                    postI = (posts[serviceName]['pending'][i])
                    postJ = (posts[serviceName]['pending'][j])
                    posts[serviceName]['pending'][i] = postJ
                    posts[serviceName]['pending'][j] = postI
                    updatePostsCache(profile['socialNetwork'])
    
        return(posts[serviceName]['pending'][i][0]+' '+ 
                  posts[serviceName]['pending'][j][0])
    
    def copyPost(self, api, log, profiles, toCopy, toWhere):
        logging.info(toCopy+' '+toWhere)
    
        profCop = toCopy[0]
        ii = int(toCopy[1])
    
        j = 0
        profWhe = ""
        i = 0
        while i < len(toWhere):
            profWhe = profWhe + toWhere[i]
            i = i + 1
        
        log.info(toCopy,"|",profCop, ii, profWhe)
        for i in range(len(profiles)):
            serviceName = profiles[i].formatted_service
            print(serviceName)
            log.info("ii: %s" %i)
            updates = getattr(profiles[j].updates, 'pending')
            update = updates[ii]
            if ('media' in update): 
                if ('expanded_link' in update.media):
                    link = update.media.expanded_link
                else:
                    link = update.media.link
            else:
                link = ""
            print(update.text, link)
           
            if (serviceName[0] in profCop):
                for j in range(len(profiles)): 
                    serviceName = profiles[j].formatted_service 
                    if (serviceName[0] in profWhe):
                        profiles[j].updates.new(urllib.parse.quote(update.text + " " + link).encode('utf-8'))
    
    def listSentPosts(self, service=""):
        api = self.service
        profiles = getProfiles(api, service)
    
        someSent = False
        outputStr = ([],[])
        for i in range(len(profiles)):
            serviceName = profiles[i].formatted_service
            logging.debug("Service %d %s" % (i,serviceName))
            if (profiles[i].counts['sent'] > 0):
                someSent = True
                logging.info("Service %s" % serviceName)
                logging.debug("There are: %d" % profiles[i].counts['sent'])
                logging.debug(profiles[i].updates.sent)
                due_time=""
                for j in range(min(8,profiles[i].counts['sent'])):
                    updatesSent = profiles[i].updates.sent[j]
                    update = Update(api=api, id= updatesSent.id)
                    if (due_time == ""):
                        due_time=update.due_time # Not used here
                        outputStr[0].append("*%s*" % serviceName)
                        outputStr[1].append("")
                    logging.debug("Service %s" % updatesSent)
                    selectionStr = "" #"%d%d) " % (i,j)
                    if ('media' in updatesSent): 
                        try:
                            lineTxt = "%s %s %s" % (selectionStr, 
                                    updatesSent.text, updatesSent.media.expanded_link)
                        except:
                            lineTxt = "%s %s %s" % (selectionStr,
                                    updatesSent.text, updatesSent.media.link)
                    else:
                        lineTxt = "%s %s" % (selectionStr,updatesSent.text)
                    logging.info(lineTxt)
                    outputStr[0].append("%s" % lineTxt)
                    outputStr[1].append(" (%d clicks)" % updatesSent['statistics']['clicks'])
                    #logging.debug("-- %s" % (pp.pformat(update)))
                    #logging.debug("-- %s" % (pp.pformat(dir(update))))
            else:
                #logging.debug("Service %d %s" % (i, serviceName))
                logging.debug("No")
        
        if someSent:
            return (outputStr, profiles)
        else:
            logging.info("No sent posts")
            return someSent

def main():
    import moduleCache
    import moduleSlack

    config = configparser.ConfigParser()
    config.read(CONFIGDIR + '/.rssBlogs')

    section = "Blog7"
    blog = moduleSlack.moduleSlack()
    blog.setUrl(config.get(section, "url"))
    blog.setSlackClient(os.path.expanduser('~/.mySocial/config/.rssSlack'))
    blog.setSocialNetworks(config, section)

    if ('bufferapp' in config.options(section)): 
        blog.setBufferapp(config.get(section, "bufferapp"))
    if ('program' in config.options(section)): 
        blog.setProgram(config.get(section, "program"))

    cache = []
    for sN in blog.getSocialNetworks():
        (sN, blog.getSocialNetworks()[sN])

        cacheAcc = moduleCache.moduleCache(blog.getUrl(), 
                sN, blog.getSocialNetworks()[sN]) 
        cache.append(cacheAcc)

    for ca in cache:
        ca.setPosts()
        #print(ca.posts)
        print(ca.name)
        ca.getPostsFormatted()
        print(ca.showPost('F1'))
        print(ca.showPost('T1'))
        print(ca.showPost('TF2'))
        print(ca.showPost('*3'))
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
