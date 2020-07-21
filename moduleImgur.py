import configparser
import logging
import time

from imgurpython import ImgurClient

from moduleContent import *
from moduleQueue import *
from configMod import *
from imgUrl import *
# Publication pending

class moduleImgur(Content,Queue):

    def __init__(self):
        super().__init__()

    def setClient(self, idName):
        if isinstance(idName, str): 
            self.name = idName
        else:
            self.name = idName[1][1]

        try:
            config = configparser.ConfigParser()
            config.read(CONFIGDIR + '/.rssImgur') 

            if config.sections(): 
                self.client_id=config.get(self.name, 'client_id') 
                self.client_secret=config.get(self.name, 'client_secret') 
                self.access_token=config.get(self.name, 'access_token') 
                self.refresh_token=config.get(self.name, 'refresh_token')

                self.client = ImgurClient(self.client_id, 
                            self.client_secret, self.access_token, 
                            self.refresh_token)
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
        self.drafts = []
        client = self.getClient()
        if client:
            for i,album in enumerate(client.get_account_albums(self.name)):
                import time
                logging.debug("{} {} {}".format(time.ctime(album.datetime),
                    i, album.title))
                text = ""
                if album.in_gallery: 
                    self.posts.insert(0,album)
                else:
                    self.drafts.insert(0,album)
        else:
            logging.warning('No client configured!')
                    
    def getPostTitle(self, post):
        return post[0]

    def getPostLink(self,post):
        return post[1]

    def getPostTitle(self, post):
        return post.title

    def getPostLink(self,post):
        return post.link

    def getLinkPosition(self, lastLink): 
        if hasattr(self, 'getPostsType'): 
            if self.getPostsType() == 'drafts': 
                posts = self.drafts 
            else: 
                posts = self.posts

            for i, post in enumerate(posts):
                if not (post.link in lastLink):
                    return(i+1)
        return -1

    def extractDataMessage(self, i):
        if hasattr(self, 'getPostsType'):
            if self.getPostsType() == 'drafts':
                posts = self.getDrafts()
            else:
                posts = self.getPosts()
        if i < len(posts):
            post = posts[i]
            logging.info("Post: %s"% post)
            theTitle = self.getPostTitle(post)
            theLink = self.getPostLink(post)
        else:
            theTitle = None
            theLink = None
        res = downloadUrl(self.getPostLink(post))
        print(res)
        text = '' 
        for iimg in res: 
            text = '{}\n<p><a href="{}"><img class="alignnone size-full wp-image-3306" src="{}" alt="" width="776" height="1035" /></a></p>'.format(text,iimg[0],iimg[1])


        return (theTitle, theLink, None, None, None, None, None, None, None, text)



    def publishPost(self, post, link='', comment=''):
        logging.debug("     Publishing in Imgur...")
        #if comment != None: 
        #    post = comment + " " + post
        try:
            logging.info("     Publishing: %s" % post) 
            print(post)
            print(link)
            # Very dirty, we need to work on this. Sometimes we need identifiers
            idPost = link.split('/')[-1]
            #idPost = self.posts[j].id 
            api = self.getClient() 
            try: 
                res = api.share_on_imgur(idPost, post, terms=0)            
                logging.info("Res: %s" % res) 
                if res: 
                    return('OK') 
            except:
                return("Fail")
        except:
            return("Fail")
        

        return('OK')


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

    config = configparser.ConfigParser()
    config.read(CONFIGDIR + '/.rssBlogs')
    section="Blog20"
    img = moduleImgur()
    img.setUrl('https://imgur.com/user/ftricas') 
    img.setClient('ftricas') 
    img.setPosts()
    print("----")
    for post in img.getPosts():
        print(img.getPostTitle(post))
    print("----")
    for post in img.getDrafts():
        print(img.getPostTitle(post))
    print("----")
    sys.exit()
    img.setSocialNetworks(config, section)
    print(img.getSocialNetworks())
    for service in img.getSocialNetworks():
        socialNetwork = (service, img.getSocialNetworks()[service])
        
        linkLast, lastTime = checkLastLink(img.getUrl(), socialNetwork)
        print("linkLast {} {}".format(socialNetwork, linkLast))
        i = img.getLinkPosition(linkLast)
        print(i)
        print(img.getNumPostsData(2,i))
 
    sys.exit()
    txt = ''
    fileName = fileNamePath(img.url)
    urls = getLastLink(fileName)
    thePost=None
    for i, post in enumerate(img.getPosts()):
        print("{}) {} {}".format(i, img.getPostTitle(post), 
            img.getPostLink(post)))
        #print(img.getPosts()[i])
        if not img.getPostTitle(post).startswith('>'):
            if not (img.getPostLink(post).encode() in urls[0]):
                print("--->",img.getPostTitle(post))
                thePost = post


    if thePost:
        res = downloadUrl(img.getPostLink(thePost))

        print()
        print(res)
        sys.exit()


        #sel = input('Publish? (p/w) ') 

        #if sel == 'p':
        #    print('pubishing! {}'.format(res [0][2]))
        #    print(img.publish(pos))
        #elif sel == 'w':
        print('Wordpressing! {}'.format(res [0][2]))
        import moduleWordpress 
        wp = moduleWordpress.moduleWordpress() 
        wp.setClient('avecesunafoto') 
        title = res [0][2]
        text = '' 
        for iimg in res: 
            text = '{}\n<p><a href="{}"><img class="alignnone size-full wp-image-3306" src="{}" alt="" width="776" height="1035" /></a></p>'.format(text,iimg[0],iimg[1])

        print('----') 
        print(title) 
        print(text) 

        theUrls = [img.getPostLink(thePost).encode(), ] + urls[0]
        wp.publishPost(text, '', title)

        updateLastLink(img.url, theUrls)
        #elif sel == 's':
        #    import pprint
        #    pprint.pprint(img.getPosts()[pos])
        #    pprint.pprint(img.getPosts()[pos].views)
        #    pprint.pprint(time.ctime(img.getPosts()[pos].datetime))
        #    pprint.pprint(img.getPosts()[pos].section)
        #    #pprint.pprint(dir(img.getPosts()[pos]))

        text = ''
        for img in res:
            text = '{}\n<p><a href="{}"><img class="alignnone size-full wp-image-3306" src="{}" alt="" width="776" height="1035" /></a></p>'.format(text,img[0],img[1])

        print("---")
        print(text)



        #print(img.publish(0))
        #img.delete(8)

if __name__ == '__main__':
    main()
