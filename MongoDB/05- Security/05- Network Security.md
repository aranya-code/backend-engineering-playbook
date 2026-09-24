# 05- Network Security

## Overview

MongoDB network security controls which systems can reach MongoDB, how connections are protected in transit, and which network paths are permitted before authentication and authorization are evaluated.

A production MongoDB security model should use multiple independent controls:

```text
Application
    ↓
Network Segmentation
    ↓
Firewall / Security Group
    ↓
Private Network Path
    ↓
TLS
    ↓
MongoDB Authentication
    ↓
MongoDB Authorization
```

Network security is therefore not a replacement for authentication or authorization. A private MongoDB endpoint reduces exposure, while TLS protects traffic, authentication establishes identity, and authorization controls database operations.

The objective is to make MongoDB:

- unreachable from unnecessary networks
- encrypted in transit
- accessible only through approved paths
- resilient to accidental exposure
- observable during normal operation and incidents

---

## MongoDB Network Exposure

A MongoDB deployment can be exposed through several network paths:

```text
Internet
   ↓
Public MongoDB Endpoint
```

or:

```text
Application VPC
   ↓
Private Subnet
   ↓
MongoDB
```

The second model is generally preferable for production application databases because the database does not need to be directly reachable from the public internet.

A secure architecture should minimize:

```text
Attack Surface
=
Reachable Network Paths
+
Exposed Ports
+
Trusted Source Networks
```

---

## MongoDB Network Security Layers

| Layer | Purpose | Example |
|---|---|---|
| VPC / VNet | Network isolation | AWS VPC |
| Subnet | Network segmentation | Private database subnet |
| Security group | Stateful traffic filtering | Allow TCP 27017 from application SG |
| Network ACL | Subnet-level filtering | Restrict network ranges |
| Firewall | Network perimeter control | Cloud or host firewall |
| TLS | Encrypt traffic | TLS certificates |
| Authentication | Establish identity | SCRAM / X.509 |
| Authorization | Restrict operations | MongoDB roles |
| Monitoring | Detect abnormal activity | Logs and metrics |

No individual layer should be treated as sufficient on its own.

---

## Default MongoDB Port

MongoDB commonly listens on TCP port:

```text
27017
```

The port number itself is not a security boundary.

Changing:

```text
27017 → 37117
```

does not meaningfully replace:

- firewall restrictions
- authentication
- TLS
- authorization
- network segmentation

Security should be based on access controls rather than port obscurity.

---

## Bind Addresses

MongoDB's network interface configuration determines which local interfaces accept connections.

A restrictive configuration might look like:

```yaml
net:
  port: 27017
  bindIp: 127.0.0.1,10.20.1.10
```

This allows MongoDB to listen on:

```text
localhost
+
specific private interface
```

rather than every available interface.

---

## Binding to All Interfaces

A configuration such as:

```yaml
net:
  bindIp: 0.0.0.0
```

means MongoDB can listen on all IPv4 interfaces.

This does not automatically mean MongoDB is publicly accessible because external firewalls may still block traffic.

However, broad binding increases the number of interfaces on which MongoDB may accept connections and should therefore be used only when the network architecture explicitly requires it.

---

## Bind Address vs Firewall

These controls operate at different layers.

```text
bindIp
    ↓
Which local interfaces accept traffic?

Firewall
    ↓
Which remote systems can reach the port?
```

For example:

```text
MongoDB
    bindIp = 10.20.1.10

Security Group
    allow 10.20.2.0/24 → TCP 27017
```

Both controls can be useful together.

---

## Public vs Private MongoDB

| Architecture | Exposure | Typical Use |
|---|---|---|
| Public MongoDB endpoint | Internet reachable | Avoid for normal production databases |
| Private VPC endpoint | Private network | Preferred application architecture |
| VPN-accessible | Private through VPN | Administrative access |
| Bastion-mediated | Restricted administrative path | Controlled operations |
| Private managed service | Provider private networking | Production cloud architecture |

The objective is not merely to hide MongoDB. The objective is to create an explicit, controlled network path.

---

## Production Network Architecture

A common AWS-oriented architecture is:

```mermaid
flowchart TB
    U[Internet Clients] --> ALB[Load Balancer]
    ALB --> API[FastAPI / Django / Services]

    API --> SG[Private Network]
    SG --> DB[(MongoDB)]

    ADMIN[Admin / Operator] --> VPN[VPN / Private Access]
    VPN --> DB

    DB -.-> MON[Monitoring]
```

The application tier is exposed through an appropriate ingress layer, while MongoDB remains on a private network.

---

## Security Groups

In AWS, a security group can restrict MongoDB access to the application security group.

Conceptually:

```text
MongoDB Security Group

Inbound:
TCP 27017
Source:
Application Security Group
```

Prefer:

```text
Application SG → Database SG
```

over:

```text
0.0.0.0/0 → TCP 27017
```

The first model expresses workload-level trust. The second exposes MongoDB to every IPv4 source permitted by the surrounding network.

---

## AWS Security Group Example

A typical architecture is:

```text
API instances
    └── sg-api

MongoDB
    └── sg-mongodb

sg-mongodb inbound:
    TCP 27017
    Source: sg-api
```

Administrative access should use a separate controlled path rather than opening MongoDB to the internet.

For example:

```text
Administrator
    ↓
VPN / private connectivity
    ↓
MongoDB
```

---

## Network ACLs

AWS Network ACLs operate at the subnet level.

They can provide an additional network filtering layer, but they are generally broader than security groups.

A simplified model is:

```text
Security Group
    ↓
Instance / ENI-level filtering

Network ACL
    ↓
Subnet-level filtering
```

Avoid creating unnecessarily complicated ACL rules when security groups already provide the required workload-level boundary.

---

## VPC Segmentation

A production deployment should separate application and database network boundaries where practical.

Example:

```text
VPC
├── Public Subnets
│   └── Load Balancer
│
├── Private Application Subnets
│   ├── FastAPI
│   ├── Django
│   └── Celery
│
└── Private Database Subnets
    └── MongoDB
```

This reduces direct network reachability from public components.

---

## Database Subnet Design

MongoDB should generally not be placed directly into a public subnet when the workload does not require public connectivity.

A private database subnet can provide:

- reduced exposure
- controlled routing
- smaller attack surface
- easier firewall management
- clearer operational boundaries

Network placement should align with the MongoDB deployment architecture, especially for replica sets and sharded clusters.

---

## Replica Set Networking

A replica set requires MongoDB members to communicate with each other.

For example:

```text
MongoDB Node A
      ↕
MongoDB Node B
      ↕
MongoDB Node C
```

Application access is only one part of the network design.

You must also allow the required member-to-member communication.

A typical architecture is:

```text
Application
    ↓
Replica Set

Node A ←→ Node B
  ↕         ↕
Node C ←────┘
```

Firewall rules should permit only the required MongoDB member traffic.

---

## Replica Set Network Boundaries

A common production design is:

```text
Application Security Group
        ↓
TCP 27017
        ↓
MongoDB Security Group

MongoDB Security Group
        ↓
TCP 27017
        ↓
MongoDB Security Group
```

The second rule supports replica-set member communication while keeping database traffic within the trusted network boundary.

---

## Sharded Cluster Networking

A sharded deployment introduces more components:

```text
Application
    ↓
mongos
    ↓
Shards
    ↓
Replica Set Members

mongos
    ↓
Config Server Replica Set
```

Network policy must account for:

- `mongos`
- shard members
- config server members
- application clients
- administrative clients

Do not expose every MongoDB component to every network.

---

## Network Segmentation for Sharding

A conceptual security model is:

```text
Application Network
       ↓
mongos Network
       ↓
Shard Network

Administrative Network
       ↓
Cluster Management
```

The exact topology depends on the deployment platform, but the principle remains:

> Components should communicate only with the systems they actually need to reach.

---

## TLS

TLS protects MongoDB network traffic from interception and tampering.

Without TLS:

```text
Application
    ↓
Plain network traffic
    ↓
MongoDB
```

With TLS:

```text
Application
    ↓
Encrypted TLS connection
    ↓
MongoDB
```

TLS should be considered essential for production deployments, especially when traffic crosses:

- availability zones
- VPC boundaries
- VPN connections
- shared infrastructure
- managed service endpoints
- public networks

---

## TLS Encryption vs Authentication

TLS and MongoDB authentication solve different problems.

```text
TLS
    ↓
Protects the communication channel

MongoDB Authentication
    ↓
Establishes database identity
```

A secure production connection commonly uses both.

---

## TLS Modes

MongoDB deployments can be configured with TLS requirements appropriate to the environment.

A production-oriented configuration should generally require TLS rather than allowing clients to silently fall back to unencrypted connections.

Example configuration structure:

```yaml
net:
  tls:
    mode: requireTLS
    certificateKeyFile: /etc/mongodb/tls/server.pem
    CAFile: /etc/mongodb/tls/ca.pem
```

The exact certificate configuration depends on the deployment architecture and certificate authority.

---

## TLS Certificate Architecture

A typical architecture is:

```text
Certificate Authority
        ↓
MongoDB Server Certificate
        ↓
MongoDB Server

Application
        ↓
Trusted CA
        ↓
TLS Verification
```

The application should validate the MongoDB server certificate rather than merely enabling encryption.

---

## Certificate Validation

Encryption without proper certificate validation can provide weaker protection than expected.

A production client should verify:

- certificate chain
- trusted CA
- hostname / server identity where applicable
- certificate validity
- expiration

Avoid configurations that effectively disable certificate verification merely to make local connectivity work.

---

## Python TLS Example

A PyMongo connection can be configured to use TLS:

```python
from pymongo import MongoClient

client = MongoClient(
    mongodb_uri,
    tls=True,
    tlsCAFile="/etc/ssl/mongodb/ca.pem",
    serverSelectionTimeoutMS=5_000,
    connectTimeoutMS=5_000,
    socketTimeoutMS=10_000,
)
```

In production, certificate paths and credentials should normally come from deployment configuration or managed secret/certificate mechanisms rather than source control.

---

## Mutual TLS

Mutual TLS can provide certificate-based client authentication.

The flow becomes:

```text
Client Certificate
        ↓
Client proves identity
        ↓
Server Certificate
        ↓
Server proves identity
        ↓
Encrypted connection
```

MongoDB supports certificate-based authentication through appropriate X.509 configurations.

This can be useful in environments requiring strong machine identity.

---

## TLS and Connection Pools

A PyMongo `MongoClient` maintains connection pools.

Creating one client per request can unnecessarily increase:

- connection establishment overhead
- TLS handshakes
- CPU consumption
- connection counts
- latency

Prefer a long-lived client:

```python
client = MongoClient(
    mongodb_uri,
    tls=True,
)
```

and reuse it throughout the application process.

---

## Docker Network Security

A Docker Compose environment might use an isolated network:

```yaml
services:
  api:
    build: .
    networks:
      - backend

  mongodb:
    image: mongo
    networks:
      - backend

networks:
  backend:
    driver: bridge
```

The application can reach MongoDB through the Docker network without publishing MongoDB to the host.

Avoid:

```yaml
ports:
  - "27017:27017"
```

unless host-level access is explicitly required.

---

## Docker Port Publishing

These configurations are materially different:

```yaml
ports:
  - "27017:27017"
```

and:

```yaml
expose:
  - "27017"
```

Publishing a port makes the service reachable through the host's networking configuration.

Internal service communication can often use the Docker network without exposing MongoDB to the host.

For local development, publishing may be useful. For production, avoid unnecessary host exposure.

---

## Kubernetes Network Security

Kubernetes deployments can use:

- private cluster networking
- NetworkPolicies
- service-level access
- TLS
- secret management
- workload identity
- namespace boundaries

A conceptual policy is:

```text
orders-api
    ↓
MongoDB Service
```

while:

```text
unrelated-service
    X
MongoDB Service
```

NetworkPolicy can enforce this network-level boundary.

---

## Kubernetes NetworkPolicy Example

A simplified policy might look like:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: mongodb-ingress
spec:
  podSelector:
    matchLabels:
      app: mongodb
  policyTypes:
    - Ingress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: orders-api
      ports:
        - protocol: TCP
          port: 27017
```

This is only a network restriction. MongoDB authentication and authorization should still be enabled.

---

## Private DNS

Production MongoDB deployments should generally use stable internal DNS names rather than hard-coded private IP addresses.

Example:

```text
mongodb.internal.example
```

instead of:

```text
10.20.1.15
```

DNS provides an abstraction layer that makes infrastructure changes easier to manage.

This is particularly useful for:

- replica-set members
- managed MongoDB services
- Kubernetes services
- failover
- infrastructure replacement

---

## Connection Strings

A production application might use:

```text
mongodb://orders_service:${MONGODB_PASSWORD}@mongodb.internal.example:27017/orders?authSource=admin&tls=true
```

Important connection properties can include:

- host
- port
- database
- authentication source
- TLS configuration
- replica-set configuration
- read preference
- timeout settings

Avoid embedding credentials directly into source code.

---

## Connection String Security

Do not commit:

```python
MONGODB_URI = "mongodb://admin:password@..."
```

to Git.

Prefer:

```python
import os

mongodb_uri = os.environ["MONGODB_URI"]
```

and inject the value through:

- AWS Secrets Manager
- Kubernetes Secrets or an external secret manager
- CI/CD secret stores
- other controlled secret-management systems

---

## DNS and SRV Records

MongoDB connection strings may use SRV records:

```text
mongodb+srv://...
```

SRV-based connections can simplify discovery for managed MongoDB deployments.

The application environment must be able to resolve the required DNS records.

When troubleshooting connectivity, verify:

```text
DNS resolution
        ↓
Network route
        ↓
TCP connectivity
        ↓
TLS
        ↓
Authentication
        ↓
Authorization
```

---

## DNS Troubleshooting

A connectivity failure does not always indicate a MongoDB problem.

Test DNS resolution from the application environment:

```bash
nslookup mongodb.internal.example
```

or:

```bash
dig mongodb.internal.example
```

For SRV-based deployments:

```bash
dig SRV _mongodb._tcp.example.mongodb.net
```

The exact command availability depends on the operating system or container image.

---

## TCP Connectivity

After DNS succeeds, verify TCP reachability.

For example:

```bash
nc -vz mongodb.internal.example 27017
```

or:

```bash
timeout 5 bash -c '</dev/tcp/mongodb.internal.example/27017'
```

A failed TCP connection generally points to:

- security group
- firewall
- NetworkPolicy
- routing
- wrong hostname
- wrong port
- MongoDB not listening

---

## Connectivity Troubleshooting Layers

A useful troubleshooting order is:

```mermaid
flowchart TD
    A[Application Cannot Connect] --> B[DNS Resolution]
    B --> C[Route / Network Path]
    C --> D[Firewall / Security Group]
    D --> E[TCP Port]
    E --> F[TLS Handshake]
    F --> G[Authentication]
    G --> H[Authorization]
    H --> I[Application Query]
```

This prevents application engineers from immediately changing database permissions when the actual problem is network reachability.

---

## Firewall Design

A production firewall rule should ideally specify:

```text
Source
Destination
Protocol
Port
Purpose
Owner
```

Example:

| Source | Destination | Protocol | Port | Purpose |
|---|---|---|---:|---|
| API SG | MongoDB SG | TCP | 27017 | Application access |
| MongoDB SG | MongoDB SG | TCP | 27017 | Replica-set communication |
| Admin VPN | MongoDB SG | TCP | 27017 | Controlled administration |

Avoid rules such as:

```text
0.0.0.0/0 → TCP 27017
```

unless there is an exceptional, explicitly reviewed requirement.

---

## Administrative Access

Administrators should not normally expose MongoDB directly to the internet for convenience.

Prefer:

```text
Administrator
    ↓
VPN / Private Connectivity
    ↓
Bastion or controlled admin network
    ↓
MongoDB
```

This provides a separate administrative access path from application traffic.

---

## Bastion Hosts

A bastion host can provide a controlled entry point into a private network.

Example:

```text
Administrator
    ↓
SSH / VPN
    ↓
Bastion
    ↓
Private MongoDB
```

A bastion should not become a general-purpose jump box with unrestricted access.

Control:

- who can access it
- what ports it can reach
- how sessions are audited
- how credentials are managed

---

## VPN and Private Connectivity

VPN or private connectivity is useful when administrators or external systems need access to a private MongoDB deployment.

Examples include:

- site-to-site VPN
- client VPN
- cloud private connectivity
- dedicated network links

The goal is:

```text
Trusted administrative path
        ↓
Private MongoDB
```

rather than:

```text
Internet
   ↓
MongoDB
```

---

## Atlas Network Security

MongoDB Atlas deployments provide managed networking controls that can include:

- IP access lists
- private connectivity
- TLS
- authentication
- cloud-provider networking integration
- network peering or private endpoints depending on architecture

For production systems, prefer private connectivity where it materially improves isolation and the application architecture supports it.

---

## IP Allowlisting

IP allowlists can restrict which source addresses can connect.

They are useful when source addresses are stable and well controlled.

However:

```text
IP allowlist ≠ identity
```

An approved network address can still contain compromised workloads.

Therefore combine allowlisting with:

- authentication
- authorization
- TLS
- monitoring

---

## Zero-Trust Considerations

A network should not be considered trusted merely because traffic originates inside a VPC.

A stronger model is:

```text
Network Reachability
        +
Cryptographic Identity
        +
Least Privilege
        +
Continuous Monitoring
```

For MongoDB, this means:

- restrict network paths
- require TLS
- authenticate every client
- minimize privileges
- monitor access

---

## Nginx and MongoDB

Nginx is normally an HTTP reverse proxy and should not be inserted between an application and MongoDB merely because it is already used as an API gateway.

Typical architecture:

```text
Client
  ↓
Nginx / Load Balancer
  ↓
FastAPI / Django
  ↓
MongoDB
```

Do not assume:

```text
Client
  ↓
Nginx
  ↓
MongoDB
```

is an appropriate database security architecture.

Database traffic should use MongoDB-aware connectivity and security controls.

---

## Network Encryption and Internal Traffic

Internal traffic can still require encryption.

Consider:

```text
FastAPI
   ↓
AWS AZ boundary
   ↓
MongoDB
```

Even though both systems are inside the same VPC, TLS can protect traffic from:

- accidental interception
- compromised network components
- misconfigured routing
- shared infrastructure risks

Private networking and encryption solve different problems.

---

## Network Security for Replica Sets

A production replica set should consider:

- member-to-member connectivity
- application-to-member connectivity
- administrative connectivity
- DNS
- TLS
- firewall rules
- failover
- monitoring

Example:

```text
                  ┌──────────────┐
                  │ Application  │
                  └──────┬───────┘
                         │
                         ▼
                ┌─────────────────┐
                │ Private Network │
                └─────────────────┘
                  │      │      │
                  ▼      ▼      ▼
               Primary Secondary Secondary
                  │      ↕      │
                  └──────┴──────┘
```

Every member must be able to communicate according to the replica-set topology.

---

## Network Security for Sharded Clusters

A sharded production cluster introduces additional trust boundaries.

```text
Application
    ↓
mongos
    ↓
Shard Replica Sets

mongos
    ↓
Config Server Replica Set
```

The application should generally communicate with `mongos` rather than directly depending on individual shard members.

Network controls should prevent unrelated workloads from reaching:

- shard members
- config servers
- internal administrative endpoints

---

## Monitoring Network Security

Monitor:

- connection counts
- connection failures
- rejected connections
- TLS handshake failures
- authentication failures
- unusual source addresses
- unexpected network traffic
- replica-set connectivity
- replication lag
- network latency
- network throughput

Network telemetry should be correlated with MongoDB logs and application logs.

---

## Connection Monitoring

An unexpected increase in connections can indicate:

- application deployment issue
- connection-pool misconfiguration
- retry storm
- network instability
- application leak
- malicious activity

For Python applications, avoid constructing a new `MongoClient` per request.

Prefer:

```text
Application Process
       ↓
One long-lived MongoClient
       ↓
Connection Pool
       ↓
MongoDB
```

---

## Network Latency

MongoDB performance depends partly on network latency.

For a request:

```text
API
 ↓
MongoDB
 ↓
Query execution
 ↓
Response
```

Network latency adds to end-to-end request latency.

High-latency architectures can become especially problematic for:

- chatty applications
- many sequential database calls
- transactions
- aggregation workloads
- distributed deployments

Prefer colocating application and database workloads appropriately while maintaining network isolation.

---

## Cross-Region Connectivity

Cross-region MongoDB traffic introduces:

- higher latency
- higher network costs
- more complex failure modes
- replication considerations
- stronger consistency trade-offs

For example:

```text
Region A
    ├── Application
    └── MongoDB

Region B
    ├── Application
    └── MongoDB
```

Cross-region traffic should be deliberately designed rather than introduced accidentally through routing.

---

## Network Security and High Availability

Network security must not accidentally prevent failover.

For example:

```text
Application
    ↓
Primary
```

is insufficient for a replica set if the application cannot reach other members required for topology discovery and failover.

A production design should verify:

```text
DNS
+
Firewall
+
TLS
+
Replica-set topology
+
Driver configuration
```

together.

---

## Network Security and Disaster Recovery

A disaster recovery plan should include network access.

A backup may be healthy, but recovery can still fail if:

```text
Recovery environment
    ↓
Cannot reach MongoDB
```

Recovery testing should therefore validate:

- DNS
- routing
- security groups
- firewall rules
- TLS certificates
- credentials
- secret retrieval
- MongoDB connectivity

---

## Security and Cost

Network security controls can also affect cloud cost.

Potential cost areas include:

- NAT gateways
- cross-AZ traffic
- cross-region traffic
- VPN
- private connectivity
- load balancers
- managed firewall services

Do not weaken security solely to reduce network costs.

Instead, design network placement and traffic flows intentionally.

---

## Common Network Security Mistakes

### Exposing MongoDB to the Internet

**Problem:**

```text
0.0.0.0/0 → TCP 27017
```

**Why it happens:** Developers want convenient remote access.

**Risk:** Significantly increased attack surface.

**Prevention:** Use private networking, VPN, private endpoints, or controlled administrative access.

---

### Relying on a Non-Default Port

**Problem:** MongoDB is moved from `27017` to another port and considered secure.

**Why it happens:** Port changes feel like security hardening.

**Risk:** Port changes do not replace authentication or network restrictions.

**Prevention:** Use firewall controls, TLS, authentication, and authorization.

---

### Binding to All Interfaces Without Firewall Controls

**Problem:**

```yaml
bindIp: 0.0.0.0
```

with broad network access.

**Risk:** MongoDB may become reachable from unintended networks.

**Prevention:** Restrict bind addresses and network access according to the deployment architecture.

---

### Disabling TLS for Internal Traffic

**Problem:** Internal VPC traffic is assumed to be inherently trusted.

**Risk:** Network isolation does not provide the same protection as encrypted communication.

**Prevention:** Use TLS for production MongoDB connections where appropriate.

---

### Disabling Certificate Validation

**Problem:** TLS connectivity fails and certificate verification is disabled as a workaround.

**Risk:** The connection may no longer provide strong server identity verification.

**Prevention:** Correct the CA chain, hostname, certificate, or trust configuration.

---

### Opening MongoDB to an Entire VPC

**Problem:**

```text
VPC CIDR → TCP 27017
```

**Risk:** Any workload inside the VPC may become network-reachable.

**Prevention:** Prefer workload-level security-group or NetworkPolicy boundaries.

---

### Creating a New MongoClient Per Request

**Problem:** Each API request creates a new database client.

**Risk:** Excessive connections, TLS handshakes, resource usage, and latency.

**Prevention:** Use a long-lived MongoClient per application process.

---

### Ignoring Replica-Set Member Traffic

**Problem:** Firewall rules allow application access but block member-to-member communication.

**Risk:** Elections, replication, or cluster health can fail.

**Prevention:** Explicitly design and test replica-set network rules.

---

### Using Hard-Coded IP Addresses

**Problem:** Applications depend on individual database IPs.

**Risk:** Infrastructure changes and failovers can break connectivity.

**Prevention:** Use stable DNS and replica-set-aware connection configuration.

---

## Troubleshooting Runbook

### Symptom

```text
Application cannot connect to MongoDB
```

### Possible Causes

- DNS failure
- routing failure
- security-group rule
- firewall rule
- wrong port
- MongoDB not listening
- TLS failure
- expired certificate
- authentication failure
- authorization failure
- replica-set topology issue

### Isolation Strategy

Run diagnostics from the same environment as the application.

```bash
nslookup mongodb.internal.example
```

Then:

```bash
nc -vz mongodb.internal.example 27017
```

Then validate MongoDB/TLS connectivity using the appropriate client configuration.

### Diagnostic Commands

Inspect MongoDB listening sockets on the host:

```bash
ss -lntp | grep 27017
```

Inspect routes:

```bash
ip route
```

Inspect DNS:

```bash
dig mongodb.internal.example
```

Inspect TCP reachability:

```bash
nc -vz mongodb.internal.example 27017
```

### Root Cause

Determine the first failing layer:

```text
DNS
 ↓
Routing
 ↓
Firewall
 ↓
TCP
 ↓
TLS
 ↓
Authentication
 ↓
Authorization
 ↓
Application query
```

### Corrective Action

Fix only the failing layer.

For example:

```text
TCP connection refused
```

should not lead to changing MongoDB roles.

Likewise:

```text
not authorized
```

should not lead to opening firewall ports.

### Prevention

Maintain:

- documented network architecture
- automated infrastructure configuration
- connectivity tests
- TLS certificate monitoring
- security-group review
- network monitoring
- replica-set connectivity tests
- disaster-recovery network tests

---

## Production Network Security Checklist

### Network Exposure

- [ ] MongoDB is not unnecessarily exposed to the public internet.
- [ ] Database subnets are appropriately isolated.
- [ ] Only required workloads can reach MongoDB.
- [ ] Administrative access uses a controlled path.
- [ ] Security groups and firewall rules are reviewed regularly.

### Transport Security

- [ ] TLS is enabled for production connections.
- [ ] Server certificates are validated.
- [ ] CA certificates are managed securely.
- [ ] Certificate expiration is monitored.
- [ ] Plaintext fallback is not unintentionally permitted.

### Application Connectivity

- [ ] Applications use stable DNS names.
- [ ] MongoClient instances are reused.
- [ ] Connection timeouts are configured.
- [ ] Replica-set topology is correctly supported.
- [ ] Connection pools are sized appropriately.

### Replica Sets

- [ ] Replica-set members can communicate.
- [ ] Application traffic reaches the required members.
- [ ] Firewall rules support elections and replication.
- [ ] DNS and topology discovery work during failover.
- [ ] Network partitions are tested.

### Kubernetes / Docker

- [ ] MongoDB is not unnecessarily published to the host.
- [ ] Kubernetes NetworkPolicies are considered.
- [ ] Internal service networking is restricted.
- [ ] MongoDB credentials are managed through secrets.
- [ ] Containers do not receive unnecessary network access.

### Operations

- [ ] Network failures are observable.
- [ ] TLS failures are monitored.
- [ ] Connection spikes are monitored.
- [ ] Security-group changes are audited.
- [ ] Recovery environments have tested network access.

## Key Takeaways

- **MongoDB network security starts with reducing network exposure: keep production databases on private networks and allow only required workloads to reach them.**
- **Use TLS, certificate validation, MongoDB authentication, and authorization as separate security layers; private networking alone is not sufficient.**
- **Design firewall rules around workload identity and explicit traffic flows, including replica-set member communication and sharded-cluster components where applicable.**
- **Treat DNS, routing, firewalls, TCP connectivity, TLS, authentication, and authorization as separate troubleshooting layers so the correct failure domain is isolated quickly.**
- **Production network security must account for performance, high availability, failover, monitoring, cost, and disaster recovery rather than treating connectivity as a one-time configuration task.**