#!/usr/bin/env python


import configparser
import os
import sys
import re
import logging
import keyring
import getpass
from robobrowser import RoboBrowser
from requests import Session
from robobrowser import RoboBrowser

import time

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC



# https://github.com/jmcarp/robobrowser

# This program tries to provide a command line interface for the puc.rediris.es
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

optTxt = {
          '' : 'No messages',
          'n': 'Nothing to do',
          'a': 'Deleting all'
        } 

def makeConnection(SERVER, USER, PASSWORD):
    url = 'https://'+SERVER+'/'

    chrome_options = Options() 
    chrome_options.add_argument("--headless") 
    chrome_options.binary_location = '/usr/bin/chromium-browser' 
    driver = webdriver.Chrome(executable_path=os.path.expanduser('~/usr/bin/chromedriver'),   chrome_options=chrome_options) 
    driver.get(url)
    time.sleep(1)
    driver.save_screenshot(os.path.join(os.path.dirname(os.path.realpath(__file__)), '/tmp', 'kk1.png'))


    elemU = driver.find_element_by_name("username")
    #while elemU:
    print("Identifying...")
    elemP = driver.find_element_by_name("password")
    elemU.clear()
    elemU.send_keys(USER)
    elemP.clear()
    elemP.send_keys(PASSWORD)

    driver.save_screenshot(os.path.join(os.path.dirname(os.path.realpath(__file__)), '/tmp', 'kk2.png'))

    elemP.send_keys(Keys.RETURN) 
    time.sleep(1)
    #    try: 
    #        elemU = driver.find_element_by_name("username").clear()
    #    except: 
    #        elemU = None

    driver.save_screenshot(os.path.join(os.path.dirname(os.path.realpath(__file__)), '/tmp', 'kk3.png'))

    return driver


    

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
        print("%d) %s"% (i, cat))
        i = i + 1

    sel = input("Category? ")

    if int(sel) < len(categories):
        return categories[int(sel)]
    else:
        return ""

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

def getMessage(logging, browser, link, number, sel):
    browser.follow_link(link)
    forms = browser.get_forms()
    listMsg = []
    selTen = sel % 10
    if len(forms) >= 4:
        form  = forms[3]

        options = list(form['mails[]'].options)
        options.reverse()
        logging.debug("Message ids %s" % options)
        trList = browser.find_all("tr")
        subjects = {}
        i = 0
        for row in trList:
            cellsS = row.find_all("td", { "class" : "subject clickable"})
            cellsA = row.find_all("td", { "class" : "sender clickable"})
            if cellsS:
                if (i == selTen):
                    break
                else:
                    i = i + 1
                    options.pop()

    return options.pop(), cellsA[0]['title'], cellsS[0]['title']

def listMessages(logging, driver):
    tr = []
    i = 0
    while(not tr):
        try:
            driver.save_screenshot(os.path.join(os.path.dirname(os.path.realpath(__file__)), '/tmp', 'kk3'+str(i)+'.png'))
            title = driver.title
            posIni = title.find('(')+1
            posFin = title.find(')')
            if posIni > 0:
                numMsgs = int(title[posIni:posFin])
            else:
                numMsgs = 0
            print("There are ... %d spam messages" % numMsgs)
            tr = driver.find_elements_by_tag_name('td')
            listMsg = []
            #print(len(tr))
            for i in range(numMsgs):
                num = 5*i
                listMsg.append((tr[num], tr[num+1].text,tr[num+2].text, tr[num+3].text, tr[num+4].text))
        except: 
            tr = []
            print("Wait...")
            time.sleep(3)
        i = i + 1

    return listMsg

def showMessages(logging, listMsg):
    i = 0
    numMsg = len(listMsg)
    #if numMsg > 10:
    #    numMsg = 10
    print("")
    for row in listMsg[0:numMsg]:
        print("%2d) %-10s %-40s" % (i, listMsg[i][1][:10].ljust(10), listMsg[i][2][:40].ljust(40)))
        i = i + 1
        #if i % 10 == 0:
        #    print("---------------------------")

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
    validSel = False
    while not validSel:
        (listMsg, form, linkMsg) = listMessages(logging, browser, links)
        logging.debug("---> %s" % listMsg)
        if listMsg:
            showMessages(logging, listMsg)
            sel = input("Message? (number for message to be moved to valid/spam mail, 'a' for deleting all messages shown) ")
            if (sel in 'an') or (sel.isdigit() and int(sel) + 1 <= len(listMsg)):
                validSel = True 
        else:
           return("", [], listMsg, linkMsg)
    return (sel, form, listMsg, linkMsg)

def getCommands(logging, driver):

    actionLinks = driver.find_elements_by_class_name('fActionLink')

    # Identificar instrucciones relevantes
    commands = {}
    for tri in actionLinks:
        operation = tri.get_attribute('data-ng-click')
        #print(operation)
        if tri.is_displayed():
            if operation == 'deleteMessage()':
                commands['delete'] = tri
            elif operation == 'toggleSelectAll()':
                commands['select'] = tri
            elif operation == 'refreshMailbox()':
                commands['refresh'] = tri
            elif operation == 'releaseMessages()':
                commands['release'] = tri
            elif operation == 'loadNextPage()':
                commands['next'] = tri
            elif operation == 'loadPreviousPage()':
                commands['prev'] = tri

    return(commands)


def main():
    config = configparser.ConfigParser()
    config.read([os.path.expanduser('~/.IMAP.cfg')])
    
    rows, columns = os.popen('stty size', 'r').read().split()

    i = 1
    print("Configured accounts:")
    for section in config.sections():
        print('%s) %s' % (str(i), section))
        i = i + 1
    selection = input('Select one: ')

    logging.basicConfig(#filename='example.log',
                        level=logging.INFO,format='%(asctime)s %(message)s')
    SERVER = config.get(config.sections()[int(selection) - 1], 'server')
    USER = config.get(config.sections()[int(selection) - 1], 'user')
    PASSWORD = getPassword(SERVER, USER)

    driver = makeConnection(SERVER, USER, PASSWORD)
    PASSWORD = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX' 

    listMsg = listMessages(logging, driver) 
    #print(driver.page_source)

    while listMsg:
        showMessages(logging, listMsg)

        commands = getCommands(logging, driver)
        rep = input("Borrar todos? (s/n) ")
        if (rep == 's'):
            print("Borraré")
            commands['select'].click()
            time.sleep(2)
            driver.save_screenshot(os.path.join(os.path.dirname(os.path.realpath(__file__)), '/tmp', 'kkSelAll.png'))
            commands = getCommands(logging, driver)
            commands['delete'].click() 
        elif rep.isdigit():
            print("Salvar %s" % rep)
            print(listMsg[int(rep)])
            listMsg[int(rep)][0].click()
            time.sleep(2)
            driver.save_screenshot(os.path.join(os.path.dirname(os.path.realpath(__file__)), '/tmp', 'kkSelect.png'))

            commands = getCommands(logging, driver)
            commands['release'].click() 
            time.sleep(1)
        elif rep == 'n':
            sys.exit()

        commands['refresh'].click()
        time.sleep(1)
        listMsg = listMessages(logging, driver)
            
if __name__ == '__main__':
    main()
    
# compactFolder()
# markAllAsRead()
# showEmptyConfirmationDialog()
# toggleselectall()
# refreshMailbox()
# releaseMessages()
# None
# markAsRead(true)
# markAsRead(false)
# addToWhiteBlackList(true)
# addToWhiteBlackList(false)
# saveAsMessage()
# None
# loadFirstPage()
# loadLastPage()
# loadPreviousPage()
# loadNextPage()
# None
# selectQuickFilter(filter)
# selectQuickFilter(filter)
# selectQuickFilter(filter)
# deleteMessage()

#<ul data-ng-show="isMailMenuVisible()" class="nav mails-top-links navbar-right" style="margin-right: 12px">
#        <li data-ng-style="{'visibility': loading?'hidden':'visible'}" style="visibility: visible;">
#            <span class="fActionLink" data-ng-click="deleteMessage()" data-ng-show="!deleteInProgress" title="">
#                <i class="fa fa-trash"></i>
#                <!-- ngIf: !uiMainState.isSmallDesktop --><span data-ng-if="!uiMainState.isSmallDesktop" class="ng-binding ng-scope">&nbsp;Borrar</span><!-- end ngIf: !uiMainState.isSmallDesktop -->
#            </span>
#            <span class="disabled ng-hide" data-ng-show="deleteInProgress">
#                <i class="fa fa-trash"></i>
#                <!-- ngIf: !uiMainState.isSmallDesktop --><span data-ng-if="!uiMainState.isSmallDesktop" class="ng-binding ng-scope">&nbsp;Borrar</span><!-- end ngIf: !uiMainState.isSmallDesktop -->
#            </span>
#        </li>
#    </ul>

#css=.nav:nth-child(6) .fActionLink > .ng-binding

