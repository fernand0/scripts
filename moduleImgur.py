import configparser
import logging
import time

from imgurpython import ImgurClient

from moduleContent import *
from moduleQueue import *
from configMod import *
from imgUrl import *

class moduleImgur(Content,Queue):

    def __init__(self):
        super().__init__()

    def setClient(self, idName):
        self.name = idName

        try:
            config = configparser.ConfigParser()
            config.read(CONFIGDIR + '/.rssImgur') 

            if config.sections(): 
                self.client_id=config.get(self.name, 'client_id') 
                self.client_secret=config.get(self.name, 'client_secret') 
                self.access_token=config.get(self.name, 'access_token') 
                self.refresh_token=config.get(self.name, 'refresh_token')

                self.client = ImgurClient(self.client_id, self.client_secret, 
                    self.access_token, self.refresh_token)
            else:
                logging.warning("Some problem with configuration file!")
                self.client = None

        except:
            logging.warning("User not configured!")
            logging.warning("Unexpected error:", sys.exc_info()[0])

        self.service = 'Imgur'

    def getClient(self):
        return self.client

    def setPosts(self): 
        self.posts = []
        client = self.getClient()
        if client:
            for i,album in enumerate(client.get_account_albums(self.name)):
                import time
                logging.info(i,album.title, time.ctime(album.datetime))
                logging.info(album.layout)
                text = ""
                self.posts.append(album)
                if not album.in_gallery: 
                    text = ">"
                    self.posts[-1].title = "> {}".format(self.posts[-1].title)
                import time
                text = "{} {} {}".format(text, time.ctime(album.datetime), 
                        self.getPostTitle(album))
                logging.debug(text)
        else:
            logging.warning('No client configured!')
                    
                
    def getPosts(self):
        return self.posts

    def getPostTitle(self, post):
        return post[0]

    def getPostLink(self,post):
        return post[1]

    def getPostTitle(self, post):
        return post.title

    def getPostLink(self,post):
        return post.link

    def publish(self, j):
        logging.info("Publishing %d"% j)                
        logging.info("servicename %s" %self.service)
        idPost = self.posts[j].id
        title = self.getPostTitle(self.posts[j])
        
        api = self.getClient()
        try:
            res = api.share_on_imgur(idPost, title, terms=0)            
            logging.info("Res: %s" % res)
            return(res)
        except:
            return("Fail")

        return("%s"% title)


    def delete(self,j):
        logging.info("Deleting %d"% j)
        post = self.obtainPostData(j)
        logging.info("Deleting %s"% post[0])
        idPost = self.posts[j].id
        logging.info("id %s"% idPost)
        logging.info(self.getClient().album_delete(idPost))
        sys.exit()
        self.posts = self.posts[:j] + self.posts[j+1:]
        self.updatePostsCache()

        logging.info("Deleted %s"% post[0])
        return("%s"% post[0])

def main(): 

    img = moduleImgur()
    img.setClient('ftricas') 
    img.setPosts()
    for i, post in enumerate(img.getPosts()):
        print("{}) {} {}".format(i, img.getPostTitle(post), 
            img.getPostLink(post)))
        print(img.getPosts()[i])

    sel = input('Select one ')

    pos =  int(sel)
    res = downloadUrl(img.getPostLink(img.getPosts()[pos]))

    print()
    print(res)

    sel = input('Publish? (p/w) ') 

    if sel == 'p':
        print('pubishing! {}'.format(res [0][2]))
        print(img.publish(pos))
    elif sel == 'w':
        print('Wordpressing! {}'.format(res [0][2]))
        import moduleWordpress 
        wp = moduleWordpress.moduleWordpress() 
        wp.setClient('avecesunafoto') 
        title = res [0][2]
        text = '' 
        for img in res: 
            text = '{}\n<p><a href="{}"><img class="alignnone size-full wp-image-3306" src="{}" alt="" width="776" height="1035" /></a></p>'.format(text,img[0],img[1])

        print('----') 
        print(title) 
        print(text) 

        wp.publishPost(text, '', title)

    text = ''
    for img in res:
        text = '{}\n<p><a href="{}"><img class="alignnone size-full wp-image-3306" src="{}" alt="" width="776" height="1035" /></a></p>'.format(text,img[0],img[1])

    print("---")
    print(text)



    #print(img.publish(0))
    #img.delete(8)

if __name__ == '__main__':
    main()
