import configparser
import logging
import requests
import json
import sys
from bs4 import BeautifulSoup

from configMod import *
from moduleContent import *
from moduleQueue import *

class moduleWordpress(Content,Queue):

    def __init__(self):
        super().__init__()
        self.user = None
        self.wp = None
        self.service = None
        self.api_base='https://public-api.wordpress.com/rest/v1/'
        self.api_user='me'
        self.api_posts='sites/{}/posts'
        self.api_posts_search='?search={}'

    def setClient(self, user):
        logging.info("     Connecting Wordpress")
        self.service = 'Wordpress'
        try:
            config = configparser.RawConfigParser()
            config.read(CONFIGDIR + '/.rssWordpress')

            self.user = user
            try: 
                self.access_token =  config.get(user, "access_token")
            except:
                logging.warning("Access key does not exist!")
                logging.warning("Unexpected error:", sys.exc_info()[0])
        except:
                logging.warning("Config file does not exists")
                logging.warning("Unexpected error:", sys.exc_info()[0])

        self.headers = {'Authorization':'Bearer '+self.access_token}
        self.my_site="{}.wordpress.com".format(user)

    def setPosts(self): 
        logging.info("  Setting posts")
        self.posts = []
        try: 
            posts = requests.get(self.api_base + 
                    self.api_posts.format(self.my_site)+'?number=100', 
                    headers = self.headers).json()['posts']
            self.posts = posts
            # More posts
            #posts2 = requests.get(self.api_base + 
            #        self.api_posts.format(self.my_site)+'?number=100&page=2', 
            #        headers = self.headers).json()['posts']
        except:
            return(self.report('Wordpress API', '' , '', sys.exc_info()))


    def getTitle(self, i):        
        post = self.getPosts()[i]
        return(self.getPostTitle(post))

    def getLink(self, i):
        post = self.getPosts()[i]
        return(self.getPostLink(post))

    def getPostTitle(self, post):
        if 'title' in post:
            return(post['title'])
        else:
            return('')

    def getPostLink(self, post):    
        if 'URL' in post:
            return(post['URL'])
        else:
            return('')

    def obtainPostData(self, i, debug=False):
        if not self.posts:
            self.setPosts()

        posts = self.getPosts()
        if not posts:
            return (None, None, None, None, None, None, None, None, None, None)

        post = posts[i]

        theContent = ''
        url = ''
        firstLink = ''
        logging.debug("i %d", i)
        logging.debug("post %s", post)

        theTitle = self.getTitle(i)
        theLink = self.getLink(i)
        print(theTitle)
        print(theLink)
        firstLink = theLink
        if 'content' in post: 
            content = post['content']
        else:
            content = theLink
        if 'excerpt' in post: 
            theSummary = post['excerpt']
        else:
            theSummary = content
        theSummaryLinks = content
        if 'attachments' in post:
            theImage=''
            for key in post['attachments']:
                if 'URL' in post['attachments'][key]:
                    theImage = post['attachments'][key]['URL']
        else:
            logging.info("Fail image")
            logging.debug("Fail image %s", post)
            theImage = ''

        comment = ''

        theSummaryLinks = ""

        if not content.startswith('http'):
            soup = BeautifulSoup(content, 'lxml')
            link = soup.a
            if link: 
                firstLink = link.get('href')
                if firstLink:
                    if firstLink[0] != 'h': 
                        firstLink = theLink

        if not firstLink: 
            firstLink = theLink

        theLinks = theSummaryLinks
        theSummaryLinks = theContent + theLinks
        
        theContent = ""
        theSummaryLinks = ""

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


def main():

    import moduleWordpress

    wp = moduleWordpress.moduleWordpress()
    wp.setClient('avecesunafoto')
    print("Testing posts")
    wp.setPosts()
    print(wp.getPosts())
    for i, post in enumerate(wp.getPosts()):
        print("p",i, ") ", post)
        #print("@%s: %s" %(tweet[2], tweet[0]))

    print(wp.getLinkPosition('https://avecesunafoto.wordpress.com/2020/01/31/guiso/'))
    sys.exit()
    print("Testing title and link")
    
    for i, post in enumerate(wp.getPosts()):
        title = wp.getPostTitle(post)
        link = wp.getPostLink(post)
        #url = tw.getPostUrl(post)
        print("{}) Title: {}\nLink: {}\nUrl:{}\n".format(i,title,link,link))


    print("Testing obtainPostData")
    for (i,post) in enumerate(wp.getPosts()):
        print(i,") ",wp.obtainPostData(i))

    sys.exit()

if __name__ == '__main__':
    main()

