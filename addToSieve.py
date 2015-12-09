#!/usr/bin/python

import sievelib,time,getpass
from sievelib.managesieve import Client
from sievelib.parser import Parser
from sievelib.factory import FiltersSet
import imaplib

headers=["address","header"] 
keyWords={"address": ["From","To"],
	  "header":  ["subject","Sender","X-Original-To","List-Id"]
	}

SERVER="ra-amon.cps.unizar.es"
USER="f.tricas@ra-amon.lan"
PASSWORD="" 

def doFolderExist(folder):
	M = imaplib.IMAP4_SSL(SERVER)
	M.login(USER , PASSWORD)
	return (M.select(folder))


def selectAction():
	i = 1
	for r in p.result:
		#print r.children
		if r.children:
			#print type(r.children[0])
			if (type(r.children[0]) == sievelib.commands.FileintoCommand):
				print i, ") Folder   ", r.children[0]['mailbox']
			elif (type(r.children[0]) == sievelib.commands.RedirectCommand):
				print i, ") Redirect ", r.children[0]['address']
			else:
				print i, ") Not implented ", type(r.children[0])
		else:
			print  i, ") Not implented ", type(r)
			
		i = i + 1
	print i, ") New folder "
	print i+1, ") New redirection"
		


	option = raw_input("Select one: ")

	print option, len(p.result)

	actions=[]

	if (int(option) <= len(p.result)):
		print p.result[int(option)-1].arguments
		print p.result[int(option)-1].dump()
		print "child ", p.result[int(option)-1].children

		action=p.result[int(option)-1].children

		for i in action:
			print i.arguments
			if i.arguments.has_key('mailbox'):
				actions.append(("fileinto",i.arguments['mailbox']))
			elif i.arguments.has_key('address'):
				actions.append(("redirect",i.arguments['address']))
			else:	
				actions.append(("stop",))
				
				
		print actions

		match=p.result[int(option)-1]['test']
		print "match ", match
	elif (int(option) == len(p.result)+1):
		folder= raw_input("Name of the folder: ")
		print "Name ", folder
		if (doFolderExist(folder)[0]!='OK'):
			print "Folder ",folder," does not exist"
			sys.exit()
		else:
			print "Let's go"
			actions.append(("fileinto", folder))
			actions.append(("stop",))
	elif (int(option) == len(p.result)+2):
		redir= raw_input("Redirection to: ")
		print "Name ", redir
		itsOK= raw_input("It's ok? (y/n)")
		if (itsOK!='y'):
			print redir," is wrong"
			sys.exit()
		else:
			print "Let's go"
			actions.append(("redirect", redir))
			actions.append(("stop",))

	return actions



def selectHeader():
	i = 1
	for j in headers:
		print i, ") ", j, "(", keyWords[headers[i-1]],")"
		i = i + 1
	return headers[int(raw_input("Select header: "))-1]
	
def selectKeyword(header):	
	i = 1
	for j in keyWords[header]:
		print i, ") ", j
		i = i + 1
	return keyWords[header][int(raw_input("Select header: "))-1]
	
c = Client(SERVER)

PASSWORD=getpass.getpass()
c.connect(USER,PASSWORD, starttls=True, authmech="PLAIN")

script = c.getscript('sogo')

# Let's do a backup
name = time.strftime("%Y-%m-%d-%H-%M-%S", time.gmtime())
c.putscript(name+'sogo',script)

p = Parser()
p.parse(script)

actions = selectAction()
header= selectHeader()
keyword = selectKeyword(header)

print actions, header, keyword

filterCond= raw_input("Text for selection: ")

conditions=[]
conditions.append((keyword, ":contains", filterCond))

print "cond ", conditions, actions, header, keyword


fs = FiltersSet("test")
#fs.addfilter("rule1",
#                 [("Sender", ":is", "toto@toto.com"), ],
#                 [("fileinto", "Toto"), ("stop",)])
#print fs
print script
fs.addfilter("",conditions,actions)

print "---->"
print fs.tosieve(open('/tmp/kkSieve','w'))
print "----"
print type(fs.tosieve())
print "----"

p2=Parser()
p2.parse(open('/tmp/kkSieve','r').read())
print type(p2.result)
lenP2 = len(p2.result)
print p2.result[lenP2-1]
p.result.append(p2.result[lenP2-1])

#kk=kk+"\n"+open('/tmp/kkSieve','r').read()

fSieve=open('/tmp/kkSieve','w')
for r in p.result:
	r.tosieve(0,fSieve)

fSieve.close()
fSieve=open('/tmp/kkSieve','r')

if not c.putscript('sogo',fSieve.read()):
	print "fail!"
#print p.dump


















#p.dump()

#print p.dump()


# cond ->  {u'header-list': '"to"', u'key-list': '"lista@coddii.org"', u'match-type': ':contains'}



#p.result[int(option)-1]['test'].addchild([("Sender", ":is", "toto@toto.com")])

#newfilter=p.addfilter(p.result[int(option)-1]
#print p.result[int(option)-1].dump()

#p.result[int(option)-1].addfilter(










#print kk
#
#print "----------------------"
#
#
##p.dump()
##print "----------------------"
#
#for r in p.result:
#	print r.dump()
#	print r.tosieve()
#
#print "----------------------"
#print "----------------------"
#print p.result[1], type(p.result[1])
#print p.result[1].tosieve()
#print p.result[1].tosieve()
#print "----------------------"
#for r in p.result[1].children:
#	print r, type(r)
#	print r.dump()
#	print "--"
#print "type ", p.result[1].get_type()
#print "exp. ", p.result[1].get_expected_first()
#print "args ", p.result[1].arguments
#print type(p.result[1].arguments)
#print "....  ", p.result[1].arguments["test"].args_definition
#print ".args ", p.result[1].arguments["test"].arguments
#print "..    ", p.result[1].arguments["test"].children
#print "chil ", p.result[1].children
#print "t chil ", type(p.result[1].children)
#print "name ", p.result[1].children[0]['mailbox']
#print p.result[1].dump()
#
#
#print "____________________________"

#conditions = []
#for cond in p.result[int(option)-1].arguments['test'].arguments['tests']:
#	print "cond -> ", cond.arguments
#	header=cond.arguments['header-list']
#	key=cond.arguments['key-list']
#	match=cond.arguments['match-type']
#	print header, key, match
#	conditions.append([header,key,match])


