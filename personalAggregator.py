#!/usr/bin/env python

import logging
import pathlib
import sys

# You need to have installed the socialModules (branch dist provides the package installed with its requirements):
#
# https://github.com/fernand0/socialModules/tree/dist
#
# You can fork or clone and install it or, if you trust the project:
# pip install social-modules@git+ssh://git@github.com/fernand0/socialModules@dist
# 
# This will change in the future, when enought test has been done
# 
# Configuration example:
# 
# There are mainly some RSS sites (blogs) and a Twitter account.
# 
# File: ~/.myconfig/social/.rssElmundo
# 
# [Blog1]
# url:http://fernand0.blogalia.com/
# rss:rss20.xml
# posts:posts
# html:
# [Blog2]
# url:http://fernand0.github.io/
# rss:feed.xml
# posts:posts
# html:
# [Blog4]
# url:http://avecesunafoto.wordpress.com/
# rss:feed/
# posts:posts
# html:
# [Blog5]
# url:https://dev.to/fernand0
# rss:https://dev.to/feed/fernand0
# posts:posts
# html:
# [Blog8]
# url:https://twitter.com/fernand0
# posts:posts
# html:

knownServices = ['reddit', 'github', 'flickr', 'goodreads', 
                'youtube', 'wordpress', 'dev.to', 'tumblr',
                ]

def main():

    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG,
            format='%(asctime)s %(message)s')

    import socialModules.moduleRules
    rules = socialModules.moduleRules.moduleRules()
    rules.checkRules(configFile = '.rssElmundo')

    i = 0
    if len(sys.argv) > 1:
        fileName = sys.argv[1]
    else:
        # We will write the messages in /tmp 
        # Later we will move them to our Jekyll directory
        fileName = '/tmp'
        # /2022-10-01-post-
    myFilePath = pathlib.Path(fileName)
    if not myFilePath.is_dir():
        sys.exit('The path should be a directory and it should exist')

    for key in rules.rules.keys():
        apiSrc = rules.readConfigSrc("", key, rules.more[key])

        apiSrc.setPosts()
        posts = apiSrc.getPosts()
        if posts and apiSrc.getPostsType():
            i = i + 1
            # print(f"{i})-> Posts: {posts}")
            postFile = myFilePath.joinpath(f'2022-10-01-post-{i:02}.md')
            with open(postFile,'w') as fSal:
                fSal.write(f'---\n')
                fSal.write(f'layout: post\n')
                fSal.write(f'title:  "{apiSrc.getSiteTitle()}"\n')
                hasService = True
                for service in knownServices:
                    if service in apiSrc.getUrl():
                        fSal.write(f"categories: {service.replace('.','')}\n")
                        hasService = True
                        continue
                if not hasService:
                    fSal.write(f'categories: {key[0]}\n')
                fSal.write(f'---\n')

                for post in posts[:10]: 
                    title = apiSrc.getPostTitle(post) 
                    link = apiSrc.getPostLink(post) 

                    # Some of my posts (mainly in social networks include 
                    # a URL in the title. In these cases we will use this 
                    # link for the title and the other in parentheses
                    pos = title.find('http')
                    posF = title.find(' ', pos + 1)
                    if pos>=0:
                        if posF < pos:
                            posF = len(title)
                        linkT = title[pos:posF]
                        title = title[:pos]
                    else:
                        linkT = link

                    title = (f" [{title}]({linkT})")
                    title = title.replace('|','\|')

                    lineFormat =  {'mastodon': f"* {title} ([toot]({link}))\n",
                                   'twitter':  f"* {title} ([tweet]({link}))\n",
                                   'general':  f"* {title}\n",
                                   }

                    if key[0] in lineFormat:
                        fSal.write(lineFormat[key[0]])
                    else:
                        fSal.write(lineFormat['general'])

    return 

if __name__ == "__main__":
    main()
