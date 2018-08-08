#!/usr/bin/env python
# encoding: utf-8

# Queue [cache] files name is composed of a dot, followed by the path of the
# URL, followed by the name of the social network and the name of the user for
# posting there.
# The filename ends in .queue
# For example:
#    .my.blog.com_twitter_myUser.queue
# This file stores a list of pending posts stored as an array of posts as
# returned by moduleBlog
# (https://github.com/fernand0/scripts/blob/master/moduleBlog.py)
#  obtainPostData method.

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

def API(Blog, pp):
    api = {}
    config = configparser.ConfigParser() 
    config.read([os.path.expanduser('~/.rssBlogs')]) 
    blog = moduleBlog.moduleBlog() 

    url = config.get(Blog, "url")
    blog.setUrl(url)

    api['blog'] = blog
    api['profiles'] = getProfiles((blog, config[Blog]), pp)
    return(api)

def fileName(blog, socialNetwork):
    print('blog', blog)
    theName = os.path.expanduser('~/.' 
                    + urllib.parse.urlparse(blog.getUrl()).netloc + '_' 
                    + socialNetwork[0] + '_' + socialNetwork[1])
    return(theName)

def getProfiles(api, pp, service=""):
    logging.info("Checking services...")

    profiles = []

    for key in api[1].keys():
        if key[0] in api[1]['program']:
            profile = {}
            profile['socialNetwork'] = (key, api[1][key]) 
            socialNetwork = profile['socialNetwork']
            fileNameQ = fileName(api[0],socialNetwork) + ".queue" 
            profile['fileName'] = fileNameQ
            profiles.append(profile)
            profile['posts'] = []

    logging.debug("->%s" % pp.pformat(profiles))
    numProfiles = len(profiles)
    logging.debug("Num. Profiles %d" % numProfiles)
    logging.debug("Profiles %s" % pp.pformat(profiles))

    return (profiles)

def getLastLink(fileName):        
    try: 
        with open(fileName, "r") as f: 
            linkLast = f.read().rstrip()  # Last published
    except:
        # File does not exist, we need to create it.
        with open(fileName, "w") as f:
            logging.warning("File %s does not exist. Creating it."
                    % fileName) 
            linkLast = ''  
            # None published, or non-existent file
    return(linkLast, os.path.getmtime(fileName))


def getPostsCache(blog, socialNetwork):        
    fileNameQ = fileName(blog,socialNetwork) + ".queue" 
    with open(fileNameQ,'rb') as f: 
        try: 
            listP = pickle.load(f) 
        except: 
            listP = [] 
    return(listP)

def listPosts(api, pp, service=""):    
    outputData = {}
    files = []

    profiles = api['profiles']
    logging.info("** %s" % profiles)
    print("** %s" % profiles)
    for profile in profiles:
        logging.info("profile %s" % pp.pformat(profile))
        print("profile %s" % pp.pformat(profile))

        fileN = profile['fileName']
        serviceName = profile['socialNetwork'][0].capitalize()
        logging.info("Service %s" % serviceName)

        outputData[serviceName] = {'sent': [], 'pending': []}
        listP = getPostsCache(api['blog'], profile['socialNetwork'])

        logging.info("-Posts %s"% listP)

        if len(listP) > 0: 
            logging.debug("Waiting in queue: %s"% fileN) 
            for element in listP: 
                outputData[serviceName]['pending'].append(element) 
        logging.info("Service posts profile %s" % profile)
        logging.info("Iter Service posts profiles %s" % profiles)

    logging.info("Service posts profiles %s" % profiles)
    return(outputData, profiles)

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
    profiles = cache['profiles']
    logging.info("Cache profiles antes %s" % pp.pformat(profiles))
    for profile in profiles: 
        if 'socialNetwork' in profile:
            serviceName = profile['socialNetwork'][0].capitalize()
            if (serviceName[0] in profMov) or toPublish[0]=='*': 
                logging.info("In %s" % pp.pformat(serviceName))
                logging.info("Profile %s" % pp.pformat(profile))
                logging.info("Profile posts %s" % pp.pformat(posts))
                (title, link, firstLink, image, summary, summaryHtml, summaryLinks, content, links, comment) = (posts[serviceName]['pending'][j])
                if serviceName == 'Twitter':
                    update = moduleSocial.publishTwitter(posts[profile['socialNetwork']][1],
                            title, link, summary, summaryHtml, summaryLinks,
                            image, content , links) 
                    profiles[i]['posts'] = profiles[i]['posts'][:j] + profiles[i]['posts'][j+1:]
                    logging.info("Updating %s" % pp.pformat(profiles[i]))
                    updatePostsCache(cache['blog'], profiles[i]['posts'], profiles[i]['socialNetwork'])
                elif serviceName == 'Facebook':
                    update = moduleSocial.publishFacebook(profile['socialNetwork'][1],
                            title, link, summary, summaryHtml, summaryLinks, 
                            image, content , links) 
                    logging.info("Publishing title: %s" % title)
                    posts[serviceName]['pending'] = posts[serviceName]['pending'][:j] + posts[serviceName]['pending'][j+1:]
                    logging.info("Updating %s" % pp.pformat(posts))
                    logging.info("Blog %s" % pp.pformat(cache['blog']))
                    updatePostsCache(cache['blog'], posts[serviceName]['pending'], profile['socialNetwork'])
                #logging.debug("Profile: %d Publishing item: %d" % (i,j)) 
    return(update)


#######################################################
# These need work
#######################################################

def deletePost(api, pp, profiles, toPublish):
    logging.info(pp.pformat(toPublish))
    i = 0
    profMov = ""
    while toPublish[i].isalpha():
        print(i)
        profMov = profMov + toPublish[i]
        i = i + 1

    postsP = listPostsProgram(['.fernand0-errbot.slack.com_facebook_me.queue','.fernand0-errbot.slack.com_twitter_fernand0.queue'], pp, "")

    print(postsP)
    sys.exit()

    j = int(toPublish[-1])    
    for i in range(len(profiles)):
        serviceName = profiles[i].formatted_service
        if (serviceName[0] in profMov) or toPublish[0]=='*':
            logging.debug("%d %d"  % (i,j))
            update = Update(api=api, id=profiles[i].updates.pending[j].id)
            logging.debug(pp.pformat(update))
            update.delete()

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
    api = API('Blog7', pp)

    logging.basicConfig(#filename='example.log',
                            level=logging.DEBUG,format='%(asctime)s %(message)s')


    print("profiles")
    print(api)
    postsP, profiles = listPosts(api, pp, '')
    print("-> Posts",postsP)
    #print("-->profiles")
    #print(profiles)
    #updatePostsCache(api['blog'], [], ('twitter','fernand0'))
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
