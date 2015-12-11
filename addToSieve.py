#!/usr/bin/python

import sievelib,time,getpass
from sievelib.managesieve import Client
from sievelib.parser import Parser
from sievelib.factory import FiltersSet
import imaplib, email

msgHeaders=['List-Id', 'From', 'Sender','Subject','To', 'X-Original-To']
headers=["address","header"] 
keyWords={"address": ["From","To"],
	  "header":  ["subject","Sender","X-Original-To","List-Id"]
	}

SERVER="ra-amon.cps.unizar.es"
USER="f.tricas@ra-amon.lan"
c = Client(SERVER)
PASSWORD=getpass.getpass()
c.connect(USER,PASSWORD, starttls=True, authmech="PLAIN")
M = imaplib.IMAP4_SSL(SERVER)
M.login(USER , PASSWORD)

def doFolderExist(folder,M):
	return (M.select(folder))


def selectAction(p,M): #header="", textHeader=""):
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
		if (doFolderExist(folder,M)[0]!='OK'):
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
	
def selectMail(M):
	M.select()
	data=M.sort('ARRIVAL', 'UTF-8', 'ALL')
	if (data[0]=='OK'):
		j=0
		msg_data=[]
		messages=data[1][0].split(' ')
		for i in messages[-15:]:
			typ, msg_data_fetch = M.fetch(i, '(BODY.PEEK[HEADER.FIELDS (From Sender To Subject List-Id)])')
			for response_part in msg_data_fetch:
				if isinstance(response_part, tuple):
					msg = email.message_from_string(response_part[1])
					msg_data.append(msg)
					print "%2d) %4s %20s %40s" %(j,i,msg['From'][:20],msg['Subject'][:40])
					j=j+1
		msg_number = raw_input("Which message? ")
		return msg_data[int(msg_number)] #messages[-10+int(msg_number)-1]
	else:	
		return 0

def selectHeaderAuto(M, msg):
	i=1
	if msg.has_key('List-Id'): 
		return ('List-Id', msg['List-Id'][msg['List-Id'].find('<')+1:-1])
	else:
		for header in msgHeaders:
			if msg.has_key(header):
				print i," ) ", header, msg[header]
			i = i + 1
		header_num=raw_input("Select header: ")
		
		header=msgHeaders[int(header_num)-1]
		textHeader=msg[msgHeaders[int(header_num)-1]]
		pos = textHeader.find('<')
		if (pos>=0):
			textHeader=textHeader[pos+1:textHeader.find('>',pos+1)]
		else:
			pos = textHeader.find('[')
			textHeader=textHeader[pos+1:textHeader.find(']',pos+1)]
		return (header, textHeader)

	

	





script = c.getscript('sogo')

msg=selectMail(M)
(header, textHeader) =selectHeaderAuto(M, msg)

print header, textHeader

p = Parser()
p.parse(script)

actions = selectAction(p,M)#, header,textHeader)
#header= selectHeader()
#keyword = selectKeyword(header)

keyword=header
header='header'
print actions 
print "Text selected: ", textHeader

filterCond= raw_input("Text for selection (empty for all): ")

if not filterCond:
	filterCond = textHeader

conditions=[]
conditions.append((keyword, ":contains", filterCond))

print "keyword", keyword
print "cond ", conditions, actions, keyword

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

# Let's do a backup
name = time.strftime("%Y-%m-%d-%H-%M-%S", time.gmtime())
c.putscript(name+'sogo',script)


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


