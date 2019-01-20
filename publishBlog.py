#!/usr/bin/env python

import os, time
import configparser
import moduleXmlrpc
# https://github.com/fernand0/scripts/blob/master/moduleXmlrpc.py

from configMod import *

def archive(blogId, blogName, blogUrl, text, postId): 
    theTime = time.localtime(time.time())
    path = os.path.join(os.path.expanduser('~') , 'Documents/bitacoras/archivo')
    path = '%s/%s/%s'%(path,blogId,time.strftime("%Y/%m", theTime))
    if not os.path.isdir(path):
	    os.makedirs(path)
    fileName = '%s/historia-%s'%(path,time.strftime("%Y%m%d%H%M%S",theTime))
    #fileName = '%s/%s/historia-%s'%(path,blogId,time.strftime("%Y%m%d%H%M%S",time.localtime(time.time())))
    fPost = open(fileName,'w')
    fPost.write(text)
    fPost.write('\n Dónde:')
    fPost.write(blogName)
    fPost.write('\n URL:')
    fPost.write(blogUrl)
    fPost.write('/historias/')
    fPost.write(str(postId))
    fPost.write('\n')
    fPost.close() 
    print('Historia guardada en %s' % fileName)
    return fileName, blogUrl[:-1]+'.blogalia.com/historias/'+str(postId)

def post(): 
    f = open('historia', "r")
    title = f.readline().strip()
    text = title
    title = title.encode('ascii', 'xmlcharrefreplace') 
    body  = f.read()
    text = text + '\n' + body
    body = body.encode('ascii', 'xmlcharrefreplace')  
    return(title, body, text)

def main():
    selOp = input ("""
        Choose one: 
        u)pdate post
        n)ew post
        d)delete post
        -> """)
    print("You have chosen ", selOp)

    config = configparser.ConfigParser()
    config.read(CONFIGDIR + '/.rssBlogs')

    blog = moduleXmlrpc.moduleXmlrpc()

    section = config.sections()[1]
    url = config.get(section, "url")
    rpc = config.get(section, "xmlrpc")
    print(url+rpc)
    blog.setUrl(url)
    blog.setXmlRpc()

    if selOp == 'u': 
        print("Updating ... %s\n"% blog.getUrl())
        title, postId = blog.selectPost()
        title, body, text = post()
        print(postId,type(postId))
        postId = blog.editPost(postId, title, body)
        fileName, theUrl = archive(blog.Id, blog.name, blog.url, text, postId)
    elif (selOp == 'n'):
        print("Sending ... %s\n"% blog.getUrl())
        title, body, text = post() 
        postId = blog.newPost(title, body)
        #postId = '12345'
        fileName, theUrl = archive(blog.Id, blog.name, blog.url, text, postId)
    elif (selOp == 'd'):
        print("Deleting ... %s\n"% blog.getUrl())
        title, postId = blog.selectPost()
        blog.deletePost(postId)
 


if (__name__ == '__main__'):
    main()
