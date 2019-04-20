# This module provides infrastructure for managing content in different 
# queues: local cache, buffer, Gmail, ... 

import configparser
import os
import logging

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
        if self.isForMe(argsIni):
            logging.info("Service %s", self.service)
            print("Service %s"% self.service)
            j = int(argsIni[-1]) 
            cmd = getattr(self, command)
            if argsCont:
                reply = reply + cmd(j, argsCont)
            else: 
                reply = reply + cmd(j)
        logging.info("Reply: %s"%reply)
        return(reply)

    def show(self, j):
        logging.info("To show post %d" % j)

        (title, link, firstLink, image, summary, summaryHtml, summaryLinks, content, links, comment) = self.obtainPostData(j)

        reply = ''
        if title and link:
            reply = reply + title + ' ' + link
        elif link:
            reply = reply +' '+link 
        elif title:
            reply = reply +' '+title 

        return(reply)

    def editPost(self, args, newTitle):
        #return(self.interpretAndExecute(args,'edit', newTitle))
        logging.info("To edit %s" % args)
        logging.info("New title %s", newTitle)
        logging.info("New name %s", self.name)
        return()
    
        udpate = None
        services = self.isForMe(args)
        j = int(args[-1])
        for serviceName in services:
            (title, link, firstLink, image, summary, summaryHtml, summaryLinks, content, links, comment) = (self.obtainPostData(serviceName, j))

            if 'Cache' in serviceName: 
                self.postsFormatted[serviceName]['pending'][j] = (newTitle, link, firstLink, image, summary, summaryHtml, summaryLinks, content, links, comment) 
                self.updatePostsCache(serviceName)
            elif 'Mail' in serviceName:
                import base64
                import email
                from email.parser import BytesParser
                api = self.getClient()
                message = api.users().drafts().get(userId="me", 
                   format="raw", id=comment).execute()['message']
                theMsg = email.message_from_bytes(base64.urlsafe_b64decode(message['raw']))
                self.setHeaderEmail(theMsg, 'subject', newTitle)
                message['raw'] = theMsg.as_bytes()
                message['raw'] = base64.urlsafe_b64encode(message['raw']).decode()

                update = api.users().drafts().update(userId='me', 
                    body={'message':message},id=comment).execute()

            else:
                pass
        else:
            update = ""

        return(update)   
    
    def publishPost(self, args):
        #return(self.interpretAndExecute(args,'publish'))
        logging.info("To publish %s" % args)
    
        udpate = None
        services = self.isForMe(args)
        j = int(args[-1])
        for serviceName in services:
            (title, link, firstLink, image, summary, summaryHtml, summaryLinks, content, links, comment) = (self.obtainPostData(serviceName, j))
            if 'Cache' in serviceName: 
                import importlib
                service = self.profiles[self.service[serviceName]]['service']
                service = service.capitalize()
                nick = self.profiles[self.service[serviceName]]['service_username']
                mod = importlib.import_module('module'+service) 
                cls = getattr(mod, 'module'+service)
                api = cls()
                api.setClient(nick)
                comment = ''
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
                    self.updatePostsCache(serviceName)
                    logging.info("UUpdate ... %s" % str(update))
                    if 'text' in update:
                        update = update['text']
                    if type(update) == tuple:
                        update = update[1]['id']
                        # link: https://www.facebook.com/[name]/posts/[second part of id]
            elif 'Mail' in serviceName:
                import moduleSocial
                publishMethod = getattr(moduleSocial, 
                        'publishMail')
                logging.debug(title, link, summary, summaryHtml, summaryLinks, image, content , links )
                logging.info(title, link, content , links )
                logging.info(publishMethod)
                logging.info("com %s" % comment)
                update = publishMethod(self, title, link, summary, summaryHtml, summaryLinks, image, content, comment)
                if update:
                    if 'text' in update: 
                        update = update['text'] 
   
                    return(update)

                return(None)
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
        services = self.isForMe(args)
        j = int(args[-1])
        for serviceName in services:
            (title, link, firstLink, image, summary, summaryHtml, summaryLinks, content, links, comment) = (self.postsFormatted[serviceName]['pending'][j])
            update = "Deleted: "+ title
            logging.debug("Posts %s" % self.postsFormatted[serviceName]['pending'])
            if 'Cache' in serviceName: 
                self.postsFormatted[serviceName]['pending'] = self.postsFormatted[serviceName]['pending'][:j] + self.postsFormatted[serviceName]['pending'][j+1:]
                self.updatePostsCache(serviceName)
            elif 'Mail' in serviceName:
                api = self.getClient()
                idPost = comment
                update = api.users().drafts().delete(userId='me', id=idPost).execute() 
            else:
                profiles = self.getProfiles()
                if serviceName in self.service:
                    i = self.service[serviceName]
                    from buffpy.models.update import Update
                    update = Update(api=self.api, id=profiles[i].updates.pending[j].id) 
                    update.detele()

            logging.debug("-Posts %s" % self.postsFormatted[serviceName]['pending'])
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
    

