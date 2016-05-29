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


def getPassword(server, user):
    # Deleting keyring.delete_password(server, user)
    password = keyring.get_password(server, user)
    if not password:
        logging.info("[%s,%s] New account. Setting password" % (server, user))
        password = getpass.getpass()
        keyring.set_password(server, user, password)
    return password

def listMessages(logging, browser, link):		
    browser.follow_link(link)
    forms = browser.get_forms()
    
    if len(forms) >= 4:
        form  = forms[3]
    # We need a copy
    options = list(form['mails[]'].options)
    options.reverse()
    
    logging.debug("Message ids %s" % options)

    trList = browser.find_all("tr")
    subjects = {}
    
    listMsg = []
    for row in trList:
        cellsS = row.find_all("td", { "class" : "subject clickable"})
        cellsA = row.find_all("td", { "class" : "sender clickable"})
        if cellsS:
    	    listMsg.append((options.pop(), cellsA[0]['title'], cellsS[0]['title']))
    
    return listMsg

def showMessages(logging, listMsg):		
    i = 0
    for row in listMsg:
    	    print i,")", listMsg[i]
    	    i = i + 1
    print i,") Next page" 

def selectMessages(logging, listMsg):
    showMessages(logging, listMsg)

def main():
    config = ConfigParser.ConfigParser()
    config.read([os.path.expanduser('~/.SERVERS.cfg')])
    sections=config.sections()
    
    logging.basicConfig(#filename='example.log',
                        level=logging.INFO,format='%(asctime)s %(message)s')
    for section in sections:
        if section == 'SPAM':
            SERVER = config.get(section, 'server')
            USER = config.get(section, 'user')
            PASSWORD = getPassword(SERVER, USER)
        else:
            logging.error("No spam account configured, check for the existence of ~/.SERVERS.cfg")
            sys.exit()

    url = 'https://'+SERVER+'/'

    browser = RoboBrowser(history=True)
    browser.open(url)
    form = browser.get_form(action='')
    form['login'].value = USER
    form['pass'].value = PASSWORD
    
    browser.submit_form(form)
    
    urlIndex = url + 'users/index.php'
    while True:
        
        browser.open(urlIndex)
        links = browser.select('a')
        i = 0
        categories = ['showSpam', 'showValidMail', 'showPendingValidationMail', 'showMailingList', 'showVirusWarnings', 'showNotifications', 'showTrash']
         
        for cat in categories:
            print "%d) %s"% (i, cat)
            i = i + 1
        
        sel = raw_input("Category? ")
        
        i = 0
        j = -1
        for link in links:
            if link['href'].find('action')>0:
                if link['href'].find(categories[int(sel)])>0:
                    j = i
                    cat = categories[int(sel)]
            i = i + 1
        
        if (j>=0):
            listMsg = listMessages(logging, browser, links[j])
            selectMessages(logging, listMsg)
	
            sel = raw_input("Message? (number for message to be moved to valid/spam mail, 'a' for deleting all messages shown) ")
            
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
            elif (int(sel) < i):
                # Select just one
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
            else:
                urlIndex = url + 'users/index.php?action=showValidMail&pageID=2'

if __name__ == '__main__':
    main()
