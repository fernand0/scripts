#!/usr/bin/env python

"""
Author : pescimoro.mattia@gmail.com
Licence : GPL v3 or any later version

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
any later version.
 
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
 
You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import os
import sys
import nmap                         # import nmap.py
import time
import pickle

try:
    nm = nmap.PortScanner()         # creates an'instance of nmap.PortScanner
    ipList = {}
except nmap.PortScannerError:
    print('Nmap not found', sys.exc_info()[0])
    sys.exit(0)
except:
    print("Unexpected error:", sys.exc_info()[0])
    sys.exit(0)

def loadData():
    try:
	fIP = open("ipList.txt","r")
        try:
            ipList=pickle.load(fIP)
        except:
            print "The file does not contain adequate data\n"
    except: 
        print "No file with stored ips \n" 
    print ipList
    return ipList

def seek():                        # defines a function to analize the network
    count = 0
    nm.scan(hosts='192.168.1.0/24', arguments='-n -sP -PE -T5')
    # executes a ping scan

    hosts_list = [(nm[x]['addresses']) for x in nm.all_hosts()]
    # saves the host list

    for addresses in hosts_list:
        count = count + 1
	try:
		if not ipList.has_key(addresses['mac']):
			ipList[addresses['mac']] = ("", addresses['ipv4'])
		
	except:
		pass

    return count                   # returns the host number

def name():                        # defines a function to analize the network
    for mac in ipList.keys():
	name = raw_input(mac+"("+ipList[mac][0]+", "+ipList[mac][1]+") Name? ")
	print mac, name
        if name != "":
	    ipList[mac]=(name, ipList[mac])
    
if __name__ == '__main__':
    count = 1

    ipList=loadData()
    print ipList
    # check if the number of addresses is still the same
    while (count <= 10):
        print "Pass: ",count, "Found: ", seek(), "Total: ", len(ipList)
        time.sleep(1)
        count = count + 1

    print "========= So .... =======\n"
    print ipList

    name()
    print ipList
    fIP = open("ipList.txt","w")
    pickle.dump(ipList,fIP)
