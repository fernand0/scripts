
from bs4 import BeautifulSoup
import configparser
import logging
import requests
import time

from moduleContent import *
from moduleQueue import *
from configMod import *

class moduleForum(Content,Queue):

    def __init__(self):
        super().__init__()
        self.url = ''
        self.selected = None
        self.selector = None
        self.idSeparator = None
        self.service = None
        self.max = 15

    def setClient(self, forumData):
        """
        [http://foro.infojardin.com/]
        forums:Identificar cactus
               9. Cactusi
               10. Suculentas (no cactáceas)
        selector:nodeTitle
                 PreviewTooltip
        idSeparator:.
        [https://cactiguide.com/forum/]
        forums:General-Succulents
               Cacti Identification
               Succulent Identification
        selector:forumtitle
                 topictitle
        idSeparator:=
        """
        try:
            config = configparser.ConfigParser()
            config.read(CONFIGDIR + '/.rssForums') 
            
            self.url = forumData 
            self.selected = config.get(self.url,'forums').split('\n') 
            self.selector = config.get(self.url,'selector').split('\n')
            self.idSeparator = config.get(self.url,'idSeparator')
        except:
            logging.warning("Forum not configured!")
            logging.warning("Unexpected error:", sys.exc_info()[0])
        self.service = 'Forum'

    def getLinks(self, url, idSelector): 
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    
        selector = self.selector[idSelector]
        response = requests.get(url, headers=headers) 
        soup = BeautifulSoup(response.content, features="lxml")
        links = soup.find_all(class_=selector)
        return(links)
    
    def getClient(self):
        return self
    
    def setPosts(self): 
        url = self.url
        selected = self.selected
        selector = self.selector
        idSeparator = self.idSeparator

        logging.info("-----------------------------")
        logging.info(url)
        logging.info("-----------------------------")
        
        forums = self.getLinks(url, 0)
        
        logging.info(" Reading in ....")
        listId = []
        posts = {}
        for i, forum in enumerate(forums): 
            if forum.name != 'a': 
                # It is inside some other tag
                forum = forum.contents[0]
            text = forum.text 
            if text in selected:
                link = url+forum.get('href') 
                if 'sid' in link:
                    link = link.split('&sid')[0]
                logging.info("  - {} {}".format(text, link))
                links = self.getLinks(link, 1)
                for j, post in enumerate(links): 
                    #print("Info: %s"%str(post))
                    textF = post.text 
                    linkF = url+post.get('href') 
                    if 'sid' in linkF:
                        linkF = linkF.split('&sid')[0]
                    posF = linkF.rfind(idSeparator)
                    if not linkF[-1].isdigit(): 
                        idPost = int(linkF[posF+1:-1])
                    else:
                        idPost = int(linkF[posF+1:])
                    #print("Id: {}".format(idPost))
                    listId.append(idPost)
                    posts[idPost] = [textF, linkF]
        
                time.sleep(1)
        
        listId = sorted(set(listId))
        self.posts = []
        self.lastId = listId[-1]
        for i in listId[-self.max:]:
            self.posts.append(posts[i])

        lastLink, lastTime = checkLastLink(self.url)
        pos = self.getLinkPosition(lastLink)
        if pos < len(self.posts) - 1:
            for i, post in enumerate(self.posts[pos:]):
                self.posts[pos+i][0] = '> {}'.format(self.posts[pos+i][0])
        
    def getPosts(self):
        return self.posts

    def getPostTitle(self, post):
        return post[0]

    def getPostLink(self,post):
        return post[1]

def main(): 
    forums = ['http://foro.infojardin.com/', 'https://cactiguide.com/forum/']
    for forumData in forums: 
        forum = moduleForum() 
        forum.setClient('http://foro.infojardin.com/') 
        forum.setPosts()
        lastLink, lastTime = checkLastLink(forum.url)
        pos = forum.getLinkPosition(lastLink)

        if pos == len(forum.getPosts()) - 1:
            print("No new posts!\n")
        else: 
            for post in forum.getPosts()[pos:]:
                print('   {}'.format(post[0]))
                print('   {}'.format(post[1]))
            updateLastLink(forum.url, forum.getPosts()[-1][1])


if __name__ == '__main__':
    main()
