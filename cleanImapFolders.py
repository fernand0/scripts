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
import imaplib
import keyring
import keyrings #keyrings.alt
import getpass
import threading
from queue import Queue
import hashlib
import binascii
import logging


def selectHash(M, folder, hashSelect):
    M.select(folder)
    typ, data = M.search(None, 'ALL')
    i = 0
    msgs = ''
    dupHash = []
    for num in data[0].split():
        m = hashlib.md5()
        typ, msg = M.fetch(num, '(BODY.PEEK[TEXT])')
        # PEEK does not change access flags
        logging.debug("%s" % msg[0][1])
        m.update(msg[0][1])
        msgDigest = binascii.hexlify(m.digest())
        if (msgDigest == hashSelect):
            if msgs:
                msgs = msgs + ' ' + num.decode('utf-8')
                # num is a string or a number?
            else:
                msgs = num.decode('utf-8')
            i = i + 1
        else:
            logging.debug("Message %s\n%s" % (num, msgDigest))
        # We are deleting duplicate messages
        if msgDigest in dupHash:
            if msgs:
                msgs = msgs + ' ' + num.decode('utf-8')
                # num is a string or a number?
            else:
                msgs = num.decode('utf-8')
            i = i + 1
        else:
            dupHash.append(msgDigest)
        if (i % 10 == 0):
            logging.debug("Counter %d" % i)

    logging.debug("END\n\n%d messages have been selected\n" % i)

    return msgs


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


def mailFolder(account, accountData, logging, res):
    SERVER = account[0]
    USER = account[1]
    PASSWORD = getPassword(SERVER, USER)

    srvMsg = SERVER.split('.')[0]
    usrMsg = USER.split('@')[0]
    import ssl
    context = ssl.create_default_context()
    #context = ssl.SSLContext(ssl.PROTOCOL_SSLv3)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    M = imaplib.IMAP4_SSL(SERVER,ssl_context=context)
    try:
        M.login(USER, PASSWORD)
        PASSWORD = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        # We do not want passwords in memory when not needed
    except Exception as ins:
        # We will ask for the new password
        print("except", SERVER, USER)
        print("except", sys.exc_info()[0])
        print("except", ins.args)
        logging.info("[%s,%s] wrong password!"
                         % (srvMsg, usrMsg))
        res.put(("no", SERVER, USER))
        return 0

    M.select()

    for actions in accountData['RULES']:
        RULES = actions[0]
        FOLDER = actions[1]

        i = 0
        msgs = ''
        for rule in RULES:
            action = rule.split(',')
            header = action[0][1:-1]
            content = action[1][1:-1]
            msgTxt = "[%s,%s] Rule: %s %s" % (srvMsg, usrMsg, header, content)
            logging.debug(msgTxt)
            if (header == 'hash'):
                msgs = selectHash(M, FOLDER, content)
                #M.select(folder)
                FOLDER = ""
            else:
                data = ''
                try:
                    cadSearch = "("+header+' "'+content+'")'
                    typ, data = M.search(None, cadSearch)
                except:
                    cadSearch = "(HEADER "+header+' "'+content+'")'
                    typ, data = M.search(None, cadSearch)
                if data and data[0]:
                    if msgs:
                        msgs = msgs + ' ' + data[0].decode('utf-8')
                    else:
                        msgs = data[0].decode('utf-8')
                else:
                    logging.debug("%s - No messages matching." % msgTxt)
                    msgTxt = "%s - No messages matching." % msgTxt

            if len(msgs)==0:
                logging.debug("%s Nothing to do" % msgTxt)
                msgTxt = "%s Nothing to do" % msgTxt
            else:
                logging.debug("%s - Let's go!" % msgTxt)
                msgTxt = "%s - Let's go!" % msgTxt
                msgs = msgs.replace(" ", ",")
                status = 'OK'
                if FOLDER:
    	    # M.copy needs a set of comma-separated mesages, we have a
    	    # list with a string
                    print("msgs", msgs)
                    sys.exit()
                    result = M.copy(msgs, FOLDER)
                    status = result[0]
                i = msgs.count(',') + 1
                logging.debug("[%s,%s] *%s* Status: %s"% (SERVER,USER,msgs,status))

                if status == 'OK':
                    # If the list of messages is too long it won't work
                    flag = '\\Deleted'
                    result = M.store(msgs, '+FLAGS', flag)
                    if result[0] == 'OK':
                        logging.debug("%s: %d messages have been deleted."
                                      % (msgTxt, i))
                        msgTxt = "%s: %d messages have been deleted." \
                                      % (msgTxt, i)
                    else:
                        logging.debug("%s -  Couldn't delete messages!" % msgTxt)
                        msgTxt = "%s -  Couldn't delete messages!" % msgTxt
                else:
                    logging.debug("%s - Couldn't move messages!" % msgTxt)
                    msgTxt = "%s - Couldn't move messages!" % msgTxt
            logging.info(msgTxt)
    M.close()
    M.logout()
    res.put(("ok", SERVER, USER))
    

def main():
    config = configparser.ConfigParser()
    config.read([os.path.expanduser('~/.IMAP.cfg')])
    if (len(sys.argv)>1 and (sys.argv[1] == "-d")):
        logging.basicConfig(#filename='example.log',
                            level=logging.DEBUG,format='%(asctime)s %(message)s')
    else:
        logging.basicConfig(#filename='example.log',
                            level=logging.INFO,format='%(asctime)s %(message)s')

    threads = []
    i = 0

    accounts = {}
    sections=config.sections()
    # sections=['IMAP6']
    logging.info("%s Starting" % sys.argv[0])
    for section in sections:
        SERVER = config.get(section, 'server')
        USER = config.get(section, 'user')
        RULES = config.get(section, 'rules').split('\n')
        if config.has_option(section, 'move'):
            FOLDER = config.get(section, "move")
        else:
            FOLDER = ""

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

    for t in threads:
        t.join()

    for ans in answers:
        anss = ans.get()
        SERVER = anss[1]
        USER = anss[2]

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

if __name__ == '__main__':
    main()
