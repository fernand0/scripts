#!/usr/bin/env python
# encoding: utf-8

# This module tries to replicate moduleCache and moduleBuffer but with mails
# stored as Drafts in a Gmail account

import configparser, os
import logging
import importlib
import sys
#importlib.reload(sys)
#sys.setdefaultencoding("UTF-8")
import moduleSocial
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
from moduleContent import *
from moduleQueue import *

class moduleGmail(Content,Queue):

    def __init__(self):
        Content().__init__()
        Queue().__init__()
        self.service = None
        self.nick = None

    def API(self, Acc):
        # Back compatibility
        self.setClient(Acc)

    def setClient(self, Acc):
        # based on get_credentials from 
        # Code from
        # https://developers.google.com/gmail/api/v1/reference/users/messages/list
        # and
        # http://stackoverflow.com/questions/30742943/create-a-desktop-application-using-gmail-api
    
        SCOPES = 'https://www.googleapis.com/auth/gmail.modify'
        self.url = SCOPES
        api = {}
    
        config = configparser.ConfigParser() 
        config.read(CONFIGDIR + '/.oauthG.cfg')
        
        self.service = 'gmail'
        self.nick = config.get(Acc,'user')+'@'+config.get(Acc,'server')
        fileStore = self.confName((config.get(Acc,'server'), 
            config.get(Acc,'user'))) 
    
        logging.debug("Filestore %s"% fileStore)
        store = file.Storage(fileStore)
        credentials = store.get()
        
        service = build('gmail', 'v1', http=credentials.authorize(Http()))
    
        self.client = service
        self.name = 'GMail' + Acc[3:]

    def getClient(self):
        return(self.client)

    def getPosts(self):
        return(self.posts)

    def setPosts(self):
        logging.info("  Setting posts")
        api = self.getClient()

        posts = api.users().drafts().list(userId='me').execute()
        logging.debug("--setPosts %s" % posts)
        if 'drafts' in posts:
            self.posts = []
            self.rawPosts = []
            for post in posts['drafts']:
                self.rawPosts.insert(0, post)
                message = self.getMessageMeta(post['id'])
                self.posts.insert(0, message)

        #outputData = {}
        #files = []

        #serviceName = self.name

        #outputData[serviceName] = {'sent': [], 'pending': []}

        #listDrafts=self.getPosts()

        #if listDrafts:
        #    logging.debug("--Posts %s"% listDrafts)
    
        #    for i in range(len(listDrafts)):
        #        # Which elements to include?
        #        outputData[serviceName]['pending'].append(self.extractDataMessage(i))
        #        i = i + 1

        #self.postsFormatted = outputData
 
    def confName(self, acc):
        theName = os.path.expanduser(CONFIGDIR + '/' + '.' 
                + acc[0]+ '_' 
                + acc[1]+ '.json')
        return(theName)
    
    def getMessage(self, id): 
        api = self.getClient()
        message = api.users().drafts().get(userId="me", 
                id=id).execute()['message']
        return message

    def getMessageRaw(self, id): 
        api = self.getClient()
        message = api.users().drafts().get(userId="me", 
                id=id, format='raw').execute()['message']
        return message

    def getMessageMeta(self, id): 
        api = self.getClient()
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
        api = self.getClient()
        results = api.users().labels().list(userId='me').execute() 
        return(results['labels'])

    def getLabelId(self, name):
        api = self.getClient()
        results = self.getLabelList() 
        for label in results: 
            if label['name'] == name: 
                labelId = label['id'] 
                break
    
        return(labelId)

    def extractDataMessage(self, i):
        logging.info("Service %s"% self.service)
        message = self.getPosts()[i]

        theTitle = self.getHeader(message, 'Subject')
        if theTitle == None:
            theTitle = self.getHeader(message, 'subject')
        snippet = self.getHeader(message, 'snippet')

        theLink = None
        if snippet:
            posIni = snippet.find('http')
            posFin = snippet.find(' ', posIni)
            posSignature = snippet.find('-- ')
            if posIni < posSignature: 
                theLink = snippet[posIni:posFin]
        theLinks = None
        content = None
        theContent = None
        firstLink = theLink
        theImage = None
        theSummary = snippet

        theSummaryLinks = message
        comment = message['id'] 

        return (theTitle, theLink, firstLink, theImage, theSummary, content, theSummaryLinks, theContent, theLinks, comment)

    def isForMe(self, args):
        serviceName = self.name
        lookAt = []
        logging.info("Args %s" % args)
        logging.info("Name %s" % serviceName)
        if (serviceName[0] in args) or ('*' in args): 
            if serviceName[0] + serviceName[-1] in args[:-1]:
                lookAt.append(serviceName)
        return lookAt

    def edit(self, j, newTitle):
        logging.info("New title %s", newTitle)

        import base64
        import email
        from email.parser import BytesParser
        api = self.getClient()
        (title, link, firstLink, image, summary, summaryHtml, summaryLinks, image, content , comment) = self.getPosts()[j]
        idPost = comment
        print(title,idPost)
        sys.exit()
        message = api.users().drafts().get(userId="me", 
           format="raw", id=idPost).execute()['message']
        theMsg = email.message_from_bytes(base64.urlsafe_b64decode(message['raw']))
        self.setHeaderEmail(theMsg, 'subject', newTitle)
        message['raw'] = theMsg.as_bytes()
        message['raw'] = base64.urlsafe_b64encode(message['raw']).decode()

        update = api.users().drafts().update(userId='me', 
            body={'message':message},id=idPost).execute()


        logging.info("Update %s" % update)
        update = "Changed "+title+" with "+newTitle
        return(update)

    def publish(self, post, j):
        logging.info("Publishing", post[1])                
        
        import moduleSocial
        publishMethod = getattr(moduleSocial, 
                'publishMail')
        print(len(post[1:]))
        (title, link, firstLink, image, summary, summaryHtml, summaryLinks, image, content , links ) = post[1:]

        logging.debug(title, link, summary, summaryHtml, summaryLinks, image, content , links )
        logging.info(title, link, content , links )
        logging.info(publishMethod)
        comment = links

        update = publishMethod(self, title, link, summary, summaryHtml, summaryLinks, image, content, comment)
        if update:
            if 'text' in update: 
                update = update['text'] 
        else:
            update = ""
   
        return(update)

    def delete(self, post, j):
        logging.info("Publishing", post[1])
        serviceName = post[0]                

        api = self.getClient()
        (title, link, firstLink, image, summary, summaryHtml, summaryLinks, image, content , comment) = post[1:]
        idPost = comment
        #print(title, link, firstLink, image, summary, summaryHtml, summaryLinks, image, content , comment)
        update = api.users().drafts().delete(userId='me', id=idPost).execute() 
 
        return("Deleted %s"% title)
 
    #def showPost(self, pp, posts, args):
    #    logging.info("To publish %s" % args)
    #
    #    update = ""
    #    serviceName = self.name

    #    title = None
    #    if self.isForMe(args):
    #        (title, link, firstLink, image, summary, summaryHtml, summaryLinks, content, links, comment) = self.obtainPostData(int(args[-1]))
    #
    #        if title: 
    #            if link: 
    #                return(title+link)
    #            else:
    #                return(title)
    #    return(None)
    #
    #def publishPost(self, args):
    #    logging.info("To publish %s" % args)
    #
    #    update = ""
    #    serviceName = self.name
    #    title = None

    #    if self.isForMe(args):
    #        (title, link, firstLink, image, summary, summaryHtml, summaryLinks, content, links, comment) = self.obtainPostData(int(args[-1]))
    #        logging.info("Ttitle %s" % title)
    #        if title:
    #            publishMethod = getattr(moduleSocial, 
    #                    'publishMail')
 
    #            logging.debug(title, link, summary, summaryHtml, summaryLinks, image, content , links )
    #            logging.info(title, link, content , links )
    #            logging.info(publishMethod)
    #            logging.info("com %s" % comment)
    #            update = publishMethod(self, title, link, summary, summaryHtml, summaryLinks, image, content, comment)
    #            if update:
    #                if 'text' in update: 
    #                    update = update['text'] 
   
    #            return(update)

    #    return(None)
    #
    #def deletePost(self, cache, pp, posts, args):
    #    api = self.getClient()
    #    logging.info("To delete %s" % args)
    #
    #    update = ""
    #    serviceName = self.name
    #    logging.info("In %s" % serviceName)
    #    title = None
    #    if self.isForMe(args):
    #        (title, link, firstLink, image, summary, summaryHtml, summaryLinks, content, links, comment) = self.obtainPostData(int(args[-1]))

    #        if title or comment:
    #            #What happens if the title is empty?
    #            idPost = comment

    #            update = api.users().drafts().delete(userId='me', id=idPost).execute()
    #            return(update)

    #    return(None)

    #def editPost(self, pp, posts, args, newTitle):
    #    api = self.getClient()
    #    logging.info("To edit %s" % args)
    #    logging.info("New title %s", newTitle)

    #    update = ""
    #    serviceName = self.name
    #    if self.isForMe(args):
    #        (title, link, firstLink, image, summary, summaryHtml, summaryLinks, content, links, comment) = self.obtainPostData(int(args[-1]))
    #        # Should we avoid two readings?
    #        #message = summaryLinks 
    #        message = api.users().drafts().get(userId="me", 
    #               format="raw", id=comment).execute()['message']
    #        theMsg = email.message_from_bytes(base64.urlsafe_b64decode(message['raw']))
    #        self.setHeaderEmail(theMsg, 'subject', newTitle)
    #        message['raw'] = theMsg.as_bytes()
    #        message['raw'] = base64.urlsafe_b64encode(message['raw']).decode()

    #        update = api.users().drafts().update(userId='me', 
    #                body={'message':message},id=comment).execute()

    #        return(newTitle)

    #    return None

    #def moveMessage(self,  message):
    #    api = self.getClient()
    #    labelId = self.getLabelId('imported')
    #    mesGE = base64.urlsafe_b64encode(message).decode()
    #    mesT = email.message_from_bytes(message)
    #    if mesT['subject']: 
    #        subj = email.header.decode_header(mesT['subject'])[0][0]
    #    else:
    #        subj = ""
    #    logging.info("Subject %s",subj)
    #
    #    try:
    #        messageR = api.users().messages().import_(userId='me',
    #                  fields='id',
    #                  neverMarkSpam=False,
    #                  processForCalendar=False,
    #                  internalDateSource='dateHeader',
    #                  body={'raw': mesGE}).execute(num_retries=5)
    #       #           media_body=media).execute(num_retries=1)
    #    except: 
    #        # When the message is too big
    #        # https://github.com/google/import-mailbox-to-gmail/blob/master/import-mailbox-to-gmail.py
    #
    #        logging.info("Fail 1! Trying another method.")
    #        if True:
    #            mesGS = BytesParser().parsebytes(message).as_string()
    #            media =  googleapiclient.http.MediaIoBaseUpload(io.StringIO(mesGS), mimetype='message/rfc822')
    #            logging.info("vamos method")
    #            messageR = api.users().messages().import_(userId='me',
    #                      fields='id',
    #                      neverMarkSpam=False,
    #                      processForCalendar=False,
    #                      internalDateSource='dateHeader',
    #                      body={},
    #                      media_body=media).execute(num_retries=3)
    #            logging.info("messageR method")
    #        else: 
    #            logging.info("Error with message %s" % message) 
    #            return("Fail 2!")
    #    msg_labels = {'removeLabelIds': [], 'addLabelIds': ['UNREAD', labelId]}
    #
    #    messageR = api.users().messages().modify(userId='me', id=messageR['id'],
    #                                                        body=msg_labels).execute()
    #
    #    return(messageR)

   
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

    # instantiate the api object 

    api = moduleGmail.moduleGmail()
    api.setClient('ACC2')
    api.setPosts()
    print(api.getPosts())
    print(api.getPosts()[0])
    print(len(api.getPosts()[0]))
    # It has 8 elements
    print(api.obtainPostData(0))
    print('G21', api.selectAndExecute('show', 'G21'))
    print('G23', api.selectAndExecute('show', 'G23'))
    print('G05', api.selectAndExecute('show', 'G05'))
    print('G25', api.selectAndExecute('edit', 'G25'+' '+'baba'))
    sys.exit()
    print('M15', api.selectAndExecute('delete', 'M15'))
    print('M10', api.selectAndExecute('publish', 'M10'))
    print('M18', api.editPost('M18', 'Vaya'))
    print('M10', api.publishPost('M10'))
    sys.exit()
    api.editPost(pp, api.getPosts(), "M17", 'Prueba.')

    logging.basicConfig(#filename='example.log',
                            level=logging.DEBUG,format='%(asctime)s %(message)s')

    print("profiles")
    print(api.profile)
    #postsP, profiles = api.listPosts(pp)
    print("-> Posts",postsP)
    print(apil.getPostsFormatted())
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
