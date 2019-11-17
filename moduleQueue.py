# This module provides infrastructure for managing content in different 
# queues: local cache, buffer, Gmail, ... 

import configparser
import os
import logging
import re

class Queue:

    def __init__(self):
        self.name = None
        self.service = None
        self.nick = None
        self.socialNetwork = None
        self.posts = None
        self.postsFormatted = None

    def getProfiles(self):
        if not self.profiles:
            self.setProfiles()
        return(self.profiles)
 
    def getPosts(self):        
        return(self.posts)

    def getPostsFormatted(self):    
        return(self.postsFormatted)

    def lenMax(self): 
        return(len(self.getPosts()))

    def reorderTitle(self, oldTitle):            
        p = re.compile('\w')
        newTitle = ''
        for word in oldTitle.split():
            if not p.search(word):
                word = ' '+word+' '
                newTitle = word.join(oldTitle.split(word)[::-1])
                break
        if not newTitle:
            newTitle = oldTitle
        return(newTitle)


    def obtainPostData(self, i, debug=False):
        return (self.extractDataMessage(i))

    def selectAndExecute(self, command, args):
        logging.info("Selecting %s" % args)
        print("Selecting %s" % args)
        argsCont = ''
        pos = args.find(' ')
        if pos > 0: 
            argsIni = args[:pos]
            argsCont = args[pos+1:]
        else: 
            argsIni = args
        reply = ""
        if True: #self.isForMe(argsIni):
            logging.info("Service %s", self.service)
            j = int(argsIni[-1]) 
            cmd = getattr(self, command)
            logging.info("Command %s %d"% (command, j))
            if argsCont:
                reply = reply + cmd(j, argsCont)
            else: 
                reply = reply + cmd(j)
        else:
            logging.info("Not for me")
        logging.info("Reply: %s"%reply)
        return(reply)

    def show(self, j):
        if j < len(self.getPosts()):
            logging.info("To show post %d" % j)

            (title, link, firstLink, image, summary, summaryHtml, summaryLinks, content, links, comment) = self.obtainPostData(j)

            reply = ''
            logging.info("title %s"%title)
            if title and link:
                reply = reply + title + ' ' + link
            elif link:
                reply = reply +' '+link 
            elif title:
                reply = reply +' '+title 
        else:
            reply = ''

        return(reply)

    
    #######################################################
    # These need work
    #######################################################
    
    def movePost(self, args):
        # Moving posts, we identify the profile by the first letter. We can use
        # several letters and if we put a '*' we'll move the posts in all the
        # social networks
        logging.info("To move %s to %s" % (toMove,toWhere))
    
        i = 0
        profMov = ""
        return(args)
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
           
            if (serviceName[0] in profCop):
                for j in range(len(profiles)): 
                    serviceName = profiles[j].formatted_service 
                    if (serviceName[0] in profWhe):
                        profiles[j].updates.new(urllib.parse.quote(update.text + " " + link).encode('utf-8'))
    

