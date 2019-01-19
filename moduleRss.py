# This module provides infrastructure for publishing and updating blog posts
# using several generic APIs  (XML-RPC, blogger API, Metaweblog API, ...)

import configparser
import os
import time
import urllib
import requests
import feedparser
import pickle
import logging
from slackclient import SlackClient
from bs4 import BeautifulSoup
from bs4 import Tag
from pdfrw import PdfReader
import moduleCache
# https://github.com/fernand0/scripts/blob/master/moduleCache.py

from configMod import *

class moduleRss():

    def __init__(self):
         self.url = ""
         self.name = ""
         self.rssFeed = ''
         self.Id = 0
         self.socialNetworks = {}
         self.linksToAvoid = ""
         self.postsRss = None
         self.time = []
         self.bufferapp = None
         self.program = None
         self.xmlrpc = None
         self.lastLinkPublished = {}
         #self.logger = logging.getLogger(__name__)
 
    def getUrl(self):
        return(self.url)

    def setUrl(self, url):
        self.url = url

    def getName(self):
        return(self.name)

    def setName(self, name):
        self.name = name

    def getRssFeed(self):
        return(self.rssFeed)

    def setRssFeed(self, feed):
        self.rssFeed = feed

    def getSocialNetworks(self):
        return(self.socialNetworks)
 
    def addSocialNetwork(self, socialNetwork):
        self.socialNetworks[socialNetwork[0]] = socialNetwork[1]

    def addLastLinkPublished(self, socialNetwork, lastLink, lastTime):
        self.lastLinkPublished[socialNetwork] = (lastLink, lastTime)

    def getLastLinkPublished(self):
        return(self.lastLinkPublished)
 
    def getLinksToAvoid(self):
        return(self.linksToAvoid)
 
    def setLinksToAvoid(self,linksToAvoid):
        self.linksToAvoid = linksToAvoid
 
    def getTime(self):
        return(self.time)
 
    def setTime(self, time):
        self.time = time

    def getBufferapp(self):
        return(self.bufferapp)
 
    def setBufferapp(self, bufferapp):
        self.bufferapp = bufferapp

    def getProgram(self):
        return(self.program)
 
    def setProgram(self, program):
        self.program = program

    def getPostsRss(self):
        return(self.postsRss)
 
    def setPostsRss(self):
        if self.rssFeed.find('http')>=0: 
            urlRss = self.rssFeed
        else: 
            urlRss = self.url+self.rssFeed
        logging.debug(urlRss)
        self.postsRss = feedparser.parse(urlRss)

    def searchChannelSlack(self, sc, name):
        chanList = sc.api_call("channels.list")['channels'] 
        for channel in chanList: 
            if channel['name_normalized'] == name: 
                return(channel['id']) 

        return(-1)

    def setPostsSlack(self):
        if self.postsSlack is None:
            self.postsSlack = []
            config = configparser.ConfigParser()
            config.read(CONFIGDIR + '/.rssSlack')
            slack_token = config["Slack"].get('api-key')
            sc = SlackClient(slack_token)
            theChannel = self.searchChannelSlack(sc, 'links')
            history = sc.api_call( "channels.history", count=1000, channel=theChannel)
            logging.debug(history)
            for msg in history['messages']:
                self.postsSlack.append(msg)

    def getPostsSlack(self):
        logging.debug("# posts", len(self.postsSlack))
        logging.debug(self.postsSlack)
        return(self.postsSlack)

    def getId(self):
        return(self.Id)

    def setId(self, Id):
        self.Id = Id

    def blogId(self, srv, usr, pwd): 
        server = self.xmlrpc[0]
        usr = self.xmlrpc[1]
        pwd = self.xmlrpc[2]

        listMet = server.system.listMethods() 
        if 'wp' in listMet[-1]:
            userBlogs = server.wp.getUsersBlogs(usr,pwd)
        else: 
            userBlogs = server.blogger.getUsersBlogs('',usr,pwd)
        for blog in userBlogs:
            identifier = self.url[self.url.find('/')+2:self.url.find('.')]
            if blog['url'].find(identifier) > 0:
                return(blog['blogid'], blog['blogName'])

        return(-1)

    def getLinkPosition(self, link):
        i = 0
        if self.getPostsRss():
            if not link:
                logging.debug(self.getPostsRss().entries)
                return(len(self.getPostsRss().entries))
            for entry in self.getPostsRss().entries:
                logging.debug(entry['link'], link)
                lenCmp = min(len(entry['link']), len(link))
                if entry['link'][:lenCmp] == link[:lenCmp]:
                    return i
                i = i + 1
        elif self.getPostsSlack():
            if not link:
                logging.debug(self.getPostsSlack())
                return(len(self.getPostsSlack()))
            for entry in self.getPostsSlack():
                if 'original_url' in entry: 
                    url = entry['original_url']
                else:
                    url = entry['text'][1:-1]
                #print(url, link)
                lenCmp = min(len(url), len(link))
                if url[:lenCmp] == link[:lenCmp]:
                    return i
                i = i + 1
        return(i)

    def datePost(self, pos):
        return(self.getPostsRss().entries[pos]['published_parsed'])

    def newPost(self, title, content): 
        server = self.xmlrpc
        data = { 'title': title, 'description': content}
        server[0].metaWeblog.newPost(self.Id, server[1], server[2], data, True)

    def editPost(self, idPost, title, content): 
        server = self.xmlrpc
        data = { 'title': title, 'description': content}
        server[0].metaWeblog.editPost(idPost, server[1], server[2], data, True)
    
    def selectPost(self):
        logging.info("Selecting post")
        server = self.xmlrpc
        logging.debug(server)
        posts = server[0].metaWeblog.getRecentPosts(self.Id, server[1], server[2], 10)
        i = 1
        print("Posts:")
        for post in posts:
            print('%d) %s - %s' %(i, post['title'], post['postid']))
            i = i + 1
        thePost = int(input("Select one: "))
        print("Post ... %s - %s" % (posts[thePost - 1]['title'], posts[thePost - 1]['postid']))
        return posts[thePost - 1]['title'], posts[thePost - 1]['postid']

    def deletePost(self, idPost): 
        logging.info("Deleting id %s" % idPost)
        if self.xmlrpc:
            server = self.xmlrpc
            result = server[0].blogger.deletePost('',idPost, server[1], server[2], True)
        elif self.getPostsSlack():
            # Needs improvement
            config = configparser.ConfigParser() 
            config.read(CONFIGDIR + '/.rssSlack')
            
            slack_token = config["Slack"].get('api-key')

            sc = SlackClient(slack_token)

            theChannel = self.searchChannelSlack(sc, 'links')

            result = sc.api_call("chat.delete", channel=theChannel, ts=idPost)

        logging.info(result)
        return(result)

    def updatePostsCache(self, listPosts, socialNetwork=()):
        #Now it is duplicated in moduleCache
        fileName = (DATADIR + '/' 
                + urllib.parse.urlparse(self.getUrl()).netloc 
                + '_'+ socialNetwork[0] + '_' + socialNetwork[1] 
                + ".queue")

        logging.info("Updating Posts Cache: %s" % fileName)

        with open(fileName, 'wb') as f:
             pickle.dump(listPosts,f)
        return(fileName)

    def listPostsCache(self,socialNetwork=()):
        fileName = (DATADIR  + '/' 
                +  urllib.parse.urlparse(self.getUrl()).netloc 
                + '_'+ socialNetwork[0] + '_' + socialNetwork[1] 
                + ".queue")

        logging.info("Listing Posts Cache: %s" % fileName)

        with open(fileName,'rb') as f:
            try: 
                listP = pickle.load(f)
            except:
                listP = []

        logging.debug("listPostsCache", socialNetwork[0])
        for i in range(len(listP)):
            logging.debug("=> ", socialNetwork[0], listP[i][0])

        return(listP)

    def checkLastLink(self,socialNetwork=()):
        fileNameL = moduleCache.fileName(self, socialNetwork)+".last"
        logging.info("Checking last link: %s" % fileNameL)
        (linkLast, timeLast) = moduleCache.getLastLink(fileNameL)
        return(linkLast, timeLast)

    def updateLastLink(self,link, socialNetwork=()):
        rssFeed = self.getUrl()+self.getRssFeed()
        if not socialNetwork: 
            fileName = (DATADIR  + '/' 
                   + urllib.parse.urlparse(rssFeed).netloc + ".last")
        else: 
            fileName = (DATADIR + '/'
                    + urllib.parse.urlparse(rssFeed).netloc +
                    '_'+socialNetwork[0]+'_'+socialNetwork[1] + ".last")
        with open(fileName, "w") as f: 
            f.write(link)

    def extractImage(self, soup):
        pageImage = soup.findAll("img")
        #  Only the first one
        if len(pageImage) > 0:
            imageLink = (pageImage[0]["src"])
        else:
            imageLink = ""
    
        if imageLink.find('?') > 0:
            return imageLink[:imageLink.find('?')]
        else:
            return imageLink

    def extractLinks(self, soup, linksToAvoid=""):
        j = 0
        linksTxt = ""
        links = soup.find_all(["a","iframe"])
        for link in soup.find_all(["a","iframe"]):
            theLink = ""
            if len(link.contents) > 0: 
                if not isinstance(link.contents[0], Tag):
                    # We want to avoid embdeded tags (mainly <img ... )
                    if link.has_attr('href'):
                        theLink = link['href']
                    else:
                        if 'src' in link: 
                            theLink = link['src']
                        else:
                            continue
            else:
                if 'src' in link: 
                    theLink = link['src']
                else:
                    continue
    
            if ((linksToAvoid == "") or
               (not re.search(linksToAvoid, theLink))):
                    if theLink:
                        link.append(" ["+str(j)+"]")
                        linksTxt = linksTxt + "["+str(j)+"] " + \
                            link.contents[0] + "\n"
                        linksTxt = linksTxt + "    " + theLink + "\n"
                        j = j + 1
    
        if linksTxt != "":
            theSummaryLinks = linksTxt
        else:
            theSummaryLinks = ""
    
        return (soup.get_text().strip('\n'), theSummaryLinks)

    def obtainPostData(self, i, debug=False):
        if self.getPostsRss():
            posts = self.getPostsRss().entries
            theSummary = posts[i]['summary']
            content = posts[i]['description']
            if content.startswith('Anuncios'): content = ''
            theDescription = posts[i]['description']
            theTitle = posts[i]['title'].replace('\n', ' ')
            theLink = posts[i]['link']
            if ('comment' in posts[i]):
                comment = posts[i]['comment']
            else:
                comment = ""

            theSummaryLinks = ""

            soup = BeautifulSoup(theDescription, 'lxml')

            link = soup.a
            if link is None:
               firstLink = theLink 
            else:
               firstLink = link['href']
               pos = firstLink.find('.')
               if firstLink.find('https')>=0:
                   lenProt = len('https://')
               else:
                   lenProt = len('http://')
               if (firstLink[lenProt:pos] == theTitle[:pos - lenProt]):
                   # A way to identify retumblings. They have the name of the
                   # tumblr at the beggining of the anchor text
                   theTitle = theTitle[pos - lenProt + 1:]

            theSummary = soup.get_text()
            if self.getLinksToAvoid():
                (theContent, theSummaryLinks) = self.extractLinks(soup, self.getLinkstoavoid())
                logging.debug("theC", theContent)
                if theContent.startswith('Anuncios'): 
                    theContent = ''
                logging.debug("theC", theContent)
            else:
                (theContent, theSummaryLinks) = self.extractLinks(soup, "") 
                logging.debug("theC", theContent)
                if theContent.startswith('Anuncios'): 
                    theContent = ''
                logging.debug("theC", theContent)

            if 'media_content' in posts[i]: 
                theImage = posts[i]['media_content'][0]['url']
            else:
                theImage = self.extractImage(soup)
            logging.debug("theImage", theImage)
            theLinks = theSummaryLinks
            theSummaryLinks = theContent + theLinks
        elif self.getPostsSlack():
            posts = self.getPostsSlack()
            theContent = ''
            url = ''
            firstLink = ''
            logging.debug("i %d", i)
            logging.debug("post %s", posts[i])
            #print("i", i)
            #print("post", posts[i])
            if 'attachments' in posts[i]:
                post = posts[i]['attachments'][0]
            else:
                post = posts[i]

            if 'title' in post:
                theTitle = post['title']
                theLink = post['title_link']
                if theLink.find('tumblr')>0:
                    theTitle = post['text']
                firstLink = theLink
                if 'text' in post: 
                    content = post['text']
                else:
                    content = theLink
                theSummary = content
                theSummaryLinks = content
                if 'image_url' in post:
                    theImage = post['image_url']
                elif 'thumb_url' in post:
                    theImage = post['thumb_url']
                else:
                    logging.info("Fail image")
                    logging.info("Fail image %s", post)
                    theImage = ''
            elif 'text' in post:
                if post['text'].startswith('<h'):
                    # It's an url
                    url = post['text'][1:-1]
                    req = requests.get(url)
                        
                    if req.text.find('403 Forbidden')>=0:
                        theTitle = url
                        theSummary = url
                        content = url
                        theDescription = url
                    else:
                        if url.lower().endswith('pdf'):
                            nameFile = '/tmp/kkkkk.pdf'
                            with open(nameFile,'wb') as f:
                                f.write(req.content)
                            theTitle = PdfReader(nameFile).Info.Title
                            if theTitle:
                                theTitle = theTitle[1:-1]
                            else:
                                theTitle = url
                            theUrl = url
                            theSummary = ''
                            content = theSummary
                            theDescription = theSummary
                        else:
                            soup = BeautifulSoup(req.text, 'lxml')
                            #print("soup", soup)
                            theTitle = soup.title
                            if theTitle:
                                theTitle = str(theTitle.string)
                            else:
                                # The last part of the path, without the dot part, and
                                # capitized
                                urlP = urllib.parse.urlparse(url)
                                theTitle = os.path.basename(urlP.path).split('.')[0].capitalize()
                            theSummary = str(soup.body)
                            content = theSummary
                            theDescription = theSummary
                else:
                    theSummary = post['text']
                    content = post['text']
                    theDescription = post['text']
                    theTitle = post['text']
            else:
                theSummary = post['title']
                content = post['title']
                theDescription = post['title']

            if 'original_url' in post: 
                theLink = post['original_url']
            elif url: 
                theLink = url
            else:
                theLink = post['text']

            if ('comment' in post):
                comment = post['comment']
            else:
                comment = ""

            #print("content", content)
            theSummaryLinks = ""

            soup = BeautifulSoup(content, 'lxml')
            if not content.startswith('http'):
                link = soup.a
                if link: 
                    firstLink = link.get('href')
                    if firstLink:
                        if firstLink[0] != 'h': 
                            firstLink = theLink

            if not firstLink: 
                firstLink = theLink

            if 'image_url' in post:
                theImage = post['image_url']
            else:
                theImage = None
            theLinks = theSummaryLinks
            theSummaryLinks = theContent + theLinks
            
            if self.getLinksToAvoid():
                (theContent, theSummaryLinks) = self.extractLinks(soup, self.getLinkstoavoid())
            else:
                (theContent, theSummaryLinks) = self.extractLinks(soup, "") 
                
            if 'image_url' in post:
                theImage = post['image_url']
            else:
                theImage = None
            theLinks = theSummaryLinks
            theSummaryLinks = theContent + theLinks


        logging.debug("=========")
        logging.debug("Results: ")
        logging.debug("=========")
        logging.debug("Title:     ", theTitle)
        logging.debug("Link:      ", theLink)
        logging.debug("First Link:", firstLink)
        logging.debug("Summary:   ", content[:200])
        logging.debug("Sum links: ", theSummaryLinks)
        logging.debug("the Links"  , theLinks)
        logging.debug("Comment:   ", comment)
        logging.debug("Image;     ", theImage)
        logging.debug("Post       ", theTitle + " " + theLink)
        logging.debug("==============================================")
        logging.debug("")


        return (theTitle, theLink, firstLink, theImage, theSummary, content, theSummaryLinks, theContent, theLinks, comment)


if __name__ == "__main__":

    import moduleBlog
    
    config = configparser.ConfigParser()
    config.read(CONFIGDIR + '/.rssBlogs')

    print("Configured blogs:")

    blogs = []

    url = 'https://fernand0-errbot.slack.com/'
    blog = moduleBlog.moduleBlog()
    blog.setPostsSlack()
    blog.setUrl(url)
    print(blog.obtainPostData(29))
    #print(blog.getPostsSlack())
    sys.exit()

    for section in config.sections():
        #print(section)
        #print(config.options(section))
        blog = moduleBlog.moduleBlog()
        url = config.get(section, "url")
        blog.setUrl(url)
        if 'rssfeed' in config.options(section): 
            rssFeed = config.get(section, "rssFeed")
            #print(rssFeed) 
            blog.setRssFeed(rssFeed)
        optFields = ["linksToAvoid", "time", "bufferapp"]
        if ("linksToAvoid" in config.options(section)):
            blog.setLinksToAvoid(config.get(section, "linksToAvoid"))
        if ("time" in config.options(section)):
            blog.setTime(config.get(section, "time"))
        if ("bufferapp" in config.options(section)):
            blog.setBufferapp(config.get(section, "bufferapp"))
        if ("program" in config.options(section)):
            blog.setBufferapp(config.get(section, "program"))

        for option in config.options(section):
            if ('ac' in option) or ('fb' in option):
                blog.addSocialNetwork((option, config.get(section, option)))
        blogs.append(blog)

    
    blogs[7].setPostsRss()
    #print(blogs[7].getPostsRss().entries)
    numPosts = len(blogs[7].getPostsRss().entries)
    for i in range(numPosts):
        print(blog.obtainPostData(numPosts - 1 - i))

    sys.exit()

    for blog in blogs:
        print(blog.getUrl())
        print(blog.getRssFeed())
        print(blog.getSocialNetworks())
        if 'twitterac' in blog.getSocialNetworks():
            print(blog.getSocialNetworks()['twitterac'])
        blog.setPostsRss()
        print(blog.getPostsRss().entries[0]['link'])
        print(blog.getLinkPosition(blog.getPostsRss().entries[0]['link']))
        print(time.asctime(blog.datePost(0)))
        print(blog.getLinkPosition(blog.getPostsRss().entries[5]['link']))
        print(time.asctime(blog.datePost(5)))
        blog.obtainPostData(0)
        if blog.getUrl().find('ando')>0:
            blog.newPost('Prueba %s' % time.asctime(), 'description %s' % 'prueba')
            print(blog.selectPost())

    for blog in blogs:
        import urllib
        urlFile = open(DATADIR + '/' 
              + urllib.parse.urlparse(blog.getUrl()+blog.getRssFeed()).netloc
              + ".last", "r")
        linkLast = urlFile.read().rstrip()  # Last published
        print(blog.getUrl()+blog.getRssFeed(),blog.getLinkPosition(linkLast))
        print("description ->", blog.getPostsRss().entries[5]['description'])
        for post in posts:
            if "content" in post:
                print(post['content'][:100])
