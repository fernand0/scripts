#!/usr/bin/env python
# encoding: utf-8

# This module tries to replicate moduleCache and moduleBuffer but with mails
# stored as Drafts in a Gmail account

import configparser, os
import pickle
from bs4 import BeautifulSoup
import logging
import importlib
import pprint
import time
import sys
import urllib
importlib.reload(sys)
#sys.setdefaultencoding("UTF-8")
import moduleSocial
import moduleHtml

import googleapiclient
from googleapiclient.discovery import build
from googleapiclient import http
from httplib2 import Http
from oauth2client import file, client, tools

import io

import base64
import email
from email.parser import BytesParser

from configMod import *

class moduleGmail():

    def __init__(self):
        self.service = None
        self.posts = None

    def API(self, Acc, pp):
        # based on get_credentials from 
        # Code from
        # https://developers.google.com/gmail/api/v1/reference/users/messages/list
        # and
        # http://stackoverflow.com/questions/30742943/create-a-desktop-application-using-gmail-api
    
        SCOPES = 'https://www.googleapis.com/auth/gmail.modify'
        api = {}
    
        config = configparser.ConfigParser() 
        config.read(CONFIGDIR + '/.oauthG.cfg')
        
        fileStore = self.confName((config.get(Acc,'server'), 
            config.get(Acc,'user'))) 
    
        logging.debug("Filestore %s"% fileStore)
        store = file.Storage(fileStore)
        credentials = store.get()
        
    
        service = build('gmail', 'v1', http=credentials.authorize(Http()))
    
        self.service = service
    
    def setPosts(self):
        api = self.service
        self.posts = api.users().drafts().list(userId='me').execute()

    def getPosts(self):
        if not self.posts:
            self.setPosts()
        return(self.posts)

    def getMessage(self, id): 
        api = self.service
        message = api.users().drafts().get(userId="me", 
                id=id).execute()['message']
        return message


    def getHeader(self, message, header = 'Subject'):
        for head in message['payload']['headers']: 
            if head['name'] == header: 
                return(head['value'])

    def getBody(self, message):
        return(message['payload']['parts'])
 

    def getLabelId(self, name):
        api = self.service
        results = api.users().labels().list(userId='me').execute() 
        for label in results['labels']: 
            if label['name'] == name: 
                labelId = label['id'] 
                break
    
        return(labelId)

    def obtainPostData(self, i, debug=False):
        api = self.service

        if not self.posts:
            self.setPosts()

        posts = []
        logging.info(self.getPosts()['drafts'])
        for post in self.getPosts()['drafts']:
            posts.insert(0, post)

        if not posts:
            return (None, None, None, None, None, None, None, None, None, None)

        post = posts[i]
        message = self.getMessage(post['id'])

        theTitle = self.getHeader(message, 'Subject')
        snippet = self.getHeader(message, 'snippet')
        parts = self.getBody(message)
        theLink = None
        posIni = message['snippet'].find('http')
        posFin = message['snippet'].find(' ', posIni)
        posSignature = message['snippet'].find('-- ')
        if posIni < posSignature: 
            theLink = message['snippet'][posIni:posFin]
        for part in parts:
            if 'data' in part['body']:
                partD = base64.b64decode(part['body']['data']) 
                html = moduleHtml.moduleHtml()
                
                theLinks = html.listLinks(partD)
            else:
                theLinks = None
        firstLink = theLink
        theImage = None
        theSummary = snippet
        content = parts[0]


        theSummaryLinks = None
        theContent = content
        comment = message['id']

        return (theTitle, theLink, firstLink, theImage, theSummary, content, theSummaryLinks, theContent, theLinks, comment)

  
    def moveMessage(self,  message):
        api = self.service
        labelId = self.getLabelId('imported')
        mesGE = base64.urlsafe_b64encode(message).decode()
        mesT = email.message_from_bytes(message)
        subj = email.header.decode_header(mesT['subject'])[0][0]
        logging.info("Subject %s",subj)
    
        try:
            messageR = api.users().messages().import_(userId='me',
                      fields='id',
                      neverMarkSpam=True,
                      processForCalendar=False,
                      internalDateSource='dateHeader',
                      body={'raw': mesGE}).execute(num_retries=5)
           #           media_body=media).execute(num_retries=1)
        except: 
            # When the message is too big
            # https://github.com/google/import-mailbox-to-gmail/blob/master/import-mailbox-to-gmail.py
    
            logging.info("Fail 1! Trying another method.")
            if True:
                mesGS = BytesParser().parsebytes(message).as_string()
                media =  googleapiclient.http.MediaIoBaseUpload(io.StringIO(mesGS), mimetype='message/rfc822')
                logging.info("vamos method")
                messageR = api.users().messages().import_(userId='me',
                          fields='id',
                          neverMarkSpam=True,
                          processForCalendar=False,
                          internalDateSource='dateHeader',
                          body={},
                          media_body=media).execute(num_retries=3)
                logging.info("messageR method")
            else: 
                logging.info("Error with message %s" % message) 
                return("Fail 2!")
        msg_labels = {'removeLabelIds': [], 'addLabelIds': ['UNREAD', labelId]}
    
        messageR = api.users().messages().modify(userId='me', id=messageR['id'],
                                                            body=msg_labels).execute()
    
        return(messageR)
    
    def getPostsCache(self):        
        api = self.service
        drafts = self.getPosts()
        if drafts:
            if 'drafts' in drafts:
                drafts = drafts['drafts']
            else:
                drafts = []
    
        listP = []
        numDrafts = len(drafts)
        for draft in range(numDrafts): 
            message = self.obtainPostData(draft)
            listP.append(message)
    
        return(listP)
    
    def listPosts(self, pp, service=""):    
        api = self.service
        outputData = {}
        files = []
    
        serviceName = 'Mail'+service
    
        outputData[serviceName] = {'sent': [], 'pending': []}
        listDrafts = self.getPostsCache()
    
        logging.debug("-Posts %s"% listDrafts)
    
        if len(listDrafts) > 0: 
            for element in listDrafts: 
                outputData[serviceName]['pending'].append(element) 
    
        #logging.info("Service posts profiles %s" % profiles)
        profiles = None
        return(outputData, profiles)
    
    def confName(self, acc):
        api = self.service
        theName = os.path.expanduser(CONFIGDIR + '/' 
                        + '.' + acc[0]+ '_' 
                        + acc[1]+ '.json')
        return(theName)
    
    def showPost(self, pp, posts, toPublish):
        logging.info("To publish %s" % pp.pformat(toPublish))
    
        profMov = toPublish[0]
        j = toPublish[1]
        logging.info("Profile %s position %d" % (profMov, j))
    
        update = ""
        title = None
        accC = 0
        (title, link, firstLink, image, summary, summaryHtml, summaryLinks, content, links, comment) = self.obtainPostData(j)
    
        if title: 
            if link: 
                return(title+link)
            else:
                return(title)
        else:
            return(None)
    
    
    def publishPost(self, pp, posts, toPublish):
        logging.info("To publish %s" % pp.pformat(toPublish))
    
        profMov = toPublish[0]
        j = toPublish[1]
        logging.info("Profile %s position %d" % (profMov, j))
    
        update = ""
        accC = 0
        (title, link, firstLink, image, summary, summaryHtml, summaryLinks, content, links, comment) = self.obtainPostData(j)
        publishMethod = getattr(moduleSocial, 
                'publishMail')
        logging.info("Publishing title: %s" % title)
 
        logging.info(title, link, summary, summaryHtml, summaryLinks, image, content , links )
        update = publishMethod(profile, title, link, summary, summaryHtml, summaryLinks, image, content, links)
        if update:
            if 'text' in update: 
                update = update['text'] 
   
        return(update)
    
    def deletePost(self, cache, pp, posts, toPublish):
        logging.info("To publish %s" % pp.pformat(toPublish))
        logging.info(pp.pformat(toPublish))
    
        profMov = toPublish[0]
        j = toPublish[1]
    
        update = ""
        accC = 0
        (title, link, firstLink, image, summary, summaryHtml, summaryLinks, content, links, comment) = self.obtainPostData(j)

        idPost = comment

        update = profile.users().drafts().delete(userId='me', id=idPost).execute()
        return(update)
    
    #######################################################
    # These need work
    #######################################################
    
    
    def copyPost(self, log, pp, profiles, toCopy, toWhere):
        api = self.service
        logging.info(pp.pformat(toCopy+' '+toWhere))
    
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
    
    def movePost(self, log, pp, profiles, toMove, toWhere):
        # Moving posts, we identify the profile by the first letter. We can use
        # several letters and if we put a '*' we'll move the posts in all the
        # social networks
        api = self.service
        i = 0
        profMov = ""
        while toMove[i].isalpha():
            profMov = profMov + toMove[i]
            i = i + 1
    
        for i in range(len(profiles)):
            serviceName = profiles[i].formatted_service
            log.info("ii: %s" %i)
            if (serviceName[0] in profMov) or toMove[0]=='*':
                listIds = []
                for j in range(len(profiles[i].updates.pending)):
                    # counts seems to be not ok
                    listIds.append(profiles[i].updates.pending[j]['id'])
    
                logging.info("to Move %s to %s" % (pp.pformat(toMove), toWhere))
                j = int(toMove[-1])
                logging.info("i %d j %d"  % (i,j))
                logging.info("Profiles[i]--> %s <--"  % pp.pformat(profiles))
                logging.info("Profiles[i]--> %s <---"  % pp.pformat(profiles[i].updates.pending[j]))
                k = int(toWhere[-1])
                idUpdate = listIds.pop(j)
                listIds.insert(k, idUpdate)
    
                update = Update(api=api, id=profiles[i].updates.pending[j].id)
                profiles[i].updates.reorder(listIds)
    
    def listSentPosts(self, pp, service=""):
        api = self.service
        profiles = getProfiles(api, pp, service)
    
        someSent = False
        outputStr = ([],[])
        for i in range(len(profiles)):
            serviceName = profiles[i].formatted_service
            logging.debug("Service %d %s" % (i,serviceName))
            if (profiles[i].counts['sent'] > 0):
                someSent = True
                logging.info("Service %s" % serviceName)
                logging.debug("There are: %d" % profiles[i].counts['sent'])
                logging.debug(pp.pformat(profiles[i].updates.sent))
                due_time=""
                for j in range(min(8,profiles[i].counts['sent'])):
                    updatesSent = profiles[i].updates.sent[j]
                    update = Update(api=api, id= updatesSent.id)
                    if (due_time == ""):
                        due_time=update.due_time # Not used here
                        outputStr[0].append("*%s*" % serviceName)
                        outputStr[1].append("")
                    logging.debug("Service %s" % pp.pformat(updatesSent))
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
    import moduleGmail

    pp = pprint.PrettyPrinter(indent=4)

    # instantiate the api object 

    api = moduleGmail.moduleGmail()
    api.API('ACC2',pp)

    logging.basicConfig(#filename='example.log',
                            level=logging.DEBUG,format='%(asctime)s %(message)s')

    #print("profiles")
    #print(api.service.users().getProfile(userId='me').execute())
    postsP, profiles = api.listPosts(pp, '')
    print("-> Posts",postsP)
    print(api.obtainPostData(0))
    sys.exit()
    msg = 353
    moveMessage(api[1], msg)

    #publishPost(api, pp, postsP, ('G',1))
    #deletePost(api, pp, postsP, ('M0',0))
    #sys.exit()

    publishPost(api, pp, profiles, ('F',1))

    posts.update(postsP)
    print("-> Posts",posts)
    #print("Posts",profiles)
    print("Keys",posts.keys())
    print(pp.pformat(profiles))
    print("Pending",type(profiles))
    print(pp.pformat(profiles))
    profiles = listSentPosts(api, pp, "")
    print("Sent",type(profiles))
    print(pp.pformat(profiles))
    print(type(profiles[1]),pp.pformat(profiles[1]))


    if profiles:
       toPublish, toWhere = input("Which one do you want to publish? ").split(' ')
       #publishPost(api, pp, profiles, toPublish)


if __name__ == '__main__':
    main()
