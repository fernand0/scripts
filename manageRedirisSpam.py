#!/usr/bin/env python


import ConfigParser
import os
import sys
import re
import logging
import keyring
import getpass
from robobrowser import RoboBrowser
# https://github.com/jmcarp/robobrowser

# This program tries to provide a command line interface for the put.rediris.es
# web application. It is intended for managing spam in academic accounts whose
# organizations have subscribed the service. I'm quite happy with the service
# but I'd prefer to have an IMAP interface or somethin like that. For this
# reason I'm programming this program that can interact with the web site
# without having to use a broswer. I think this approach is way more adequate,
# at least for me. I'll try to improve usability, capabilities and son on,
# because in the actual state the usage is pretty basic and primitive.

# Next message.
# Spam: https://puc.rediris.es/users/index.php?set_proxy_panel=PROXY_USER&pageID=2
# Valid: https://puc.rediris.es/users/index.php?set_proxy_panel=PROXY_USER&action=showValidMail&pageID=2

def getPassword(server, user):
    # Deleting keyring.delete_password(server, user)
    password = keyring.get_password(server, user)
    if not password:
        logging.info("[%s,%s] New account. Setting password" % (server, user))
        password = getpass.getpass()
        keyring.set_password(server, user, password)
    return password

def selectCategory(logging):        
    categories = ['showSpam', 'showValidMail', 'showPendingValidationMail', 'showMailingList', 'showVirusWarnings', 'showNotifications', 'showTrash']
         
    i = 0
    for cat in categories:
        print "%d) %s"% (i, cat)
        i = i + 1

    sel = raw_input("Category? ")

    return categories[int(sel)]

def selectCategoryLink(logging, catName, links):
    i = 0
    j = -1
    for link in links:
       if link['href'].find('action=show')>0:
           if link['href'].find(catName)>0:
               j = i
               cat = catName
       i = i + 1

    return links[j]


def listMessages(logging, browser, link):		

    linkFollowing = link
    page = 0
    listMsg = []
    linkMsg = []

    while (linkFollowing):
        linkMsg.append(linkFollowing)
        browser.follow_link(linkFollowing)
        forms = browser.get_forms()
        
        if len(forms) >= 4:
            form  = forms[3]
        # We need a copy
            options = list(form['mails[]'].options)
            options.reverse()
            
            logging.debug("Message ids %s" % options)

            trList = browser.find_all("tr")
            subjects = {}
            
            for row in trList:
                cellsS = row.find_all("td", { "class" : "subject clickable"})
                cellsA = row.find_all("td", { "class" : "sender clickable"})
                if cellsS:
            	    listMsg.append((options.pop(), cellsA[0]['title'], cellsS[0]['title'], page))
            
            links = browser.get_links()
            matches = list(x for x in links if (x.contents and x.contents[0].find('siguiente') >= 0))
            if matches:
                linkFollowing = matches[0]
                page = page + 1
            else:
                linkFollowing = ""
            logging.debug("Link following %s"% linkFollowing)
        else:
             listMsg = []
             form = []
    #print len(listMsg), listMsg
    #print linkMsg
    return (listMsg, form, linkMsg)

def showMessages(logging, listMsg):		
    i = 0
    numMsg = len(listMsg)
    #if numMsg > 10:
    #    numMsg = 10
    for row in listMsg[0:numMsg]:
    	    print "%2d) %-20s %-40s" % (i, listMsg[i][1][:25], listMsg[i][2][:50])
    	    i = i + 1
    if len(listMsg) > 10:
        print "%2d) Next page" % i

def selectMessageText(logging, browser, text, link):
    links = link
    (listMsg, form, linkMsg) = listMessages(logging, browser, links)
    for line in listMsg:
        if (line[2].find(text)>=0):
            return (line, linkMsg)

    return ("","")

def selectMessages(logging, browser, link):
    links = link
    sel = '10'
    while (sel <> 'a') and (int(sel) == 10):
        (listMsg, form, linkMsg) = listMessages(logging, browser, links)
        if listMsg:
            showMessages(logging, listMsg)
            sel = raw_input("Message? (number for message to be moved to valid/spam mail, 'a' for deleting all messages shown) ")
            if (sel <> 'a'):
                if (int(sel) == 10):
                    links = listMsg[10]
                elif int(sel) + 1 > len(listMsg):
                    links = link
                    sel = 10
        else:
            sel = '11'
            form = []
    return (sel, form, listMsg)

def main():
    config = ConfigParser.ConfigParser()
    config.read([os.path.expanduser('~/.SERVERS.cfg')])
    
    i = 1
    print "Configured accounts:"
    for section in config.sections():
        print '%s) %s' % (str(i), section)
        i = i + 1
    selection = raw_input('Select one: ')

    logging.basicConfig(#filename='example.log',
                        level=logging.INFO,format='%(asctime)s %(message)s')
    SERVER = config.get(config.sections()[int(selection) - 1], 'server')
    USER = config.get(config.sections()[int(selection) - 1], 'user')
    PASSWORD = getPassword(SERVER, USER)

    url = 'https://'+SERVER+'/'

    browser = RoboBrowser(history=True)
    browser.open(url)
    form = browser.get_form(action='')
    form['login'].value = USER
    form['pass'].value = PASSWORD
    
    browser.submit_form(form)
    texts = browser.find_all(text=True) 
    for line in texts:
        if line.find('Incorrect')>0:
            logging.info("[%s,%s] New account. Setting password" % (SERVER, USER))
            password = getpass.getpass()
            keyring.set_password(SERVER, USER, password)
            sys.exit()
   
    urlIndex = url + 'users/index.php'
    while True:
        
        browser.open(urlIndex)
        links = browser.select('a')
        
        catName = selectCategory(logging)
        link = selectCategoryLink(logging, catName, links)

        if (link):
            if len(sys.argv) >= 3:
                if sys.argv[1] == "-s":
                     (line, linkMsg) = selectMessageText(logging, browser, sys.argv[2], link)
                     if line:
                         print "Borramos? ", line
                         browser.follow_link(linkMsg[line[3]]) 
                         forms = browser.get_forms()
                         if len(forms) >= 4:
                             form  = forms[3]
                             form['mails[]'].value = [line[0]]
                             form['action'] = 'spamEmailsFrom_mailarch'
                             browser.submit_form(form)
                     else:
                         print "Not found ", sys.argv[2]
        
            else:
                (sel, form, listMsg) = selectMessages(logging, browser, link)
	
                if (sel == 'a'):
                    # Select just one
                    print form['mails[]'].options
                    form['mails[]'].value = form['mails[]'].options
                    form['action'] = 'deleteEmailsFrom_spam'
                    #deleteEmailsFrom_spam
                    #noSpamEmailsFrom_spam
                    #spamEmailsFrom_mailarch
                    print 'Options:', form['globalSelector'].options
                    print 'Selector:', form['globalSelector'].value
                    browser.submit_form(form)
                    urlIndex = url + 'users/index.php'
                elif (int(sel) < 10):
                    # Select just one
                    print sel, i
                    print [listMsg[int(sel)][0]]
                    form['mails[]'].value = [listMsg[int(sel)][0]]
                    
                    print "marked ", form['mails[]'].value
                    
                    print form
                
                    if cat == 'showSpam':
                        form['action'] = 'noSpamEmailsFrom_spam'
                    elif cat == 'showValidMail':
                        form['action'] = 'spamEmailsFrom_mailarch'
                    elif cat == 'showMailingList':
                        form['action'] = 'spamEmailsFrom_lists'
                    print form['globalSelector'].options
                    print form['globalSelector'].value
                    browser.submit_form(form)
                    urlIndex = url + 'users/index.php'

if __name__ == '__main__':
    main()
