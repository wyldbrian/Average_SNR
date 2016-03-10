#!/usr/bin/env python

#+-----------------------------------------------------------------------+
#| File Name: avg_snr.py                                                 |
#|                                                                       |
#| Description: Sum SNR of every modem in list of cisco UBR's (threaded) |
#|      and divide by number of interface occurrences to obtain average  |
#|      SNR by upstream.                                                 |
#|                                                                       |
#+-----------------------------------------------------------------------+
#| Authors: KwithH and wyldbrian                                         |
#+-----------------------------------------------------------------------+
#| Date: 2016-03-09                                                      |
#+-----------------------------------------------------------------------+

from __future__ import division
import paramiko
import unicodedata
import subprocess
import re
import threading

ubr_ips = ['xxx.xxx.xxx.xxx', 'xxx.xxx.xxx.xxx', 'xxx.xxx.xxx.xxx', 'xxx.xxx.xxx.xxx']


####################################################
#  Get number of occurrances of specific upstream  #
####################################################

def getDivisor(port, cableInterface):
        divisor = cableInterface.count(port)
        return divisor


####################################################
#      Gather node labels and cable upstreams      #
#           from CMTS(s) for comparison            #
####################################################

def getNodes(ip):

        cable = []
        label = []
        node = {}

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect( ip, username='USERNAME', password='PASSWORD', look_for_keys=False)

        stdin, stdout, stderr = ssh.exec_command("show cable modem summary")
        for line in stdout:
                if "Cust:" in line and not "No Monitor" in line:
                        cable.append(re.search("C\d+\/\d+\/\d+\/U\d+", line).group())
                        label.append(line[line.find("{")+1:line.find("}")])
        ssh.close()

        label = [value.encode('UTF8') for value in label]
        cable = [value.encode('UTF8') for value in cable]

        i = 0
        while i < len(cable):
                for item in cable:
                        node[cable[i]] = label[i]
                        i += 1

        return node

####################################################
#     Gather, average, and report on average       #
#           modem SNR by cable upstream            #
####################################################

def getSNR(ip):
        cableInterface = []
        snr = []

        nodes = getNodes(ip)


        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect( ip, username='USERNAME', password='PASSWORD', look_for_keys=False)

        stdin, stdout, stderr = ssh.exec_command("show cable modem phy")
        for line in stdout:
                if 'tdma' in line:
                        cableInterface.append(line.split()[1].strip())
                        snr.append(line.split()[4].strip())
        ssh.close()

        cableInterface = [value.encode('UTF8') for value in cableInterface]
        snr = [value.encode('UTF8') for value in snr]

        x = 0
        snrDict = {}
        while x < (len(cableInterface)):
                for port in cableInterface:
                        if port in snrDict.keys():
                                if snr[x] == '-----':
                                        snr[x] = 0.0
                                snrDict[port] = (float(snrDict[port]) + float(snr[x]))
                                x += 1
                        else:
                                if snr[x] == '-----':
                                        snr[x] = 0.0
                                snrDict[port] = float(snr[x])
                                x += 1

        for port, value in snrDict.items():
                divisor = getDivisor(port, cableInterface)

				# This check uses print, but you can call whatever action you want.
                if (value / divisor) < 30:
                        try:
                                print(port + " " + nodes[port])
                                print(value / divisor)
                                print('\n')
                        except:
                                print(ip)
                                print(port + " not found in snrDict! (probably doesn't have modems)\n")


####################################################
#        Thread SSH cons & alarm on avg SNR        #
####################################################

def main():

        threads = []

        for ip in ubr_ips:
                t = threading.Thread(target=getSNR, args=(ip,))
                t.start()
                threads.append(t)

        for t in threads:
                t.join()

main()