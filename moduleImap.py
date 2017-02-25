#!/usr/bin/env python

# We will have here the set of functions related to imap mail management

import configparser
import os
import sys
import logging
import time
import getpass
import imaplib
import email
import hashlib
import binascii
import distance
import io
import keyring
from email.header import Header
from email.header import decode_header
import ssl

msgHeaders = ['List-Id', 'From', 'Sender', 'Subject', 'To', 
              'X-Original-To', 'X-Envelope-From', 
              'X-Spam-Flag', 'X-Forward']
headers = ["address", "header"]
keyWords = {"address": ["From", "To"],
            "header":  ["subject", "Sender", "X-Original-To", "List-Id"]
            }

def getPassword(server, user):
    # Deleting keyring.delete_password(server, user)
    password = keyring.get_password(server, user)
    if not password:
        logging.info("[%s,%s] New account. Setting password" % (server, user))
        password = getpass.getpass()
        keyring.set_password(server, user, password)
    return password

def stripRe(header):
    # Drop some standard strings added by email clients
    Res = ['Fwd', 'Fw', 'Re', 'RV']
    for h in Res:
        header = header.replace(h+': ', '')
    return(header)


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

def mailFolder(account, accountData, logging, res):
    SERVER = account[0]
    USER = account[1]
    PASSWORD = getPassword(SERVER, USER)

    srvMsg = SERVER.split('.')[0]
    usrMsg = USER.split('@')[0]
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
        total = 0
        msgs = ''
        for rule in RULES:
            action = rule.split(',')
            logging.debug(action)
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
                        total = total + i
                    else:
                        logging.debug("%s -  Couldn't delete messages!" % msgTxt)
                        msgTxt = "%s -  Couldn't delete messages!" % msgTxt
                else:
                    logging.debug("%s - Couldn't move messages!" % msgTxt)
                    msgTxt = "%s - Couldn't move messages!" % msgTxt
            logging.info(msgTxt)
    M.close()
    M.logout()
    res.put(("ok", SERVER, USER, total))
 
def doFolderExist(folder, M):
    if not folder.startswith(('"', "'")):
        folderName = '"%s"'%folder
    else:
        folderName = folder

    return (M.select(folderName))

def selectHeader():
    i = 1
    for j in headers:
        print(i, ") ", j, "(", keyWords[headers[i-1]], ")")
        i = i + 1
    return headers[int(input("Select header: ")) - 1]

def selectMessageAndFolder(M):
    msg_number =""
    startMsg = 0
    folder = "INBOX"
    while (not msg_number.isdigit() or (startMsg < 0)):
        rows, columns = os.popen('stty size', 'r').read().split()
        numMsgs = 24
        if rows:
           numMsgs = int(rows) - 3
        print("folder",folder)
        M.select(folder)
        data = M.sort('ARRIVAL', 'UTF-8', 'ALL')
        if (data[0] == 'OK'):
            j = 0
            msg_data = []
            messages = data[1][0].decode("utf-8").split(' ')
            #lenId = len(str(messages[-1]))
            print("Number of messsages", len(messages))
            if startMsg == 0: 
                startMsg = len(messages) - numMsgs + 1
            else:
		# It will be a negative number, we'll use it a starting point
		# changing the sing
                startMsg = -startMsg - 1

            #print("start", startMsg)
            #print(messages[0], messages[1])
            for i in messages[startMsg:startMsg + numMsgs - 1]:
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
                        #print(headFrom)
                        #print(headSubject)
                        headFromDec = headerToString(headFrom)
                        headSubjDec = headerToString(headSubject)
                        print(fmt % (j,
                                     headFromDec[:20],#[0][0][:20],
                                     headSubjDec[:40]))#[0][0][:40]))
                        j = j + 1
            msg_number = input("Which message? ([-] switches mode: [number] starting point [string] folder name)\n")
            if msg_number.isdigit():
                startMsg = int(msg_number)
            elif (len(msg_number) > 0) and (msg_number[0] == '-'):
                if msg_number[1:].isdigit():
                    startMsg = int(msg_number)
                else:
                    folder = selectFolder(M, msg_number[1:])
                    folder = nameFolder(folder) 
        else:
            return 0

    return (folder, msg_data[int(msg_number)])  # messages[-10+int(msg_number)-1]


def selectMessage(M):
    msg_number =""
    startMsg = 0
    folder = "INBOX"
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

def selectAllMessages(folder, M):
    msgs = ""
    M.select(folder)
    data = M.sort('ARRIVAL', 'UTF-8', 'ALL')
    if (data[0] == 'OK'):
        messages = data[1][0].decode("utf-8").split(' ')

    return ",".join(messages)

def selectMessageSubject(folder, M, sbj):
    msg_number =""
    rows, columns = os.popen('stty size', 'r').read().split()
    numMsgs = 24
    msgs = ""
    distMsgs = ""
    if rows:
       numMsgs = int(rows) - 3
    try: 
        M.select(folder)
    except:
        return("","")
        
    data = M.sort('ARRIVAL', 'UTF-8', 'ALL')
    sbjDec = stripRe(headerToString(sbj))
    if (data[0] == 'OK'):
        j = 0
        msg_data = []
        messages = data[1][0].decode("utf-8").split(' ')
        lenId = len(str(messages[-1]))
        print("")
        for i in messages: #[-40:]: #[-numMsgs:]:
            typ, msg_data_fetch = M.fetch(i, '(BODY.PEEK[HEADER.FIELDS (SUBJECT FROM)])')
            # print msg_data_fetch
            for response_part in msg_data_fetch:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    msg_data.append(msg)
                    # Variable length fmt
                    fmt = "%2s) %-20s %-40s"
                    headFrom = msg['From']
                    headSubject = msg['Subject']
                    headSubjDec =  stripRe(headerToString(headSubject))
                    minLen = min(len(headSubjDec), len(sbjDec))
                    maxLen = max(len(headSubjDec), len(sbjDec))
		    # What happens when the subjects are very similar in the
		    # final part only?
                    # ayudita
                    # b'Visualizaci\xc3\xb3n ayudica'
		    #dist = distance.levenshtein(headSubject[-minLen:], sbj[-minLen:])
                    if minLen > maxLen/2:
                        if minLen > 0:
                            #print("len",minLen)
                            #print("he",headSubjDec[-minLen:])
                            #print("sb",sbjDec[-minLen:])
                            if minLen < 20:
                                # print("he",headSubjDec[-minLen:])
                                # print("sb",sbjDec[-minLen:])
                                dist = distance.hamming(headSubjDec[-minLen:], sbjDec[-minLen:])
                            else:
                                dist = distance.levenshtein(headSubjDec[-minLen:], sbjDec[-minLen:])
                        else:
                            dist = minLen
                    else:
                        dist = maxLen
                    #print("dist", dist)
                 

                    if (dist < minLen/4):
                        print("+", end = "", flush = True)
                        if msgs:
                           msgs = msgs + ',' + str(i)
                           distMsgs = distMsgs + ',' + str(dist)
                        else:
                           msgs = str(i)
                           distMsgs = str(dist)
                    else:
                        print(".", end ="", flush = True)
        print("")

    return (msgs,distMsgs)

def selectMessagesNew(M):
    M.select()
    end = ""
    while (not end):
       # Could we move this parsing part out of the while?
       # We are going to filter based on one message
       msgs = ""
       listMsgs = ""
       moreMessages = ""
       while not moreMessages:
            (folder, msg) = selectMessageAndFolder(M)
            sbj = msg['Subject']
            (msgs, distMsgs) = selectMessageSubject(folder, M, sbj)

            printMessageHeaders(M, msgs)

            if listMsgs: 
                listMsgs = listMsgs + ',' + msgs
            else:
                listMsgs = msgs

            moreMessages = input("More messages? ")    

       if listMsgs:
            printMessageHeaders(M, listMsgs)
            folder = selectFolder(M, moreMessages)
            print("Selected folder (before): ", folder)
            folder = nameFolder(folder) 
            print("Selected folder (final): ", folder)
            moveMails(M,listMsgs, folder)
       end = input("More rules? (empty to continue) ")

def selectFolder(M, moreMessages = ""):
    resp, data = M.list('""', '*')
    listFolders = ""
    numberFolder = -1
    while listFolders == "":
        inNameFolder = input("String in the folder ("+moreMessages+') ')
        i = 0
        if not inNameFolder: inNameFolder = moreMessages
        for name in data:
            if inNameFolder.encode('ascii').lower() in name.lower():
                listFolders = listFolders + "%d) %s\n" % (i, nameFolder(name))
                numberFolder = i
            i = i + 1
    print(listFolders, end = "")
    iFolder = input("Folder number ("+str(numberFolder)+") ")
    if not iFolder:
        iFolder = data[numberFolder]
    else:
        iFolder = data[int(iFolder)]
    return(iFolder)

def selectMessages(M):
    M.select()
    end = ""
    while (not end):
       # Could we move this parsing part out of the while?
       # We are going to filter based on one message
       msgs = ""
       listMsgs = ""
       moreMessages = ""
       while not moreMessages:
            (folder, msg) = selectMessage(M)
            sbj = msg['Subject']
            (msgs, distMsgs) = selectMessageSubject(folder, M, sbj)

            printMessageHeaders(M, msgs)

            if listMsgs: 
                listMsgs = listMsgs + ',' + msgs
            else:
                listMsgs = msgs

            moreMessages = input("More messages? ")    

       if listMsgs:
            printMessageHeaders(M, listMsgs)
            folder = selectFolder(M, moreMessages)
            print("Selected folder (before): ", folder)
            folder = nameFolder(folder) 
            print("Selected folder (final): ", folder)
            moveMails(M,listMsgs, folder)
       end = input("More rules? (empty to continue) ")

def loadImapConfig():
    config = configparser.ConfigParser()
    config.read([os.path.expanduser('~/.IMAP.cfg')])
 
    return(config, len(config.sections()))

def readImapConfig(config, confPos = 0):
    # sections=['IMAP6']
    sections=config.sections()

    SERVER = config.get(sections[confPos], "server")
    USER = config.get(sections[confPos], "user")
    PASSWORD = getPassword(SERVER, USER)
    RULES = config.get(sections[confPos], 'rules').split('\n')
    if config.has_option(sections[confPos], 'move'):
        FOLDER = config.get(sections[confPos], "move")
    else:
        FOLDER = ""
    return (SERVER, USER, PASSWORD, RULES, FOLDER)

def makeConnection(SERVER, USER, PASSWORD):
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

    return M

def nameFolder(folder):
    # b'(\\HasNoChildren) "/" Departamento/estudiantes' b'Departamento/estudiantes'
    #   01234567890123456789012
    # b'(\\HasChildren) "/" "unizar/aa vrtic/sicuz/servicios/web"'
    folder = folder.decode()
    folder = folder[folder.find('"/" ')+4:]

    return(folder)

def moveMails(M, msgs, folder):
    print("Copying ", msgs, " in ", folder)
    (status, resultMsg) = M.copy(msgs, folder)
    if status == 'OK':
        # If the list of messages is too long it won't work
        flag = '\\Deleted'
        result = M.store(msgs, '+FLAGS', flag)
        if result[0] != 'OK':
            print("fail!")
    M.expunge()
    # msgs contains the index of the message, we can retrieve/move them


def printMessageHeaders(M, msgs):
    if msgs:
        print (msgs)
        for i in msgs.split(','):
            typ, msg_data_fetch = M.fetch(i, '(BODY.PEEK[HEADER.FIELDS (SUBJECT FROM)])')
            for response_part in msg_data_fetch:
                if isinstance(response_part, tuple):
                    msgI = email.message_from_bytes(response_part[1])
                    print(headerToString(msgI['Subject']))


def listMessages(M, folder):
    # List the headers of all e-mails in a folder
    M.select(folder)
    data = M.sort('ARRIVAL', 'UTF-8', 'ALL')
    if (data[0] == 'OK'):
        messages = data[1][0].decode("utf-8").split(' ')
        for i in messages: #[-40:]: #[-numMsgs:]:
            typ, msg_data_fetch = M.fetch(i, '(BODY.PEEK[HEADER.FIELDS (SUBJECT FROM DATE)])')
            for response_part in msg_data_fetch:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    headSubject = msg['Subject']
                    headFrom = msg['From']
                    headDate = msg['Date']
                    print(headerToString(headFrom),
                          headerToString(headSubject),
                          headerToString(headDate))
            
def main():

    config = configparser.ConfigParser()
    config.read([os.path.expanduser('~/.IMAP.cfg')])

    SERVER = config.get("IMAP1", "server")
    USER = config.get("IMAP1", "user")
    PASSWORD = getPassword(SERVER, USER)

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

    listMessages(M, 'INBOX')

if __name__ == "__main__":
    main()