#!/usr/bin/env python

import configparser
import os
import sys
import sievelib
import time
import getpass
import imaplib
import email
import io
import keyring
from email.header import Header
from email.header import decode_header
from sievelib.managesieve import Client
from sievelib.parser import Parser
from sievelib.factory import FiltersSet
from git import Repo
import ssl

msgHeaders = ['List-Id', 'From', 'Sender', 'Subject', 'To', 
              'X-Original-To', 'X-Envelope-From', 
              'X-Spam-Flag', 'X-Forward']
headers = ["address", "header"]
keyWords = {"address": ["From", "To"],
            "header":  ["subject", "Sender", "X-Original-To", "List-Id"]
            }
FILE_SIEVE = "/tmp/sieveTmp"

repoDir='/home/ftricas/Documents/config/'
repoFile='sogo.sieve'

def printRule(rule):
    print("Rule ")
    for cond in rule[1]:
        cond.tosieve()
        print()

def printRules(listRules):
    # For debugging
    for rule in list(listRules.keys()):
        printRule(listRules[rule])

def addRule(rules, more, keyword, filterCond, actions):
        #printRules(rules)
        #print(rules['"Docencia/master/masterbdi"'])
        #print(type(rules['"Docencia/master/masterbdi"']))
        theActions = actions[0][1].strip('"')
        if theActions not in rules:
                rules[theActions] = ['fileinto', []]
            
        #printRule(rule)

        # Is there a better way to do this?
        cmd = sievelib.factory.get_command_instance("header",
                                                    rules[theActions])
        cmd.check_next_arg("tag", ":contains")
        # __quote_if_necessary
        if not filterCond.startswith(('"', "'")):
            filterCond = '"%s"' % filterCond
        if not keyword.startswith(('"', "'")):
            #print(keyword)
            keyword = '"%s"' % keyword
        cmd.check_next_arg("string", keyword)
        cmd.check_next_arg("string", filterCond)
#print("cmd Cmd",cmd)
        #print("theActions",theActions[1])
        rules[theActions][1].append(cmd)
        #print("theActions++",theActions[1])

        # print "--------------------"
        #printRule(rules[theActions])
        # print "--------------------"
        #print(rules[theActions])
        #if theActions in more:
        #    print(more[theActions])
        #sys.exit()
        newActions = constructActions(rules, more)

        # print "actions, ", actions
        return newActions

def extractActions(p):
    i = 1
    rules = {}
    more = {}
    for r in p.result:
        # print("children", r.children)
        if r.children:
            # print type(r.children[0])
            key = r.children[0]
            if len(r.children) > 2:
                # If there are more actions (just one more
                # action, in fact), we will store it in more
                theKey = key['address'].strip('"') 
                more[theKey] = []
                more[theKey].append(r.children[1]['address'])
            if (type(key) == sievelib.commands.FileintoCommand):
                # print(i, ") Folder   ", key['mailbox'])
                tests = r.arguments['test'].arguments['tests']
                if key['mailbox'] in rules:
                    #print("tests-mailbox.", )
                    #tests[0].tosieve()
                    #print()
                    theKey = key['mailbox'].strip('"') 
                    rules[theKey][1] = rules[theKey][1] + tests
                else:
                    #print("rules..",rules)
                    #print("tests..",dir(tests[0]))
                    #print("\ntests..", vars(tests[0]))
                    #print("\ntosieve...") 
                    #tests[0].tosieve()
                    #print()
                    #print("key..",key['mailbox'])
                    theKey = key['mailbox'].strip('"') 
                    rules[theKey] = []
                    rules[theKey].append("fileinto")
                    rules[theKey].append(tests)
                    #print("rules..++",rules)
            elif (type(key) == sievelib.commands.RedirectCommand):
                # print i, ") Redirect ", key['address']
                tests = r.arguments['test'].arguments['tests']
                theKey = key['address'].strip('"') 
                if theKey in rules:
                    rules[theKey][1] = rules[theKey][1] + tests
                else:
                    rules[theKey] = []
                    rules[theKey].append("redirect")
                    rules[theKey].append(tests)
            else:
                print(i, ") Not implented ", type(key))
        else:
            print(i, ") Not implented ", type(r))

        i = i + 1

    return (rules, more)


def constructActions(rules, more):
    actions = []
    for rule in list(rules.keys()):
        action = []
        #print("\n----------------------------")
        #print("rule", rule)
        #print("rules[rule]",rules[rule])
        #print("-----")
        #print(rules[rule][0])
        #print("-----")
        #printRule(rules[rule])
        #print("more",more)
        #print("rule",rule)
        act = []
        if rule in more:
            action.append((rules[rule][0],
                          (rule, more[rule][0]), rules[rule][1]))
        else:
            #print("actions",rules[rule][0], rule, rules[rule][1])
            #if not rules[rule][0].startswith(('"', "'")):
            #    rules[rule][0] = '"%s"' % rules[rule][0]
            #if not rule.startswith(('"', "'")):
            #    theRule = '"%s"' % rule
            #else:
            theRule = rule
            #print("actions 2",rules[rule][0], theRule, rules[rule][1])
            action.append((rules[rule][0], (theRule,), rules[rule][1]))
        # action.append(act)

        actions.append(action)
    # print "actions, ", actions
    return actions


def constructFilterSet(actions):
    fs = FiltersSet("test")
    for action in actions:
        #print("cfS-> act ", action)
        conditions = action[0][2]
        #print("cfS-> cond", conditions)
        cond = []
        for condition in conditions:
            #print("cfS condition -> ", condition)
            # print(type(condition))
            #print(condition.arguments)
            head = ()
            (key1, key2, key3) = list(condition.arguments.keys())
            #print("keys",key1, key2, key3)
            #print("keys",condition.arguments[key1], condition.arguments[key2], condition.arguments[key3])
            head = head + (condition.arguments['match-type'].strip('"'),
                           condition.arguments['header-names'].strip('"'),
                           condition.arguments['key-list'].strip('"'))#.decode('utf-8'))
            # We will need to take care of these .decode's
            #print(head)
            cond.append(head)

        # print "cond ->", cond
        act = []
        for i in range(len(action[0][1])):
            act.append((action[0][0], action[0][1][i]))
        act.append(("stop",))
        #print("cfS cond ->", cond)
        #print("cfS act ->", act)
        aList = [()]
        #for a in cond[0]:
        #    print("cfS ",a)
        #    aList[0] = aList[0] + (a.strip('"'),)
        #print("cfS aList", aList)
        #print("cfS cond", cond)
        #print("cfS act", act)
        fs.addfilter("", cond, act)
        #fs.addfilter("", aList, act)
        # print "added!"

    return fs

def headerToString(header):
    if not (header is None):
        headRes = ""
        for (headDec, enc) in decode_header(header):
            # It is a list of coded and not coded strings
            if (enc is None) or (enc == 'unknown-8bit'): 
                enc = 'iso-8859-1'
            if (not isinstance(headDec, str)):
                headDec = headDec.decode(enc)
            headRes = headRes + headDec
    else:
        headRes = ""

    return headRes

def doFolderExist(folder, M):
    if not folder.startswith(('"', "'")):
        folderName = '"%s"'%folder
    else:
        folderName = folder

    return (M.select(folderName))


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
        print(cad[3:], cad[:3])

    option = input("Select one: ")

    print(option, len(p.result))

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
        folder = input("Name of the folder: ")
        print("Name ", folder)
        if (doFolderExist(folder, M)[0] != 'OK'):
            print("Folder ", folder, " does not exist")
            sys.exit()
        else:
            print("Let's go")
            actions.append(("fileinto", folder))
            actions.append(("stop",))
    elif (int(option) == len(p.result)+2):
        redir = input("Redirection to: ")
        print("Name ", redir)
        itsOK = input("It's ok? (y/n)")
        if (itsOK != 'y'):
            print(redir, " is wrong")
            sys.exit()
        else:
            print("Let's go")
            actions.append(("redirect", redir))
            actions.append(("stop",))

    return actions


def selectHeader():
    i = 1
    for j in headers:
        print(i, ") ", j, "(", keyWords[headers[i-1]], ")")
        i = i + 1
    return headers[int(input("Select header: ")) - 1]


def selectKeyword(header):
    i = 1
    for j in keyWords[header]:
        print(i, ") ", j)
        i = i + 1
    return keyWords[header][int(input("Select header: ")) - 1]

def selectMessage(M):
    msg_number =""
    while (not msg_number.isdigit()):
        rows, columns = os.popen('stty size', 'r').read().split()
        numMsgs = 24
        if rows:
           numMsgs = int(rows) - 3
        M.select()
        data = M.sort('ARRIVAL', 'UTF-8', 'ALL')
        if (data[0] == 'OK'):
            j = 0
            msg_data = []
            messages = data[1][0].decode("utf-8").split(' ')
            lenId = len(str(messages[-1]))
            for i in messages[-numMsgs:]:
                typ, msg_data_fetch = M.fetch(i, '(BODY.PEEK[])')
                # print msg_data_fetch
                for response_part in msg_data_fetch:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        msg_data.append(msg)
                        # Variable length fmt
                        fmt = "%2s) %-20s %-40s"
                        headFrom = msg['From']
                        headSubject = msg['Subject']
                        if (not headSubject):
                            headSubject = ""
                        print(fmt % (j,
                                 headerToString(headFrom)[:20],#[0][0][:20],
                                 headerToString(headSubject)[:55]))#[0][0][:40]))
                        j = j + 1
            msg_number = input("Which message? ")
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
                print(i, " ) ", header, msg[header])
            i = i + 1
        import locale
        header_num = input("Select header: ")

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

        print("Filter: (header) ", header, ", (text) ", textHeader)
        filterCond = input("Text for selection (empty for all): ")
        # Trying to solve the problem with accents and so
        filterCond = filterCond#.decode('utf-8')

        if not filterCond:
            filterCond = textHeader

    return (header, filterCond)

def getPassword(server, user):
    # Deleting keyring.delete_password(server, user)
    password = keyring.get_password(server, user)
    if not password:
        logging.info("[%s,%s] New account. Setting password" % (server, user))
        password = getpass.getpass()
        keyring.set_password(server, user, password)
    return password


def main():

    config = configparser.ConfigParser()
    config.read([os.path.expanduser('~/.IMAP.cfg')])

    SERVER = config.get("IMAP1", "server")
    USER = config.get("IMAP1", "user")
    # PASSWORD = getpass.getpass()
    PASSWORD = getPassword(SERVER, USER)

    # Make connections to server
    # Sieve client connection
    c = Client(SERVER)
    if not c.connect(USER, PASSWORD, starttls=True, authmech="PLAIN"):
        print("Connection failed")
        return 0
    # IMAP client connection
    context = ssl.create_default_context()
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

    PASSWORD = "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@"
    M.select()

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
        # print("actions ", actions[0][1])
        # print(rules[actions[0][1].strip('"')])

        # For a manual selection option?
        # header= selectHeader()
        # keyword = selectKeyword(header)

        # Eliminate
        # conditions = []
        # conditions.append((keyword, ":contains", filterCond))

        #print("filtercond", filterCond)
        newActions = addRule(rules, more, keyword, filterCond, actions)

        #print("nA",newActions)
        #print("nA 0",newActions[0][0][2][0].tosieve())
        #print("nA 0")

        fs = constructFilterSet(newActions)

        sieveContent = io.StringIO()
        # fs.tosieve(open(FILE_SIEVE, 'w'))
        # fs.tosieve()
        # sys.exit()
        fs.tosieve(sieveContent)

        #import time
        #time.sleep(5)
        # Let's do a backup of the old sieve script
        name = time.strftime("%Y-%m-%d-%H-%M-%S", time.gmtime())
        res  = c.putscript(name+'sogo', script)
        print("res",res)

        # Now we can put the new sieve filters in place
        # fSieve = open(FILE_SIEVE, 'r')
        # if not c.putscript('sogo', fSieve.read()):
        #print(sieveContent.getvalue())

        if not c.putscript('sogo', sieveContent.getvalue()):
            print("fail!")

        # Let's start the git backup

        repo = Repo(repoDir)
        index = repo.index

        print("listscripts",c.listscripts())
        listScripts=c.listscripts()
        print("listscripts",listScripts)
        if (listScripts != None):
            listScripts=listScripts[1]
            listScripts.sort() 
            print("listscripts",c.listscripts())
            print(listScripts[0])

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

        end = input("More rules? (empty to continue) ")

if __name__ == "__main__":
    main()
