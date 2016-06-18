#!/usr/bin/env python

import ConfigParser
import os
import sys
import sievelib
import time
import getpass
import imaplib
import email
import StringIO
import keyring
from email import Header
from sievelib.managesieve import Client
from sievelib.parser import Parser
from sievelib.factory import FiltersSet
from git import Repo

msgHeaders = ['List-Id', 'From', 'Sender', 'Subject', 'To',
              'X-Original-To', 'X-Envelope-From', 'X-Spam-Flag']
headers = ["address", "header"]
keyWords = {"address": ["From", "To"],
            "header":  ["subject", "Sender", "X-Original-To", "List-Id"]
            }
FILE_SIEVE = "/tmp/sieveTmp"

repoDir='/home/ftricas/Documents/config/'
repoFile='sogo.sieve'

def printRule(rule):
    print "rule "
    for cond in rule[1]:
        print cond.tosieve()

def printRules(listRules):
    # For debugging
    for rule in listRules.keys():
        printRule(listRules[rule])

def addRule(rules, more, keyword, filterCond, actions):
        #printRules(rules)
        print rules['"Docencia/master/masterbdi"']
	print type(rules['"Docencia/master/masterbdi"'])
        if actions[0][1] not in rules:
                rules[actions[0][1]] = ['fileinto', []]
            
        #printRule(rule)

        # Is there a better way to do this?
        cmd = sievelib.factory.get_command_instance("header",
                                                    rules[actions[0][1]])
        cmd.check_next_arg("tag", ":contains")
        # __quote_if_necessary
        if not keyword.startswith(('"', "'")):
            keyword = '"%s"' % keyword
        cmd.check_next_arg("string", keyword)
        if not filterCond.startswith(('"', "'")):
            filterCond = '"%s"' % filterCond
        cmd.check_next_arg("string", filterCond)
        rules[actions[0][1]][1].append(cmd)

        # print "--------------------"
        # printRule(rules[actions[0][1]])
        # print "--------------------"
        # print rules[actions[0][1]]
        newActions = constructActions(rules, more)

        # print "actions, ", actions
        return newActions

def extractActions(p):
    i = 1
    rules = {}
    more = {}
    for r in p.result:
        # print r.children
        if r.children:
            # print type(r.children[0])
            key = r.children[0]
            if len(r.children) > 2:
                # If there are more actions (just one more
                # action, in fact), we will store it in more
                more[key['address']] = []
                more[key['address']].append(r.children[1]['address'])
            if (type(key) == sievelib.commands.FileintoCommand):
                # print i, ") Folder   ", key['mailbox']
                tests = r.arguments['test'].arguments['tests']
                if key['mailbox'] in rules:
                    rules[key['mailbox']][1] = rules[key['mailbox']][1] + tests
                else:
                    rules[key['mailbox']] = []
                    rules[key['mailbox']].append("fileinto")
                    rules[key['mailbox']].append(tests)
            elif (type(key) == sievelib.commands.RedirectCommand):
                # print i, ") Redirect ", key['address']
                tests = r.arguments['test'].arguments['tests']
                if key['address'] in rules:
                    rules[key['address']][1] = rules[key['address']][1] + tests
                else:
                    rules[key['address']] = []
                    rules[key['address']].append("redirect")
                    rules[key['address']].append(tests)
            else:
                print i, ") Not implented ", type(key)
        else:
            print i, ") Not implented ", type(r)

        i = i + 1

    return (rules, more)


def constructActions(rules, more):
    actions = []
    for rule in rules.keys():
        action = []
        # print "----------------------------"
        # print rules[rule]
        # print rule
        # print "-----"
        # print rules[rule][0]
        # act = []
        if rule in more:
            action.append((rules[rule][0],
                          (rule, more[rule][0]), rules[rule][1]))
        else:
            action.append((rules[rule][0], (rule,), rules[rule][1]))
        # action.append(act)

        actions.append(action)
    # print "actions, ", actions
    return actions


def constructFilterSet(actions):
    fs = FiltersSet("test")
    for action in actions:
        # print "-> ", action
        conditions = action[0][2]
        # print "-> ", conditions
        cond = []
        for condition in conditions:
            # print "condition -> ", condition
            # print type(condition)
            # print condition.arguments
            head = ()
            (key1, key2, key3) = condition.arguments.keys()
            head = head + (condition.arguments[key1],
                           condition.arguments[key3],
                           condition.arguments[key2].decode('utf-8'))
            # We will need to take care of these .decode's
            cond.append(head)

        # print "cond ->", cond
        act = []
        for i in range(len(action[0][1])):
            act.append((action[0][0], action[0][1][i]))
        act.append(("stop",))
        # print "act ->", act
        fs.addfilter("", cond, act)
        # print "added!"

    return fs


def doFolderExist(folder, M):
    return (M.select(folder))


def selectAction(p, M):  # header="", textHeader=""):
    i = 1
    txtResults = ""
    for r in p.result:
        if r.children:
            txtResults = txtResults + "%02d " % len(r.arguments['test'].arguments['tests'])
            if (type(r.children[0]) == sievelib.commands.FileintoCommand):
                txtResults = txtResults + "%02d) Folder  %s\n" % (i, r.children[0]['mailbox'])
            elif (type(r.children[0]) == sievelib.commands.RedirectCommand):
                txtResults = txtResults + "%02d) Address %s\n" % (i, r.children[0]['address'])
            else:
                txtResults = txtResults + "%02d) Not implemented %s\n" % (i, type(r.children[0]))
        else:
            txtResults = txtResults + "%02d) Not implemented %s\n" % (i, type(r))

        i = i + 1
    txtResults = txtResults + "99 %02d) New folder \n" % i
    txtResults = txtResults + "99 %02d) New redirection\n" % (i+1)


    for cad in sorted(txtResults.split('\n')):
        print cad[3:], cad[:3]

    option = raw_input("Select one: ")

    print option, len(p.result)

    actions = []

    if (int(option) <= len(p.result)):
        action = p.result[int(option)-1].children

        for i in action:
            if 'mailbox' in i.arguments:
                actions.append(("fileinto", i.arguments['mailbox']))
            elif 'address'in i.arguments:
                actions.append(("redirect", i.arguments['address']))
            else:
                actions.append(("stop",))

        # print actions

        match = p.result[int(option)-1]['test']
        # print "match ", match
    elif (int(option) == len(p.result)+1):
        folder = raw_input("Name of the folder: ")
        print "Name ", folder
        if (doFolderExist(folder, M)[0] != 'OK'):
            print "Folder ", folder, " does not exist"
            sys.exit()
        else:
            print "Let's go"
            actions.append(("fileinto", folder))
            actions.append(("stop",))
    elif (int(option) == len(p.result)+2):
        redir = raw_input("Redirection to: ")
        print "Name ", redir
        itsOK = raw_input("It's ok? (y/n)")
        if (itsOK != 'y'):
            print redir, " is wrong"
            sys.exit()
        else:
            print "Let's go"
            actions.append(("redirect", redir))
            actions.append(("stop",))

    return actions


def selectHeader():
    i = 1
    for j in headers:
        print i, ") ", j, "(", keyWords[headers[i-1]], ")"
        i = i + 1
    return headers[int(raw_input("Select header: ")) - 1]


def selectKeyword(header):
    i = 1
    for j in keyWords[header]:
        print i, ") ", j
        i = i + 1
    return keyWords[header][int(raw_input("Select header: ")) - 1]


def selectMessage(M):
    msg_number =""
    while (not msg_number.isdigit()):
        M.select()
        data = M.sort('ARRIVAL', 'UTF-8', 'ALL')
        if (data[0] == 'OK'):
            j = 0
            msg_data = []
            messages = data[1][0].split(' ')
            lenId = len(str(messages[-1]))
            for i in messages[-24:]:
                typ, msg_data_fetch = M.fetch(i, '(BODY.PEEK[])')
                # print msg_data_fetch
                for response_part in msg_data_fetch:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_string(response_part[1])
                        msg_data.append(msg)
                        # Variable length fmt
                        fmt = "%2s) %-20s %-40s"
                        headFrom = msg['From']
                        headSubject = msg['Subject']
                        print fmt % (j,
                                     Header.decode_header(headFrom)[0][0][:20],
                                     Header.decode_header(headSubject)[0][0][:40])
                        j = j + 1
            msg_number = raw_input("Which message? ")
        else:
            return 0

    return msg_data[int(msg_number)]  # messages[-10+int(msg_number)-1]

def selectHeaderAuto(M, msg):
    i = 1
    if 'List-Id' in msg:
        return ('List-Id', msg['List-Id'][msg['List-Id'].find('<')+1:-1])
    else:
        for header in msgHeaders:
            if header in msg:
                print i, " ) ", header, msg[header]
            i = i + 1
	import locale
        header_num = raw_input("Select header: ")

        header = msgHeaders[int(header_num)-1]
        textHeader = msg[msgHeaders[int(header_num)-1]]
        pos = textHeader.find('<')
        if (pos >= 0):
            textHeader = textHeader[pos+1:textHeader.find('>', pos + 1)]
        else:
            pos = textHeader.find('[')
            if (pos >= 0):
                textHeader = textHeader[pos+1:textHeader.find(']', pos + 1)]
            else:
                textHeader = textHeader

        print "Filter: (header) ", header, ", (text) ", textHeader
        filterCond = raw_input("Text for selection (empty for all): ")
        # Trying to solve the problem with accents and so
        filterCond = filterCond.decode('utf-8')

        if not filterCond:
            filterCond = textHeader

    return (header, filterCond)


def main():

    config = ConfigParser.ConfigParser()
    config.read([os.path.expanduser('~/.IMAP.cfg')])

    SERVER = config.get("IMAP1", "server")
    USER = config.get("IMAP1", "user")
    # PASSWORD = getpass.getpass()
    PASSWORD = keyring.get_password(SERVER, USER)

    # Make connections to server
    # Sieve client connection
    c = Client(SERVER)
    c.connect(USER, PASSWORD, starttls=True, authmech="PLAIN")
    # IMAP client connection
    M = imaplib.IMAP4_SSL(SERVER)
    M.login(USER, PASSWORD)

    PASSWORD = "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@"

    end = ""
    while (not end):
        # Could we move this parsing part out of the while?
        script = c.getscript('sogo')
        p = Parser()
        p.parse(script)
        (rules, more) = extractActions(p)
	

        # We are going to filter based on one message
        msg = selectMessage(M)
        (keyword, filterCond) = selectHeaderAuto(M, msg)


        actions = selectAction(p, M)
        # actions[0][1] contains the rule selector
        # print "actions ", actions[0][1]
        # print rules[actions[0][1]]

        # For a manual selection option?
        # header= selectHeader()
        # keyword = selectKeyword(header)

	# Eliminate
        # conditions = []
        # conditions.append((keyword, ":contains", filterCond))

        newActions = addRule(rules, more, keyword, filterCond, actions)

        print newActions

        fs = constructFilterSet(newActions)

        sieveContent = StringIO.StringIO()
        # fs.tosieve(open(FILE_SIEVE, 'w'))
        fs.tosieve(sieveContent)

        # Let's do a backup of the old sieve script
        name = time.strftime("%Y-%m-%d-%H-%M-%S", time.gmtime())
        c.putscript(name+'sogo', script)

        # Now we can put the new sieve filters in place
        # fSieve = open(FILE_SIEVE, 'r')
        # if not c.putscript('sogo', fSieve.read()):
        if not c.putscript('sogo', sieveContent.getvalue()):
            print "fail!"

	# Let's start the git backup

	repo = Repo(repoDir)
	index = repo.index

	listScripts=c.listscripts()[1]
	listScripts.sort() 

	print len(listScripts)
	print listScripts[0]
	# script = listScripts[-1] # The last one
	sieveFile=c.getscript('sogo')
	file=open(repoDir+repoFile,'w')
	file.write(sieveFile)
	file.close()
	index.add(['*'])
	index.commit(name+'sogo')

	if len(listScripts)>6:
		# We will keep the last five ones (plus the active one)
		numScripts = len(listScripts) - 6
		i = 0
		while numScripts > 0:
			script = listScripts[i]
			c.deletescript(script)
			i = i + 1
			numScripts = numScripts - 1

        end = raw_input("More rules? (empty to continue) ")

if __name__ == "__main__":
    main()
