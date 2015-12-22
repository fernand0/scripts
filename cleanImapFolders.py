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
# Future plans:
# - Include the  deletion rule in the config file
#      (typ,data = M.search(None,'FROM', 'Cron Daemon') )
# - Evaluate the way to include the password or some alternative 
#   identification method?
 

import ConfigParser
import os, sys, getpass, imaplib
import threading

def mailFolder(server, user, password, rules, folder):
	SERVER = server
	USER   = user
	PASSWORD = password
	RULES  = rules
	FOLDER = folder

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
		print "[",SERVER,USER,"]","Rule: ", header, content
		typ,data = M.search(None,header,content)
		if data[0]: 
			if msgs:
				msgs[0] = msgs[0] +' '+ data[0]
			else: 
				msgs=data

	if not msgs:
		print "[",SERVER,USER,"]","Nothing to do"
		sys.exit()
	msgs=msgs[0].replace(" ",",")
	status='OK'
	if FOLDER:
		# M.copy needs a set of comma-separated mesages, we have a list with a string
		result = M.copy(msgs,FOLDER) 
		status=result[0]
	i=msgs.count(',')+1			
	# M.store needs a set of comma-separated mesages, we have a list with a
	# string
	if status == 'OK':
		flag='\\Deleted'
		result = M.store(msgs,'+FLAGS',flag)
		if result[0] == 'OK': 
			print "[",SERVER,USER,"]","SERVER %s: %d messages have been deleted END\n" % (SERVER, i)
		else:	
			print "[",SERVER,USER,"]","Couldn't delete messages!"
	else:	
		print "[",SERVER,USER,"]","Couldn't move messages!"
	M.close()
	M.logout()

def main():
	config = ConfigParser.ConfigParser()
	config.read([os.path.expanduser('~/.IMAP.cfg')])

	threads=[]
	i=0

	accounts={}
	for section in config.sections():
		SERVER = config.get(section, 'server')
		USER   = config.get(section, 'user')
		RULES  = config.get(section, 'rules').split('\n')
		if config.has_option(section, 'move'):
			FOLDER = config.get(section,"move")
		else:	
			FOLDER = ""

		print SERVER,USER
		if not accounts.has_key(USER):
			PASSWORD = getpass.getpass()
			accounts[USER]=PASSWORD
		else:
			PASSWORD = accounts[USER]
			print "Known password!"
		
		t = threading.Thread(target=mailFolder, args=(SERVER, USER, PASSWORD, RULES, FOLDER))
		PASSWORD = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
		# We do not want passwords in memory when not needed
		threads.append(t)
		i = i + 1
	for user in accounts.keys():
		accounts[user]="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

	for t in threads:
		t.start()

	for t in threads:
		t.join()

	print "The end!"

if __name__ == '__main__':
   main()
