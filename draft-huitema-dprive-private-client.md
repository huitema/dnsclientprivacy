---
title: Privacy Oriented DNS Client
abbrev: DNS-Client-Privacy
docname: draft-huitema-dprive-private-client-00
category: info
date: 2019

stand_alone: yes

ipr: trust200902
area: General
kw: Internet-Draft

coding: us-ascii
pi: [toc,  sortrefs, symrefs, comments]

author:
      -
        ins: C. Huitema
        name: Christian Huitema
        org: Private Octopus Inc.
        street: 427 Golfcourse Rd
        city: Friday Harbor
        code: WA 98250
        country: U.S.A
        email: huitema@huitema.net

--- abstract

This document presents a DNS Name Resolution approach that does not
rely on server trust to provide DNS Privacy. The proposed solution
depends on availability of TSL and encrypted SNI, because in the
absence of both services attempts at DNS Privacy are futile. It
recommends obtaining ESNI records through trusted off-path resolvers
and caching them on the client before the actual connection. It
also recommends obtaining the fronting server addresses through the
locally provisioned resolvers, so as to minimize the amount of
information leaked to off-path services.

--- middle

# Introduction

Historically, adversaries have been able to monitor the use of web
services through three primary channels: looking 
at IP addresses in packet headers, looking at the data stream between
user and services, and looking at DNS requests.
These channels are getting progressively closed.
A growing fraction of
Internet communication is encrypted, mostly using Transport Layer Security
(TLS) {{?RFC5246}}. There is work in progress to encrypt
the Service Name Information (SNI) TLS extension {{?RFC6066}}. More and
more services are colocated on multiplexed servers, loosening the
relation between IP address and web service. For example, in virtual hosting
solutions, multiple services can be hosted as co-tenants on the same server,
and the IP address and port do not uniquely identify a service. In cloud or 
Content Delivery Networks (CDNs) solutions, a given platform hosts the services
or servers of a lot of organizations, and looking up to what netblock
an IP address belongs reveals little.  
Progressive deployment of solutions like DNS in
TLS (DTLS) {{?RFC7858}} and DNS over HTTPS (DoH) {{?RFC8484}} 
mitigates the disclosure of DNS information. However, while these
solutions hide the DNS traffic from on-path observers, the entire stream
of queries from a given client is still available to the
recursive servers that handle the clients' queries.

This document discusses strategies for reinforcing DNS privacy by minimizing
the amount of information available to third parties.

# Minimal Information Disclosure {#minimum-disclo}

Most Internet exchanges are preceded by a  domain name resolution, which involves
repeated queries to series of servers. Eventually, the resolution returns the
IP address of the target, a connection to that target is established, and
an application protocol runs over that connection. This process is bound to
leak at least some data. The minimal set would be:

* The IP addresses in the packet headers, available to any observer of the
  connection,
  
* The identify of the target service, available to the server hosting that
  service.

DNS privacy leaks happen when observers obtain more information than the IP
addresses in the packet headers. In particular, when the IP address does not
identify the service, a privacy leak happens when the target service can be
identified by other parties than the hosting server. Example of
privacy leaks occuring today include:

* DNS traffic in clear text revealing the IP address of the client and the
  target domain name.

* DNS queries sent to a recursive resolver and logged by that resolver.

Our goal is to define name resolution strategies that minimize such privacy leaks.

# Key assumptions

## IP address and identity

We have to assume that both the DNS server will be able to identify the client
based on its IP address.

When the DNS server is managed by the connectivity provider, we assume that
the client's identity was provided as part of obtaining connectivity. There
may be some networks where that is not the case, such as for example some
permissive Wi-Fi hot spots, but these are more the exception than the rule.

When the DNS service is provided by an off path provider, we assume that the
provider can link the client identity to the IP address of incoming queries.
This is obvious when the off path provider manages multiple web services,
and can obtain client login information on any of these services. Without
that, we can expect the linkage between IP address and client identity to
be obtained through web trackers and other such devices.

## Central role of TLS and ESNI {#esni-central}

We assume that the client's traffic is encrypted, most likely using TLS.
If the client traffic was not encrypted, examination of the clear text
traffic would quickly reveal the nature and identity of the server.

We also assume that when using TLS, the client uses ESNI. If carried
in clear text, the SNI would reveal the identity of the target server.

When the traffic is not encrypted, or when the SNI is carried in clear
text, attempts at DNS privacy are futile. The safest attitude is to
send queries to the default DNS resolver provisioned by the network.
This is preferable to using an off-path resolver, because the network
provided has access to network level data, while the off path DNS
resolver does not. Sending queries off path would just leak that
knowledge to the off-path resolver, without any privacy benefit.

# Private DNS queries with SNI Encryption

Clients that use SNI Encryption to contact a hidden server learn first the name
of the fronting server that will accept connections on its behalf, and the
cryptographic key used to encrypt the server name. The SNI Encryption specification
{{?I-D.ietf-tls-esni}} defines an ESNI record in which the "public name"
element conveys the name of the fronting server and the "ESNI Keys" elements
convey public keys that can be used to encrypt the ESNI parameters. The
ESNI record is typically published in the DNS, so the exchanges will work
like that:

1- Obtain the ESNI record for the hidden server, "hidden.example.com"

2- Examine the ESNI record and retrieve the name of the fronting server,
   "fronting.example.com"

3- Resolve the name of the fronting server and find its IP address,

4- Establish a TCP connection to the fronting server,

5- Establish a TLS connection in which the "public" SNI is set to
   the public server name, "fronting.example.com", but the ESNI
   extension encodes the name of hidden server "hidden.example.com"
   to which the fronting server will relay the connection.

Of course, if the client executes all these steps for each request,
there will not be much privacy benefit, because the DNS request in step 1
will disclose the client's interest in "hidden.example.com". But suppose
instead that the client has performed the first step in advance and
has cached the result. At that point, the various observers will only see:

* A DNS request for "fronting.example.com",

* A series of packets in which the IP destination is set to the
  IP address of "fronting.example.com",

* and, a TLS connection in which the SNI is set to "fronting.example.com".

The IP addresses and the SNI parameters are visible to the local network
provider. Sending a DNS query to the DNS server provisioned by that
provider will not disclose any information that could not be gained
by examining the traffic itself, which meets the requirement expressed
in (#minimum-disco). This is true even if the DNS query is not encrypted.

Sending the DNS Query to an alternative provider, in contrast, would
create an additional disclosure to that provider. The alternative
provider is usually not on-path, and thus does not have access to
IP headers or packet contents.

In this ESNI scenario, we achieve our goal of privacy if the
ESNI record was obtained and cached before the connection. This is
often possible, but not always. The ESNI record may not be in the cache
if this is the first contact with the hidden server, or if the time to
live of the record expired since the previous contact. We
have traded the difficult problem of hiding the real time DNS
transaction for the related problem of hiding the specific DNS
transactions that acquire the ESNI record.

## Private acquisition of ESNI Records

The acquisition of
the ESNI record associated with the hidden service needs to be kept
private, and also needs to be kept secure in order to avoid the fronting
server spoofing attacks discussed in {{?I-D.ietf-tls-sniencryption}}.
Using an encrypted DNS service like DoH or DTLS helps. It
keeps the data out of sight of anyone but the selected resolver,
and also provides some amount of protection against spoofing attacks.

The first proposal would thus be:

1- If there is no ESNI record in the cache, obtain it
   from a trusted DNS server using an encrypted transport like DoH or
   DTLS.

2- Examine the ESNI record and retrieve the name of the fronting server,
   "fronting.example.com"

3- Resolve the name of the fronting server and find its IP address
   using the default resolver.

4- Establish a TCP connection to the fronting server,

5- Establish a TLS connection in which the "public" SNI is set to
   the public server name, "fronting.example.com", but the ESNI
   extension encodes the name of hidden server "hidden.example.com"
   to which the fronting server will relay the connection.

This approach provides some robust protections, but it runs all ESNI
requests through an off path resolver, which is still a privacy
issue. There are some options for mitigating this leakage of
information:

* The client may want to perform ESNI lookup for a variety of names,
  not just the one names that it is looking for. If the 
  resolver is off path and does not observe the packet exchanges,
  it will not be able to distinguish the actual queries from
  the cover queries.

* The server may be able to provide the client with updated copies of
  the ESNI record. This will not help the first connection, but it
  will increase the chances that the ESNI record is in the cache for
  the next connection.

* The client may be able to spread the ESNI lookup through several
  trusted DNS servers, not just one. The spreading should be organized
  saw that repeated queries for the same name are performed through the
  same server, because otherwise the spreading will just manage to
  duplicate the leaks on several servers.

* The client may want to perform the initial ESNI lookups using
  a VPN connection, a web proxy, or some onion routing system, thus
  hiding its identity from the server.

* The client may want to use off-line provisioning mechanisms to
  install specific DNS records in the local cache, much like it
  could add known IP addresses to a local /etc/host file.
  
## Managing DNS requests for clear text servers
 
We saw in (#esni-central) that when the server is accessed in clear text,
or even when the server is using TLS but fails to use ESNI, then attempts
at DNS privacy are not only futile but also somewhat counter-productive.
There are cases when the client knows in advance that the connection
will happen in clear text, in which case the policy is simple to
implement. But when the client knows that the connection will happen
over TLS, it needs to ascertain whether the connection will use ESNI
or not.

The recommendation is to use negative caching. 








--- back










