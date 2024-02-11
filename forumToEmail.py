from bs4 import BeautifulSoup
import configparser
import requests
import time
import sys

import socialModules
from socialModules.configMod import *
import socialModules.moduleForum
from socialModules.moduleContent import *

def main(): 

    import socialModules
    
    logging.basicConfig(stream=sys.stdout, 
                        level=logging.INFO, 
                        format='%(asctime)s %(message)s')

    config = configparser.ConfigParser()
    config.read(CONFIGDIR + '/.rssForums') 
    
    thePosts = {}

    numPosts = 0
    numForums = 0
    for i,forumData in enumerate(config.sections()): 
        name = (str(i), forumData)
        forum = socialModules.moduleForum.moduleForum() 
        forum.setClient(forumData) 
        forum.setPostsType('posts')
        forum.setPosts()
        lastLink, lastTime = checkLastLink(forum.url)
        logging.debug(f"lastLink {lastLink}")
        pos = forum.getLinkPosition(lastLink)
        posts = forum.getPosts()
        if posts: 
            numForums = numForums + 1
            logging.debug(f"Position: {pos} Len: {len(posts)}")

            if pos == len(forum.getPosts()):
                posts.append(("No new posts!",'',''))
            else: 
                link = None
                posts = []
                for post in forum.getPosts()[pos:]:
                    numPosts = numPosts + 1
                    title = post[0].split('\n')[0]
                    link  = post[1]
                    posts.append((title, link, ''))
                logging.debug(f"Posts: {posts}")
                logging.debug(f"Forum: {forum.url}")
                logging.debug(f"Link: {link}")

                if link: 
                    # As in buffer.py (err-buffer)
                    updateLastLink(forum.url, link)
        else:
            logging.debug(f"No posts")

        thePosts[name] = posts

    compResponse = []
    for socialNetwork in thePosts.keys():
        theUpdates = []
        if not thePosts[socialNetwork]:
            continue
        # print(f"sN: {socialNetwork} thePosts: {thePosts[socialNetwork]}")
        for update in thePosts[socialNetwork]:
            if update:
                if len(update)>0:
                    logging.debug("Update %s " % str(update))
                    logging.debug("Update %s " % update[0])
                    if update[0]:
                        theUpdatetxt = update[0].replace('_','\_')
                    else:
                        # This should not happen
                        theUpdatetxt = ''
                    if len(update)>2:
                        theUpdates.append((theUpdatetxt, update[1], update[2])) 
                    else:
                        theUpdates.append((theUpdatetxt, update[1], '')) 

                        #time.strftime("%Y-%m-%d-%H:%m", 
        if thePosts[socialNetwork]: 
            if theUpdates[0][0] != 'Empty': 
                socialTime = theUpdates[0][2] 
            else: 
                socialTime = ""
        else:
            socialTime = ""
    
        tt = 'pending'
        if theUpdates: 
            compResponse.append((tt, 
                socialNetwork[0].capitalize()
                                 +' ('+socialNetwork[1]+')', theUpdates))

    from jinja2 import Environment, FileSystemLoader
    env = Environment( 
            loader=FileSystemLoader(searchpath="/home/ftricas/usr/src/scripts/")) 
    template = env.get_template('buffer.html')
    response = ''
    for rep in compResponse:
        response = response + template.render({'type': rep[0],
                        'nameSocialNetwork': rep[1], 
                        'updates': rep[2]})
    response = f"{response}"

    logging.info(f"Resp: {response}")
    from datetime import date
    today = date.today()
    response = f"Forums: {today}\n{response}"
    logging.info(f"Sending mail. numPosts {numPosts} {numForums}")

    # logging.info(f"Response: {response}")

    if numPosts > numForums: #There is an inactive forum
        import socialModules.moduleSmtp
        smtpServer = socialModules.moduleSmtp.moduleSmtp()

        smtpServer.setClient('ftricas@elmundoesimperfecto.com')
        logging.info(smtpServer.publishPost(response, 
                                            f"Forums {format(time.asctime())}",  
                                            f'<html><body>{response}'
                                            f'</body></html>'))

if __name__ == '__main__':
    main()
