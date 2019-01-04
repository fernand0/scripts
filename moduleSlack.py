#!/usr/bin/env python

import configparser
import pickle
import os
import moduleBlog
import moduleSocial
import urllib
from slackclient import SlackClient
import sys

def listPosts(api, pp = None, service=""):
    outputData = {}

    serviceName = 'Slack'
    outputData[serviceName] = {'sent': [], 'pending': []}
    posts = api.getPostsSlack()
    for post in posts:
        if 'attachments' in post:
            outputData[serviceName]['pending'].append(
                (post['text'][1:-1], post['attachments'][0]['title'], '', '', '', '', '', '', post['ts'], ''))
        else:
            #print(post)
            outputData[serviceName]['pending'].append(
                (post['text'][1:-1], '', '', '', '', '', '', '', post['ts'], ''))
    return(outputData, posts)


