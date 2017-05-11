#!/usr/bin/env python
#
# This program deletes and moves some messages from some mail account using
# IMAP
#
# defined in ~/.IMAP.cfg
#
# The code is multithreaded, in order to avoid waiting. The result of
# paralelism is not very interesting. It would be enough to get the passwords
# and delete messages sequentially.
#
# It will do the operations in the configured accounts
#
# We can now add an optional field called move. If present, messages selected
# following the rules will be moved to the folder and then they will be
# deleted.
#
# The config file should look like this:
# [IMAP1]
# server:imap.server.com
# user:user@imap.server.com
# rules:'FROM','Cron Daemon'
#      'SUBJECT','A problem with your document'
# move:Twitter
#
# [IMAP2]
# server:...
#
# Now the program uses the keyring system for storing passwords. When a new
# account is added it will ask for the password and it will store it. There is
# no code for changes of passwords and so on.
#
# Future plans:
# - Include the  deletion rule in the config file
#      (typ,data = M.search(None,'FROM', 'Cron Daemon') )


import configparser
import os
import sys
import keyring
import getpass
import threading
from queue import Queue
import ssl
from moduleSieve import *


def getPassword(server, user):
    # Para borrar keyring.delete_password(server, user)
    password = keyring.get_password(server, user)
    srvMsg = server.split('.')[0]
    usrMsg = user.split('@')[0]
    if not password:
        logging.info("[%s,%s] New account. Setting password" % (srvMsg, usrMsg))
        password = getpass.getpass()
        keyring.set_password(server, user, password)
    return password


def organize():
    # This function allous us to select mails from a folder and move them to
    # other in an interactive way
    config = loadImapConfig()[0]
    (server, user, password, rules, folder) = readImapConfig(config)
    rules = ""
    folder = "" # not used here
    M = makeConnection(server, user, password)
    password = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

    if not M:
        sys.exit("Connection failure")

    moveSent(M)
    selectMessagesNew(M)


def main():

    if (len(sys.argv)>1 and (sys.argv[1] == "-d")):
        logging.basicConfig(filename = os.path.expanduser('~/usr/var/IMAP.log'),
                            level=logging.DEBUG,format='%(asctime)s %(message)s')
                            #filename='example.log',
    else:
        logging.basicConfig(filename = os.path.expanduser('~/usr/var/IMAP.log'),
                            level=logging.INFO,format='%(asctime)s %(message)s')
                            #filename='example.log',

    (config, nSec) = loadImapConfig()
    threads = []
    i = 0

    logging.info("%s Starting" % sys.argv[0])
    accounts = {}

    while (i < nSec):
        (SERVER, USER, PASSWORD, RULES, FOLDER) = readImapConfig(config, i)
        srvMsg = SERVER.split('.')[0]
        usrMsg = USER.split('@')[0]
        logging.info("[%s,%s] Reading config" % (srvMsg, usrMsg))

        # We are grouping accounts in order to avoid interference among rules
        # on the same account 
        if (SERVER, USER) not in accounts:
            accounts[(SERVER, USER)] = {}
            # PASSWORD = getPassword(SERVER, USER)
            # accounts[(SERVER, USER)]['PASSWORD'] = PASSWORD
            accounts[(SERVER, USER)]['RULES'] = []
            accounts[(SERVER, USER)]['RULES'].append((RULES, FOLDER))
        else:
            accounts[(SERVER, USER)]['RULES'].append((RULES, FOLDER))
            # logging.info("[%s,%s] Known password!" % (SERVER, USER))
        i = i + 1

    keys = keyring.get_keyring()
    #keys._unlock()
    # We need to unlock the keyring because if not each thread will ask for the
    # keyring password

    answers = []

    for account in accounts.keys():
        answers.append(Queue())
        t = threading.Thread(target=mailFolder,
                             args=(account, accounts[account], logging, 
                                   answers[-1]))
    # We are using sequential code because when there are several set of
    # rules for a folder concurrency causes problems
        # Hopefully solved
    # mailFolder(account, accounts[account], logging)
        # PASSWORD = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        # We do not want passwords in memory when not needed
        threads.append(t)
        i = i + 1
    #for user in accounts.keys():
    #    accounts[user] = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

    for t in threads:
        t.start()

    if (len(sys.argv) > 1) and (sys.argv[1] == "-a"):
        addToSieve()
    else:
        organize()

    for t in threads:
        t.join()

    totalDeleted = 0
    for ans in answers:
        anss = ans.get()
        SERVER = anss[1]
        USER = anss[2]
        totalDeleted = totalDeleted + anss[3]


        srvMsg = SERVER.split('.')[0]
        usrMsg = USER.split('@')[0]
        if (anss[0] == 'no'):
       
            logging.info("[%s,%s] Wrong password. Changing" % (srvMsg, usrMsg))
            print("Wrong password " + SERVER + " " + USER + \
                  " write a new one")

            # Maybe it should ask if you want to change the password
            PASSWORD = getpass.getpass()
            keyring.set_password(SERVER, USER, PASSWORD)
            PASSWORD = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

    logging.info("%s The end!" % sys.argv[0])
    print("%s The end! Deleted %d messages" % (sys.argv[0], totalDeleted))

if __name__ == '__main__':
    main()
