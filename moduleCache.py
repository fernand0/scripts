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
    
    def __init__(self, url, socialNetworks):
        self.service = None
        self.profiles = None
        self.posts = None
        self.rawPosts = None
        self.name = "Cache"
        self.url = url
        self.socialNetworks = socialNetworks
        self.profile = None

    def getProfiles(self, service=""):
        # Needs improvement
        logging.info("Checking services...")
    
        profiles = []
    
        for soc in self.socialNetworks.keys():
            socialNetwork = (soc, self.socialNetworks[soc])
            profile = {}
            profile['socialNetwork'] = socialNetwork
            fileNameQ = self.fileName(socialNetwork) + ".queue" 
            profile['fileName'] = fileNameQ
            profiles.append(profile)
            profile['posts'] = []
    
        logging.debug("->%s" % profiles)
        numProfiles = len(profiles)
        logging.debug("Num. Profiles %d" % numProfiles)
        logging.debug("Profiles %s" % profiles)
    
        self.profiles =  profiles
    
    def fileName(self, socialNetwork):
        print(self.url)
        print(self)
        theName = os.path.expanduser(DATADIR + '/' 
                        + urllib.parse.urlparse(self.url).netloc 
                        + '_' 
                        + socialNetwork[0] + '_' + socialNetwork[1])
        return(theName)
    
    def getLastLink(self, fileName):        
        try: 
            with open(fileName, "rb") as f: 
                linkLast = f.read().rstrip()  # Last published
        except:
            # File does not exist, we need to create it.
            with open(fileName, "w") as f:
                logging.warning("File %s does not exist. Creating it."
                        % fileName) 
                linkLast = ''  
                # None published, or non-existent file
        return(linkLast, os.path.getmtime(fileName))
    
    def getPostsCache(self, socialNetwork):        
        fileNameQ = self.fileName(socialNetwork) + ".queue" 
        with open(fileNameQ,'rb') as f: 
            try: 
                listP = pickle.load(f) 
            except: 
                listP = [] 
        return(listP)
    
    def listPosts(self, service=""):    
        outputData = {}
        files = []
    
        profiles = self.profiles
        logging.info("** %s" % profiles)
    
        for profile in profiles:
            fileN = profile['fileName']
            serviceName = profile['socialNetwork'][0].capitalize()
            logging.info("Service %s" % serviceName)
    
            outputData[serviceName] = {'sent': [], 'pending': []}
            listP = self.getPostsCache(profile['socialNetwork'])
    
            logging.info("-Posts %s"% listP)
    
            if len(listP) > 0: 
                logging.debug("Waiting in queue: %s"% fileN) 
                for element in listP: 
                    outputData[serviceName]['pending'].append(element) 
            logging.info("Service posts profile %s" % profile)
            logging.info("Iter Service posts profiles %s" % profiles)
    
        logging.info("Service posts profiles %s" % profiles)
        return(outputData, profiles)
    
    def updatePostsCache(self, socialNetwork=()):
        fileNameQ = self.fileName(socialNetwork) + ".queue" 
    
        #print("Updating Posts Cache: %s" % fileNameQ)
    
        with open(fileNameQ, 'wb') as f:
             pickle.dump(self.posts[socialNetwork[0].capitalize()]['pending'],f)
        return(fileNameQ)
    
    def listPostsCache(self, socialNetwork=()):
       fileName = (DATADIR  + '/' 
               +  urllib.parse.urlparse(self.url).netloc 
               + '_'+ socialNetwork[0] + '_' + socialNetwork[1] 
               + ".queue")
    
       logging.info("Listing Posts Cache: %s" % fileName)
    
       with open(fileName,'rb') as f:
           try: 
               listP = pickle.load(f)
           except:
               listP = []
    
       logging.debug("listPostsCache", socialNetwork[0])
       for i in range(len(listP)):
           logging.debug("=> ", socialNetwork[0], listP[i][0])
    
       return(listP)
    
    def checkLastLink(self, socialNetwork=()):
        fileNameL = self.fileName(socialNetwork)+".last"
        logging.info("Checking last link: %s" % fileNameL)
        (linkLast, timeLast) = self.getLastLink(fileNameL)
        return(linkLast, timeLast)
    
    def updateLastLink(self, link, socialNetwork=()):
        if not socialNetwork: 
            fileName = (DATADIR  + '/' 
                   + urllib.parse.urlparse(self.url).netloc + ".last")
        else: 
            fileName = (DATADIR + '/'
                    + urllib.parse.urlparse(self.url).netloc +
                    '_'+socialNetwork[0]+'_'+socialNetwork[1] + ".last")
        with open(fileName, "w") as f: 
            f.write(link)
    
    def isForMe(self, profile, args):
        if 'socialNetwork' in profile:
            serviceName = profile['socialNetwork'][0].capitalize()
            nick = profile['socialNetwork'][1]
            if (serviceName[0] in args) or ('*' in args): 
                return True
        return False
    
    def showPost(self, args):
        logging.info("To publish %s" % args)
    
        update = ""
        logging.info("Cache antes %s" % self)
        profiles = self.profiles
        logging.info("Cache profiles antes %s" % profiles)
        title = None
        for profile in profiles: 
            logging.info("Social Network %s" % profile)
            if self.isForMe(profile, args): 
                serviceName = profile['socialNetwork'][0].capitalize()
                j = int(args[-1])
                (title, link, firstLink, image, summary, summaryHtml, summaryLinks, content, links, comment) = (self.posts[serviceName]['pending'][j])
                    
        if title:
            return(title+' '+link)
        else:
            return(None)
    
    def publishPost(self, args):
        logging.info("To publish %s" % args)
    
        update = ""
        profiles = self.profiles
        for profile in profiles: 
            logging.info("Social Network %s" % profile)
            if self.isForMe(profile, args):
                serviceName = profile['socialNetwork'][0].capitalize()
                j = int(args[-1])
                (title, link, firstLink, image, summary, summaryHtml, summaryLinks, content, links, comment) = (self.posts[serviceName]['pending'][j])
                publishMethod = getattr(moduleSocial, 
                        'publish'+ serviceName)
                logging.info("Publishing title: %s" % title)
                logging.info("Social network: %s Nick: %s" % (serviceName, nick))
                update = publishMethod(nick, title, link, summary, summaryHtml, summaryLinks, image, content, links)
                if not isinstance(update, str) or (isinstance(update, str) and update[:4] != "Fail"):
                    self.posts[serviceName]['pending'] = self.posts[serviceName]['pending'][:j] + posts[serviceName]['pending'][j+1:]
                    logging.info("Updating %s" % posts)
                    logging.info("Blog %s" % cache['blog'])
                    self.updatePostsCache(profile['socialNetwork'])
                    if 'text' in update:
                        update = update['text']
    
        return(update)
    
    def deletePost(self, args):
        logging.info("To Delete %s" % args)
    
        update = ""
        profiles = self.profiles
        for profile in profiles: 
            if self.isForMe(profile, args):
                serviceName = profile['socialNetwork'][0].capitalize()
                j = int(args[-1])
                logging.info("Posts %s" % posts[serviceName]['pending'])
                self.posts[serviceName]['pending'] = self.posts[serviceName]['pending'][:j] +  self.posts[serviceName]['pending'][j+1:]
                logging.info("-Posts %s" % posts[serviceName]['pending'])
                self.updatePostsCache(profile['socialNetwork'])
    
        return(update)
    
    def editPost(self, args, newTitle):
        logging.info("To edit %s" % args)
        logging.info("New title %s", newTitle)
    
        update = ""
        profiles = self.profiles
        title = None
        for profile in profiles: 
            logging.info("Social Network %s" % profile)
            if self.isForMe(profile, args):
                serviceName = profile['socialNetwork'][0].capitalize()
                j = int(args[-1])
                (title, link, firstLink, image, summary, summaryHtml, summaryLinks, content, links, comment) = (self.posts[serviceName]['pending'][j])
                self.posts[serviceName]['pending'][j] = (newTitle, link, firstLink, image, summary, summaryHtml, summaryLinks, content, links, comment) 
                print("--->",self.posts[serviceName]['pending'][j])
                print("--->",len(self.posts[serviceName]['pending'][j]))
    
                self.updatePostsCache(profile['socialNetwork'])
    
                return(newTitle+' '+link)
        return(None)
    
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
                    updatePostsCache(cache['blog'], posts[serviceName]['pending'], profile['socialNetwork'])
    
        return(posts[serviceName]['pending'][i][0]+' '+ 
                  posts[serviceName]['pending'][j][0])
    
    
    #######################################################
    # These need work
    #######################################################
    
    
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

    if ('bufferapp' in config.options(section)): 
        blog.setBufferapp(config.get(section, "bufferapp"))
    if ('program' in config.options(section)): 
        blog.setProgram(config.get(section, "program"))

    blog.setSocialNetworks(config, section)

    cache = moduleCache.moduleCache(blog.getUrl(), blog.getSocialNetworks())

    logging.basicConfig(#filename='example.log',
                            level=logging.DEBUG,format='%(asctime)s %(message)s')

    print("profiles")
    cache.getProfiles()
    print(cache.profiles)
    postsP, profiles = cache.listPosts('')
    print("-> Posts",postsP)
    for soc in cache.profiles:
        print(cache.checkLastLink(soc['socialNetwork']))
    print(cache.showPost(postsP, 'F1'))
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
