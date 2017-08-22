# High Security Setup

The following describes a high-security, best-practice system setup of Crossbar.io Fabric and application components.

**Contents:**

1. [Operating Systems](#operating-systems)
1. [Going to Production](#going-to-production)
1. [Host Firewall](#host-firewall)
1. [Running Dockerized](#running-dockerized)
1. [Public facing transports](#public-facing-transports)
1. [Backend Application Components](#backend-application-components)
   - [Dockerizing Components](#dockerizing-components)
   - [Network Isolation](#network-isolation)
   - [Disk Isolation](#disk-isolation)
   - [Router Connections and Authentication](#router-connections-and-authentication)
1. [What you don't need](#what-you-dont-need)
   - [Static Web Content](#static-web-content)
   - [Router Components](#router-components)
   - [Container Components](#container-components)
   - [Guest Workers](#guest-workers)

---


## Operatings Systems

Write me.

---


## Going to Production

We have a series of hints and tips [going to production](http://crossbar.io/docs/Going-to-Production/) with Crossbar.io that also touch on security aspects.

---


## Host Firewall

**In short: use Linux iptables and deny any traffic but in- and outgoing traffic on TCP/443.**

It is highly recommended to run a kernel based, stateful, layer 4 firewall on the host running Crossbar.io Fabric.

On Linux systems running Ubuntu Server eg, this often means Linux **iptables** to access and configure the Linux kernel firewall.

The recommended configuration is as follows:

1. allow incoming traffic on port TCP/443 (secure Web and WebSocket) _incoming_ on the network interface _facing the clients_ that should connect to this Crossbar.io Fabric node
2. allow outgoing traffic to port TCP/443 (secure Web and WebSocket) _outgoing_ on the network interface _facing the public Internet_ with the CFC uplink connection for node management, or router-to-router links to other CF nodes
3. allow outgoing traffic to port UDP/53 (DNS) _outgoing_ on the network interface _facing the public internet_

**Everything else should be forbidden and filtered by the firewall.**

Possible exceptions:

* If the clients connecting might try port 80 first, this port could be opened as well, as long as the node is configured to redirect that to port 443 (see other chapter here).
* If the host is to be managed, you might open port 22 for SSH, possibly further restricted to originating interface or network (only internal).
* You might also consider enabling at least ICMP ping requests and responses, so that the host can be pinged for administration purposes.

---


## Host Network Segregation

Write me.


## Running Dockerized

**In short: use our official Docker images for Crossbar.io Fabric.**

Using Docker is our recommended way of [Getting Started with Crossbar.io](http://crossbar.io/docs/Getting-Started/).

Crossbar.io Fabric is currently available as a Docker image, and it will be available as a Ubuntu Core snap.

**You should only run Crossbar.io Fabric from our official Docker images** which are available on DockerHub here:

* [Crossbar.io Fabric (x86-64)](https://hub.docker.com/r/crossbario/crossbar-fabric/)
* [Crossbar.io Fabric (armhf)](https://hub.docker.com/r/crossbario/crossbar-fabric-armhf/)
* [Crossbar.io Fabric (aarch64)](https://hub.docker.com/r/crossbario/crossbar-fabric-aarch64/)

For production, usually only the following network ports are enabled for the Docker container running Crossbar.io Fabric:

* incoming TCP/80 (insecure WebSocket)
* incoming TCP/443 (secure WebSocket)
* outgoing TCP/443 (secure WebSocket)
* outgoing UDP/53 (DNS)

The Crossbar.io Fabric node directory inside the Docker container should be mounted from a host directory that is properly protected using filesystem permissions.

---


## Public facing transports

**In short: use TLS-only with WebSocket**

For WAMP listening transports on Crossbar.io Fabric router workers that accept connections from clients over the public Internet, we recommend this transport:

* WebSocket (with all serializers active)
* WebSocket compression enabled
* WebSocket [production settings recommendations](http://crossbar.io/docs/WebSocket-Options/#production-settings)

```javascript
{
    "type": "websocket",
    "url": "wss://wamp.example.com",
    "serializers": [
        "cbor", "msgpack", "ubjson", "json"
    ],
    "options": {
        "enable_webstatus": true,
        "max_frame_size": 1048576,
        "max_message_size": 1048576,
        "auto_fragment_size": 65536,
        "fail_by_drop": true,
        "open_handshake_timeout": 2500,
        "close_handshake_timeout": 1000,
        "auto_ping_interval": 10000,
        "auto_ping_timeout": 5000,
        "auto_ping_size": 4,
        "compression": {
            "deflate": {
                "request_no_context_takeover": false,
                "request_max_window_bits": 13,
                "no_context_takeover": false,
                "max_window_bits": 13,
                "memory_level": 5
            }
        }
    }
}
```

Further, we recommend to redirect port 80 to 443

```javascript
{
    "type": "web",
    "endpoint": {
        "type": "tcp",
        "port": 80
    },
    "paths": {
        "/": {
            "type": "redirect",
            "url": "https://wamp.example.com"
        }
    }
}
```


and run exclusively over TLS and [secure WebSocket](http://crossbar.io/docs/Secure-WebSocket-and-HTTPS/).

```javascript
"endpoint": {
    "type": "tcp",
    "port": 443,
    "tls": {
        "key": "server.key",
        "certificate": "server.crt",
        "chain_certificates": [
            "lets-encrypt-x3-cross-signed.pem"
        ],
        "dhparam": "dhparam.pem",
        "ciphers": "ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-SHA384:ECDHE-RSA-AES128-SHA256:DHE-RSA-AES256-SHA256:DHE-RSA-AES128-SHA256"
    }
},
"options": {
    "hsts": true,
    "hsts_max_age": 31536000
},
```

A couple of noteworthy thing about this TLS configuration:

* it runs TLS on standard port TCP/443
* it uses [HSTS](https://en.wikipedia.org/wiki/HTTP_Strict_Transport_Security) with a long lifetime
* it use a host generated Diffie-Hellman parameter file
* it uses a hand selected list of active ciphers in a specific order
* it uses a Let's Encrypt server certificate

All of this combined leads to a A+ ranking on [SSL Labs Test](https://www.ssllabs.com/ssltest/).

It's recommended to test your final setup using above SSL Labs Test. Don't forget to retest after configuration change touching the transports configuration in Crossbar.io Fabric.

---


## Backend Application Components

**In short: use Docker based app components connected over Unix domain sockets**

Backend application components are WAMP components (often Autobahn based) that are run in the backend parts of an application, often on cloud systems, that is system which are reachable in the public Internet.

To integrate backend application components into the overall system, two things are needed:

- they need to run somewhere/somehow and also be started by someone
- they need to connect (and possibly authenticate) to Crossbar.io Fabric nodes

---


### Dockerizing Components

**In short: package and run your app components as Docker images and containers**

The recommended setup runs backend application components in Docker containers.

Each backend application component is run in a separate Docker container, and the container image is derived of one of the official Autobahn Docker images.

The actual application code and any additional dependencies can be included in the user Docker image deriving of one of the official Autobahn images.

Using Docker in this way comes with a couple of benefits:

- exactly reproducible deployment of your components
- run-time isolation in both security and resource consumption
- allows simple and complete network isolation (see below)


### Network Isolation

**In short: no need to allow any networking (ingoing and outgoing) for app containers**

When backend application components provide business logic only, and do not need to talk to the outside world other than via WAMP and Crossbar.io, then there is no need for the backend component to be given _any_ network access.

Such backend components do not need to listen for incoming network connections, nor do they need to establish outgoing network connections (other than WAMP, and for that, see below).

To achieve this kind of full network isolation is easy using Docker, since when starting the backend application component in a Docker container without providing a network for the container to connect to, no networking (other than loopback) will be possible for the backend application component.


### Disk Isolation

**In short: no need to mount any disk/filesystem to an app container.**

Backend components - in general - should not store data persistently on disk. There should be database backed services elsewhere in overall system. (there are exceptions of course)

Since we are running backend application components in Docker containers, filesystem and disk isolation is already there. In particular, applicaton component hosting Docker containers do not need any specific block devices or filesystems mounted.

The one exception being private key files, eg for TLS client certificate based authentication or for WAMP-cryptosign based authentication, both methods being public-private key based.

But _backend_ application components don't even need that - they can be authenticated implicitly when using Unix domain sockets for transport (see below).


### Router Connections and Authentication

**In short: use Unix domain sockets (per component) with WAMP/RawSocket-CBOR**

So how does the backend application component connect to Crossbar.io, given that we have denied it _any_ kind of network access - even to another container (such as Crossbar.io) running on the same host!

**Unix domain sockets (UDS)** are like network sockets, but do not exist in an IP namespace, but reside in the filesystem namespace.

And because of that, permissions to Unix domain sockets can be controlled and enforced using filesystem permissions.

Further, because we start the backend application component in a Docker container, we need to explicitly mount the Unix domain socket path into the Docker container when starting.

To take this approach further, **recommended is running one separate Unix domain socket for each backend application component** co-residing on the host that runs the Crossbar.io Fabric node the component is supposed to connect to.

When doing so, an additional benefit becomes obvious: because now Crossbar.io Fabric essentially runs a separate transport for each backend application component, it automatically knows that it must be that component that is connecting. In other words, **backend application components are implicitly authenticated**.

For the WAMP transport type used with backend application components, recommended is:

* RawSocket using CBOR
* no TLS

In this case, TLS is not required, as the traffic between the backend application component and Crossbar.io runs over a UDS, which means through kernel, and protected from other user processes anyways.


### Static Web Content

**In short: use a CDN.**

Crossbar.io Fabric, when used as a simple Web server for static content is [pretty fast](https://github.com/crossbario/crossbar-examples/tree/master/benchmark/web). Nginx is faster of course. Then who needs to push millions of Web requests per second?

However, the point is not being able to saturate a 10GbE link using a couple of cores on a single box in a data-center anyways.

The point with bringing static Web content to the masses with low latency (!) is that you probably want a CDN.

CDNs deliver static content like nothing else. And this part of your traffic is now completely managed by the CDN (= their problem!), including fighting off DDoS attacks on a large scale.

---


### Router Components

**In short: use Dockerzized application components.**

---


### Container Components

**In short: use Dockerzized application components.**

---