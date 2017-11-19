#!/usr/bin/env python

import os
import moduleBlog
import configparser

def post(): 
    f = open('historia', "r", encoding="latin-1")
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
    config.read([os.path.expanduser('~/.rssBlogs')])

    blog = moduleBlog.moduleBlog()

    section = config.sections()[5]
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
    elif (selOp == 'n'):
        print("Sending ... %s\n"% blog.getUrl())
        title, body, text = post()
        postId = blog.newPost(title, body)
    elif (selOp == 'd'):
        print("Deleting ... %s\n"% blog.getUrl())
        title, postId = blog.selectPost()
        blog.deletePost(postId)

 


if (__name__ == '__main__'):
    main()
