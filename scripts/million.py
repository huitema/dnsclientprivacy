#!/usr/bin/python
# coding=utf-8
#
import sys
import codecs
import urllib.request as request
import csv
import json
import random
import dns.resolver

class millionLine:
    def __init__(self, dnsName, refs, sumRefs):
        self.dnsName = dnsName
        self.refs = refs
        self.sumRefs = sumRefs

def getUrlText(url):
    text = ""
    try:
        with request.urlopen(url) as response:
            if response.getcode() == 200:
                html_response = response.read()
                encoding = response.headers.get_content_charset('utf-8')
                text = html_response.decode(encoding)
            else:
                print("error for <" + url + ">")
    except Exception as e:
        print("Cannot download <" + url +">: " + str(e))
    return text

def loadCsv(fname):
    table = []
    with open(fname, 'r', encoding='UTF-8', errors='replace') as f:
        reader = csv.reader(f)
        nbLine = 0
        sumRefs = 0
        try:
            for row in reader:
                nbLine += 1
                if nbLine > 1:
                    refCount = int(row[4])
                    sumRefs += refCount
                    table.append(millionLine(row[2], refCount, sumRefs))
        except Exception as e:
            print("Line " + str(nbLine) + ", error: " + str(e))
    return table

def randomLine(table):
    rLimit = float(table[len(table)-1].sumRefs)
    r = random.random()*rLimit
    target = int(r)

    imin = 0
    imax = len(table) - 1
    if target <= table[imin].sumRefs or len(table) < 2:
        return imin
    elif target > table[imax-1].sumRefs:
        return len(table)-1
    else:
        while imin+1 < imax:
            imed = int((imin + imax)/2)
            if target > table[imed].sumRefs:
                imin = imed
            elif target > table[imed-1].sumRefs:
                return imed
            else:
                imax = imed
        return imin

def findCname(target):
    found = 0
    while found == 0:
        try:
            answers = dns.resolver.query(target, 'CNAME')
            if len(answers) > 0:
                target = str(answers[0].target)
            else:
                found = 1
        except dns.resolver.NoAnswer:
            found = 1
        except Exception as e:
            target= ""
            break
    return target

def findIP(target):
    ip = "0.0.0.0"
    try:
        answers = dns.resolver.query(target, 'A')
        if len(answers) > 0:
            ip = str(answers[0].address)
    except:
        pass
    return ip

# TODO: the recursive part is somewhat wrong, because just counting the name
# parts may overshoot in cases like "xxx.co.uk". Should be using the
# guidance from the domain list published by Mozilla et al.

def findNS(target):
    ns = ""
    while True:
        try:
            answers = dns.resolver.query(target, 'NS')
            if len(answers) > 0:
                ns = str(answers[0].target)
            break
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN) as e:
            parts = target.split('.')
            if len(parts) > 3:
                ipart = 0
                target = ""
                for x in parts:
                    if ipart > 0 and len(x) > 0:
                        target += x + "."
                    ipart += 1
            else:
                break
        except Exception as e:
            print("NS(" + target + "): " + str(e))
            break
    return ns

# TODO: recognize the names of common CDN services and cloud services
# Also, recognize the names of large DNS providers.
# This will provide the first pass into recognizing CDN and VPN concentration 


# Check that the million file is recent enough, and if not try to update it.
# Load the file in memory
# Pick names at random

fname = "majestic_million.csv"
nbNames = 25

if len(sys.argv) == 3:
    nbNames = int(sys.argv[2])
elif len(sys.argv) == 2:
    fname = sys.argv[1]
elif len(sys.argv) != 1:
    print("Usage {sys.argv[0]} [ majestic_million.csv [25]]")
    exit (-1)

table = loadCsv(sys.argv[1])
print("Table has: " + str(len(table)) + " rows.")
totalRefs = table[len(table)-1].sumRefs
print("Total refs: " + str(totalRefs))
i = 0
while i < nbNames :
    j = randomLine(table)
    target = table[j].dnsName
    if target.endswith('.') == False:
        target += '.'
    cName = findCname(target)
    if cName == target or cName == "":
        cName = findCname("www." + target)
        if cName == "":
            cName = target
    if cName.endswith('.') == False:
        cName += '.'
    ip = findIP(cName)
    ns = findNS(cName)
    print (str(j) + ", " + target + ", " + cName  + ", " + ip + ", " + ns)
    i+=1