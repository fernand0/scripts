# This module provides infrastructure for publishing and updating blog posts
# using several generic APIs  (XML-RPC, blogger API, Metaweblog API, ...)

import configparser
import xmlrpc.client
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

class moduleBlog():

    def __init__(self):
         self.url = ""
         self.name = ""
         self.rssFeed = ''
         self.Id = 0
         self.socialNetworks = {}
         self.linksToAvoid = ""
         self.postsRss = None
         self.postsSlack = None
         self.postsXmlrpc = None
         self.time = []
         self.buffer = None
         self.program = None
         self.xmlrpc = None
         self.lastLinkPublished = {}
         self.logger = logging.getLogger(__name__)
 
    def getUrl(self):
        return(self.url)

    def setUrl(self, url):
        self.url = url

    def getName(self):
        return(self.name)

    def setName(self, name):
        if not self.xmlrpc:
            self.setXmlRpc()
        else:
            self.name = name

    def getRssFeed(self):
        return(self.rssFeed)

    def setRssFeed(self, feed):
        self.rssFeed = feed

    def getSocialNetworks(self):
        return(self.socialNetworks)
 
    def addSocialNetwork(self, socialNetwork):
        self.socialNetworks[socialNetwork[0]] = socialNetwork[1]

    def addLastLinkPublished(self, socialNetwork):
        self.lastLinkPublished[socialNetwork[0]] = socialNetwork[1]
 
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

    def getXmlRpc(self):
        return(self.xmlrpc)

    def setXmlRpc(self):
        conf = configparser.ConfigParser() 
        conf.read(os.path.join(os.path.expanduser('~') , '.blogaliarc')) 
        for section in conf.sections(): 
            usr = conf.get(section,'login') 
            pwd = conf.get(section,'password') 
            srv = conf.get(section,'server')
            domain = self.url[self.url.find('.'):]
            if srv.find(domain)>0:
                self.xmlrpc = (xmlrpc.client.ServerProxy(srv), usr, pwd)
                blogId, blogName = self.blogId(srv, usr, pwd)
                self.setId(blogId)
                self.setName(blogName)

    def getPostsRss(self):
        return(self.postsRss)
 
    def setPostsRss(self):
        urlRss = self.url+self.rssFeed
        self.logger.debug(urlRss)
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
            config.read([os.path.expanduser('~/.rssSlack')])
            slack_token = config["Slack"].get('api-key') 
            sc = SlackClient(slack_token) 
            theChannel = self.searchChannelSlack(sc, 'links')
            history = sc.api_call( "channels.history", channel=theChannel)
            self.logger.debug(history)
            for msg in history['messages']: 
                self.postsSlack.append(msg)

    def getPostsSlack(self):
        self.logger.debug("# posts", len(self.postsSlack))
        self.logger.debug(self.postsSlack)
        return(self.postsSlack)

    def getPostsXmlrpc(self):
        return(self.postsRss)
 
    def setPostsXmlrpc(self):
        if self.xmlrpc and self.Id:
            self.postsRss = self.xmlrpc[0].blogger.getRecentPosts('', self.Id, 
                    self.xmlrpc[1], self.xmlrpc[2], 10)

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
                self.logger.debug(self.getPostsRss().entries)
                return(len(self.getPostsRss().entries))
            for entry in self.getPostsRss().entries:
                self.logger.debug(entry['link'], link)
                lenCmp = min(len(entry['link']), len(link))
                if entry['link'][:lenCmp] == link[:lenCmp]:
                    return i
                i = i + 1
        elif self.getPostsSlack():
            if not link:
                self.logger.debug(self.getPostsSlack())
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
        self.logger.info("Selecting post")
        server = self.xmlrpc
        self.logger.debug(server)
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
        self.logger.info("Deleting id",idPost)
        if self.xmlrpc:
            server = self.xmlrpc
            result = server[0].blogger.deletePost('',idPost, server[1], server[2], True)
        elif self.getPostsSlack():
            # Needs improvement
            config = configparser.ConfigParser() 
            config.read(os.path.expanduser('~/' + '.rssSlack'))
            
            slack_token = config["Slack"].get('api-key')

            sc = SlackClient(slack_token)

            theChannel = self.searchChannelSlack(sc, 'links')

            result = sc.api_call("chat.delete", channel=theChannel, ts=idPost)

        self.logger.info(result)
        return(result)

    def updatePostsCache(self, listPosts, socialNetwork=()):
        fileName = os.path.expanduser('~/.' 
                +  urllib.parse.urlparse(self.getUrl()).netloc 
                + '_'+ socialNetwork[0] + '_' + socialNetwork[1] 
                + ".queue")

        self.logger.info("Updating Posts Cache: %s" % fileName)

        with open(fileName, 'wb') as f:
             pickle.dump(listPosts,f)
        return(fileName)

    def listPostsCache(self,socialNetwork=()):
        fileName = os.path.expanduser('~/.' 
                +  urllib.parse.urlparse(self.getUrl()).netloc 
                + '_'+ socialNetwork[0] + '_' + socialNetwork[1] 
                + ".queue")

        self.logger.info("Listing Posts Cache: %s" % fileName)

        with open(fileName,'rb') as f:
            try: 
                listP = pickle.load(f)
            except:
                listP = []

        self.logger.debug("listPostsCache", socialNetwork[0])
        for i in range(len(listP)):
            self.logger.debug("=> ", socialNetwork[0], listP[i][0])

        return(listP)

    def checkLastLink(self,socialNetwork=()):
        url = self.getUrl()
        if not socialNetwork: 
            fileName = os.path.expanduser("~" + "/."  
                    + urllib.parse.urlparse(url).netloc + ".last")
        else:    
            fileName = os.path.expanduser("~" + "/."  +
                    urllib.parse.urlparse(url).netloc +
                    '_'+socialNetwork[0]+'_'+socialNetwork[1] + ".last")
            self.logger.info("Checking last link: %s" % fileName)

        try: 
            with open(fileName, "r") as f: 
                linkLast = f.read().rstrip()  # Last published
        except:
            # File does not exist, we need to create it.
            with open(fileName, "w") as f:
                self.logger.warning("File %s does not exist. Creating it."
                        % fileName) 
                linkLast = ''  
                # None published, or non-existent file

        return(linkLast, os.path.getmtime(fileName))

    def updateLastLink(self,link, socialNetwork=()):
        rssFeed = self.getUrl()+self.getRssFeed()
        if not socialNetwork: 
            fileName = os.path.expanduser("~" + "/."  +
                    urllib.parse.urlparse(rssFeed).netloc + ".last")
        else: 
            fileName = os.path.expanduser("~" + "/."  +
                    urllib.parse.urlparse(rssFeed).netloc +
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
                    if link.has_key('href'):
                        theLink = link['href']
                    else:
                        theLink = link['src']
            else:
                theLink = link['src']
    
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
                self.logger.debug("theC", theContent)
                if theContent.startswith('Anuncios'): 
                    theContent = ''
                self.logger.debug("theC", theContent)
            else:
                (theContent, theSummaryLinks) = self.extractLinks(soup, "") 
                self.logger.debug("theC", theContent)
                if theContent.startswith('Anuncios'): 
                    theContent = ''
                self.logger.debug("theC", theContent)

            if 'media_content' in posts[i]: 
                theImage = posts[i]['media_content'][0]['url']
            else:
                theImage = self.extractImage(soup)
            self.logger.debug("theImage", theImage)
            theLinks = theSummaryLinks
            theSummaryLinks = theContent + theLinks
        elif self.getPostsSlack():
            posts = self.getPostsSlack()
            url = ''
            for j in range(len(posts)): 
                self.logger.debug("post ", j, posts[j]['text'])
            if 'attachments' in posts[i]:
                post = posts[i]['attachments'][0]
            else:
                post = posts[i]

            if 'title' in post:
                theTitle = post['title']
                theLink = post['title_link']
                firstLink = theLink
                if 'text' in posts: 
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
                    print("Fail image")
                    self.logger.warning("Fail image")
                    theImage = ''
            elif 'text' in post:
                if debug: 
                    self.logger.debug(post['text'])
                if post['text'].startswith('<h'):
                    # It's an url
                    url = post['text'][1:-1]
                    req = requests.get(url)
                    if req.text.find('403 Forbidden'):
                        theTitle = url
                        theSummary = url
                        content = url
                        theDescription = url
                    else:
                        soup = BeautifulSoup(req.text, 'lxml')
                        theTitle = str(soup.title.string)
                        theSummary = str(soup.body.string)
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

            theSummaryLinks = ""

            soup = BeautifulSoup(content, 'lxml')
            firstLink = theLink

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


        self.logger.debug("=========")
        self.logger.debug("Results: ")
        self.logger.debug("=========")
        self.logger.debug("Title:     ", theTitle)
        self.logger.debug("Link:      ", theLink)
        self.logger.debug("First Link:", firstLink)
        self.logger.debug("Summary:   ", content[:200])
        self.logger.debug("Sum links: ", theSummaryLinks)
        self.logger.debug("the Links"  , theLinks)
        self.logger.debug("Comment:   ", comment)
        self.logger.debug("Image;     ", theImage)
        self.logger.debug("Post       ", theTitle + " " + theLink)
        self.logger.debug("==============================================")
        self.logger.debug("")


        return (theTitle, theLink, firstLink, theImage, theSummary, content, theSummaryLinks, theContent, theLinks, comment)


if __name__ == "__main__":

    import moduleBlog
    
    config = configparser.ConfigParser()
    config.read([os.path.expanduser('~/.rssBlogs')])

    print("Configured blogs:")

    blogs = []

    #url = 'https://fernand0-errbot.slack.com/'
    #blog = moduleBlog.moduleBlog()
    #blog.setPostsSlack()
    #blog.setUrl(url)
    #print(blog.getPostsSlack())
    #sys.exit()

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
        if ("xmlrpc" in config.options(section)):
            blog.setXmlRpc()

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
        urlFile = open(os.path.expanduser("~" + "/."  
              + urllib.parse.urlparse(blog.getUrl()+blog.getRssFeed()).netloc
              + ".last"), "r")
        linkLast = urlFile.read().rstrip()  # Last published
        print(blog.getUrl()+blog.getRssFeed(),blog.getLinkPosition(linkLast))
        print("description ->", blog.getPostsRss().entries[5]['description'])
        blog.setPostsXmlrpc()
        posts = blog.getPostsXmlrpc()
        for post in posts:
            if "content" in post:
                print(post['content'][:100])
