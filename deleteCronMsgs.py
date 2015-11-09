#!/usr/bin/python
# 
# This program deletes 'Cron Daemon' messages from some backup mail account 
# defined in ~/IMAP.cfg
#
# The config file should look like this:
# [IMAP1]
# server:imap.server.com
# user:user@imap.server.com
#
# Future plans:
# - Include the  deletion rule in the config file
#      (typ,data = M.search(None,'FROM', 'Cron Daemon') )
# - Evaluate the way to include the password or some alternative 
#   identification method?
# - Operate on several accounts, with different deletion partterns.
# - Leave the account unchanged for messages not deleted (it can mark as read
#   the messages, and this is not convenient in some cases).
# 

import ConfigParser
import os, sys, getpass, imaplib

config = ConfigParser.ConfigParser()
config.read([os.path.expanduser('~/IMAP.cfg')])

SERVER = config.get('IMAP1', 'server')
USER   = config.get('IMAP1', 'user')

M = imaplib.IMAP4_SSL(SERVER)
M.login(USER , getpass.getpass())
M.select()
typ,data = M.search(None,'FROM', 'Cron Daemon')
i = 0
if data[0]: 
	for num in data[0].split():
		M.store(num, '+FLAGS', '\\Deleted')
		if (i%10 == 0):
			print i
		i = i + 1
print "END\n\n%d messages have been deleted\n" % i
M.close()
M.logout()
