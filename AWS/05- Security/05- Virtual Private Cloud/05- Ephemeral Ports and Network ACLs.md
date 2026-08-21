# 05- Ephemeral Ports and Network ACLs

## Overview

Ephemeral ports are temporary TCP or UDP source ports selected by operating systems for outbound connections. They become particularly important when designing AWS Network Access Control Lists (NACLs) because NACLs are **stateless**.

A client connecting to a server typically uses a well-known or application-specific destination port while the client uses an ephemeral source port:

```text
Client
10.20.10.25:49152
        |
        | TCP
        | destination port 443
        v
Server
10.20.20.10:443
```

The response reverses the port relationship:

```text
Server
10.20.20.10:443
        |
        | TCP
        | destination port 49152
        v
Client
10.20.10.25:49152
```

A stateful Security Group can track this connection and automatically allow the related response traffic. A NACL cannot. The inbound and outbound traffic must independently satisfy the applicable NACL rules.

This makes ephemeral ports one of the most important concepts to understand when designing restrictive NACLs.

---

## What Is an Ephemeral Port?

An ephemeral port is a temporary transport-layer port selected by a client operating system or application for an outbound connection.

Servers commonly listen on stable ports:

| Service | Typical Destination Port |
|---|---:|
| HTTP | 80 |
| HTTPS | 443 |
| SSH | 22 |
| PostgreSQL | 5432 |
| MySQL | 3306 |
| DNS | 53 |

A client does not normally need a fixed source port for every connection.

For example:

```text
Client A: 10.20.10.10:49152
Client B: 10.20.10.11:49153
Client C: 10.20.10.12:49154

                 |
                 v

Server: 10.20.20.10:443
```

The operating system allocates temporary source ports so that multiple simultaneous connections can coexist.

The complete TCP flow is identified by the connection's addressing and port information:

```text
Source IP
Source Port
Destination IP
Destination Port
Protocol
```

For TCP, this combination allows the host networking stack to associate response traffic with the correct connection.

---

## Why Ephemeral Ports Matter in AWS

Ephemeral ports matter because NACLs are stateless.

Suppose an application in a private subnet connects to PostgreSQL:

```text
Application
10.20.10.25:49152
        |
        | TCP destination 5432
        v
PostgreSQL
10.20.20.15:5432
```

The request is:

```text
10.20.10.25:49152
        ->
10.20.20.15:5432
```

The response is:

```text
10.20.20.15:5432
        ->
10.20.10.25:49152
```

The database response is therefore sent to the client's ephemeral port.

If the NACL on the application subnet or database subnet does not permit the return traffic, the connection can fail even though the initial request was allowed.

---

## Stateful vs Stateless Filtering

The distinction can be summarized as:

```text
Security Group
    |
    | Tracks connection state
    v
Request allowed
    |
    v
Related response automatically permitted
```

Compared with:

```text
NACL
    |
    | Does not track connection state
    v
Request evaluated
    |
    v
Response evaluated independently
```

### Security Group Example

An API Security Group might allow:

```text
TCP 5432
Source: database-client security group
```

If the API initiates a TCP connection to PostgreSQL and the connection is permitted, the response traffic is handled according to the Security Group's stateful behavior.

### NACL Example

A NACL must independently permit traffic in each direction.

Therefore:

```text
Request:
Client ephemeral port -> Server 5432

Response:
Server 5432 -> Client ephemeral port
```

must both be considered.

---

## Ephemeral Port Lifecycle

A simplified outbound TCP connection looks like:

```mermaid
sequenceDiagram
    participant C as Client
    participant N1 as Client Subnet NACL
    participant N2 as Server Subnet NACL
    participant S as Server

    C->>N1: SYN source:49152 destination:443
    N1->>N2: Forward SYN
    N2->>S: Deliver SYN
    S->>N2: SYN-ACK source:443 destination:49152
    N2->>N1: Return packet
    N1->>C: Deliver SYN-ACK
    C->>N1: ACK source:49152 destination:443
    N1->>N2: Forward ACK
    N2->>S: Deliver ACK
```

Every packet crossing the subnet boundary is independently subject to the relevant NACL rules.

---

## Ephemeral Port Ranges

There is no single universal ephemeral-port range that should be assumed for every environment.

The range can depend on:

- Operating system
- Kernel configuration
- Network stack
- Application behavior
- Protocol
- Container environment
- NAT behavior

For Linux systems, the ephemeral port range can be inspected with:

```bash
cat /proc/sys/net/ipv4/ip_local_port_range
```

A typical result might look like:

```text
32768 60999
```

The exact range should be treated as environment-specific.

For production NACL design, do not blindly assume that a particular port range is universally correct.

---

## TCP Example

Consider a Python FastAPI service connecting to PostgreSQL.

The API server may establish:

```text
API:
10.20.10.25:42136

PostgreSQL:
10.20.20.15:5432
```

The connection is:

```text
10.20.10.25:42136
        |
        | TCP
        v
10.20.20.15:5432
```

The PostgreSQL response uses:

```text
10.20.20.15:5432
        |
        | TCP
        v
10.20.10.25:42136
```

The API does not need to listen on port `42136` as an application service. It is a temporary local transport endpoint associated with the connection.

---

## UDP Example

The same general concept exists with UDP, although UDP is connectionless.

For example, an application might send a DNS request:

```text
Client
10.20.10.25:53000
        |
        | UDP destination 53
        v
DNS
10.20.0.2:53
```

The response can be:

```text
DNS
10.20.0.2:53
        |
        | UDP destination 53000
        v
Client
10.20.10.25:53000
```

Because UDP does not establish a TCP-style connection, the traffic model is different, but NACLs still evaluate packets independently.

---

## Client-to-Server Traffic Model

A useful generic model is:

```text
Client
Source Port: Ephemeral
       |
       | Request
       | destination: Service Port
       v
Server
Listening Port
       |
       | Response
       | destination: Client Ephemeral Port
       v
Client
```

For example:

```text
API -> PostgreSQL

10.20.10.25:49152
        |
        | TCP/5432
        v
10.20.20.15:5432
```

Response:

```text
10.20.20.15:5432
        |
        | TCP/49152
        v
10.20.10.25:49152
```

This pattern applies to many backend systems:

- Django -> PostgreSQL
- FastAPI -> PostgreSQL
- Application -> Redis
- Worker -> Kafka
- API -> external HTTPS endpoint
- EC2 -> AWS service endpoint
- Kubernetes node -> external service
- Service -> internal microservice

---

## NACL Rule Design

A common mistake is to think only about the destination service port.

For example:

```text
ALLOW TCP 5432
```

may describe only one side of the traffic.

A complete traffic model should document:

```text
Source CIDR
Source Port
Destination CIDR
Destination Port
Protocol
Direction
```

For example:

```text
Source:
10.20.10.0/24

Destination:
10.20.20.0/24

Request:
TCP ephemeral -> 5432

Response:
TCP 5432 -> ephemeral
```

This is the correct level of reasoning for NACL design.

---

## Example: Application to PostgreSQL

Assume:

```text
Application subnet:
10.20.10.0/24

Database subnet:
10.20.20.0/24
```

The application connects to:

```text
10.20.20.15:5432
```

A simplified request is:

```text
10.20.10.25:49152
        ->
10.20.20.15:5432
```

The response is:

```text
10.20.20.15:5432
        ->
10.20.10.25:49152
```

The NACL design must account for both directions.

Conceptually:

```text
Application NACL
    |
    | outbound request
    v
Database NACL
    |
    | inbound request
    v
PostgreSQL
    |
    | outbound response
    v
Database NACL
    |
    | inbound response
    v
Application NACL
```

The exact rule set depends on the desired security posture and the traffic requirements.

---

## Example: HTTPS From a Private Application

Consider an API running in a private subnet:

```text
Private API
10.20.10.25
     |
     | HTTPS
     v
External Service
```

The API may use:

```text
Source:
10.20.10.25:49152

Destination:
External IP:443
```

The response is:

```text
External IP:443
        ->
10.20.10.25:49152
```

If the private subnet's NACL allows outbound HTTPS but does not permit the corresponding return traffic, the application may experience connection failures.

This is particularly important when using restrictive NACLs around private application subnets.

---

## Example: ALB to Backend

Suppose an Application Load Balancer sends traffic to a backend service on port `8000`.

```text
ALB
10.20.10.20
   |
   | TCP/8000
   v
API
10.20.20.25
```

The ALB's source port can be an ephemeral port.

The backend listens on:

```text
8000
```

The request may therefore look like:

```text
10.20.10.20:45000
        ->
10.20.20.25:8000
```

The response:

```text
10.20.20.25:8000
        ->
10.20.10.20:45000
```

A restrictive NACL must account for this traffic pattern.

---

## Example: NAT Gateway

NAT Gateway architectures make ephemeral ports particularly important.

Consider:

```text
Private Application
        |
        v
Private Subnet
        |
        v
NAT Gateway
        |
        v
Internet Gateway
        |
        v
Internet
```

An application might generate:

```text
10.20.10.25:49152
        ->
External IP:443
```

The NAT Gateway performs address and port translation.

Conceptually:

```text
Private:
10.20.10.25:49152

        NAT

Public:
NAT-IP:ephemeral-port
```

The exact translated source port should not be assumed to equal the application's original ephemeral port.

This is one reason restrictive NACLs around NAT architectures must be tested carefully.

---

## NAT Gateway and Return Traffic

The complete flow is approximately:

```mermaid
sequenceDiagram
    participant A as Private Application
    participant N as NAT Gateway
    participant I as Internet Service

    A->>N: Source ephemeral -> destination 443
    N->>I: Translated source -> destination 443
    I->>N: Response destination translated port
    N->>A: Response destination original ephemeral port
```

NACLs can apply at the subnet boundaries involved in the traffic path.

When diagnosing NAT connectivity, inspect:

- Private subnet route table
- Private subnet NACL
- NAT Gateway state
- Public subnet route table
- Public subnet NACL
- Internet Gateway path
- Security Group
- Destination service

---

## Ephemeral Ports and Load Balancers

Load balancers frequently use dynamic source ports when communicating with backend targets.

For example:

```text
ALB
10.20.10.10:45000
        |
        | TCP/8000
        v
API
10.20.20.10:8000
```

The API should not assume that the ALB always uses one fixed source port.

This is one reason NACL rules that permit only a tiny set of source ports can be fragile.

For application-level access control, Security Groups are generally better suited to workload relationships.

---

## Ephemeral Ports and Microservices

Consider:

```text
API
 |
 +----> User Service
 |
 +----> Order Service
 |
 +----> Payment Service
 |
 +----> PostgreSQL
 |
 +----> Redis
```

Each outbound connection can use an ephemeral source port.

For example:

```text
API -> User Service
49152 -> 8001

API -> Order Service
49153 -> 8002

API -> PostgreSQL
49154 -> 5432

API -> Redis
49155 -> 6379
```

A microservice architecture therefore produces many short-lived and long-lived connections.

Restrictive NACLs must account for the resulting connection patterns without accidentally allowing unnecessary network access.

---

## Connection Pools

Backend applications commonly use connection pools.

For example, a Django or FastAPI service may maintain several PostgreSQL connections:

```text
API
 |
 +-- 10.20.10.25:41001 -> DB:5432
 |
 +-- 10.20.10.25:41002 -> DB:5432
 |
 +-- 10.20.10.25:41003 -> DB:5432
 |
 +-- 10.20.10.25:41004 -> DB:5432
```

The source ports can differ for each connection.

A pool also means that a connection may remain established for a long period.

This has two important implications:

- NACLs must permit the traffic pattern required by the pool.
- Network policy changes can affect existing and newly created connections differently depending on the packet path and current connection state.

NACL changes should therefore be tested against both existing application traffic and new connection establishment.

---

## Short-Lived vs Long-Lived Connections

Applications may use:

| Connection Type | Example | Ephemeral Port Behavior |
|---|---|---|
| Short-lived HTTP | REST API request | New client-side port may be used |
| HTTP keep-alive | Reused HTTP connection | Existing connection may be reused |
| PostgreSQL pool | Django/FastAPI DB connection | Port remains associated with connection |
| Redis connection | Persistent client connection | Long-lived source port |
| gRPC | Persistent HTTP/2 connection | Connection can remain open |
| Kafka | Persistent broker connection | Long-lived source port |

Do not assume every application request creates a new TCP connection.

Connection reuse can significantly reduce connection establishment overhead.

---

## Ephemeral Ports and gRPC

gRPC typically runs over HTTP/2 and can maintain long-lived TCP connections.

For example:

```text
Service A
10.20.10.10:45000
        |
        | HTTP/2 over TCP
        v
Service B
10.20.20.10:50051
```

The client-side source port may be ephemeral:

```text
45000
```

while the gRPC server listens on:

```text
50051
```

A long-lived connection does not eliminate the need for correct NACL rules. It simply changes the connection lifecycle and traffic characteristics.

---

## Ephemeral Ports and Kubernetes

Kubernetes adds additional networking layers.

A simplified architecture might be:

```text
Client
   |
   v
Load Balancer
   |
   v
Node / Pod Networking
   |
   v
Pod
```

Pods may create outbound connections using ephemeral ports.

Examples include:

```text
Pod -> PostgreSQL:5432
Pod -> Redis:6379
Pod -> AWS API:443
Pod -> External API:443
```

When EKS uses VPC-native networking, pod traffic can interact directly with VPC networking controls depending on the specific configuration.

Do not design NACLs based solely on Kubernetes Service ports. Model the underlying VPC traffic and the actual source and destination addresses.

---

## Ephemeral Ports and Security Groups

A common misconception is:

> If ephemeral ports matter to NACLs, I should open the same ephemeral ports in every Security Group.

That is generally incorrect.

Security Groups are stateful.

For example:

```text
API SG
   |
   | TCP 5432
   v
DB SG
```

The database Security Group can permit PostgreSQL traffic from the API Security Group without requiring a separate inbound rule for every ephemeral client port.

NACLs are different because they are stateless.

The distinction is:

```text
Security Group
    |
    +-- Stateful
    +-- Workload-level
    +-- No explicit deny
    +-- Tracks connections

NACL
    |
    +-- Stateless
    +-- Subnet-level
    +-- Allow + deny
    +-- Each direction evaluated independently
```

---

## Choosing an Ephemeral Port Range for NACLs

There are two common approaches.

### Broad Ephemeral Range

Permit the expected ephemeral range.

Advantages:

- Easier to operate
- Less likely to break legitimate connections
- Better compatibility with varied clients

Limitations:

- Broader network exposure
- Less granular filtering

### Narrow Application-Specific Range

Permit only a known range.

Advantages:

- Tighter policy
- Smaller permitted port space

Limitations:

- More operational complexity
- Greater risk of incompatibility
- Requires strong control over operating systems and workloads
- Can break after platform changes

For most production environments, NACLs should not be used to create unnecessarily complicated source-port policies when Security Groups can provide the workload-level control.

---

## Why `0.0.0.0/0` Does Not Mean All Ports

This distinction is important.

```text
0.0.0.0/0
```

means:

> Any IPv4 address.

It does **not** mean:

> Every port.

A rule such as:

```text
TCP 443
Source: 0.0.0.0/0
```

allows TCP traffic to port `443` from any IPv4 source, subject to the rule's direction and other network controls.

Similarly:

```text
TCP 1024-65535
Source: 10.20.0.0/16
```

means the specified port range from that CIDR, not all IPv4 traffic.

Always evaluate:

```text
Protocol
+
Port
+
CIDR
+
Direction
```

together.

---

## Common NACL Failure Pattern

A common production failure looks like:

```text
Application
    |
    | TCP 49152 -> 443
    v
External Service
```

The engineer adds:

```text
Outbound:
ALLOW TCP 443
```

The request leaves the application subnet.

The response:

```text
External Service:443
        ->
Application:49152
```

is then rejected by the relevant NACL.

The application reports:

```text
Connection timeout
```

The engineer sees:

```text
Outbound 443 = ALLOW
```

and assumes the network is correct.

The actual issue is that the return path was not modeled.

This is one of the most common NACL troubleshooting mistakes.

---

## NACL Rule Ordering and Ephemeral Ports

Consider:

```text
100 DENY 10.20.10.0/24 TCP 1024-65535
200 ALLOW 10.20.10.0/24 TCP 443
```

These rules apply to different destination-port conditions.

But if the response traffic arrives at:

```text
TCP destination 49152
```

the ephemeral-port rule determines whether it is allowed.

The first matching rule wins.

When debugging NACLs, inspect the actual packet's:

```text
Source IP
Source Port
Destination IP
Destination Port
Protocol
Direction
```

rather than reasoning only from the application's service port.

---

## IPv4 and IPv6 Ephemeral Traffic

Dual-stack applications can generate both IPv4 and IPv6 traffic.

For IPv4:

```text
0.0.0.0/0
```

For IPv6:

```text
::/0
```

A rule for IPv4 does not automatically permit IPv6.

For example:

```text
IPv4:
TCP 1024-65535
0.0.0.0/0

IPv6:
No equivalent rule
```

can result in different behavior depending on which address family the client selects.

Production dual-stack systems should explicitly model:

- IPv4 source/destination
- IPv6 source/destination
- Service ports
- Ephemeral ports
- Return traffic

---

## VPC Flow Logs

VPC Flow Logs are particularly useful when investigating ephemeral-port failures.

The logs can help answer:

```text
Who communicated?
Where did they communicate?
Which protocol?
Which ports?
Was traffic accepted or rejected?
```

A useful investigation is:

```text
Application:
10.20.10.25

Destination:
10.20.20.15

Protocol:
TCP

Destination port:
5432

Observed source port:
49152
```

Then inspect whether the reverse flow is permitted.

The exact Flow Log format and fields depend on the configured version and fields, so use the configured flow-log schema when interpreting production records.

---

## Troubleshooting Workflow

When an application reports a timeout, do not immediately modify the NACL.

Follow the traffic path.

### Identify the Flow

```text
Source:
10.20.10.25

Source port:
49152

Destination:
10.20.20.15

Destination port:
5432

Protocol:
TCP
```

### Check Routing

Verify that the source and destination subnets have valid routes.

### Check Source NACL

Verify outbound traffic is permitted.

### Check Destination NACL

Verify inbound traffic is permitted.

### Check Return Traffic

Verify the response path is permitted:

```text
5432 -> 49152
```

### Check Security Groups

Verify:

```text
Source workload -> Destination workload
```

is permitted.

### Check the Application

Verify that the destination is actually listening:

```bash
ss -lntp
```

### Check Flow Logs

Look for rejected traffic and compare observed source/destination ports with the expected flow.

---

## Production Design Example

Consider a production backend:

```text
                         Internet
                            |
                            v
                     Application Load
                         Balancer
                            |
                  +---------+---------+
                  |                   |
                 AZ-A                AZ-B
                  |                   |
            Public Subnet        Public Subnet
                  |                   |
                  +---------+---------+
                            |
                       App Subnets
                  +---------+---------+
                  |                   |
                 API                 API
                  |                   |
                  +---------+---------+
                            |
                     Database Subnets
                  +---------+---------+
                  |                   |
              PostgreSQL           PostgreSQL
```

Traffic patterns include:

```text
Internet -> ALB:443
ALB -> API:8000
API -> PostgreSQL:5432
API -> Redis:6379
API -> External APIs:443
```

Each request can involve ephemeral source ports.

For example:

```text
ALB:45000 -> API:8000

API:45001 -> PostgreSQL:5432

API:45002 -> Redis:6379

API:45003 -> External API:443
```

Return traffic targets those ephemeral source ports.

A robust network design therefore starts with a traffic matrix.

---

## Traffic Matrix

A production traffic matrix might look like:

| Source | Destination | Protocol | Destination Port | Return Traffic |
|---|---|---|---:|---|
| Internet | ALB | TCP | 443 | Yes |
| ALB | API | TCP | 8000 | Yes |
| API | PostgreSQL | TCP | 5432 | Yes |
| API | Redis | TCP | 6379 | Yes |
| API | External API | TCP | 443 | Yes |
| Worker | Kafka | TCP | 9092/9094 as configured | Yes |
| Monitoring | API | TCP | Application port | Yes |

The exact port and encryption configuration depends on the deployed architecture.

The important part is that every flow has both:

```text
Forward direction
+
Return direction
```

when designing stateless network controls.

---

## Security Considerations

Ephemeral ports should not automatically be exposed to the entire Internet.

Avoid policies such as:

```text
ALLOW TCP 1024-65535
Source: 0.0.0.0/0
```

unless there is a very specific architectural requirement.

A broad ephemeral-port policy can unnecessarily increase the attack surface.

Prefer restricting:

- Source CIDR
- Destination CIDR
- Protocol
- Direction
- Required service ports

For workload-to-workload communication, use Security Groups to express service relationships where possible.

For example:

```text
API SG
   |
   | TCP 5432
   v
DB SG
```

is more expressive than broadly opening PostgreSQL access based on large CIDR ranges.

---

## Security vs Operability

NACL design requires balancing:

```text
Security
    |
    +---- Narrow rules
    |
    +---- Explicit denies
    |
    +---- Smaller CIDRs
    |
    v
Operational complexity
```

Extremely restrictive NACLs can become difficult to operate.

For example, a rule set that attempts to enumerate every ephemeral source port can create unnecessary complexity.

A senior design asks:

> Which security property does this NACL provide that a simpler Security Group architecture does not?

If the answer is unclear, the NACL may be providing complexity without meaningful security improvement.

---

## High Availability Considerations

Ephemeral-port behavior must be considered across all Availability Zones.

For example:

```text
                ALB
             /       \
            v         v
          AZ-A       AZ-B
           API        API
            \         /
             \       /
              PostgreSQL
```

Traffic can take different paths depending on:

- Load balancing
- DNS
- AZ availability
- Application topology
- Routing
- Failover

NACL policies should be consistent across equivalent subnet roles.

Test:

- Normal traffic
- Cross-AZ traffic where applicable
- Load balancer health checks
- Failover
- New connections after failure
- Existing connections during policy changes

---

## Performance Considerations

Ephemeral ports themselves do not generally create a significant packet-processing overhead.

The important performance implications are connection behavior and connection management.

High-throughput services can create large numbers of connections:

```text
10,000 requests
      |
      v
Many TCP connections
      |
      v
Many ephemeral ports
```

Connection pooling and keep-alive can reduce unnecessary connection establishment.

For Python applications, this is relevant to:

- Django database connections
- SQLAlchemy connection pools
- Redis clients
- HTTP clients
- gRPC channels
- Kafka clients

A well-designed application should avoid unnecessarily creating a new TCP connection for every request.

---

## Port Exhaustion

A client has a finite number of available local ephemeral ports for a given destination and protocol combination.

Very high connection rates can therefore create port pressure.

For example:

```text
Client
   |
   +-- ephemeral port 40001
   +-- ephemeral port 40002
   +-- ephemeral port 40003
   +-- ...
   +-- ephemeral port N
```

Potential symptoms include:

- Connection failures
- `EADDRNOTAVAIL`
- Increased connection latency
- Large numbers of short-lived connections
- High TIME_WAIT counts

On Linux, inspect socket state with:

```bash
ss -s
```

Inspect active TCP connections with:

```bash
ss -tan
```

Inspect the configured local ephemeral range with:

```bash
cat /proc/sys/net/ipv4/ip_local_port_range
```

Port exhaustion is primarily a host/application networking problem, but understanding it is important when designing high-throughput backend systems.

---

## TIME_WAIT and Short-Lived Connections

TCP connections that close can remain in `TIME_WAIT` for a period of time.

A service that continuously creates short-lived outbound connections can therefore consume many local ports.

For example:

```text
Request
  |
  v
Create TCP connection
  |
  v
Send request
  |
  v
Close connection
  |
  v
TIME_WAIT
```

Repeated at high rates:

```text
Connection
Connection
Connection
Connection
Connection
...
```

can produce significant socket churn.

Connection reuse through:

- HTTP keep-alive
- PostgreSQL pooling
- Redis persistent connections
- gRPC channels
- Kafka persistent connections

can substantially reduce this overhead.

---

## Observability

Monitor network behavior at multiple layers.

### Application Metrics

Track:

- Connection failures
- Connection latency
- Timeout rate
- Pool exhaustion
- Request failures

### Host Metrics

Inspect:

```bash
ss -s
```

and:

```bash
ss -tan
```

### AWS Network Observability

Use:

- VPC Flow Logs
- CloudWatch metrics where applicable
- Load balancer metrics
- NAT Gateway metrics
- Network monitoring tools

### Application Logs

Record useful network errors such as:

```text
Connection timeout
Connection refused
Temporary failure
Address unavailable
```

Do not log sensitive connection credentials or secrets.

---

## Common Mistakes

### Mistake: Treating the Service Port as the Only Port

Incorrect reasoning:

```text
API -> DB
Port = 5432
```

Correct reasoning:

```text
API:ephemeral -> DB:5432
DB:5432 -> API:ephemeral
```

### Mistake: Treating NACLs as Stateful

Allowing outbound traffic does not automatically authorize the return packet through a stateless NACL.

### Mistake: Opening All Ephemeral Ports Globally

Avoid:

```text
0.0.0.0/0
TCP
1024-65535
```

unless explicitly required.

### Mistake: Assuming Every OS Uses the Same Range

Ephemeral-port ranges vary.

### Mistake: Ignoring NAT Translation

The source port visible beyond a NAT boundary can differ from the application's original local source port.

### Mistake: Ignoring IPv6

IPv4 and IPv6 require independently considered rules.

### Mistake: Solving Every Problem With NACLs

Security Groups are usually better suited for workload-level access control.

### Mistake: Creating Excessive Short-Lived Connections

High connection churn can cause port exhaustion and unnecessary CPU/network overhead.

---

## Interview Traps

### Is an ephemeral port a server port?

Usually no. It is commonly a temporary client-side source port.

### Is port 443 an ephemeral port?

No. `443` is the conventional HTTPS service port. A client connecting to HTTPS might use an ephemeral source port.

### Are ephemeral ports always in a fixed range?

No. The range depends on the operating system and networking environment.

### Why do ephemeral ports matter to NACLs?

Because NACLs are stateless, and return traffic can target the client's ephemeral source port.

### Do Security Groups require explicit ephemeral-port return rules?

Normally no. Security Groups are stateful.

### Can an application listen on an ephemeral port?

Yes. "Ephemeral" describes how ports are commonly allocated and used; it does not mean the port can never be used as a listening port.

### Does NAT preserve the original source port?

Not necessarily. NAT can translate source addresses and ports.

### Does every HTTP request use a new ephemeral port?

No. HTTP connection reuse and persistent connections can reuse an existing TCP connection.

### Does gRPC eliminate ephemeral ports?

No. gRPC commonly uses long-lived TCP connections, but the client still has a local transport endpoint and source port.

---

## Practical Debugging Commands

Inspect listening sockets:

```bash
ss -lntp
```

Inspect all TCP sockets:

```bash
ss -tan
```

Inspect socket statistics:

```bash
ss -s
```

Inspect the Linux ephemeral range:

```bash
cat /proc/sys/net/ipv4/ip_local_port_range
```

Inspect established connections to a PostgreSQL server:

```bash
ss -tan dst 10.20.20.15:5432
```

Inspect established HTTPS connections:

```bash
ss -tan dst :443
```

The exact output depends on the operating system, kernel, process privileges, and networking environment.

---

## Production Design Guidelines

Use the following principles when working with ephemeral ports and NACLs:

- Model complete bidirectional traffic flows.
- Treat NACLs as stateless.
- Do not assume a universal ephemeral-port range.
- Keep workload-level access control in Security Groups where practical.
- Restrict NACL source and destination CIDRs appropriately.
- Avoid globally opening large ephemeral ranges.
- Consider NAT port translation when troubleshooting Internet access.
- Account for IPv4 and IPv6 independently.
- Use connection pooling and persistent connections where appropriate.
- Monitor connection churn and port exhaustion in high-throughput systems.
- Use VPC Flow Logs when packet-level network behavior is unclear.
- Test NACL changes across all Availability Zones.
- Manage NACL configuration through Infrastructure as Code.
- Document the request and response path for critical network flows.

---

## Reference Architecture

```mermaid
flowchart LR
    CLIENT["Client"] -->|"TCP ephemeral -> 443"| ALB["Application Load Balancer"]
    ALB -->|"TCP ephemeral -> 8000"| API["Django / FastAPI"]
    API -->|"TCP ephemeral -> 5432"| DB["PostgreSQL"]
    API -->|"TCP ephemeral -> 6379"| REDIS["Redis"]
    API -->|"TCP ephemeral -> 443"| EXT["External API"]

    API -. "Return traffic -> ephemeral port" .-> ALB
    DB -. "Return traffic -> ephemeral port" .-> API
    REDIS -. "Return traffic -> ephemeral port" .-> API
    EXT -. "Return traffic -> ephemeral port" .-> API
```

Each arrow represents a logical network flow. In a real VPC, the traffic can additionally pass through:

```text
Route Tables
     |
     v
NACLs
     |
     v
Security Groups
     |
     v
NAT / Transit Gateway / Firewall
     |
     v
Destination
```

The exact path depends on the architecture.

---

## Key Takeaways

- **Ephemeral ports are temporary client-side transport ports** used for outbound TCP and UDP communication, while destination services commonly listen on stable ports such as `443`, `5432`, or `6379`.
- **NACLs are stateless**, so both the request and return paths must independently satisfy the relevant NACL rules; return traffic commonly targets the client's ephemeral source port.
- **Security Groups are stateful**, making them better suited for workload-level relationships such as `API SG -> PostgreSQL SG`, while NACLs provide broader subnet-level controls.
- Do not assume a universal ephemeral-port range or blindly open large ephemeral ranges; derive the policy from the actual operating systems, workloads, routing, NAT behavior, and traffic requirements.
- High-throughput backend systems should consider **connection pooling, persistent connections, port exhaustion, TIME_WAIT, VPC Flow Logs, and complete bidirectional traffic analysis** when troubleshooting network failures.