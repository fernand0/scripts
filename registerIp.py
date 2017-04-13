#!/usr/bin/env python

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import socket
import time
import pwd
import inspect

# Based on code from: https://www.twilio.com/blog/2017/02/an-easy-way-to-read-and-write-to-a-google-spreadsheet-in-python.html


def getIp():
    # http://stackoverflow.com/questions/166506/finding-local-ip-addresses-using-pythons-stdlib/1267524#1267524
    return([l for l in ([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")][:1], [[(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]) if l][0][0])


def main():
    hostname = socket.gethostname()
    dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) # script directory

    ip = getIp()
    user = dir[:dir.find('/',len('/home/'))]

    print(hostname, user, ip, time.time())

    client_secret =  user + '/.ssh/otros/errBot Youtube-7ff8701bdfdd.json'

    sheet_name = 'Registro IPs'
    
    # use creds to create a client to interact with the Google Drive API
    scope = ['https://spreadsheets.google.com/feeds']
    creds = ServiceAccountCredentials.from_json_keyfile_name(client_secret, scope)
    client = gspread.authorize(creds)
    
    sheet = client.open(sheet_name)
    
    
    try:
        worksheet = sheet.worksheet(hostname)
    except gspread.exceptions.WorksheetNotFound:
        worksheet = sheet.add_worksheet(hostname, 5, 5)
    
    worksheet.insert_row([time.time(), ip],2)

if __name__ == '__main__':
    main()
