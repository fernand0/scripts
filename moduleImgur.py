import configparser
import json
import logging
import sys
import time

from imgurpython import ImgurClient

from moduleContent import *
from moduleQueue import *
from configMod import *

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
                logging.debug("{} {} {}".format(time.ctime(album.datetime),
                    i, album.title))
                text = ""
                if album.in_gallery: 
                    self.posts.insert(0,album)
                else:
                    self.drafts.insert(0,album)
        else:
            logging.warning('No client configured!')
        self.posts = self.posts[-20:]
        # We set some limit
                    
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
            thePost = self.getImagesCode(i)
            theTags = self.getImagesTags(i)
        else:
            theTitle = None
            theLink = None
            thePost = None
            theTags = None

        return (theTitle, theLink, None, None, None, None, None, None, theTags, thePost)



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

    def extractImages(self, post):
        theTitle = self.getPostTitle(post)
        theLink = self.getPostLink(post) 
        page = urlopen(theLink).read() 
        soup = BeautifulSoup(page,'lxml') 

        res = []
        script = soup.find_all('script')
        pos = script[9].text.find('image')
        pos = script[9].text.find('{',pos+1)
        pos2 = script[9].text.find('\n',pos+1)
        data = json.loads(script[9].text[pos:pos2-1])
        title = data['title']
        for img in data['album_images']['images']:
            urlImg = 'https://i.imgur.com/{}.jpg'.format(img['hash'])
            if 'description' in img:
                titleImg = img['description']
                if titleImg:
                    description = titleImg.split('#')
                    description, tags = description[0], description[1:]
                    aTags= []
                    while tags: 
                        aTag = tags.pop().strip()
                        aTags.append(aTag) 
                    tags = aTags
                else:
                    description = ""
                    tags = []
            else:
                titleImg = ""
            res.append((urlImg,title, description, tags))
        return res

def main(): 

    logging.basicConfig(stream=sys.stdout, 
            level=logging.INFO, 
            format='%(asctime)s %(message)s')

    config = configparser.ConfigParser()
    config.read(CONFIGDIR + '/.rssBlogs')
    sections=["Blog21"]
    for section in sections:
        img = moduleImgur()
        img.setUrl('https://imgur.com/user/ftricas') 
        img.setClient('ftricas') 
        if 'posts' in config.options(section):
            img.setPostsType(config.get(section, 'posts'))
        print(img.getPostsType())
        img.setPosts()
        print("---- Posts ----")
        for i, post in enumerate(img.getPosts()):
            print(img.getPostTitle(post))
            #print(img.getImagesCode(i))
        print("---- Drafts ----")
        for post in img.getDrafts():
            print(img.getPostTitle(post))
        print("----.")
        time.sleep(2)
    pos=3
    post = img.getImages(pos)
    postWP = img.getImagesCode(pos)
    title = img.getPostTitle(img.getPosts()[pos])
    tags = img.getImagesTags(pos)
    print("---post images ----")
    print(post)
    print("---title----")
    print (title)
    print("---postWP----")
    print(postWP)
    print("---tags----")
    print(tags)

    # Testing Wordpress publishing
    img.setSocialNetworks(config, section)
    print(img.getSocialNetworks())
    service='wordpress'
    socialNetwork = (service, img.getSocialNetworks()[service])

    import moduleWordpress
    wp = moduleWordpress.moduleWordpress()
    wp.setClient('avecesunafoto')


    print(wp.publishPost(title, '', postWP, tags=post[-1]))
 
    sys.exit()
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
