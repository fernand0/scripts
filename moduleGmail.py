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
import moduleImap

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
        self.rawPosts = None
        self.name = "Mail"
        self.profile = None

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

        self.name = self.name + Acc[3:]
        #self.profile = self.service.users().getProfile(userId='me').execute()

    def confName(self, acc):
        api = self.service
        theName = os.path.expanduser(CONFIGDIR + '/' 
                        + '.' + acc[0]+ '_' 
                        + acc[1]+ '.json')
        return(theName)
    
    def setPosts(self):
        api = self.service
        posts = api.users().drafts().list(userId='me').execute()
        logging.info("--setPosts %s" % posts)
        if 'drafts' in posts:
            self.posts = []
            self.rawPosts = []
            for post in posts['drafts']:
                self.posts.insert(0, post)
                message = self.getMessageRaw(post['id'])
                self.rawPosts.insert(0, message)

    def getPosts(self):
        self.setPosts()
        return(self.rawPosts)

    def getMessage(self, id): 
        api = self.service
        message = api.users().drafts().get(userId="me", 
                id=id).execute()['message']
        return message

    def getMessageRaw(self, id): 
        api = self.service
        message = api.users().drafts().get(userId="me", 
                id=id, format='raw').execute()['message']
        return message

    def getMessageMeta(self, id): 
        api = self.service
        message = api.users().drafts().get(userId="me", 
                id=id, format='metadata').execute()['message']
        return message

    def setHeader(self, message, header, value):
        for head in message['payload']['headers']: 
            if head['name'] == header: 
                head['value'] = value

    def setHeaderEmail(self, message, header, value):
        # Email methods are related to the email.message objetcs
        if header in message:
            del message[header]
            message[header]= value

    def getHeader(self, message, header = 'Subject'):
        for head in message['payload']['headers']: 
            if head['name'] == header: 
                return(head['value'])

    def getHeaderEmail(self, message, header = 'Subject'):
        if header in message:
            return(moduleImap.headerToString(message[header]))

    def getHeaderRaw(self, message, header = 'Subject'):
        if header in message:
            return(message[header])

    def getEmail(self, messageRaw):
        messageEmail = email.message_from_bytes(base64.urlsafe_b64decode(messageRaw['raw']))
        return(messageEmail)


    def getBody(self, message):
        return(message['payload']['parts'])
 
    def getLabelList(self):
        api = self.service
        results = api.users().labels().list(userId='me').execute() 
        return(results['labels'])

    def getLabelId(self, name):
        api = self.service
        results = self.getLabelList() 
        for label in results: 
            if label['name'] == name: 
                labelId = label['id'] 
                break
    
        return(labelId)

    def obtainPostData(self, i, debug=False):
        api = self.service

        if not self.posts:
            self.setPosts()

        if not self.rawPosts or (i>=(len(self.rawPosts))):
            return (None, None, None, None, None, None, None, None, None, None)

        messageRaw = self.rawPosts[i]
        messageEmail = self.getEmail(messageRaw)

        theTitle = self.getHeaderEmail(messageEmail, 'Subject')
        snippet = self.getHeaderRaw(messageRaw, 'snippet')

        theLink = None
        posIni = snippet.find('http')
        posFin = snippet.find(' ', posIni)
        posSignature = snippet.find('-- ')
        if posIni < posSignature: 
            theLink = snippet[posIni:posFin]
        theLinks = None
        for part in messageEmail.walk():
            if part.get_content_type() == 'text/html':
                content = part.get_payload()
                html = moduleHtml.moduleHtml()
                theLinks = html.listLinks(content)
            elif part.get_content_type() == 'text/plain':
                theContent = part
        firstLink = theLink
        theImage = None
        theSummary = snippet

        theSummaryLinks = messageRaw
        comment = self.posts[i]['id']

        return (theTitle, theLink, firstLink, theImage, theSummary, content, theSummaryLinks, theContent, theLinks, comment)

    def getPostsCache(self):        
        api = self.service
        drafts = self.getPosts()
    
        listP = []
        if drafts:
            numDrafts = len(drafts)
            for draft in range(numDrafts): 
                message = self.obtainPostData(draft)
                print(message)
                listP.append(message)
    
        return(listP)
    
    def listPosts(self, pp):    
        api = self.service
        outputData = {}
        files = []
    
        serviceName = self.name
    
        outputData[serviceName] = {'sent': [], 'pending': []}
        listDrafts = self.getPostsCache()
    
        if listDrafts:
            logging.debug("--Posts %s"% listDrafts)
    
            for element in listDrafts: 
                    outputData[serviceName]['pending'].append(element) 
    
        #logging.info("Service posts profiles %s" % profiles)
        profiles = None
        return(outputData, profiles)
    
    def isForMe(self, args):
        serviceName = self.name
        if (serviceName[0] in args) or ('*' in args): 
            if serviceName[0] + self.name[-1] in args[:-1]:
                return True
        return False

    def showPost(self, pp, posts, args):
        logging.info("To publish %s" % args)
    
        update = ""
        serviceName = self.name

        title = None
        if self.isForMe(args):
            (title, link, firstLink, image, summary, summaryHtml, summaryLinks, content, links, comment) = self.obtainPostData(int(args[-1]))
    
            if title: 
                if link: 
                    return(title+link)
                else:
                    return(title)
        return(None)
    
    def publishPost(self, pp, posts, args):
        logging.info("To publish %s" % args)
    
        update = ""
        serviceName = self.name
        title = None

        if self.isForMe(args):
            (title, link, firstLink, image, summary, summaryHtml, summaryLinks, content, links, comment) = self.obtainPostData(int(args[-1]))
            if title:
                publishMethod = getattr(moduleSocial, 
                        'publishMail')
                logging.info("Publishing title: %s" % title)
 
                logging.info(title, link, summary, summaryHtml, summaryLinks, image, content , links )
                logging.info(publishMethod)
                update = publishMethod(self, title, link, summary, summaryHtml, summaryLinks, image, content, comment)
                if update:
                    if 'text' in update: 
                        update = update['text'] 
   
                return(update)

        return(None)
    
    def deletePost(self, cache, pp, posts, args):
        logging.info("To delete %s" % args)
    
        update = ""
        serviceName = self.name
        title = None
        if self.isForMe(args):
            (title, link, firstLink, image, summary, summaryHtml, summaryLinks, content, links, comment) = self.obtainPostData(int(args[-1]))

            if title:
                idPost = comment

                update = self.service.users().drafts().delete(userId='me', id=idPost).execute()
                return(update)

        return(None)

    def editPost(self, pp, posts, args, newTitle):
        logging.info("To edit %s" % args)
        logging.info("New title %s", newTitle)

        update = ""
        serviceName = self.name
        if self.isForMe(args):
            (title, link, firstLink, image, summary, summaryHtml, summaryLinks, content, links, comment) = self.obtainPostData(int(args[-1]))
            # Should we avoid two readings?
            message = summaryLinks 
            #self.service.users().drafts().get(userId="me", 
            #    format="raw", id=comment).execute()['message']
            theMsg = email.message_from_bytes(base64.urlsafe_b64decode(message['raw']))
            self.setHeaderEmail(theMsg, 'subject', newTitle)
            message['raw'] = theMsg.as_bytes()
            message['raw'] = base64.urlsafe_b64encode(message['raw']).decode()

            update = self.service.users().drafts().update(userId='me', 
                    body={'message':message},id=comment).execute()

            return(newTitle)

        return None

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

   
    #######################################################
    # These need work
    #######################################################
    

    def listSentPosts(self, pp, service=""):
        # Undefined
        pass
    
    def copyPost(self, log, pp, profiles, toCopy, toWhere):
        # Undefined
        pass
    
    def movePost(self, log, pp, profiles, toMove, toWhere):
        # Undefined
        pass
    

def main():
    import moduleGmail

    pp = pprint.PrettyPrinter(indent=4)

    # instantiate the api object 

    api = moduleGmail.moduleGmail()
    api.API('ACC1',pp)
    api.setPosts()
    api.getPostsCache()
    api.editPost(pp, api.getPosts(), "M17", 'Prueba.')
    sys.exit()

    logging.basicConfig(#filename='example.log',
                            level=logging.DEBUG,format='%(asctime)s %(message)s')

    print("profiles")
    print(api.profile)
    postsP, profiles = api.listPosts(pp)
    print("-> Posts",postsP)
    sys.exit()
    api.editPost(pp, api.getPosts(), "M11", 'No avanza.')
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
