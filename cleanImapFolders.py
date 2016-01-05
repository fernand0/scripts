#!/usr/bin/python
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


import ConfigParser
import os
import sys
import imaplib
import keyring
import getpass
import threading
import hashlib
import binascii


def selectHash(M, folder, hashSelect):
    M.select(folder)
    typ, data = M.search(None, 'ALL')
    i = 0
    msgs = ['']
    for num in data[0].split():
        m = hashlib.md5()
        typ, msg = M.fetch(num, '(BODY.PEEK[TEXT])')
        # PEEK does not change access flags
        print msg[0][1]
        m.update(msg[0][1])
        if (binascii.hexlify(m.digest()) == hashSelect):
            if msgs[0]:
                msgs[0] = msgs[0] + ' ' + data[0]
            else:
                msgs[0] = data[0]
            i = i + 1
        else:
            print 'Message %s\n%s\n%s\n' % (num, data[0][1], binascii.hexlify(m.digest()))
        if (i % 10 == 0):
            print i
    print "\nEND\n\n%d messages have been selected\n" % i
    return msgs


def getPassword(server, user):
    # Para borrar keyring.delete_password(server, user)
    password = keyring.get_password(server, user)
    if not password:
        print "New account. Setting password"
        password = getpass.getpass()
        keyring.set_password(server, user, password)
    return password


def mailFolder(server, user, password, rules, folder):
    SERVER = server
    USER = user
    PASSWORD = password
    RULES = rules
    FOLDER = folder

    M = imaplib.IMAP4_SSL(SERVER)
    M.login(USER, PASSWORD)
    password = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    # We do not want passwords in memory when not needed
    M.select()
    i = 0
    msgs = []
    for rule in RULES:
        action = rule.split(',')
        header = action[0][1:-1]
        content = action[1][1:-1]
        msg = "[%s,%s] Rule: %s %s\n" % (SERVER, USER, header, content)
        if (header == 'hash'):
            msgs = selectHash(M, folder, content)
            # M.select(folder)
            FOLDER = ""
        else:
            typ, data = M.search(None, header, content)
            if data[0]:
                if msgs:
                    msgs[0] = msgs[0] + ' ' + data[0]
                else:
                    msgs = data
            else:
                print msg + " -> No messages matching"

    if not msgs:
        print "["+SERVER+","+USER+"]"+" -> Nothing to do"
        sys.exit()
    print "["+SERVER+","+USER+"]"+" -> Let's go!"
    msgs = msgs[0].replace(" ", ",")
    status = 'OK'
    if FOLDER:
        # M.copy needs a set of comma-separated mesages, we have a list with a
        # string
        print "Entra"
        result = M.copy(msgs, FOLDER)
        status = result[0]
    i = msgs.count(',') + 1
    # M.store needs a set of comma-separated mesages, we have a list with a
    # string
    if status == 'OK':
        # If the list of messages is too long it won't work
        flag = '\\Deleted'
        result = M.store(msgs, '+FLAGS', flag)
        if result[0] == 'OK':
            print "[%s,%s] SERVER %s: %d messages have been deleted.\n" % (SERVER, USER, SERVER, i)
        else:
            print "[", SERVER, USER, "]", "Couldn't delete messages!"
    else:
        print "[", SERVER, USER, "]", "Couldn't move messages!"
    M.close()
    M.logout()


def main():
    config = ConfigParser.ConfigParser()
    config.read([os.path.expanduser('~/.IMAP.cfg')])

    threads = []
    i = 0

    accounts = {}
    for section in config.sections():
        SERVER = config.get(section, 'server')
        USER = config.get(section, 'user')
        RULES = config.get(section, 'rules').split('\n')
        if config.has_option(section, 'move'):
            FOLDER = config.get(section, "move")
        else:
            FOLDER = ""

        print SERVER, USER
        if USER not in accounts:
            PASSWORD = getPassword(SERVER, USER)
            accounts[USER] = PASSWORD
        else:
            PASSWORD = accounts[USER]
            print "Known password!"

        t = threading.Thread(target=mailFolder,
                             args=(SERVER, USER, PASSWORD, RULES, FOLDER))
        PASSWORD = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        # We do not want passwords in memory when not needed
        threads.append(t)
        i = i + 1
    for user in accounts.keys():
        accounts[user] = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    print "The end!"

if __name__ == '__main__':
    main()
