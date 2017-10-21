
import configparser
import os
import time
import urllib
import feedparser
from bs4 import BeautifulSoup
from bs4 import Tag

class moduleBlog():

    def __init__(self):
         self.rssFeed = ''
         self.socialNetworks = {}
         self.linksToAvoid = ""
         self.posts = None
         self.time = []
         self.buffer = None
 
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

    def getPosts(self):
        return(self.posts)
 
    def setPosts(self, posts):
        self.posts = posts

    def getBlogPosts(self):
        self.setPosts(feedparser.parse(self.rssFeed))

    def getLinkPosition(self, link):
        i = 0
        if self.getPosts():
            for entry in self.getPosts().entries:
                lenCmp = min(len(entry['link']), len(link))
                if entry['link'][:lenCmp] == link[:lenCmp]:
                       return i
                i = i + 1
        return(-1)

    def datePost(self, pos):
        return(self.getPosts().entries[pos]['published_parsed'])

    def checkLastLink(self):
        rssFeed = self.getRssFeed()
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
                if not isinstance(link.contents[0], Tag):
                    # We want to avoid embdeded tags (mainly <img ... )
                    theLink = link['href']
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
        posts = self.getPosts().entries
        theSummary = posts[i]['summary']
        content = posts[i]['description']
        theDescription = posts[i]['description']
        theTitle = posts[i]['title']
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
           lenProt = len('http://')
           if (firstLink[lenProt:pos] == theTitle[:pos - lenProt]):
               # A way to identify retumblings. They have the name of the
               # tumblr at the beggining of the anchor text
               logging.debug("It's a retumblr")
               logging.debug(theTitle)
               logging.debug(theTitle[pos - lenProt + 1:])
               theTitle = theTitle[pos - lenProt + 1:]

        #if 'description' in posts[i]:
        #    content = posts[i]['description']
        #else:
        #    content = ""
        #elif 'content' in posts[i]:
        #    content = posts[i]['content'][0]['value']
        #else:    
        #    content = posts[i]['summary']

        #soup = BeautifulSoup(content, 'lxml')

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
        print("\n")


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
        blog.setRssFeed(rssFeed)
        optFields = ["linksToAvoid", "time", "bufferapp"]
        if ("linksToAvoid" in config.options(section)):
            blog.setLinksToAvoid(config.get(section, "linksToAvoid"))
        if ("time" in config.options(section)):
            blog.setTime(config.get(section, "time"))
        if ("bufferapp" in config.options(section)):
            blog.setBufferapp(config.get(section, "bufferapp"))

        for option in config.options(section):
            if ('ac' in option) or ('fb' in option):
                blog.addSocialNetwork((option, config.get(section, option)))
        blog.getBlogPosts()
        blogs.append(blog)

    for blog in blogs:
        print(blog.getRssFeed())
        print(blog.getSocialNetworks())
        if 'twitterac' in blog.getSocialNetworks():
            print(blog.getSocialNetworks()['twitterac'])
        print(blog.getPosts().entries[0]['link'])
        print(blog.getLinkPosition(blog.getPosts().entries[0]['link']))
        print(time.asctime(blog.datePost(0)))
        print(blog.getLinkPosition(blog.getPosts().entries[5]['link']))
        print(time.asctime(blog.datePost(5)))
        blog.obtainPostData(0)

    for blog in blogs:
        import urllib
        urlFile = open(os.path.expanduser("~" + "/."  
              + urllib.parse.urlparse(blog.getRssFeed()).netloc
              + ".last"), "r")
        linkLast = urlFile.read().rstrip()  # Last published
        print(blog.getRssFeed(),blog.getLinkPosition(linkLast))
        print("description ->", blog.getPosts().entries[5]['description'])



