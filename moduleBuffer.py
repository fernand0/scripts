#!/usr/bin/env python
# encoding: utf-8

#
# - This module comes from https://github.com/fernand0/err-buffer.git
#
# - The second one includes the secret data of the buffer app [~/.rssBuffer]
# [appKeys]
# client_id:XXXXXXXXXXXXXXXXXXXXXXXX
# client_secret:XXXXXXXXXXXXXXXXXXXXXXXXXXXxXXXX
# redirect_uri:XXXXXXXXXXXXXXXXXXXXXXXXX
# access_token:XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
# 
# These data can be obtained registering an app in the bufferapp site.
# Follow instructions at:
# https://bufferapp.com/developers/api
# 
# - The third one contains the last published URL [~/.rssBuffer.last]
# It contains just an URL which is the last one published. 
# At this moment it only considers one blog
# 
# We are adding now the ability to read a local queue. It is stored in the
# following way:
#
# Queue files name is composed of a dot, followed by the path of the URL,
# followed by the name of the social network and the name of the user for
# posting there.
# The filename ends in .queue
# For example:
#    .my.blog.com_twitter_myUser.queue
# This file stores a list of pending posts stored as an array of posts as
# returned by moduleBlog
# (https://github.com/fernand0/scripts/blob/master/moduleBlog.py)
#  obtainPostData method.
# For the moment, it will read the filenames from
#  .rssProgram
# One file at each line


import configparser, os
import logging
import time
import sys
import urllib
import importlib
importlib.reload(sys)
#sys.setdefaultencoding("UTF-8")

# sudo pip install buffpy version does not work
# Better use:
# git clone https://github.com/vtemian/buffpy.git
# cd buffpy
# sudo python setup.py install
from colorama import Fore
import buffpy
from buffpy.models.update import Update
from buffpy.managers.profiles import Profiles
from buffpy.managers.updates import Updates


# We can put as many items as the service with most items allow
# The limit is ten.
# Get all pending updates of a social network profile

#[{'_Profile__schedules': None, u'formatted_service': u'Twitter', u'cover_photo': u'https://pbs.twimg.com/profile_banners/62983/1355263933', u'verb': u'tweet', u'formatted_username': u'@fernand0', u'shortener': {u'domain': u'buff.ly'}, u'timezone': u'Europe/Madrid', u'counts': {u'daily_suggestions': 25, u'pending': 0, u'sent': 10862, u'drafts': 0}, u'service_username': u'fernand0', u'id': u'4ed35f97512f7ebb5d00000b', u'disconnected': False, u'statistics': {u'followers': 5736}, u'user_id': u'4ed35f8e512f7e325e000001', u'avatar_https': u'https://pbs.twimg.com/profile_images/487165212391256066/DFRGycds_normal.jpeg', u'service': u'twitter', u'default': True, u'schedules': [{u'days': [u'mon', u'tue', u'wed', u'thu', u'fri', u'sat', u'sun'], u'times': [u'09:10', u'09:45', u'10:09', u'10:34', u'11:10', u'11:45', u'12:07', u'13:29', u'15:15', u'16:07', u'16:42', u'17:07', u'17:40', u'18:10', u'18:33', u'19:05', u'19:22', u'20:15', u'21:30', u'22:45', u'23:10', u'23:25', u'23:45']}], u'reports_logo': None, 'api': <buffpy.api.API object at 0x7f4f1a8508d0>, u'avatar': u'http://pbs.twimg.com/profile_images/487165212391256066/DFRGycds_normal.jpeg', u'service_type': u'profile', u'service_id': u'62983', u'_id': u'4ed35f97512f7ebb5d00000b', u'utm_tracking': u'enabled', u'disabled_features': []}, {'_Profile__schedules': None, u'formatted_service': u'LinkedIn', u'cover_photo': u'https://d3ijcis4e2ziok.cloudfront.net/default-cover-photos/blurry-blue-background-iii_facebook_timeline_cover.jpg', u'verb': u'post', u'timezone_city': u'Madrid - Spain', u'formatted_username': u'Fernando Tricas', u'shortener': {u'domain': u'buff.ly'}, u'timezone': u'Europe/Madrid', u'counts': {u'daily_suggestions': 25, u'pending': 0, u'sent': 4827, u'drafts': 0}, u'service_username': u'Fernando Tricas', u'id': u'4f4606ec512f7e0766000003', u'disconnected': False, u'statistics': {u'connections': 500}, u'user_id': u'4ed35f8e512f7e325e000001', u'avatar_https': u'https://media.licdn.com/mpr/mprx/0_zVbmG3KX1MsA8cT9vyLgGCt5Ay0Aucl9BjPAGC1ZaMIhPPQnMpBCuGbn0-xffrKVqJ5KDLD_G-D1', u'service': u'linkedin', u'default': True, u'schedules': [{u'days': [u'mon', u'tue', u'wed', u'thu', u'fri', u'sat', u'sun'], u'times': [u'01:46', u'05:52', u'07:13', u'08:54', u'09:27', u'10:13', u'10:49', u'11:58', u'12:03', u'12:03', u'12:41', u'13:05', u'15:23', u'16:35', u'16:57', u'17:23', u'18:02', u'18:37', u'19:58', u'20:17', u'21:13', u'22:00', u'23:05', u'23:07', u'23:49']}], u'reports_logo': None, 'api': <buffpy.api.API object at 0x7f4f1a8508d0>, u'avatar': u'https://media.licdn.com/mpr/mprx/0_zVbmG3KX1MsA8cT9vyLgGCt5Ay0Aucl9BjPAGC1ZaMIhPPQnMpBCuGbn0-xffrKVqJ5KDLD_G-D1', u'service_type': u'profile', u'service_id': u'x4Eu0cqIhj', u'_id': u'4f4606ec512f7e0766000003', u'utm_tracking': u'enabled', u'disabled_features': []}, {'_Profile__schedules': None, u'formatted_service': u'Facebook', u'cover_photo': u'https://scontent.xx.fbcdn.net/hphotos-xfp1/t31.0-8/s720x720/904264_10151421662663264_1461180243_o.jpg', u'verb': u'post', u'timezone_city': u'Zaragoza - Spain', u'formatted_username': u'Fernando Tricas', u'shortener': {u'domain': u'buff.ly'}, u'timezone': u'Europe/Madrid', u'counts': {u'pending': 0, u'sent': 5971, u'drafts': 0}, u'service_username': u'Fernando Tricas', u'id': u'5241b3f0351ff0a83500001b', u'disconnected': False, u'user_id': u'4ed35f8e512f7e325e000001', u'avatar_https': u'https://scontent.xx.fbcdn.net/hprofile-xpf1/v/t1.0-1/c0.0.50.50/p50x50/10500300_10152337396498264_6509296623992251600_n.jpg?oh=1870d57d20aa70388bed86f1383051f2&oe=578BF216', u'service': u'facebook', u'default': True, u'schedules': [{u'days': [u'mon', u'tue', u'wed', u'thu', u'fri', u'sat', u'sun'], u'times': [u'00:58', u'07:53', u'09:06', u'09:44', u'10:03', u'10:30', u'11:07', u'11:37', u'12:16', u'13:04', u'13:40', u'16:02', u'16:32', u'16:51', u'17:18', u'17:38', u'18:03', u'18:44', u'19:14', u'23:02', u'23:41']}], u'reports_logo': None, 'api': <buffpy.api.API object at 0x7f4f1a8508d0>, u'avatar': u'https://scontent.xx.fbcdn.net/hprofile-xpf1/v/t1.0-1/c0.0.50.50/p50x50/10500300_10152337396498264_6509296623992251600_n.jpg?oh=1870d57d20aa70388bed86f1383051f2&oe=578BF216', u'service_type': u'profile', u'service_id': u'503403263', u'_id': u'5241b3f0351ff0a83500001b', u'utm_tracking': u'enabled', u'disabled_features': []}, {'_Profile__schedules': None, u'formatted_service': u'Google+ Page', u'cover_photo': u'https://d3ijcis4e2ziok.cloudfront.net/default-cover-photos/blurry-blue-background-iii_facebook_timeline_cover.jpg', u'verb': u'post', u'formatted_username': u'Reflexiones e Irreflexiones', u'shortener': {u'domain': u'buff.ly'}, u'timezone': u'Europe/London', u'counts': {u'daily_suggestions': 25, u'pending': 0, u'sent': 0, u'drafts': 0}, u'service_username': u'Reflexiones e Irreflexiones', u'id': u'521f6df14ddfcbc91600004a', u'disconnected': False, u'user_id': u'4ed35f8e512f7e325e000001', u'avatar_https': u'https://lh6.googleusercontent.com/-yAIEsEEQ220/AAAAAAAAAAI/AAAAAAAAAC8/Q8K1Li_kZSY/photo.jpg?sz=50', u'service': u'google', u'default': False, u'schedules': [{u'days': [u'mon', u'tue', u'wed', u'thu', u'fri', u'sat', u'sun'], u'times': [u'10:50', u'17:48']}], u'reports_logo': None, 'api': <buffpy.api.API object at 0x7f4f1a8508d0>, u'avatar': u'https://lh6.googleusercontent.com/-yAIEsEEQ220/AAAAAAAAAAI/AAAAAAAAAC8/Q8K1Li_kZSY/photo.jpg?sz=50', u'service_type': u'page', u'service_id': u'117187804556943229940', u'_id': u'521f6df14ddfcbc91600004a', u'utm_tracking': u'enabled', u'disabled_features': []}]

from configMod import *
from moduleQueue import *

class moduleBuffer(Queue):

    def __init__(self): #, url, socialNetwork, nick):
        super().__init__()
        self.service = None
        self.nick = None
        #self.buffer = None
        self.profiles = None
        #self.url = url
        #self.socialNetwork = (socialNetwork, nick)

    def setClient(self, url, socialNetwork):
        config = configparser.ConfigParser()
        logging.debug("Config...%s" % CONFIGDIR)
        config.read(CONFIGDIR + '/.rssBuffer')
    
        clientId = config.get("appKeys", "client_id")
        clientSecret = config.get("appKeys", "client_secret")
        redirectUrl = config.get("appKeys", "redirect_uri")
        accessToken = config.get("appKeys", "access_token")
        
        # instantiate the api object 
        api = buffpy.api.API(client_id=clientId,
                  client_secret=clientSecret,
                  access_token=accessToken)
    
        self.client = api

        self.url = url
        self.service = socialNetwork[0]
        self.nick = socialNetwork[1]

    #def setBuffer(self):
    #    config = configparser.ConfigParser()
    #    logging.debug("Config...%s" % CONFIGDIR)
    #    config.read(CONFIGDIR + '/.rssBuffer')
    #
    #    clientId = config.get("appKeys", "client_id")
    #    clientSecret = config.get("appKeys", "client_secret")
    #    redirectUrl = config.get("appKeys", "redirect_uri")
    #    accessToken = config.get("appKeys", "access_token")
    #    
    #    # instantiate the api object 
    #    api = buffpy.api.API(client_id=clientId,
    #              client_secret=clientSecret,
    #              access_token=accessToken)
    #
    #    self.api = api

    def setProfile(self, service=""):
        logging.info("  Checking services...")
        
        if (service == ""):
            logging.info("  All available in Buffer")
            profiles = Profiles(api=self.client).all()
        else:
            logging.info("  Profile %s" % service)
            profiles = Profiles(api=self.client).filter(service=service)
            
        logging.debug("Profiles %s" % profiles)

        self.profile = profiles[0]

    def getProfile(self):
        return(self.profile)

    def setPosts(self):
        self.setProfile(self.service)
        profile = self.getProfile()
        logging.info("Profile %s" % profile)
    
        #serviceName = profile['service']
        #nickName = profile['service_username']
        #bufferName = 'Buffer_' + serviceName + '_' + nickName
        #self.service[bufferName] = i
        #i = i + 1
    
        #logging.info("   Service %s" % serviceName)
    
        #outputData[bufferName] = {'sent': [], 'pending': []}
        for method in ['sent', 'pending']:
            if (profile.counts[method] > 0):
                updates = getattr(profile.updates, method)
                if method == 'pending': 
                    self.posts = updates
                else:
                    self.posted = updates
            #    #for j in range(min(10,len(updates))):
            #    #    update = updates[j]
            #    #    if method == 'pending':
            #    #        toShow = update.due_time
            #    #    else:
            #    #        toShow = update.statistics.clicks
            #    #    if ('media' in update): 
            #    #        if ('expanded_link' in update.media):
            #    #            link = update.media.expanded_link
            #    #        else:
            #    #            link = update.media.link
            #    #    else:
            #    #        link = ''
            #    #    if update.text: 
            #    #        outputData[bufferName][method].append((update.text, link, toShow, '', '', '', '', '', '', ''))
            #    #    else:
            #    #        outputData[bufferName][method].append((link, link, toShow, '', '', '', '', '', '', ''))
            #else:
            #            outputData[bufferName][method].append(('Empty', 'Empty', 'Empty', '', '', '', '', '', '', ''))

        #self.lenMax[serviceName] = len(outputData[serviceName]['pending'])
    
        #self.postsFormatted = outputData

    def addPosts(self, listPosts):
        linkAdded = ''
        logging.info("    Adding posts to %s" % self.service)
        for post in listPosts: 
            (title, link) = post[:2] 
            textPost = title + " " + link
            logging.info("    Post: %s" % link)
            entry = urllib.parse.quote(textPost)
            try:
                if post[3]: 
                    print(post[3])
                    entry = urllib.parse.quote(post[0])
                    self.getProfile().updates.new(entry, 
                            media={'photo':post[3]})
                else: 
                    self.getProfile().updates.new(entry)
            except: 
                logging.warning("Buffer posting failed!") 
                logging.warning("Entry: %s"% entry) 
                logging.warning("Unexpected error: %s"% sys.exc_info()[0]) 
                logging.warning("Unexpected error: %s"% sys.exc_info()[1]) 
                return(linkAdded)
            linkAdded = link
                
            time.sleep(1)
        logging.info("    Added posts to LinkedIn")

        return(linkAdded)

    def extractDataMessage(self, i):
        logging.info("Service %s"% self.service)
        messageRaw = self.getPosts()[i]

        theTitle = messageRaw['text']
        theLink = ''
        content = ''
        if 'media' in messageRaw:
            if ('expanded_link' in messageRaw['media']):
                theLink = messageRaw['media']['expanded_link']
            else:
                theLlink = messageRaw['media']['link']
            if ('description' in messageRaw['media']): 
                content = messageRaw['media']['description']

        theLinks = None
        theContent = content
        firstLink = theLink
        theImage = None
        theSummary = content

        theSummaryLinks = content
        comment = None

        return (theTitle, theLink, firstLink, theImage, theSummary, content, theSummaryLinks, theContent, theLinks, comment)

    #def deletePost(self, profiles, args):
    #    api = self.buffer
    #    logging.info("To Delete %s" % args)
    #
    #    update = None
    #    for i in range(len(profiles)):
    #        serviceName = profiles[i].formatted_service
    #        if self.isForMe(serviceName, args):
    #            j = int(args[-1])
    #            update = Update(api=api, id=profiles[i].updates.pending[j].id)
    #            logging.debug(update)
    #            update.delete()
    #
    #    return(update)
    #
    #def copyPost(self, log, profiles, toCopy, toWhere):
    #    api = self.buffer
    #    logging.info(toCopy+' '+toWhere)
    #
    #    profCop = toCopy[0]
    #    ii = int(toCopy[1])
    #
    #    j = 0
    #    profWhe = ""
    #    i = 0
    #    while i < len(toWhere):
    #        profWhe = profWhe + toWhere[i]
    #        i = i + 1
    #    
    #    log.info(toCopy,"|",profCop, ii, profWhe)
    #    for i in range(len(profiles)):
    #        serviceName = profiles[i].formatted_service
    #        print(serviceName)
    #        log.info("ii: %s" %i)
    #        updates = getattr(profiles[j].updates, 'pending')
    #        update = updates[ii]
    #        if ('media' in update): 
    #            if ('expanded_link' in update.media):
    #                link = update.media.expanded_link
    #            else:
    #                link = update.media.link
    #        else:
    #            link = ""
    #        print(update.text, link)
    #       
    #        if (serviceName[0] in profCop):
    #            for j in range(len(profiles)): 
    #                serviceName = profiles[j].formatted_service 
    #                if (serviceName[0] in profWhe):
    #                    profiles[j].updates.new(urllib.parse.quote(update.text + " " + link).encode('utf-8'))
    #
    #def movePost(self, log, profiles, toMove, toWhere):
    #    # Moving posts, we identify the profile by the first letter. We can use
    #    # several letters and if we put a '*' we'll move the posts in all the
    #    # social networks
    #    api = self.buffer
    #    i = 0
    #    profMov = ""
    #    while toMove[i].isalpha():
    #        profMov = profMov + toMove[i]
    #        i = i + 1
    #
    #    for i in range(len(profiles)):
    #        serviceName = profiles[i].formatted_service
    #        log.info("ii: %s" %i)
    #        if (serviceName[0] in profMov) or toMove[0]=='*':
    #            listIds = []
    #            for j in range(len(profiles[i].updates.pending)):
    #                # counts seems to be not ok
    #                listIds.append(profiles[i].updates.pending[j]['id'])
    #
    #            logging.info("to Move %s to %s" % (toMove, toWhere))
    #            j = int(toMove[-1])
    #            logging.info("i %d j %d"  % (i,j))
    #            logging.info("Profiles[i]--> %s <--"  % profiles)
    #            logging.info("Profiles[i]--> %s <---"  % profiles[i].updates.pending[j])
    #            k = int(toWhere[-1])
    #            idUpdate = listIds.pop(j)
    #            listIds.insert(k, idUpdate)
    #
    #            update = Update(api=api, id=profiles[i].updates.pending[j].id)
    #            profiles[i].updates.reorder(listIds)
    #
    #def listSentPosts(self, service=""):
    #    api = self.buffer
    #    profiles = self.getProfiles(service)
    #
    #    someSent = False
    #    outputStr = ([],[])
    #    for i in range(len(profiles)):
    #        serviceName = profiles[i].formatted_service
    #        logging.debug("Service %d %s" % (i,serviceName))
    #        if (profiles[i].counts['sent'] > 0):
    #            someSent = True
    #            logging.debug(" Service %s" % serviceName)
    #            logging.debug("There are: %d" % profiles[i].counts['sent'])
    #            logging.debug(profiles[i].updates.sent)
    #            due_time=""
    #            for j in range(min(8,profiles[i].counts['sent'])):
    #                updatesSent = profiles[i].updates.sent[j]
    #                update = Update(api=api, id= updatesSent.id)
    #                if (due_time == ""):
    #                    due_time=update.due_time # Not used here
    #                    outputStr[0].append("*%s*" % serviceName)
    #                    outputStr[1].append("")
    #                logging.debug("Service %s" % updatesSent)
    #                selectionStr = "" #"%d%d) " % (i,j)
    #                if ('media' in updatesSent): 
    #                    try:
    #                        lineTxt = "%s %s %s" % (selectionStr, 
    #                                updatesSent.text, updatesSent.media.expanded_link)
    #                    except:
    #                        lineTxt = "%s %s %s" % (selectionStr,
    #                                updatesSent.text, updatesSent.media.link)
    #                else:
    #                    lineTxt = "%s %s" % (selectionStr,updatesSent.text)
    #                logging.info(lineTxt)
    #                outputStr[0].append("%s" % lineTxt)
    #                outputStr[1].append(" (%d clicks)" % updatesSent['statistics']['clicks'])
    #        else:
    #            logging.debug("No")
    #    
    #    if someSent:
    #        return (outputStr, profiles)
    #    else:
    #        logging.info("No sent posts")
    #        return someSent
    #
    #
    #def listPendingPosts(self, service=""):
    #    api = self.buffer
    #    profiles = self.getProfiles(service)
    #    
    #    somePending = False
    #    outputStr = [] 
    #    for i in range(len(profiles)):
    #        serviceName = profiles[i].formatted_service
    #        logging.debug("Service %d %s" % (i,serviceName))
    #        if (profiles[i].counts['pending'] > 0):
    #            somePending = True
    #            logging.info("Service %s" % serviceName)
    #            logging.debug("There are: %d" % profiles[i].counts['pending'])
    #            logging.debug(profiles[i].updates.pending)
    #            due_time=""
    #            for j in range(profiles[i].counts['pending']):
    #                updatesPending = profiles[i].updates.pending[j]
    #                update = Update(api=api, id=updatesPending.id)
    #                if (due_time == ""):
    #                    due_time=update.due_time
    #                    outputStr.append("*%s* ( %s )" % (serviceName, due_time))
    #
    #                logging.debug("Service %s" % updatesPending)
    #                selectionStr = "%d%d) " % (i,j)
    #                if ('media' in updatesPending): 
    #                    try:
    #                        lineTxt = "%s %s %s" % (selectionStr,
    #                                updatesPending.text, updatesPending.media.expanded_link)
    #                    except:
    #                        lineTxt = "%s %s %s" % (selectionStr,
    #                                updatesPending.text, updatesPending.media.link)
    #                else:
    #                    lineTxt = "%s %s" % (selectionStr,updatesPending.text)
    #                logging.info(lineTxt)
    #                outputStr.append(lineTxt)
    #                logging.debug("-- %s" % (update))
    #                logging.debug("-- %s" % (dir(update)))
    #        else:
    #            logging.debug("Service %d %s" % (i, serviceName))
    #            logging.debug("No")
    #    
    #    if somePending:
    #        return (outputStr, profiles)
    #    else:
    #        logging.info("No pending posts")
    #        return somePending

    def getTitle(self, i):
        if i < len(self.getPosts()): 
            post = self.getPosts()[i]
            title = post['media']['title']
            return (title)
        return(None)

    def getLink(self, i):
        if i < len(self.getPosts()): 
            post = self.getPosts()[i]
            link = post['media']['expanded_link']
            return (link)
        return(None) 
    
    def getPostTitle(self, post):
        logging.info(post)
        if post:
            title = post['media']['title']
            return (title)
        return(None)

    def getPostLink(self, post):
        if post:
            link = post['media']['expanded_link']
            return (link)
        return(None)

    def isForMe(self, args):
        profile = self.getProfile()
        return (profile['service'][0].capitalize() in args) or ('*' in args) 

    def edit(self, j, newTitle):
        logging.info("New title %s", newTitle)
        thePost = self.obtainPostData(j)
        oldTitle = thePost[0]
        profile = self.getProfile()
        logging.info("servicename %s" %self.service)
        from buffpy.models.update import Update
        i=0
        update = Update(api=self.client, id=profile.updates.pending[j].id) 
        print(update)
        update = update.edit(text=newTitle)

        title = oldTitle
        update = "Changed "+title+" with "+newTitle

        logging.info("Res update %s" % update)

        return(update)

    def publish(self, j):
        logging.info("Publishing %d"% j)
        sys.exit()
        post = self.obtainPostData(j)
        logging.info("Publishing %s"% post[0])
        profile = self.getProfile() 
        update = Update(api=self.client, id=profile.updates.pending[j].id) 
        update = update.publish()
        logging.info("Update before return %s"% update)
        return(update[0])
    
    def delete(self, j):
        logging.info("Deleting %d"% j)
        post = self.obtainPostData(j)
        logging.info("Deleting %s"% post[0])
        profile = self.getProfile()
        from buffpy.models.update import Update
        update = Update(api=self.client, id=profile.updates.pending[j].id) 
        update = update.delete()

        logging.debug("Update before return %s"% update)
        return(update)
 
def main():

    import moduleBuffer
        
    buf = moduleBuffer.moduleBuffer()
    buf.setClient('http://fernand0-errbot.slack.com/', 
            ('linkedin', 'Fernando Tricas'))
    buf.setPosts()
    print(buf.getPosts())
    print(buf.getPosts()[0])
    print(len(buf.getPosts()[0]))
    sys.exit()
    # It has 30 elements
    print(buf.obtainPostData(0))

    print('F1', buf.selectAndExecute('show', 'F1'))
    print('L3', buf.selectAndExecute('show', 'L3'))
    print('TL2', buf.selectAndExecute('show', 'TL2'))
    print('*4', buf.selectAndExecute('show', '*4'))
    #print('edit L2', buf.selectAndExecute('edit', 'L2'+' '+'El tren del tambor.'))
    #print('pub L0', buf.selectAndExecute('publish','L0'))
    sys.exit()
    print('delete linkedin', buf.selectAndExecute('delete', 'L1'))
    print("-> PostsP",postsP)
    posts.update(postsP)
    print("-> Posts",posts)
    #print("Posts",profiles)
    print("Keys",posts.keys())
    sys.exit()
    posts = listPendingPosts("")
    print(profiles)
    print("Pending",type(profiles))
    print(profiles)
    profiles = listSentPosts("")
    print("Sent",type(profiles))
    print(profiles)
    print(type(profiles[1]),profiles[1])


    if profiles:
       toPublish, toWhere = input("Which one do you want to publish? ").split(' ')
       #publishPost(api, pp, profiles, toPublish)


if __name__ == '__main__':
    main()
