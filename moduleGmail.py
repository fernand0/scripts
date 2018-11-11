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
import moduleBlog
import moduleSocial

from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools

from configMod import *

def API(pp):
    # based on get_credentials from 
    # Code from
    # https://developers.google.com/gmail/api/v1/reference/users/messages/list
    # and
    # http://stackoverflow.com/questions/30742943/create-a-desktop-application-using-gmail-api

    SCOPES = 'https://www.googleapis.com/auth/gmail.modify'
    api = {}
    #conf = configparser.ConfigParser() 
    #logging.info("Config...%s" % CONFIGDIR)
    credential_dir = CONFIGDIR
    store = file.Storage(credential_dir+'/token.json')
    credentials = store.get()

    service = build('gmail', 'v1', http=credentials.authorize(Http()))

    return(service)

def getPostsCache(api):        
    drafts = api.users().drafts().list(userId='me').execute()
    drafts = drafts['drafts']

    listP = []
    for draft in drafts: 
        message = api.users().drafts().get(userId="me", id=draft['id']).execute()
        listP.insert(0,message)

    return(listP)

def listPosts(api, pp, service=""):    
    outputData = {}
    files = []

    serviceName = 'Mail'

    outputData[serviceName] = {'sent': [], 'pending': []}
    listDrafts = getPostsCache(api)

    listP = []
    for draft in listDrafts: 
        for header in draft['message']['payload']['headers']: 
            if header['name'] == 'Subject': 
                listP.append((header['value'], '', '', '', '', '', '', '', listDrafts[0]['id'], ''))


    logging.info("-Posts %s"% listP)

    if len(listP) > 0: 
        for element in listP: 
            outputData[serviceName]['pending'].append(element) 

    #logging.info("Service posts profiles %s" % profiles)
    profiles = None
    return(outputData, profiles)

# Pending work \/ \/ \/ \/

def updatePostsCache(blog, listPosts, socialNetwork=()):
    fileNameQ = fileName(blog,socialNetwork) + ".queue" 

    logging.info("Updating Posts Cache: %s" % fileNameQ)
    print("Updating Posts Cache: %s" % fileNameQ)

    with open(fileNameQ, 'wb') as f:
         pickle.dump(listPosts,f)
    return(fileNameQ)

def publishPost(cache, pp, posts, toPublish):
    logging.info("To publish %s" % pp.pformat(toPublish))

    profMov = toPublish[0]
    j = toPublish[1]

    update = ""
    logging.info("Cache antes %s" % pp.pformat(cache))
    profiles = ["Mail"] #cache['profiles']
    print(profiles)
    logging.info("Cache profiles antes %s" % pp.pformat(profiles))
    print("Cache profiles antes %s" % pp.pformat(profiles))
    for profile in profiles: 
        print(profile)
        logging.info("Social Network %s" % profile)
        #if 'socialNetwork' in profile:
        serviceName = profile[0].capitalize()
        #nick = profile['socialNetwork'][1]
        if (serviceName[0] in profMov) or toPublish[0]=='*': 
            logging.info("In %s" % pp.pformat(serviceName))
            logging.info("Profile %s" % pp.pformat(profile))
            logging.info("Profile posts %s" % pp.pformat(posts))
            logging.info("Service name %s" % serviceName)
            numPosts = len(posts[profile]['pending'])
            # We have reordered the posts for the presentation
            # Maybe we could improve this
            j = numPosts - (j + 1)
            (title, link, firstLink, image, summary, summaryHtml, summaryLinks, content, links, comment) = (posts[profile]['pending'][j])
            print(title, link, firstLink, image, summary, summaryHtml, summaryLinks, content, links, comment) 
            publishMethod = getattr(moduleSocial, 
                    'publish'+ profile)
            logging.info("Publishing title: %s" % title)
            logging.info("Social network: %s Nick: (pending)"  % profile)
            logging.info(cache, title, link, summary, summaryHtml, summaryLinks, image, content , links )
            update = publishMethod(cache, title, link, summary, summaryHtml, summaryLinks, image, content, links)
            if not isinstance(update, str) or (isinstance(update, str) and update[:4] != "Fail"):
                posts[profile]['pending'] = posts[profile]['pending'][:j] + posts[profile]['pending'][j+1:]
                logging.info("Updating %s" % pp.pformat(posts))
                logging.info("Blog %s" % pp.pformat(cache['blog']))
                #updatePostsCache(cache['blog'], posts[profile]['pending'], profile['socialNetwork'])
                if 'text' in update:
                    update = update['text']

    return(update)


#######################################################
# These need work
#######################################################

def deletePost(cache, pp, posts, toPublish):
    logging.info("To publish %s" % pp.pformat(toPublish))
    logging.info(pp.pformat(toPublish))

    profMov = toPublish[0]
    j = toPublish[1]

    update = ""
    logging.info("Cache antes %s" % pp.pformat(cache))
    profiles = cache['profiles']
    logging.info("Cache profiles antes %s" % pp.pformat(profiles))
    for profile in profiles: 
        if 'socialNetwork' in profile:
            serviceName = profile['socialNetwork'][0].capitalize()
            if (serviceName[0] in profMov) or toPublish[0]=='*': 
                logging.info("In %s" % pp.pformat(serviceName))
                logging.info("Profile %s" % pp.pformat(profile))
                logging.info("Profile posts %s" % pp.pformat(posts))
                posts[serviceName]['pending'] = posts[serviceName]['pending'][:j] +  posts[serviceName]['pending'][j+1:]
                logging.info("Profile posts after %s" % pp.pformat(posts))
                updatePostsCache(cache['blog'], posts[serviceName]['pending'], profile['socialNetwork'])
    return(update)

def copyPost(api, log, pp, profiles, toCopy, toWhere):
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

def movePost(api, log, pp, profiles, toMove, toWhere):
    # Moving posts, we identify the profile by the first letter. We can use
    # several letters and if we put a '*' we'll move the posts in all the
    # social networks
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

def listSentPosts(api, pp, service=""):
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
    pp = pprint.PrettyPrinter(indent=4)

    # instantiate the api object 
    api = API(pp)

    logging.basicConfig(#filename='example.log',
                            level=logging.DEBUG,format='%(asctime)s %(message)s')


    print("profiles")
    print(api)
    postsP, profiles = listPosts(api, pp, '')
    print("-> Posts",postsP)
    publishPost(api, pp, postsP, ('G',1))
    sys.exit()

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
