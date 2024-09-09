import email
import base64
import io
import time
import logging
import os
import pprint
import configparser

from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
from apiclient.http import MediaIoBaseUpload
from email.parser import BytesParser

import socialModules.moduleImap
import socialModules.moduleGmail

# This program moves all mails with a given label between selected accounts.
# It needs several configuration files:
#
# .oauth.cfg will contain the relevant data of configured accounts:
#
# [ACC1]
# server:server1
# user:user1
# [ACC2]
# server:server2
# user:user2
#
# For each account we will need a json file with the oauth credentials as generated, for example, by:
# https://github.com/gsuitedevs/python-samples/blob/master/gmail/quickstart/quickstart.py
# with name
# .server_user.json
# for example: .server2_user2.json
# in the adequate directory
#
# You can call it with:
#
# python moveMail.py
#
# It will ask about the tag and the account.
# Use it at your own risk



def main():

    PREFIX = 'moveMail'
    logging.basicConfig(filename=os.path.expanduser('~/usr/var/' + PREFIX +
        '.log'), level=logging.INFO, format='%(asctime)s %(message)s')

    try:
        from configMod import CONFIGDIR
    except:
        CONFIGDIR = '·/'

    config = configparser.ConfigParser()
    config.read(CONFIGDIR + '/.oauthG.cfg')

    label = input('Label to move? ')
    print(config.sections()[1])
    for (i, acc) in enumerate(config.sections()):
        print("%d) %s - %s" % (i,acc,config.get(acc,'user')+'@'+config.get(acc,'server')))
    origSec = config.sections()[int(input("Origin: "))]
    destSec = config.sections()[int(input("Destination: "))]
    print("Label: %s" % label)
    print("Moving from: %s" % config.get(origSec,'user')+'@'+config.get(origSec,'server'))
    print("         to: %s" % config.get(destSec,'user')+'@'+config.get(destSec,'server'))

    serviceOrig = socialModules.moduleGmail.moduleGmail()
    serviceOrig.setClient(origSec)
    serviceOrig.setLabels()
    serviceDest = socialModules.moduleGmail.moduleGmail()
    serviceDest.setClient(destSec)
    serviceDest.setLabels()
    labels = serviceOrig.getLabelsIds(label)
    print(labels)
    ok = input('Label ok? (y/n) ')
    if ok != 'y':
        sys.exit()
    serviceOrig.setPosts(label=labels, mode='raw')
    j = 0
    while serviceOrig.getPosts():
        for (i, msg) in enumerate(serviceOrig.getPosts()):
            j = j + 1
            print("Msg: %d" % j)
            if 'raw' in msg:
                logging.info("i: %d, Snippet: %s" % (i, msg['raw']['snippet']))
                logging.info("Result: %s" %
                        serviceDest.copyMessage(msg['raw'], [label]))
                serviceOrig.trash(i,'message')
        serviceOrig.setPosts(label=labels, mode='raw')
        print("Waiting ...")
        time.sleep(5)


if __name__ == "__main__":
    main()
