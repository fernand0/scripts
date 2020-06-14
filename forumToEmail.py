
from bs4 import BeautifulSoup
import configparser
import requests
import time
import moduleForum

from moduleContent import *
from configMod import *


def main(): 
    config = configparser.ConfigParser()
    config.read(CONFIGDIR + '/.rssForums') 
    
    thePosts = {}

    for i,forumData in enumerate(config.sections()): 
        name = (str(i), forumData)
        forum = moduleForum.moduleForum() 
        forum.setClient(forumData) 
        forum.setPosts()
        lastLink, lastTime = checkLastLink(forum.url)
        pos = forum.getLinkPosition(lastLink)
        posts = []

        if pos == len(forum.getPosts()) - 1:
            posts.append(("No new posts!",'',''))
        else: 
            for post in forum.getPosts()[pos:]:
                title = post[0].split('\n')[0]
                link  = post[1]
                posts.append((title, link, ''))
        thePosts[name] = posts

    compResponse = []
    for socialNetwork in thePosts.keys():
        theUpdates = []
        for update in thePosts[socialNetwork]:
            if update:
                if len(update)>0:
                    logging.info("Update %s " % str(update))
                    logging.info("Update %s " % update[0])
                    if update[0]:
                        theUpdatetxt = update[0].replace('_','\_')
                    else:
                        # This should not happen
                        theUpdatetxt = ''
                    theUpdates.append((theUpdatetxt, update[1], update[2])) 
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
                socialNetwork[0].capitalize()+' ('+socialNetwork[1]+')', theUpdates))

    #print(compResponse)
    from jinja2 import Environment, FileSystemLoader
    env = Environment( 
            loader=FileSystemLoader(searchpath=".")) 
    template = env.get_template('buffer.html')
    response = ''
    for rep in compResponse:
        response = response + template.render({'type': rep[0],
                        'nameSocialNetwork': rep[1], 
                        'updates': rep[2]})

 
    import moduleSmtp
    smtpServer = moduleSmtp.moduleSmtp()

    smtpServer.setClient('fernand0')
    smtpServer.publishPost(response, 'Forums {}'.format(time.asctime()), 'fernand0@elmundoesimperfecto.com')

if __name__ == '__main__':
    main()
