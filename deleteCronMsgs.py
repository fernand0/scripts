#!/usr/bin/python
# 
# This program deletes 'Cron Daemon' messages from some backup mail account 
# defined in ~/IMAP.cfg
#
# The code is multithreaded, in order to avoid waiting. The result of
# paralelism is not very interesting. It would be enough to get the passwords
# and delete messages sequentially.
#
# It will do the operations in the configured accounts
#
# The config file should look like this:
# [IMAP1]
# server:imap.server.com
# user:user@imap.server.com
# rules:'FROM','Cron Daemon'
#      'SUBJECT','A problem with your document'
# 
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
# rules:Cron Daemon
 

import ConfigParser
import os, sys, getpass, imaplib
import threading

config = ConfigParser.ConfigParser()
config.read([os.path.expanduser('~/.IMAP.cfg')])
RULES = config.get('IMAP1','rules').split('\n')

def mailFolder(server, user, password, space):
	SERVER = server
	USER   = user
	PASSWORD = password

	print SERVER
	M = imaplib.IMAP4_SSL(SERVER)
	M.login(USER , PASSWORD)
	password = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
	# We do not want passwords in memory when not needed
	M.select()
	i = 0
	msgs = []
	for rule in RULES:
		action=rule.split(',')
		header  = action[0][1:-1]
		content = action[1][1:-1]
		print "Rule: ", header, content
		typ,data = M.search(None,header,content)
		if data[0]: 
			if msgs:
				msgs[0] = msgs[0] +' '+ data[0]
			else: 
				msgs=data
		print msgs

	if not msgs:
		print "Nothing to do"
		sys.exit()
	msgs=msgs[0].replace(" ",",")
	i=msgs.count(',')+1			
	# M.store needs a set of comma-separated mesages, we have a list with a
	# string
	
	print msgs
	
	flag='\\Deleted'
	result = M.store(msgs,'+FLAGS',flag)
	if result[0] == 'OK': 
		print space+"SERVER %s: %d messages have been deleted END\n" % (SERVER, i)
	else:	
		print "Couldn't delete messages!"
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
	PASSWORD = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
	# We do not want passwords in memory when not needed
	threads.append(t)
	i = i + 1

for t in threads:
	t.start()

for t in threads:
	t.join()

print "The end!"
