#!/usr/bin/env python

"""
This program tries to be a Fing-like tool 
https://play.google.com/store/apps/details?id=com.overlook.android.fing&hl=en 
It scans your Wi-Fi network, and discovers which devices are connected.

Author: Fernando Tricas García (fernand0@elmundoesimperfecto.com) 
Based on a work of pescimoro.mattia@gmail.com that can be found at:
https://github.com/mpescimoro/WiFinder

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
import pwd, grp
import time
import pickle

# File used to store data
fileName=os.path.expanduser('~')+'/.ipList.txt'

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
	fIP = open(fileName,"r")
        try:
            ipList=pickle.load(fIP)
        except:
            print "The file does not contain adequate data\n"
    except: 
        print "No file with stored ips \n" 
	ipList={}

    return ipList


# http://stackoverflow.com/questions/2699907/dropping-root-permissions-in-python
#Throws OSError exception (it will be thrown when the process is not allowed
#to switch its effective UID or GID):

def drop_privileges():
    if os.getuid() != 0:
        # We're not root so, like, whatever dude
        return

    # Get the uid/gid from the name
    user_name = os.getenv("SUDO_USER")
    pwnam = pwd.getpwnam(user_name)

    # Remove group privileges
    os.setgroups([])

    # Try setting the new uid/gid
    os.setgid(pwnam.pw_gid)
    os.setuid(pwnam.pw_uid)

    #Ensure a reasonable umask
    old_umask = os.umask(0o22)


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
	name = raw_input(mac+" ("+ipList[mac][0]+","+ipList[mac][1]+") Name? ")
        if name != "":
	    ipList[mac]=(name, ipList[mac][1])
    
if __name__ == '__main__':
    count = 1

    ipList=loadData()
    # check if the number of addresses is still the same
    while (count <= 10):
        print "Pass: ",count, "Found: ", seek(), "Total: ", len(ipList)
        time.sleep(1)
        count = count + 1

    print(os.getresuid())
    print "We do not need root privileges anymore ...\n"
    drop_privileges()
    print(os.getresuid())

    print "========= So .... =======\n"
    print ipList

    name()
    print ipList
    fIP = open(fileName,"w")
    pickle.dump(ipList,fIP)
