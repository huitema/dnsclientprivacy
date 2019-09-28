#!/usr/bin/python
# coding=utf-8
#
# This scripts tries to evaluate the CDN associated with a specific target name
#
# Examples for tests:
# www.nytimes.com => fastly.net
# www.youtube.com => google.com
# www.disney.com => akamai.net
# www.instagram.com =>facebook.com.
# www.linkedin.com => own servers
# www.zendesk.com => cloudflare.net
# www.aka.ms => akamaiedge.net
#
# First method is to roll down the chain of CNAME. Success if the final CNAME
# ends up with one of the target domains.
# Possible test: take list of domains, roll the CNAME, find the end,
# tabulate the most common endings. Are these CDN?
#
# Working by cname does not always work. For example, the test of 
# www.digitalocean.com has no CNAME. The DNS server is managed by cloudflare,
# but this may be misleading. The IP address is 104.16.24.4, which belongs
# to a group managed by cloud flare. Finding that requires looking at BGP
# tables and AS domains.

import sys
import dns.resolver

if len(sys.argv) > 1:
    target = sys.argv[1]
else:
    target = "www.example.com"

found = 0

if target.endswith('.') == False:
    target += '.'

answers = dns.resolver.query(target, 'A')
for ip in answers:
    print ('Host ' + target + 'has IP ' + str(ip.address))

while found == 0:
    try:
        answers = dns.resolver.query(target, 'CNAME')
        if len(answers) > 0:
            print("There are "+ str(len(answers)) + " answers")
            for rdata in answers:
                print ('Host ' + target + ' has cname: ' + str(rdata.target))
            target = str(answers[0].target)
        else:
            print ("No CNAME for " + target)
            found = 1
    except dns.resolver.NoAnswer:
       found = 1
    except Exception as e:
        print ("Exception querying CNAME for " + target + ": " + str(e))
        found = 1

print ('Final: ' + str(target) )

found = 0
name_domain = target

while found == 0:
    try:
        answers = dns.resolver.query(name_domain, 'NS')
        if len(answers) > 0:
            for rdata in answers:
                print ('Host ' + name_domain + ' has NS ' + str(rdata))
                found = 1
    except dns.resolver.NoAnswer:
        pass
    except Exception as e:
       	print ("Exception querying NS for " + name_domain + ": " + str(e))
    if found == 0:
        parts = name_domain.split('.', 1)
        if len(parts) > 1:
            print ("After " + name_domain + " try: " + parts[1])
            name_domain = parts[1]
        else:
            found = 1
    