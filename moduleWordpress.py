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
        self.api_tags='sites/{}/tags'
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
            print(self.api_base + self.api_posts.format(self.my_site))
            posts = requests.get(self.api_base + 
                    self.api_posts.format(self.my_site)+'?number=100', 
                    headers = self.headers).json()['posts']
            self.posts = posts
            # More posts
            #posts2 = requests.get(self.api_base + 
            #        self.api_posts.format(self.my_site)+'?number=100&page=2', 
            #        headers = self.headers).json()['posts']
        except KeyError:
            return(self.report('Wordpress API expired', '' , '', sys.exc_info()))
        except:
            return(self.report('Wordpress API', '' , '', sys.exc_info()))

    def checkTags(self, tags):
        self.api_base2 = 'https://public-api.wordpress.com/wp/v2/'
        self.api_base2 = 'https://avecesunafoto.wordpress.com/?rest_route=/wp/v2/sites/avecesunafoto.wordpress.com/tags'
        self.api_base2 = 'https://public-api.wordpress.com/rest/v1.1/sites/avecesunafoto.wordpress.com/tags'
        idTags = []
        for tag in tags: 
            payload = {"name":tag}
            # I'm trying to create, if not possible, they exist
            res = requests.post(self.api_base 
                    + self.api_tags.format(self.my_site)+'/new', 
                    headers = self.headers,
                    data = payload)
            reply = json.loads(res.text)
            if 'ID' in reply:
                idTags.append(reply['ID'])
            else:
                res = requests.get(self.api_base + self.api_tags.format(self.my_site)) 
                result = json.loads(res.text)
                for ttag in result['tags']:
                    if ttag['name'] == tag:
                        idTags.append(ttag['ID'])
                        
        return(idTags)

    def publishPost(self, post, link='', comment='', tags=[]):
        logging.debug("     Publishing in Wordpress...")
        title = post
        #if comment != None: 
        #    title = comment 
        res = None
        try:
            print("     Publishing: %s" % post)
            logging.info("     Publishing: %s" % post)
            self.api_base2 = 'https://avecesunafoto.wordpress.com/?rest_route=/wp/v2/posts'
            # The tags must be checked/added previously
            idTags = self.checkTags(tags)
            print(idTags)
            idTags = ','.join(str(v) for v in idTags)
            print(idTags)
            payload = {"title":title,"content":comment,"status":'draft', 
                    'tags':idTags}
            print("payload", payload)
            self.api_base2 = 'https://public-api.wordpress.com/wp/v2/'
            res = requests.post(self.api_base2 
                    + self.api_posts.format(self.my_site), 
                    headers = self.headers,
                    data = payload)
            print(res)
            print(res.text)


            if res: 
                logging.info("Res: %s" % res)
                #urlTw = "https://twitter.com/%s/status/%s" % (self.user, res['id'])
                #logging.info("     Link: %s" % urlTw)
                #return(post +'\n'+urlTw)

        #except twitter.api.TwitterHTTPError as twittererror:        
        #    for error in twittererror.response_data.get("errors", []): 
        #        logging.info("      Error code: %s" % error.get("code", None))
        #    return(self.report('Twitter', post, link, sys.exc_info()))
        except:        
            print("Fail")
            print(self.report('Wordpress', post, link, sys.exc_info()))
            logging.info("Fail!")
            return(self.report('Wordpress', post, link, sys.exc_info()))
        return 'OK'

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
        if not posts or (i>=len(posts)):
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
        theImage=[]
        if 'content' in post:
            soupImg = BeautifulSoup(post['content'], 'lxml')
            imgs = soupImg.find_all('img')
            for i in imgs: 
                theImage.append(i.get('data-large-file').split('?')[0])
            #if not isinstance(theImage, str):
            #    theImage = theImage[0]
        elif 'attachments' in post:
            for key in post['attachments']:
                print(post['attachments'])
                if 'URL' in post['attachments'][key]:
                    theImage = post['attachments'][key]['URL']
        else:
            print("Fail image")
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
    for i,post in enumerate(wp.getPosts()):
        print("{}) {} {}".format(i, wp.getPostTitle(post), 
            wp.getPostLink(post)))

    sel = input('Select one ')
    pos =  int(sel)
    post = wp.getPosts()[pos]
    print("{}) {} {}".format(pos, wp.getPostTitle(post), 
            wp.getPostLink(post)))
    sys.exit()


    #pos = wp.getLinkPosition('https://avecesunafoto.wordpress.com/2020/03/10/gamoncillo/')
    #img = wp.obtainPostData(pos)
    #print(img)
    #if img[3]:
    #    print(img[3])
    #    print(len(img[3]))
    ##for i in img[3]:
    #    #resizeImage(i)
    #    #input('next?')

    print("Testing posting")
    print(title, post)

    sys.exit()
    wp.publishPost(post, '', title)


    sys.exit()
    for i, post in enumerate(wp.getPosts()):
        print("p",i, ") ", post)
        #print("@%s: %s" %(tweet[2], tweet[0]))

    print(pos)
    print(wp.getPosts()[pos])
    title = wp.obtainPostData(pos)
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

