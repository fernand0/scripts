#!/usr/bin/python
# 
# This program deletes 'Cron Daemon' messages from some backup mail account 
# defined in ~/IMAP.cfg
#
# The code is multithreaded, in order to avoid waiting
#
# It will do the operations in the configured accounts
#
# The config file should look like this:
# [IMAP1]
# server:imap.server.com
# user:user@imap.server.com
# [IMAP2]
# server:...
#
# Future plans:
# - Include the  deletion rule in the config file
#      (typ,data = M.search(None,'FROM', 'Cron Daemon') )
# - Evaluate the way to include the password or some alternative 
#   identification method?
# - Leave the account unchanged for messages not deleted (it can mark as read
#   the messages, and this is not convenient in some cases).
#
# [IMAP1]
# server:imap.server.com
# user:user@imap.server.com
# delete:Cron Daemon
 

import ConfigParser
import os, sys, getpass, imaplib
import threading

config = ConfigParser.ConfigParser()
config.read([os.path.expanduser('~/IMAP.cfg')])


def mailFolder(server, user, password,space):
	SERVER = server
	USER   = user
	PASSWORD = password

	print SERVER
	M = imaplib.IMAP4_SSL(SERVER)
	M.login(USER , password)
	M.select()
	typ,data = M.search(None,'FROM', 'Cron Daemon')
	i = 0
	if data[0]: 
		for num in data[0].split():
			M.store(num, '+FLAGS', '\\Deleted')
			if (i%10 == 0):
				print space+"SERVER: ", SERVER, " ", i
			i = i + 1
	print "SERVER: %s END\n\n%d messages have been deleted\n" % (SERVER, i)
	M.close()
	M.logout()

space="                             "
threads=[]
i=0

for section in config.sections():
	SERVER = config.get(section, 'server')
	USER   = config.get(section, 'user')

	print SERVER
	PASSWORD = getpass.getpass()
	
	t = threading.Thread(target=mailFolder, args=(SERVER, USER, PASSWORD,space*i))
	threads.append(t)
	i = i + 1

for t in threads:
	t.start()

for t in threads:
	t.join()

print "The end!"
