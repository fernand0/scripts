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

    def createLabel(self, labelName):
        api = self.getClient()
        label_object = {'messageListVisibility': 'show', 
                'name': labelName, 'labelListVisibility': 'labelShow'}
        return(api.users().labels().create(userId='me', 
                body=label_object).execute())

    def setLabels(self):
        api = self.getClient()
        response = api.users().labels().list(userId='me').execute()
        if 'labels' in response:
            self.labels = response['labels']

    def getLabels(self, sel=''):
        return(list(filter(lambda x: sel in x['name'] ,self.labels)))

    def getLabelsIds(self, sel=''):
        labels = (list(filter(lambda x: sel in x['name'] ,self.labels)))
        return (list(map(lambda x: x['id'], labels)))

    def getPosts(self):
        return(self.posts)

    def setPosts(self, label='drafts', mode=''):
        logging.info("  Setting posts")
        api = self.getClient()

        self.posts = []
        if label == 'drafts':
            typePosts = 'drafts'
            posts = api.users().drafts().list(userId='me').execute()
        else:
            typePosts = 'messages'
            posts = api.users().messages().list(userId='me',labelIds=label).execute()

        logging.debug("--setPosts %s" % posts)

        if typePosts in posts:
           self.rawPosts = []
           for post in posts[typePosts]: 
               if mode != 'raw':
                   meta = self.getMessageMeta(post['id'],typePosts)
                   message = {}
                   message['list'] = post
                   message['meta'] = meta
                   self.posts.insert(0, message)
               else:
                   raw = self.getMessageRaw(post['id'],typePosts)
                   message = {}
                   message['list'] = post
                   message['meta'] = ''
                   message['raw'] = raw
                   self.posts.insert(0, message)

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

    def getMessageRaw(self, msgId, typePost='drafts'): 
        api = self.getClient()
        if typePost == 'drafts': 
            message = api.users().drafts().get(userId="me", 
                id=msgId, format='raw').execute()['message']
        else:
            message = api.users().messages().get(userId="me", 
                id=msgId, format='raw').execute()

        return message

    def getMessageMeta(self, msgId, typePost='drafts'): 
        api = self.getClient()
        if typePost == 'drafts': 
            message = api.users().drafts().get(userId="me", 
                id=msgId, format='metadata').execute()['message']
        else:
            message = api.users().messages().get(userId="me", 
                id=msgId, format='metadata').execute()
        return message

    def setHeader(self, message, header, value):
        for head in message['payload']['headers']: 
            if head['name'].capitalize() == header.capitalize(): 
                head['value'] = value

    def setHeaderEmail(self, message, header, value):
        # Email methods are related to the email.message objetcs
        if header in message:
            del message[header]
            message[header]= value

    def getHeader(self, message, header = 'Subject'):
        if 'meta' in message:
            message = message['meta']
        for head in message['payload']['headers']: 
            if head['name'].capitalize() == header.capitalize(): 
                return(head['value'])

    def getPostId(self, message):
        if 'list' in message:
            message = message['meta']
        return(message['id'])

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
        labelId = None
        for label in results: 
            if label['name'] == name: 
                labelId = label['id'] 
                break
    
        return(labelId)

    def extractDataMessage(self, i):
        logging.info("Service %s"% self.service)
        message = self.getPosts()[i]
        logging.info("Message %s"% message)

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
        comment = self.getPostId(message) 

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

    def editl(self, j, newTitle):
        return('Not implemented!')

    def edit(self, j, newTitle):
        logging.info("New title %s", newTitle)
        thePost = self.obtainPostData(j)
        oldTitle = thePost[0]
        logging.info("servicename %s" %self.service)

        import base64
        import email
        from email.parser import BytesParser
        api = self.getClient()

        idPost = self.getPosts()[j]['list']['id'] #thePost[-1]
        title = self.getHeader(self.getPosts()[j]['meta'], 'Subject')
        message = self.getMessageRaw(idPost)
        theMsg = email.message_from_bytes(base64.urlsafe_b64decode(message['raw']))
        self.setHeaderEmail(theMsg, 'subject', newTitle)
        message['raw'] = theMsg.as_bytes()
        message['raw'] = base64.urlsafe_b64encode(message['raw']).decode()

        update = api.users().drafts().update(userId='me', 
            body={'message':message},id=idPost).execute()


        logging.info("Update %s" % update)
        update = "Changed "+title+" with "+newTitle
        return(update)

    def publish(self, j):
        logging.info("Publishing %d"% j)                
        logging.info("servicename %s" %self.service)
        idPost = self.getPosts()[j]['list']['id'] #thePost[-1]
        title = self.getHeader(self.getPosts()[j]['meta'], 'Subject')
        
        api = self.getClient()
        try:
            res = api.users().drafts().send(userId='me', 
                       body={ 'id': idPost}).execute()
            logging.info("Res: %s" % res)
        except:
            return(self.report('Gmail', idPost, '', sys.exc_info()))

        return("%s"% title)

    def trash(self, j, typePost='drafts'):
        logging.info("Trashing %d"% j)

        api = self.getClient()
        idPost = self.getPosts()[j]['list']['id'] #thePost[-1]
        try: 
            title = self.getHeader(self.getPosts()[j]['meta'], 'Subject')
        except:
            title = ''
        if typePost == 'drafts': 
            update = api.users().drafts().trash(userId='me', id=idPost).execute() 
        else:
            update = api.users().messages().trash(userId='me', id=idPost).execute() 
 
        return("Trashed %s"% title)
 
    def delete(self, j, typePost='drafts'):
        logging.info("Deleting %d"% j)

        api = self.getClient()
        idPost = self.getPosts()[j]['list']['id'] #thePost[-1]
        try: 
            title = self.getHeader(self.getPosts()[j]['meta'], 'Subject')
        except:
            title = ''
        if typePost == 'drafts': 
            update = api.users().drafts().delete(userId='me', id=idPost).execute() 
        else:
            update = api.users().messages().delete(userId='me', id=idPost).execute() 
 
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

    def copyMessage(self,  message, labels =''):
        api = self.getClient()
        labelIdName = 'importedd'
        labelId = self.getLabelId(labelIdName)
        if not labelId:
            labelId = self.createLabel(labelIdName)
        labelIds = [labelId]
        labelIdsNames = [labelIdName]
        if labels:
            for label in labels: 
                print("label %s"%label)
                labelId = self.getLabelId(label)
                if not labelId: 
                    labelId = self.createLabel(label)
                labelIds.append(labelId)
                labelIdsNames.append(label)

        if not isinstance(message,dict):
            mesGE = base64.urlsafe_b64encode(message).decode()
            mesT = email.message_from_bytes(message)
            if mesT['subject']: 
                subj = email.header.decode_header(mesT['subject'])[0][0]
            else:
                subj = ""
            logging.info("Subject %s",subj)
        else:
            if 'raw' in message: 
                mesGE = message['raw']
    
        try:
            messageR = api.users().messages().import_(userId='me',
                      fields='id',
                      neverMarkSpam=False,
                      processForCalendar=False,
                      internalDateSource='dateHeader',
                      body={'raw': mesGE}).execute(num_retries=5)
           #           media_body=media).execute(num_retries=1)
        except: 
           # When the message is too big
           # https://github.com/google/import-mailbox-to-gmail/blob/master/import-mailbox-to-gmail.py
    
           logging.info("Fail 1! Trying another method.")
           try: 
               if not isinstance(message,dict): 
                   mesGS = BytesParser().parsebytes(message).as_string()
                   media =  googleapiclient.http.MediaIoBaseUpload(io.StringIO(mesGS), mimetype='message/rfc822')
                   logging.info("vamos method")
               else:
                    media = message
               #print(media)
                 
               messageR = api.users().messages().import_(userId='me',
                           fields='id',
                           neverMarkSpam=False,
                           processForCalendar=False,
                           internalDateSource='dateHeader',
                           body={},
                           media_body=media).execute(num_retries=3)
               logging.info("messageR method")
           except: 
               logging.info("Error with message %s" % message) 
               return("Fail 2!")

        msg_labels = {'removeLabelIds': [], 'addLabelIds': ['UNREAD', labelId]}
        msg_labels = {'removeLabelIds': [], 'addLabelIds': labelIds }# ['UNREAD', labelId]}
    
        messageR = api.users().messages().modify(userId='me',
                id=messageR['id'], body=msg_labels).execute()
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
    sys.exit()
    print('G29', api.selectAndExecute('publish', 'G29'))
    print('G29', api.selectAndExecute('delete', 'G29'))
    print('G25', api.selectAndExecute('edit', 'G27'+' '+'Cebollinos (hechos)'))
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
    copyMessage(api[1], msg)

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
