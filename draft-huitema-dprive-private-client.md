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
TLS (DoT) {{?RFC7858}} and DNS over HTTPS (DoH) {{?RFC8484}} 
mitigates the disclosure of DNS information. However, while these
solutions hide the DNS traffic from on-path observers, the entire stream
of queries from a given client is still available to the
recursive servers that handle the clients' queries. In (#minimum-disclo),
we develop the argument that moving DNS requests to an off path
resolver using DoH is only beneficial for privacy if the subsequent
communications are encrypted and do not expose clear text metadata
like the SNI. If such data is exposed, sending requests to an off path
resolver merely enables additional privacy leaks to the off path resolver,
without reducing leakage to the local network provider. It may
provide some benefit if the local provider is not yet able to extract
the information from packet headers and clear text metadata, but that
benefit is only temporary.


This document discusses strategies for reinforcing DNS privacy by minimizing
the amount of information available to third parties.

# Minimal Information Disclosure {#minimum-disclo}

DNS Privacy proponents are concerned that the DNS requests
carry a large amount of privacy sensitive data {{?RFC7626}}. However,
privacy sensitive data also leaks in IP packet headers and in clear
text parameters found in data packets. Focusing on the DNS requests
without considering the other leakages leads to imprecise
policies:

* In general, using the local resolver has no impact on privacy. If the
local resolver is engaged in data collection through DNS, the local
network is most probably also engaged in data collection through TCP
dump or similar methods. The local resolver does
not gain any information that the local network would not be able to
obtain anyhow.

* In general, sending DNS to an off-path resolver is a net loss for
privacy. The off-path resolver does not see IP headers, the content of
clear-text application packets, or the SNI parameter in TLS packets. By
getting the DNS stream, it acquires data that would otherwise only be
visible to the local network. Even if the privacy policy of the off-path
attacker is benign, this is a net privacy loss has the data is now
available to two parties instead of just one.

* There is only an exception when the connection uses TLS and ESNI. In
that case, the local network only sees the name of the public server.
Hiding acquisition of ESNI record from the local network does help
privacy, because it hides usage of the hidden server. 

The ESNI capable client can be expected to
perform two series of requests for each connection:

1) DNS queries to retrieve the ESNI information, or verify that
no such information is available for the target server.

2) DNS queries to retrieve the IP address of the public server
selected by the target, or the IP address of the target itself if
ESNI will not be used.

We obtain minimal disclosure if:

1) The ESNI information or its absence is obtained in a privacy respecting way
and cached at the client.

2) The IP address of the public server is obtained by DNS queries
sent to the local resolver.

Of course, the next question is whether the ESNI information can be obtained
without leaking just as much privacy sensitive data. It is easy to envisage
retrieval strategies that would not meet that requirement. For example,
if every connection was preceded by an ESNI retrieval request to an off path
server, the off path server would get as much information as if it was
seeing all DNS requests. It is also clear that retrieving the ESNI data
through the local server just prior to connecting to the public server
will jeopardize the benefits of ESNI.

## Minimal disclosure and hosting servers

Before developing an ESNI data retrieval strategy, we make another
observation related to minimal disclosure:

* There is no addtional privacy leakage if the ESNI is retrieved from an
off path resolver that also hosts the public server for the target.

The public server of the target will be able to access the server name
or the client IP address by observing the traffic to the hosted server,
even if traffic and SNI are encrypted. If the public server supports
DoH or DoT, it can process DNS requests for the target server while
maintaining minimal disclosure.

# Privacy Oriented ESNI Data Retrieval {#esni-retrieval}

We propose an ESNI retrieval data based on four options:

1) If the ESNI data or its absence is cached and the cached data is
not expired, there is no need for an additional query.

2) If the relation between target server and public server is known,
and if the public server supports DoH or DoT, retrieve the ESNI data
through that server.

3) If the public server is not known or cannot be accessed through DoH
or DoT, retrieve the ESNI data through an off-path trusted resolver.

4) Send gratuitous ESNI retrieval queries through the trusted resolver
to diminish the value of DNS information logged at that resolver.

## Using cached data minimizes tracking {#esni-caches}

The strategy proposed in (#minimum-disclo) separates the retrieval of
ESNI data and the establishment of connection. If ESNI data is cached,
the off path resolvers will not see an ESNI query for each connection.
If we assume that they cannot monitor the actual traffic, caching
the ESNI data diminishes the predictive value of DNS logs maintained
by the off-path resolvers.

## Obtaining the relation between target and public server {#hosting-server}

The ESNI data includes the name of the public server. The data in the
cache will become stale over time, but we can assume that the relation
between target and public server will remain somewhat stable. Using
stale values for the ESNI encryption keys would be dangerous, but
the downside of using a stale relation is limited tot he privacy leak
of the interest for the target server. If the DoH or DoT server
provides a recursive resolver, the client will obtain the correct
value of the ESNI data and learn the name of the up-to-date public
server, correcting the previous misdirection.

The identification of the public server is not directly available
when the target server does not support ESNI. In that case, ESNI
data retrieval will fail. Even so, it is important to identify the
hosting server of the target site. After the negative cache information
of ESNI absence expires, we will minimize privacy disclosure if the
subsequent query is sent to the DoH or DoT server managed by the
hosting service.

In many cases, the hosting service for a non ESNI supporting site can
be infered from a CNAME lookup. For example, a CNAME request
for "www.example.com" might return a response of the form
"example.com.12345.cdn.example.net". The local software can
notice that "cdn.example.net" designates a well known hosting service,
for which a DoH server is available. The name
of the hosting service may also be infered in other cases from the
IP address of the target server, if that IP address belongs to a
known address range of a known service.

## Using a trusted off path resolver maintains ESNI privacy {#esni-off-path}

Retrieving the ESNI data or testing its absence through an off path
resolver does provide information to that resolver, but still has
privacy benefits compared to retrieving the information from a
local resolver. If the client sends queries for ESNI data to a
local resolver, the resolver can correlate later that with later
requests for the public server. In contrast, the off-path resolver
will not see the later requests to the public server.

The privacy of this process can be augmented by adding "chaff" queries
for target names picked at random. This would have limited value against
a local resolver, because observing the traffic will reveal which
DNS requests were followed by actual connections. But the off-path
server does not have access to the traffic, and thus cannot simply
differentiate chaff from grain.

# Centralization considerations {#centralization}

Experience in other areas such as e-mail services taught us that
when infrastructure based services and off path services compete freely,
a small number of centralized off-path services come to dominate the
market. In the case of DNS, this could create a single point of
attacks such as censorship or tracking. The currently competing off-path
services appear willing to provide privacy and transparence guarantees,
but they could still feel the pressure of various authorities. It is
thus quite reasonable to be worried about centralization.

The strategy delineated in (#minimum-disclo) mitigates the centralization
risk in two ways: it provides incentives for hosting servers to deploy
their own DoH or DoT servers, thus ensuring some level of competition;
and, it reduce the amount of data available to the potentially
dominant centralized services.

The ESNI retrieval strategy presented in (#esni-retrieval) privileges
sending requests for information about a target to the hosting provider
of that target. Hosting providers will have reasonable incentives to
provide a DoH or DoT service. The service will increase the reliability
of their hosting service, and will also contribute to the
indepence of that service from the competing off-path providers.

The amount of data available to the centralized off-path providers will
be limited to mostly ESNI data retrieval, which is somewhat less sensitive
than the combination of ESNI data retrieval and real time connection
information. If sufficient number of hosting providers support DoT or
DoH, the centralized providers will only see a fraction of the ESNI
data retrieval, which again reduces the data leakage. Finally, the
insertion of "chaff" traffic will reduce the value of the data collected
by the centralized services.

# Security Considerations

The strategies presented in (#minimum-disclo) and (#esni-retrieval)
are designed for minimal disruption of the current infrastructure
of local resolvers. They can accomodate split DNS configurations
that are common in enterprises, and can enable filtering of malware
traffic.

Many enterprises adopt "split DNS" configurations, in which the names
of local servers are only visible from inside the enterprise network.
Attempting to resolve these names through off path resolvers would
leak these names outside the enterprise, which is a privacy violation.
The strategy described in (#esni-retrieval) could accomodate a step
in which, if the name is recognized as local, ESNI data is never
retrieved, or only retrieved through a dedicated enterprise server.

Nodes infected by malware need to contact the "command and control"
server of the attacker, and for that rely on resolving a set of
DNS names. Many local resolvers are programmed to intercept these
queries, which can disrupt the botnet or enable detection
of malware infections. The strategy described in (#minimum-disclo)
will resolve non-ESNI traffic through the local resolver, and
the filtering of malware will continue to work.

Malware authors could attempt to use ESNI, but they will still
need to expose the name of the public server. Responsible
public services will normally attempt to detect malware and
block them. Irresponsible services would probably be considered
as enablers of the malware, and be blocked as such.

# IANA Considerations

This draft does not require any IANA action.











--- back










