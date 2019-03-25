# This module provides infrastructure for managing content in different 
# queues: local cache, buffer, Gmail, ... 

import configparser
import os
import logging

class Queue:

    def __init__(self):
        self.name = None
        self.service = None
        self.socialNetwork = None
        self.profiles = None
        self.posts = None
        self.postsFormatted = None
        self.lenMax = -1

    def getProfiles(self):
        if not self.profiles:
            self.setProfiles()
        return(self.profiles)
 
    def getPosts(self):        
        return(self.posts)

    def getPostsFormatted(self):    
        return(self.postsFormatted)

    
    def showPost(self, args):
        #return(self.interpretAndExecute(args,'show'))
        logging.info("To show %s" % args)

        go = self.isForMe(args)
        if go:
            j = int(args[-1])
            if self.socialNetwork:
                serviceName = 'Cache_'+self.socialNetwork[0]+'_'+self.socialNetwork[1] #self.name.capitalize()
            else:
                serviceName = go
            logging.debug(self.postsFormatted)
            (title, link, firstLink, image, summary, summaryHtml, summaryLinks, content, links, comment) = (self.obtainPostData(j))
            if title:
                return(title+' '+link)
            else:
                return("")
        return("")

    def editPost(self, args, newTitle):
        #return(self.interpretAndExecute(args,'edit', newTitle))
        logging.info("To edit %s" % args)
        logging.info("New title %s", newTitle)
    
        udpate = None
        go = self.isForMe(args)
        if go:
            j = int(args[-1])

            (title, link, firstLink, image, summary, summaryHtml, summaryLinks, content, links, comment) = (self.obtainPostData(j))

            if self.socialNetwork: 
                serviceName = 'Cache_'+self.socialNetwork[0]+'_'+self.socialNetwork[1]
                self.postsFormatted[serviceName]['pending'][j] = (newTitle, link, firstLink, image, summary, summaryHtml, summaryLinks, content, links, comment) 
                self.updatePostsCache()
            else:
                serviceName = go
                profiles = self.getProfiles()
                i = self.service[serviceName]
                from buffpy.models.update import Update
                update = Update(api=self.api, id=profiles[i].updates.pending[j].id) 
                update = update.edit(text=newTitle)

            update = "Changed "+title+" with "+newTitle
        else:
            update = ""

        return(update)   
    
    def publishPost(self, args):
        #return(self.interpretAndExecute(args,'publish'))
        logging.info("To publish %s" % args)
    
        udpate = None
        go = self.isForMe(args)
        if go:
            j = int(args[-1])
            if self.socialNetwork: 
                nick = self.socialNetwork[1]
                serviceName = 'Cache_'+self.socialNetwork[0]+'_'+self.socialNetwork[1]
            else:
                serviceName = go

            (title, link, firstLink, image, summary, summaryHtml, summaryLinks, content, links, comment) = (self.postsFormatted[serviceName]['pending'][j])
            if self.socialNetwork: 
                import importlib
                mod = importlib.import_module('module'+self.socialNetwork[0].capitalize()) 
                cls = getattr(mod, 'module'+self.socialNetwork[0].capitalize())
                api = cls()
                api.setClient(nick)
                update = api.publishPost(title, link, comment)
                print(update)
                #publishMethod = getattr(moduleSocial, 
                #        'publish'+ self.socialNetwork[0].capitalize())
                logging.info("Publishing title: %s" % title)
                logging.info("Social network: %s Nick: %s" % (serviceName, nick))
                #update = publishMethod(nick, title, link, summary, summaryHtml, summaryLinks, image, content, links)
                if not isinstance(update, str) or (isinstance(update, str) and update[:4] != "Fail"):
                    self.postsFormatted[serviceName]['pending'] = self.postsFormatted[serviceName]['pending'][:j] + self.postsFormatted[serviceName]['pending'][j+1:]
                    logging.debug("Updating %s" % self.postsFormatted)
                    #logging.info("Blog %s" % cache['blog'])
                    self.updatePostsCache()
                    logging.info("UUpdate ... %s" % str(update))
                    if 'text' in update:
                        update = update['text']
                    if type(update) == tuple:
                        update = update[1]['id']
                        # link: https://www.facebook.com/[name]/posts/[second part of id]
            else:
                profiles = self.getProfiles()
                i = self.service[serviceName]
                from buffpy.models.update import Update
                update = Update(api=self.api, id=profiles[i].updates.pending[j].id) 
                update = update.publish()

            logging.info("Update before return", update)
    
            return(update)
        return ""
    
    def deletePost(self, args):
        #return(self.interpretAndExecute(args,'delete'))
        logging.info("To Delete %s" % args)
    
        udpate = ""
        if self.isForMe(args):
            j = int(args[-1])
            serviceName = 'Cache_'+self.socialNetwork[0]+'_'+self.socialNetwork[1] #self.name.capitalize()
            (title, link, firstLink, image, summary, summaryHtml, summaryLinks, content, links, comment) = (self.postsFormatted[serviceName]['pending'][j])
            update = "Deleted: "+ title
            logging.debug("Posts %s" % self.postsFormatted[serviceName]['pending'])
            self.postsFormatted[serviceName]['pending'] = self.postsFormatted[serviceName]['pending'][:j] + self.postsFormatted[serviceName]['pending'][j+1:]
            logging.debug("-Posts %s" % self.postsFormatted[serviceName]['pending'])
            logging.info("social network %s - %s" 
                    % (self.socialNetwork[0], self.socialNetwork[1]))
            self.updatePostsCache()
            return(update)
    
        return("")
    

    
   
    
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
    

