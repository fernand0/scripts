import configparser
import xmlrpc.client
import os
import time
import urllib
import feedparser
from bs4 import BeautifulSoup
from bs4 import Tag

class moduleBlog():

    def __init__(self):
         self.url = ""
         self.rssFeed = ''
         self.Id = 0
         self.socialNetworks = {}
         self.linksToAvoid = ""
         self.postsRss = None
         self.postsXmlrpc = None
         self.time = []
         self.buffer = None
         self.xmlrpc = ''
 
    def getUrl(self):
        return(self.url)

    def setUrl(self, url):
        self.url = url

    def getRssFeed(self):
        return(self.rssFeed)

    def setRssFeed(self, feed):
        self.rssFeed = feed

    def getSocialNetworks(self):
        return(self.socialNetworks)
 
    def addSocialNetwork(self, socialNetwork):
        self.socialNetworks[socialNetwork[0]] = socialNetwork[1]
 
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

    def getXmlRpc(self):
        return(self.rssFeed)

    def setXmlRpc(self, xmlrpc):
        self.xmlrpc = xmlrpc

    def getPostsRss(self):
        return(self.postsRss)
 
    def setPostsRss(self, posts):
        self.postsRss = posts

    def getPostsXmlrpc(self):
        conf = configparser.ConfigParser() 
        conf.read('/home/ftricass/.blogaliarc') 
        for section in conf.sections(): 
            usr = conf.get(section,'login') 
            pwd = conf.get(section,'password') 
            srv = conf.get(section,'server')
            if (self.url in srv):
                self.setId(blogId(srv, usr, pws))

        return(self.postsRss)
 
    def setPostsXmlrpc(self, posts):
        self.postsRss = posts

    def getId(self):
        return(self.Id)

    def setId(self, Id):
        self.Id = Id

    def getBlogPostsRss(self):
        self.setPostsRss(feedparser.parse(self.url+self.rssFeed))

    def blogId(self, srv, usr, pwd): 
        server = xmlrpc.client.ServerProxy(srv)
        listMet = server.system.listMethods() 
        if 'wp' in listMet[-1]:
            userBlogs = server.wp.getUsersBlogs(usr,pwd)
        else: 
            server.blogger.getUsersBlogs('',usr,pwd)

    def getLinkPosition(self, link):
        i = 0
        if self.getPostsRss():
            for entry in self.getPostsRss().entries:
                lenCmp = min(len(entry['link']), len(link))
                if entry['link'][:lenCmp] == link[:lenCmp]:
                       return i
                i = i + 1
        return(-1)

    def datePost(self, pos):
        return(self.getPostsRss().entries[pos]['published_parsed'])

    def checkLastLink(self):
        rssFeed = self.getUrl()+self.getRssFeed()
        urlFile = open(os.path.expanduser("~" + "/."  
                  + urllib.parse.urlparse(rssFeed).netloc
                  + ".last"), "r")
        linkLast = urlFile.read().rstrip()  # Last published
        return(linkLast)


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
                print(link)
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
            theSummaryLinks = soup.get_text().strip('\n') + "\n\n" + linksTxt
        else:
            theSummaryLinks = soup.get_text().strip('\n')
    
        return theSummaryLinks

    def obtainPostData(self, i):
        posts = self.getPostsRss().entries
        theSummary = posts[i]['summary']
        content = posts[i]['description']
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
               logging.debug("It's a retumblr")
               logging.debug(theTitle)
               logging.debug(theTitle[pos - lenProt + 1:])
               theTitle = theTitle[pos - lenProt + 1:]


        theSummary = soup.get_text()
        if self.getLinksToAvoid():
            theSummaryLinks = self.extractLinks(soup, self.getLinkstoavoid())
        else:
            theSummaryLinks = self.extractLinks(soup, "")


        theImage = self.extractImage(soup)

        print("=========")
        print("Results: ")
        print("=========")
        print("Title:     ", theTitle)
        print("Link:      ", theLink)
        print("First Link:", firstLink)
        print("Summary:   ", content[:200])
        print("Sum links: ", theSummaryLinks)
        print("Comment:   ", comment)
        print("Image;     ", theImage)
        print("Post       ", theTitle + " " + theLink)
        print("==============================================")


        return (theTitle, theLink, firstLink, theImage, theSummary, content ,theSummaryLinks, comment)


if __name__ == "__main__":

    import moduleBlog
    
    config = configparser.ConfigParser()
    config.read([os.path.expanduser('~/.rssBlogs')])

    print("Configured blogs:")

    blogs = []

    for section in config.sections():
        rssFeed = config.get(section, "rssFeed")
        print(rssFeed)
        blog = moduleBlog.moduleBlog()
        url = config.get(section, "url")
        blog.setUrl(url)
        blog.setRssFeed(rssFeed)
        optFields = ["linksToAvoid", "time", "bufferapp"]
        if ("linksToAvoid" in config.options(section)):
            blog.setLinksToAvoid(config.get(section, "linksToAvoid"))
        if ("time" in config.options(section)):
            blog.setTime(config.get(section, "time"))
        if ("bufferapp" in config.options(section)):
            blog.setBufferapp(config.get(section, "bufferapp"))
        if ("xmlrpc" in config.options(section)):
            blog.setXmlRpc(config.get(section, "xmlrpc"))

        for option in config.options(section):
            if ('ac' in option) or ('fb' in option):
                blog.addSocialNetwork((option, config.get(section, option)))
        blog.getBlogPostsRss()
        blogs.append(blog)

    for blog in blogs:
        print(blog.getUrl())
        print(blog.getRssFeed())
        print(blog.getSocialNetworks())
        if 'twitterac' in blog.getSocialNetworks():
            print(blog.getSocialNetworks()['twitterac'])
        print(blog.getPostsRss().entries[0]['link'])
        print(blog.getLinkPosition(blog.getPostsRss().entries[0]['link']))
        print(time.asctime(blog.datePost(0)))
        print(blog.getLinkPosition(blog.getPostsRss().entries[5]['link']))
        print(time.asctime(blog.datePost(5)))
        blog.obtainPostData(0)

    for blog in blogs:
        import urllib
        urlFile = open(os.path.expanduser("~" + "/."  
              + urllib.parse.urlparse(blog.getUrl()+blog.getRssFeed()).netloc
              + ".last"), "r")
        linkLast = urlFile.read().rstrip()  # Last published
        print(blog.getUrl()+blog.getRssFeed(),blog.getLinkPosition(linkLast))
        print("description ->", blog.getPostsRss().entries[5]['description'])
