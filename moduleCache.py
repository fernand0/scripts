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
import moduleSocial

from configMod import *
from moduleQueue import *

class moduleCache(Queue):
    
    def __init__(self):
        super().__init__()
        #self.url = url
        #self.socialNetwork = (socialNetwork, nick)

    def getClient(self):
        return(self.cache)

    def setClient(self, url, socialNetworks, program=""):
        self.url = url
        self.socialNetworks = socialNetworks
        self.program = program

    def getProgram(self):
        return (self.program)

    def getSocialNetworks(self):
        return (self.socialNetworks)

    def setProfiles(self, service=""):
        logging.info("  Checking services...")

        socialNetworks = self.getSocialNetworks()
        self.profiles = []
        for sN in socialNetworks:
            print(sN)
            if sN[0] in self.getProgram():
                cacheAcc = {}
                # Maybe adding 'Cache_'?
                cacheAcc['service'] = sN
                cacheAcc['service_username'] = socialNetworks[sN]
                self.profiles.append(cacheAcc)

    def getService(self):
        return(self.socialNetwork[0].capitalize())

    def setPosts(self):        
        outputData = {}

        self.setProfiles()
        profiles = self.getProfiles()

        self.service = {}
        i = 0

        for profile in profiles:
            serviceName = profile['service']
            nick = profile['service_username']
            fileNameQ = fileNamePath(self.url, (serviceName, nick)) + ".queue" 
            with open(fileNameQ,'rb') as f: 
                try: 
                    listP = pickle.load(f) 
                except: 
                    listP = [] 
            profile['posts'] = listP
            self.lenMax= len(profile['posts'])

            files = []
    
            serviceName = 'Cache_'+serviceName.capitalize()+'_'+nick
            logging.debug("   Service %s" % serviceName)
    
            outputData[serviceName] = {'sent': [], 'pending': []}
            #listP = self.getPosts()

            logging.debug("-Posts %s"% listP)
    
            if listP and len(listP) > 0: 
                for element in listP: 
                    outputData[serviceName]['pending'].append(element) 
    
            self.postsFormatted = outputData
    
    def addPosts(self, blog, profile, listPosts):
        nameCache = profile
        self.setPosts()
        self.setPostsFormatted()
        serviceName = self.name
        logging.info("    Adding posts to %s"% serviceName)
        listP = self.postsFormatted[serviceName]['pending']
        newListP = listP + listPosts
        self.postsFormatted[serviceName]['pending'] = newListP
        self.updatePostsCache()
        logging.info("    Added posts to %s"% serviceName)

    def updatePostsCache(self):
        fileNameQ = fileNamePath(self.url, self.socialNetwork) + ".queue" 

        #serviceName = self.name.capitalize()
        serviceName = 'Cache_'+self.socialNetwork[0]+'_'+self.socialNetwork[1]
        serviceName = self.name
    
        with open(fileNameQ, 'wb') as f:
            pickle.dump(self.postsFormatted[serviceName]['pending'], f)
        logging.debug("Writing in %s" % fileNameQ)

 
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

    def isForMe(self, args):
        profiles = self.getProfiles()
        lookAt = []
        for prof in profiles:
            if (prof['service'][0].capitalize() in args) or ('*' in args): 
                lookAt.append('Cache_'+prof['service'].capitalize()+'_'+prof['service_username'])
        return(lookAt)

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

    blog.cache.setProfiles()
    blog.cache.setPosts()
    print('F1', blog.cache.showPost('F1'))
    print('T3', blog.cache.showPost('T3'))
    print('TF2', blog.cache.showPost('TF2'))
    print('*4', blog.cache.showPost('*4'))
    #print('edit T7', blog.cache[ca].editPost('T7', 'Indico.'))
    #print('publish T7', blog.cache[ca].publishPost('T7'))
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
