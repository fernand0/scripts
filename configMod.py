#!/usr/bin/env python
import logging
import os
import urllib

HOME = os.path.expanduser("~")
LOGDIR = HOME + "/usr/var/log"
APPDIR = HOME + "/.mySocial"
CONFIGDIR = APPDIR + "/config"
DATADIR = APPDIR + "/data"

def fileNamePath(url, socialNetwork):
    theName = os.path.expanduser(DATADIR + '/' 
                    + urllib.parse.urlparse(url).netloc 
                    + '_' 
                    + socialNetwork[0] + '_' + socialNetwork[1])
    return(theName)

def getLastLink(fileName):        
    try: 
        with open(fileName, "rb") as f: 
            linkLast = f.read().rstrip()  # Last published
    except:
        # File does not exist, we need to create it.
        with open(fileName, "wb") as f:
            logging.warning("File %s does not exist. Creating it."
                    % fileName) 
            linkLast = ''  
            # None published, or non-existent file
    return(linkLast, os.path.getmtime(fileName))

def checkLastLink(url, socialNetwork=()):
    # Redundant with moduleCache
    if not socialNetwork: 
        fileNameL = (DATADIR  + '/' 
               + urllib.parse.urlparse(url).netloc + ".last")
    else:
        fileNameL = fileNamePath(url, socialNetwork)+".last"
    logging.debug("Checking last link: %s" % fileNameL)
    (linkLast, timeLast) = getLastLink(fileNameL)
    return(linkLast, timeLast)

def updateLastLink(url, link, socialNetwork=()):
    if not socialNetwork: 
        fileName = (DATADIR  + '/' 
               + urllib.parse.urlparse(url).netloc + ".last")
    else: 
        fileName = fileNamePath(url, socialNetwork) + ".last"

    with open(fileName, "w") as f: 
        f.write(link)


