# 11- AWS Direct Connect

## Overview

AWS Direct Connect provides a dedicated network connection between an AWS environment and an external network such as an enterprise data center, colocation facility, or corporate network.

Unlike Site-to-Site VPN, which transports encrypted traffic across the public Internet, Direct Connect establishes a private network path between the customer network and AWS.

A simplified architecture is:

```text
On-Premises Data Center
        |
        | Customer Router
        |
        v
Customer / Colocation Facility
        |
        | Direct Connect
        |
        v
AWS Direct Connect Location
        |
        v
AWS Region
        |
        v
Transit Gateway / Virtual Private Gateway
        |
        v
VPC
```

Direct Connect is primarily a connectivity service. It does not automatically provide application-level security, routing, DNS, or workload authorization. Those responsibilities remain with the surrounding network architecture.

For production systems, Direct Connect should be designed together with:

- BGP
- Virtual interfaces
- Direct Connect Gateway
- Transit Gateway
- VPC routing
- Security Groups
- Network ACLs
- DNS
- Site-to-Site VPN
- Monitoring
- High availability
- Disaster recovery

The central engineering distinction is:

```text
VPN:
Private traffic over an encrypted Internet path

Direct Connect:
Private network path into AWS
```

Direct Connect is particularly useful when an organization requires predictable network connectivity, sustained traffic, lower network-path variability, or integration with existing enterprise networking.

---

## Why Direct Connect Exists

Many enterprise applications have substantial traffic between AWS and on-premises infrastructure.

Examples include:

- Applications running in AWS accessing on-premises databases.
- On-premises applications consuming AWS-hosted APIs.
- Large-scale data replication.
- Hybrid Kubernetes environments.
- Enterprise identity integrations.
- Backup and disaster recovery.
- Data analytics pipelines.
- Migration of workloads from data centers to AWS.
- Hybrid microservice architectures.

For example:

```text
                    Corporate Data Center
                            |
                       Core Router
                            |
                            v
                    Direct Connect
                            |
                            v
                    AWS Direct Connect
                         Location
                            |
                            v
                    Direct Connect Gateway
                            |
                            v
                    Transit Gateway
                     /            \
                    /              \
                   v                v
            Production VPC      Data VPC
                 |                  |
                 v                  v
           Django / API        PostgreSQL
```

Without Direct Connect, the same traffic might use a VPN:

```text
Corporate Network
       |
       v
VPN Gateway
       |
    Internet
       |
       v
AWS VPN
       |
       v
AWS Network
```

The two approaches solve related but different connectivity requirements.

---

## Direct Connect vs Site-to-Site VPN

| Characteristic | Direct Connect | Site-to-Site VPN |
|---|---|---|
| Transport | Dedicated/private network path | Public Internet |
| IPsec encryption | Not inherent | Yes |
| Provisioning | More involved | Faster |
| Network predictability | Generally higher | Internet-dependent |
| Bandwidth options | Dedicated connection options | VPN tunnel limits |
| Primary use | Enterprise hybrid connectivity | Rapid hybrid connectivity and backup |
| Physical dependency | Direct Connect location/provider | Internet + customer gateway |
| Failover design | Requires deliberate redundancy | Two tunnels are provided |
| Typical operational complexity | Higher | Lower |
| Common backup pattern | VPN backup | Direct Connect primary |

Direct Connect does not automatically encrypt application traffic.

If encryption is required by the organization, additional encryption mechanisms may still be necessary.

---

## Core Direct Connect Components

A Direct Connect architecture contains several logical and physical components.

| Component | Purpose |
|---|---|
| Direct Connect Location | AWS or partner facility where the physical connection terminates |
| Connection | Physical network connection into AWS |
| Customer Router | Customer-side network device |
| Virtual Interface | Logical interface used to connect into AWS networking |
| Private VIF | Provides private connectivity to VPC resources through supported AWS architectures |
| Transit VIF | Used to connect to a Direct Connect Gateway and Transit Gateway |
| Public VIF | Provides connectivity to AWS public services using public AWS IP addresses |
| Direct Connect Gateway | Global routing component used to connect a Direct Connect connection to supported AWS resources |
| Transit Gateway | Central routing hub for multiple VPCs and network attachments |
| Virtual Private Gateway | VPC-specific AWS-side gateway |
| BGP | Dynamic routing protocol used by Direct Connect virtual interfaces |

The most important conceptual distinction is:

```text
Physical Connection
        |
        v
Virtual Interface
        |
        v
Direct Connect Gateway
        |
        v
Transit Gateway
        |
        v
VPC
```

---

## Direct Connect Location

A Direct Connect connection does not normally terminate directly inside the customer's VPC.

Instead, the physical connection is established through a Direct Connect location or an approved connectivity provider.

Conceptually:

```text
Customer Network
      |
      v
Customer Router
      |
      v
Colocation / Direct Connect Location
      |
      v
AWS Direct Connect
      |
      v
AWS Region
```

This introduces physical infrastructure considerations that do not exist in a purely cloud-based VPN architecture.

When selecting a location, evaluate:

- Geographic proximity
- Provider availability
- Facility reliability
- Cross-connect availability
- Carrier diversity
- Latency
- Operational support
- Physical redundancy
- Disaster recovery requirements

The closest Direct Connect location is not necessarily the best architectural choice.

---

## Direct Connect Connection

A Direct Connect connection represents the physical network connectivity into AWS.

The connection bandwidth and physical design depend on the selected connection type and provider architecture.

For high-throughput environments, capacity planning should consider:

```text
Current traffic
+
Peak traffic
+
Growth
+
Failover traffic
+
Replication traffic
+
Operational overhead
```

Do not size a connection solely around average utilization.

For example, if an organization normally uses:

```text
2 Gbps average
```

but needs:

```text
8 Gbps during database replication
```

then average traffic alone is insufficient for capacity planning.

---

## Virtual Interfaces

Virtual interfaces, or VIFs, provide logical connectivity over a Direct Connect connection.

The major categories are:

| VIF | Primary Purpose |
|---|---|
| Private VIF | Private connectivity to AWS resources |
| Transit VIF | Connectivity through Direct Connect Gateway to supported transit architectures |
| Public VIF | Connectivity to AWS public services |

The VIF determines how traffic enters the AWS network and which AWS resources it can reach.

---

## Private Virtual Interface

A private VIF provides private connectivity to AWS resources.

A simplified architecture is:

```text
On-Premises
    |
    v
Direct Connect
    |
    v
Private VIF
    |
    v
Virtual Private Gateway
    |
    v
VPC
```

This model is useful for relatively straightforward connectivity to a VPC.

For larger multi-VPC environments, Transit Gateway and Direct Connect Gateway provide a more scalable design.

---

## Transit Virtual Interface

A transit VIF is used with a Direct Connect Gateway to provide connectivity to transit architectures.

A common enterprise architecture is:

```text
On-Premises
    |
    v
Direct Connect
    |
    v
Transit VIF
    |
    v
Direct Connect Gateway
    |
    v
Transit Gateway
    |
    +----------+----------+
    |          |          |
    v          v          v
  VPC A      VPC B      VPC C
```

This allows Direct Connect connectivity to become part of a centralized AWS network architecture.

---

## Public Virtual Interface

A public VIF is used when connectivity to AWS public services is required through Direct Connect.

Examples can include supported AWS public endpoints and services.

The important distinction is:

```text
Private VIF:
Private AWS network resources

Public VIF:
AWS public services
```

A public VIF does not mean that arbitrary Internet access should be granted.

Network architecture and AWS service requirements should determine whether public or private connectivity is appropriate.

---

## Direct Connect Gateway

A Direct Connect Gateway, or DX Gateway, provides a logical connection point between Direct Connect and supported AWS networking resources.

A common architecture is:

```text
                On-Premises
                     |
                Direct Connect
                     |
                 Transit VIF
                     |
                     v
           Direct Connect Gateway
                     |
                     v
              Transit Gateway
               /     |      \
              v      v       v
            VPC A  VPC B   VPC C
```

This is particularly useful for enterprise environments where one Direct Connect architecture needs to reach multiple VPCs.

The Direct Connect Gateway should be viewed as a connectivity aggregation layer rather than as a general-purpose routing replacement.

---

## Transit Gateway Integration

Transit Gateway provides centralized routing for multiple VPCs and other network attachments.

A mature hybrid architecture may look like:

```mermaid
flowchart LR
    CORP["Corporate Network"]
    RTR["Enterprise Router"]

    DX1["Direct Connect 1"]
    DX2["Direct Connect 2"]

    DXGW["Direct Connect Gateway"]
    TGW["Transit Gateway"]

    VPC1["Production VPC"]
    VPC2["Shared Services VPC"]
    VPC3["Data VPC"]

    VPN["Backup VPN"]

    CORP --> RTR
    RTR --> DX1
    RTR --> DX2

    DX1 --> DXGW
    DX2 --> DXGW
    DXGW --> TGW

    RTR --> VPN
    VPN --> TGW

    TGW --> VPC1
    TGW --> VPC2
    TGW --> VPC3
```

This design provides:

- Centralized routing
- Multi-VPC connectivity
- Hybrid connectivity
- Network segmentation
- A path for VPN backup
- Centralized operational visibility

---

## BGP

Border Gateway Protocol is fundamental to most production Direct Connect architectures.

BGP allows the customer network and AWS to dynamically exchange network prefixes.

Conceptually:

```text
Customer Router
      |
      | BGP
      |
      v
Direct Connect
      |
      | Advertisements
      |
      v
AWS Network
```

The customer router may advertise:

```text
172.16.0.0/16
172.17.0.0/16
172.18.0.0/16
```

AWS may advertise:

```text
10.10.0.0/16
10.20.0.0/16
10.30.0.0/16
```

This allows routing to change dynamically without manually configuring every route on every device.

---

## Why BGP Matters

Static routing can work for small environments, but enterprise networks quickly become difficult to manage manually.

Consider:

```text
3 VPCs
2 data centers
2 Direct Connect connections
1 VPN backup
20 network prefixes
```

Manually maintaining every route becomes operationally fragile.

BGP provides:

- Dynamic route exchange
- Route convergence
- Failover support
- Prefix advertisements
- Routing-policy control

However, BGP does not remove the need for careful network design.

Incorrect route advertisements can still cause:

- Traffic black holes
- Asymmetric routing
- Unintended paths
- Excessive traffic
- Network exposure

---

## BGP Route Design

Production BGP should be intentionally designed.

Important considerations include:

- Which prefixes AWS advertises
- Which prefixes the customer advertises
- Prefix filtering
- Route summarization
- AS path policy
- Local preference
- MED
- Failover behavior
- Maximum-prefix controls
- Route propagation

For example:

```text
Customer Router
      |
      +---- Primary DX
      |
      +---- Secondary DX
      |
      +---- VPN Backup
```

The organization can use routing policy to determine the preferred path.

Do not rely on accidental route selection.

---

## Direct Connect High Availability

A single Direct Connect connection is not a complete high-availability design.

A simplified single-path architecture is:

```text
Corporate Network
       |
       v
Single Router
       |
       v
Single Direct Connect
       |
       v
AWS
```

Potential failures include:

- Router failure
- Cross-connect failure
- Provider failure
- Facility failure
- Direct Connect connection failure
- AWS-side network failure

A stronger architecture introduces independent paths:

```text
                 Corporate Network
                  /             \
                 /               \
          Router A             Router B
             |                     |
             v                     v
        Direct Connect A     Direct Connect B
             |                     |
             +----------+----------+
                        |
                        v
                  AWS Network
```

For stronger resilience, the connections should be evaluated for independence rather than merely counted.

Two connections in the same failure domain do not provide the same resilience as two genuinely independent paths.

---

## Multi-Location Architecture

Organizations with strict availability requirements may use multiple Direct Connect locations.

```text
              Corporate Network
                 /          \
                /            \
               v              v
         DX Location A    DX Location B
               |              |
               v              v
          Direct Connect  Direct Connect
               |              |
               +------+-------+
                      |
                      v
             AWS Network Layer
                      |
                      v
                Transit Gateway
```

This protects against failures affecting a single connectivity facility.

The exact redundancy model should consider:

- Physical location
- Provider
- Router
- Carrier
- Power
- Cross-connect
- AWS connectivity path

---

## Direct Connect + VPN Backup

A common enterprise design uses Direct Connect as the primary path and Site-to-Site VPN as backup.

```mermaid
flowchart LR
    CORP["Corporate Network"]

    DX["Primary Direct Connect"]
    VPN["Backup Site-to-Site VPN"]

    DXGW["Direct Connect Gateway"]
    TGW["Transit Gateway"]

    VPC["Production VPC"]

    CORP --> DX
    CORP --> VPN

    DX --> DXGW
    DXGW --> TGW

    VPN --> TGW
    TGW --> VPC
```

The VPN backup can provide connectivity if Direct Connect becomes unavailable.

However, failover depends on routing policy.

BGP configuration should be designed so that the desired path is preferred under normal conditions and the backup path becomes usable during failure.

---

## Direct Connect and Encryption

Direct Connect provides a private network connection but does not inherently provide application-level encryption equivalent to an IPsec VPN.

This distinction is important:

```text
Direct Connect
    |
    | Private connectivity
    v
AWS
```

does not automatically mean:

```text
Application traffic
    |
    | End-to-end encryption
    v
Destination
```

If the security requirement is encryption in transit, consider appropriate mechanisms such as:

- TLS
- mTLS
- Application-level encryption
- MACsec where applicable to the selected Direct Connect architecture and requirements
- VPN-based encryption where appropriate

For example:

```text
Django
  |
 TLS
  |
  v
Internal API
```

remains useful even when the underlying network uses Direct Connect.

---

## Direct Connect and Security Groups

Direct Connect does not bypass AWS Security Groups.

Suppose:

```text
Corporate Network
       |
       v
Direct Connect
       |
       v
Transit Gateway
       |
       v
Private EC2
       |
       v
PostgreSQL
```

The destination Security Group must still permit the required traffic.

For example:

```text
Protocol: TCP
Port: 5432
Source: 172.16.20.0/24
```

Avoid broad rules such as:

```text
TCP 5432
Source: 0.0.0.0/0
```

when the database only needs to be reachable from a specific corporate subnet.

---

## Routing Through Direct Connect

A successful Direct Connect configuration requires correct routing at every layer.

For example:

```text
Application
    |
    v
Subnet Route Table
    |
    v
Transit Gateway
    |
    v
Direct Connect Gateway
    |
    v
Direct Connect
    |
    v
Customer Router
    |
    v
Corporate Network
```

The response must have a valid reverse path.

```text
Corporate Network
    |
    v
Customer Router
    |
    v
Direct Connect
    |
    v
Direct Connect Gateway
    |
    v
Transit Gateway
    |
    v
VPC
```

Routing is therefore bidirectional.

A healthy BGP session does not prove that the application path is correct.

---

## CIDR Planning

Hybrid networking requires careful address-space planning.

Example:

```text
AWS:
10.0.0.0/8

Corporate:
172.16.0.0/12
```

This creates clear address-space separation.

Overlapping CIDRs create significant problems:

```text
AWS:
10.10.0.0/16

Corporate:
10.10.0.0/16
```

A destination such as:

```text
10.10.20.15
```

is ambiguous from a routing perspective.

CIDR planning should therefore happen before large-scale hybrid deployment.

This is especially important when the organization expects to add:

- New AWS accounts
- New VPCs
- Kubernetes clusters
- Acquired companies
- New data centers
- Partner networks
- Disaster-recovery regions

---

## Direct Connect and DNS

Direct Connect provides network connectivity but does not automatically solve DNS.

A hybrid environment might use:

```text
AWS Application
       |
       v
Route 53 Resolver
       |
       v
Direct Connect
       |
       v
Corporate DNS
```

For example:

```text
postgres.corp.internal
```

may resolve to:

```text
172.16.20.50
```

The application can then connect through the Direct Connect path.

DNS failures should be diagnosed separately from network failures.

A useful troubleshooting distinction is:

```text
DNS:
Can I resolve the destination?

Routing:
Can I reach the destination?

Security:
Am I allowed to reach it?

Application:
Is the destination service working?
```

---

## Backend Engineering Example

Consider a Django application running in AWS while PostgreSQL remains in an enterprise data center.

```text
                       AWS
                        |
                 Private Subnet
                        |
                     Django
                        |
                        v
                  Transit Gateway
                        |
                        v
               Direct Connect Gateway
                        |
                        v
                  Direct Connect
                        |
                        v
               Corporate Network
                        |
                        v
                    PostgreSQL
```

The application can use a normal PostgreSQL connection:

```python
import os

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ["DATABASE_NAME"],
        "USER": os.environ["DATABASE_USER"],
        "PASSWORD": os.environ["DATABASE_PASSWORD"],
        "HOST": os.environ["DATABASE_HOST"],
        "PORT": os.getenv("DATABASE_PORT", "5432"),
        "CONN_MAX_AGE": 60,
        "OPTIONS": {
            "connect_timeout": 5,
        },
    }
}
```

The application does not need Direct Connect-specific code.

The networking layer is transparent to Django.

However, application architecture must account for the fact that the database is a remote dependency.

Important considerations include:

- Connection latency
- Connection pooling
- Connection limits
- Query performance
- Failover
- Timeouts
- Retries
- Circuit breakers
- Database availability
- Network path failures

A dedicated network connection does not turn a remote database into a local database.

---

## Direct Connect and FastAPI

The same model applies to FastAPI:

```text
FastAPI
   |
   v
Private Subnet
   |
   v
Transit Gateway
   |
   v
Direct Connect
   |
   v
Corporate Service
```

For service-to-service communication:

```text
FastAPI → gRPC → Corporate Service
```

or:

```text
FastAPI → HTTPS → Corporate REST API
```

can use the Direct Connect path without application-specific Direct Connect logic.

The application should still use:

- TLS
- Authentication
- Authorization
- Connection timeouts
- Retry policies
- Circuit breaking
- Health checks

---

## Latency and Performance

Direct Connect can provide a more predictable network path than Internet-based connectivity, but it does not eliminate latency.

Total application latency can be modeled approximately as:

```text
Application Processing
        +
Network Latency
        +
Remote Service Processing
        +
Response Network Latency
```

For a remote PostgreSQL query:

```text
AWS Application
      |
      | Request
      v
Direct Connect
      |
      v
Corporate Network
      |
      v
PostgreSQL
      |
      | Response
      v
AWS Application
```

Poor application design can amplify network latency.

For example:

```text
100 database queries
×
5 ms network round trip
=
~500 ms network component
```

This is simplified and excludes database processing and connection behavior, but illustrates why excessive chatty communication is problematic.

Prefer:

- Batch operations
- Efficient queries
- Connection reuse
- Appropriate caching
- Reduced round trips
- Service-local data where appropriate

---

## Direct Connect and Microservices

Hybrid microservices require careful service-boundary design.

A problematic architecture might look like:

```text
AWS Service A
    |
    v
On-Prem Service B
    |
    v
AWS Service C
    |
    v
On-Prem Service D
```

Every request crosses the hybrid boundary multiple times.

A more efficient architecture often keeps high-volume synchronous dependencies within the same network domain where practical:

```text
AWS
 |
 +---- Service A
 |
 +---- Service B
 |
 +---- Service C
 |
 +---- Cache
 |
 +---- Database
```

while using Direct Connect for carefully selected enterprise integrations.

The goal is not to eliminate hybrid connectivity, but to avoid making every request dependent on a cross-network hop.

---

## Direct Connect and Kubernetes

Kubernetes workloads can consume Direct Connect connectivity through the underlying VPC network.

For example:

```text
EKS
 |
 | Pod
 v
VPC
 |
 v
Transit Gateway
 |
 v
Direct Connect
 |
 v
Corporate Service
```

Applications inside Kubernetes still require appropriate:

- Route tables
- Security Groups
- Network policies
- DNS
- Firewall rules
- Service discovery
- Observability

Do not assume that Kubernetes network connectivity automatically means that every pod can reach every corporate service.

Least-privilege network policy remains important.

---

## MTU and Packet Size

Direct Connect can support large packet sizes depending on the connection and architecture, but the effective MTU depends on the complete path.

A packet may traverse:

```text
Application
   |
   v
VPC
   |
   v
Transit Gateway
   |
   v
Direct Connect
   |
   v
Customer Router
   |
   v
Corporate Network
```

Every layer and encapsulation mechanism can influence the effective packet size.

Symptoms of MTU problems can include:

- Large requests failing
- Large responses timing out
- TLS problems
- gRPC instability
- TCP retransmissions
- Inconsistent application behavior

Test the actual application path rather than relying only on basic ping tests.

---

## Monitoring and Observability

Direct Connect should be monitored as a production dependency.

Important metrics include:

| Category | Examples |
|---|---|
| Connection | Connection state |
| VIF | Operational state |
| BGP | Session state |
| Traffic | Bytes in/out |
| Capacity | Utilization |
| Errors | Packet errors |
| Routing | Advertised/received routes |
| Latency | Application RTT |
| Availability | Path availability |
| Application | Timeout/error rate |

Monitoring should exist at multiple layers:

```text
Application
    ↓
VPC
    ↓
Transit Gateway
    ↓
Direct Connect Gateway
    ↓
Direct Connect
    ↓
Customer Router
    ↓
Corporate Network
```

A healthy Direct Connect connection does not prove that the application is healthy.

---

## CloudWatch Monitoring

CloudWatch should be used to monitor relevant Direct Connect and surrounding network metrics.

Typical operational alerts include:

- Direct Connect connection unavailable
- VIF down
- BGP session down
- Unexpected traffic drop
- Sustained high utilization
- Route changes
- Abnormal error rates

Alerts should be based on service impact rather than every transient event.

For example:

```text
BGP session down
        |
        v
Is backup path available?
        |
    +---+---+
    |       |
   Yes      No
    |       |
    v       v
Monitor   Page
```

---

## VPC Flow Logs

VPC Flow Logs help investigate traffic entering and leaving network interfaces and can provide useful evidence during hybrid connectivity troubleshooting.

For example:

```text
Application
    |
    v
EC2 ENI
    |
    v
VPC Flow Logs
```

A flow can help determine whether traffic was accepted or rejected at the VPC networking layer.

Flow Logs should be combined with:

- Route analysis
- Security Group inspection
- NACL inspection
- Transit Gateway route inspection
- Direct Connect metrics
- Customer router logs
- Firewall logs

No single log source provides complete visibility across a hybrid network.

---

## Troubleshooting Workflow

A structured troubleshooting process prevents random configuration changes.

### Verify Application DNS

```bash
dig postgres.corp.internal
```

Confirm that the hostname resolves to the expected private address.

### Test Basic TCP Connectivity

From an appropriate host:

```bash
nc -vz 172.16.20.50 5432
```

This verifies TCP connectivity rather than database authentication.

### Verify VPC Routes

Confirm the subnet route table contains the destination prefix.

Example:

```text
172.16.0.0/16 → Transit Gateway
```

### Verify Transit Gateway Routing

Check that the Transit Gateway knows how to reach the destination network.

### Verify Direct Connect Routing

Confirm that the required prefixes are being advertised through the expected VIF.

### Verify BGP

Check:

```text
BGP state
Advertised routes
Received routes
Routing policy
```

### Verify Customer Router

Confirm that the customer router has:

- The expected BGP session
- Correct route advertisements
- Correct routing policy
- Correct return routes

### Verify Firewall

Inspect the corporate firewall and any AWS inspection layer.

### Verify Security Groups

Confirm that the AWS destination allows the expected source CIDR and port.

### Verify NACLs

Check both directions because NACLs are stateless.

### Verify Return Traffic

Confirm the response path exists.

### Verify Application

Only after the network path is established should application-level debugging become the primary focus.

---

## Useful AWS CLI Commands

List Direct Connect connections:

```bash
aws directconnect describe-connections
```

List virtual interfaces:

```bash
aws directconnect describe-virtual-interfaces
```

Inspect a specific virtual interface:

```bash
aws directconnect describe-virtual-interfaces \
  --virtual-interface-id dxvif-xxxxxxxx
```

List Direct Connect gateways:

```bash
aws directconnect describe-direct-connect-gateways
```

List Direct Connect gateway associations:

```bash
aws directconnect describe-direct-connect-gateway-associations
```

List Transit Gateways:

```bash
aws ec2 describe-transit-gateways
```

Inspect VPC route tables:

```bash
aws ec2 describe-route-tables \
  --filters "Name=vpc-id,Values=vpc-xxxxxxxx"
```

Inspect Transit Gateway route tables:

```bash
aws ec2 describe-transit-gateway-route-tables
```

Search for active Transit Gateway routes:

```bash
aws ec2 search-transit-gateway-routes \
  --transit-gateway-route-table-id tgw-rtb-xxxxxxxx \
  --filters "Name=state,Values=active"
```

CLI output is useful for investigation, but production infrastructure should generally be managed through Infrastructure as Code.

---

## Infrastructure as Code

Direct Connect infrastructure should be reproducible and version-controlled where the selected resources and provider architecture support Infrastructure as Code management.

A simplified Terraform example might look like:

```hcl
resource "aws_dx_connection" "primary" {
  name      = "primary-direct-connect"
  bandwidth = "1Gbps"
  location  = var.direct_connect_location

  tags = {
    Environment = "production"
  }
}

resource "aws_dx_gateway" "main" {
  name = "production-dx-gateway"
}
```

The exact Terraform resources required depend on whether the architecture uses:

- Dedicated Direct Connect
- Hosted connections
- Private VIFs
- Transit VIFs
- Direct Connect Gateway
- Transit Gateway
- Partner-provided connectivity

A production module should also account for:

- BGP configuration
- ASN management
- Route policy
- VPC routing
- Transit Gateway routing
- Monitoring
- Alerts
- Tags
- Environment ownership

Infrastructure changes should be reviewed through CI/CD.

---

## Security Considerations

Direct Connect changes the network path, not the application security model.

Recommended practices include:

- Use least-privilege Security Groups.
- Restrict corporate firewall rules.
- Use TLS or mTLS where required.
- Control BGP route advertisements.
- Filter unexpected prefixes.
- Segment production and non-production networks.
- Monitor route changes.
- Monitor unexpected traffic.
- Protect router credentials.
- Apply change control to network configuration.
- Keep network devices maintained and patched.
- Avoid exposing unnecessary services through the hybrid network.

A useful layered model is:

```text
Routing
    ↓
Can packets reach the destination?

Network Controls
    ↓
Is the traffic allowed?

Transport Encryption
    ↓
Is the communication protected?

Authentication
    ↓
Who is the caller?

Authorization
    ↓
What may the caller do?
```

Direct Connect addresses the connectivity layer, not all of these layers.

---

## Cost Considerations

Direct Connect introduces costs beyond ordinary VPC networking.

Potential cost categories include:

- Direct Connect connection charges
- Hosted connection charges
- Cross-connect charges
- Colocation charges
- Connectivity-provider charges
- Data transfer
- Transit Gateway data processing
- Additional redundant connections

The total cost must therefore include both AWS and external network-provider costs.

For enterprise environments, compare:

```text
Direct Connect
+
Provider
+
Colocation
+
Redundancy
```

against:

```text
VPN
+
Internet connectivity
+
Operational requirements
```

Cost should be evaluated alongside:

- Availability
- Throughput
- Latency
- Operational risk
- Compliance
- Business impact

---

## Capacity Planning

Capacity planning should account for both normal and failure conditions.

Suppose two Direct Connect connections exist:

```text
DX-A = 5 Gbps
DX-B = 5 Gbps
```

A naive calculation may assume:

```text
Total = 10 Gbps
```

But if DX-A fails, the surviving connection may need to handle the production workload.

Therefore, design for:

```text
Normal capacity
+
Growth
+
Peak traffic
+
Failure traffic
```

A useful principle is:

> Redundancy should not depend on the failed component being unnecessary during peak traffic.

For critical systems, test whether the remaining path can actually carry the workload.

---

## Direct Connect and Data Replication

Direct Connect is useful for sustained data movement.

Examples include:

```text
On-Prem PostgreSQL
        |
        | Replication
        v
AWS Database
```

or:

```text
On-Prem Data Lake
        |
        | High-volume transfer
        v
AWS Analytics
```

However, application architecture should still consider:

- Throughput
- Latency
- Compression
- Encryption
- Backpressure
- Retry behavior
- Failure recovery
- Data consistency
- Recovery point objectives

Network capacity alone does not guarantee successful replication.

---

## Direct Connect and Kafka

Hybrid Kafka deployments require particularly careful network design.

For example:

```text
AWS Consumer
     |
     v
Direct Connect
     |
     v
Corporate Kafka
```

Kafka clients may establish connections to multiple brokers.

Therefore, it is not enough to make only the Kafka bootstrap address reachable.

The AWS environment must be able to reach the broker addresses advertised by Kafka.

This is a common hybrid networking failure mode.

The same principle applies to systems that dynamically advertise node addresses.

---

## Direct Connect and Redis

A remote Redis deployment can also use Direct Connect:

```text
AWS Application
      |
      v
Direct Connect
      |
      v
Corporate Redis
```

However, Redis is latency-sensitive.

A remote Redis dependency can introduce significant application performance impact if every request crosses the hybrid network boundary.

Prefer local caching where appropriate:

```text
Application
    |
    +---- Local / AWS Redis
    |
    +---- Remote enterprise service
```

Use cross-network caching intentionally rather than assuming that a dedicated connection eliminates latency concerns.

---

## Reliability and Failure Modes

Direct Connect introduces infrastructure outside the immediate AWS workload.

Potential failure domains include:

```text
Application
    |
AWS VPC
    |
Transit Gateway
    |
Direct Connect Gateway
    |
Direct Connect
    |
Cross-Connect
    |
Provider
    |
Customer Router
    |
Firewall
    |
Corporate Network
```

Every layer can fail independently.

A mature architecture documents:

- Failure detection
- Failover path
- Route convergence
- Application behavior
- Alerting
- Recovery procedures
- Ownership

---

## Disaster Recovery

Direct Connect can be part of a hybrid disaster-recovery architecture.

For example:

```text
                 Corporate Network
                    /          \
                   /            \
                  v              v
          Direct Connect       VPN
                  |              |
                  +------+-------+
                         |
                         v
                  Transit Gateway
                    /          \
                   v            v
              Primary VPC    DR VPC
```

For cross-region architectures:

```text
On-Premises
     |
Direct Connect
     |
Transit Gateway
     |
+----+-------------+
|                  |
v                  v
Region A          Region B
VPC               VPC
```

The DR plan should specify:

- Which connectivity path is primary
- Which path is backup
- How routes change
- How DNS changes
- How applications reconnect
- How databases fail over
- How monitoring detects failure
- How the environment is restored

Disaster recovery is a tested operational capability, not simply a redundant network diagram.

---

## Common Mistakes

### Treating Direct Connect as a VPN Replacement

Direct Connect and VPN provide different network characteristics.

Direct Connect provides private connectivity but does not inherently provide IPsec encryption.

### Assuming One Direct Connect Connection Is Highly Available

A single physical connection has multiple potential failure points.

Use independent connectivity paths when availability requirements justify them.

### Creating Two Connections in the Same Failure Domain

Two connections that depend on the same router, facility, or provider may still fail together.

### Ignoring BGP

BGP is central to scalable Direct Connect routing.

Poor BGP design can create outages even when the physical connection is healthy.

### Forgetting the Return Path

A route from AWS to on-premises is only half of the communication path.

### Ignoring CIDR Overlap

Overlapping address spaces complicate or prevent routing between networks.

### Assuming Direct Connect Encrypts Everything

Private connectivity is not equivalent to end-to-end encryption.

Use TLS or other required encryption mechanisms.

### Allowing Excessive Network Access

A private network should not automatically be treated as a trusted network.

Apply least privilege at the Security Group, firewall, application, and identity layers.

### Ignoring DNS

A healthy Direct Connect path does not guarantee that private hostnames resolve correctly.

### Designing for Average Bandwidth

Failover and peak traffic must be included in capacity planning.

### Making Every Microservice Call Cross the Hybrid Boundary

Repeated cross-network calls increase latency and operational coupling.

Keep high-volume synchronous dependencies close to the application when practical.

### Assuming Direct Connect Eliminates Latency

Direct Connect provides a private path, not zero-latency communication.

---

## Production Design Checklist

- [ ] Business requirement for Direct Connect is clearly defined.
- [ ] AWS and corporate CIDRs do not overlap.
- [ ] Direct Connect location has been selected based on latency and resilience.
- [ ] Connectivity provider requirements are documented.
- [ ] Customer router architecture is redundant where required.
- [ ] Direct Connect connections are appropriately sized.
- [ ] Independent connectivity paths are used for critical workloads.
- [ ] Virtual interfaces are correctly configured.
- [ ] BGP is configured and monitored.
- [ ] Prefix advertisements are explicitly controlled.
- [ ] Direct Connect Gateway requirements are documented.
- [ ] Transit Gateway routing is correctly configured.
- [ ] VPC route tables contain required prefixes.
- [ ] Corporate return routes exist.
- [ ] Security Groups allow only required traffic.
- [ ] Network ACLs are correctly configured.
- [ ] Corporate firewall rules are explicitly defined.
- [ ] DNS resolution works across the hybrid boundary.
- [ ] TLS or other required encryption is implemented.
- [ ] Direct Connect metrics are monitored.
- [ ] BGP state is monitored.
- [ ] Traffic utilization is monitored.
- [ ] Capacity is sufficient during failover.
- [ ] VPN backup is evaluated for critical environments.
- [ ] Failover has been tested.
- [ ] Application reconnect behavior has been tested.
- [ ] Disaster recovery procedures are documented.
- [ ] Network ownership and escalation paths are defined.
- [ ] Infrastructure is managed through Infrastructure as Code where practical.
- [ ] Network changes are reviewed through controlled deployment processes.

---

## Interview Traps

### What Is AWS Direct Connect?

AWS Direct Connect provides dedicated or logically provisioned private network connectivity between an external network and AWS through a Direct Connect location or supported connectivity provider.

### How Is Direct Connect Different From Site-to-Site VPN?

VPN provides encrypted IPsec connectivity over the Internet. Direct Connect provides a private connectivity path and generally offers more predictable network characteristics.

### Does Direct Connect Encrypt Traffic?

Direct Connect itself should not be treated as an application-level encryption mechanism. If encryption in transit is required, use appropriate encryption mechanisms such as TLS, mTLS, or supported link-level encryption options.

### What Is a Virtual Interface?

A Virtual Interface is a logical interface over a Direct Connect connection that determines how the connection accesses AWS networking resources or public AWS services.

### What Are Private, Transit, and Public VIFs?

Private VIFs provide private AWS connectivity, transit VIFs are used with Direct Connect Gateway and supported transit architectures, and public VIFs provide access to supported AWS public services.

### What Is a Direct Connect Gateway?

A Direct Connect Gateway is a logical AWS networking component that allows Direct Connect connectivity to be associated with supported AWS network resources across regions and accounts depending on the architecture.

### Why Is BGP Used?

BGP dynamically exchanges routes between the customer network and AWS, enabling scalable routing and controlled failover.

### Does Direct Connect Automatically Route Traffic to a VPC?

No. The required VIF, Direct Connect Gateway or Virtual Private Gateway, Transit Gateway where applicable, route tables, and customer-side routes must all be correctly configured.

### Is One Direct Connect Connection Highly Available?

No. A single connection remains vulnerable to failures in the customer router, cross-connect, provider, facility, or connection itself.

### Why Use VPN Together With Direct Connect?

VPN can provide backup connectivity when Direct Connect is unavailable and can also provide an alternative path during maintenance or network failures.

### Does Direct Connect Replace Security Groups?

No. Direct Connect provides network connectivity. Security Groups and other controls continue to determine whether traffic is allowed to reach workloads.

### Why Can Direct Connect Be Healthy While an Application Is Down?

The Direct Connect connection can be healthy while routing, BGP advertisements, Security Groups, firewalls, DNS, MTU, return routes, or the destination application is broken.

### Why Is Direct Connect Useful for Large Data Transfers?

It provides a private network path with dedicated or provisioned connectivity options that can be better suited to sustained enterprise traffic than Internet-based VPN connectivity.

### Does Direct Connect Eliminate Network Latency?

No. It can provide a more predictable path, but physical distance, routing, network devices, processing, and application architecture still contribute latency.

### Why Is CIDR Planning Important?

AWS and corporate networks need address spaces that can be routed unambiguously. Overlapping CIDRs make hybrid routing difficult or impossible in many architectures.

## Key Takeaways

- AWS Direct Connect provides private network connectivity between enterprise networks and AWS, while Site-to-Site VPN provides encrypted connectivity over the Internet.
- Production Direct Connect architectures depend heavily on BGP, virtual interfaces, routing policy, CIDR planning, and correct return paths.
- Direct Connect Gateway and Transit Gateway enable scalable multi-VPC and hybrid network architectures.
- High availability requires independent connectivity paths and should account for routers, providers, facilities, cross-connects, and sufficient failover capacity.
- Direct Connect solves network connectivity, not application security or resilience; production systems still require encryption where appropriate, least-privilege controls, observability, timeouts, tested failover, and resilient application design.