# 09- Hybrid Connectivity Architecture

## Overview

Hybrid connectivity connects AWS workloads with infrastructure outside AWS, most commonly an enterprise data center or corporate network. It allows applications to operate across AWS and existing infrastructure while maintaining controlled routing, security boundaries, and operational ownership.

Typical hybrid environments contain:

- AWS VPCs
- On-premises data centers
- Corporate networks
- Direct Connect
- Site-to-Site VPN
- Transit Gateway
- Enterprise routers and firewalls
- Private DNS
- Legacy applications
- Databases
- Identity and authentication systems

A basic architecture is:

```text
                     Corporate Network
                            |
                  +---------+---------+
                  |                   |
             Direct Connect       Site-to-Site VPN
                  |                   |
                  +---------+---------+
                            |
                            v
                    Transit Gateway
                     /      |      \
                    /       |       \
                   v        v        v
             Production   Data    Shared Services
                VPC        VPC          VPC
```

The key engineering principle is that hybrid connectivity is not simply a VPN configuration. It is a distributed network architecture involving routing, CIDR allocation, path selection, DNS, security controls, failure domains, observability, and application behavior.

---

## Why Hybrid Connectivity Exists

Most organizations do not migrate every workload to AWS simultaneously. Existing databases, enterprise applications, identity systems, and regulated workloads may remain outside AWS while new services are deployed in AWS.

A migration may therefore evolve through several stages.

### Initial Environment

```text
Corporate Network
       |
       +---- Applications
       +---- PostgreSQL
       +---- Identity
       +---- File Systems
       +---- Legacy Systems
```

### Hybrid Environment

```text
                         Corporate Network
                          /             \
                         /               \
                        v                 v
                 On-Premises             AWS
                 Workloads              Workloads
                    |                      |
                    +----------+-----------+
                               |
                         Hybrid Connectivity
```

### Long-Term Architecture

```text
Corporate Network
       |
       v
Enterprise Network Hub
       |
       +------------------- AWS Network -------------------+
       |                                                   |
       v                                                   v
Shared Services                                      Workload VPCs
                                                       |
                                      +----------------+----------------+
                                      |                |                |
                                   Prod VPC         Data VPC         Platform VPC
```

Hybrid connectivity is commonly required for:

- Incremental cloud migration
- Accessing on-premises databases from AWS
- Maintaining legacy systems
- Enterprise identity integration
- Private API integration
- Data synchronization
- Disaster recovery
- Cross-environment processing
- Long-term hybrid application architectures

---

## Core Hybrid Connectivity Options

AWS provides several mechanisms for connecting private networks.

| Technology | Primary Purpose | Typical Use |
|---|---|---|
| Site-to-Site VPN | Encrypted IP connectivity over the Internet | Rapid deployment, backup connectivity |
| Direct Connect | Dedicated network connectivity into AWS | Enterprise and high-volume workloads |
| Transit Gateway | Centralized network routing | Multi-VPC and hybrid architectures |
| Direct Connect Gateway | Extends Direct Connect connectivity to supported AWS network resources | Multi-VPC and multi-Region designs |
| Transit Gateway VPN Attachment | Connects VPN directly to a Transit Gateway | Centralized hybrid connectivity |
| PrivateLink | Private service-level connectivity | Exposing specific services without broad network access |
| Client VPN | Remote-user connectivity | Individual or distributed workforce access |

A common enterprise architecture combines several of these services:

```text
                    On-Premises
                         |
             +-----------+-----------+
             |                       |
             v                       v
      Direct Connect             VPN
             |                       |
             +-----------+-----------+
                         |
                         v
                 Transit Gateway
                  /      |      \
                 v       v       v
              VPC A    VPC B    VPC C
```

---

## Site-to-Site VPN

AWS Site-to-Site VPN provides encrypted IPsec connectivity between AWS and a customer network.

A simplified architecture is:

```text
On-Premises Network
        |
Customer Gateway
        |
        | IPsec
        |
    Internet
        |
        |
AWS VPN Connection
        |
        v
Transit Gateway / Virtual Private Gateway
        |
        v
       VPC
```

### When to Use VPN

VPN is appropriate when:

- Connectivity must be established quickly.
- The environment has moderate traffic requirements.
- Internet-based transport is acceptable.
- Direct Connect is not yet available.
- VPN is needed as a backup path.
- The connection is temporary.
- The organization is still migrating.

### Advantages

- Encrypted IPsec connectivity
- Faster deployment than dedicated connectivity
- No dedicated physical circuit required
- Can connect directly to Transit Gateway
- Useful as a backup path

### Limitations

- Depends on Internet connectivity
- Network latency is less predictable than dedicated connectivity
- Throughput is constrained by the VPN architecture
- Customer-side networking equipment remains a dependency
- Internet-path failures can affect connectivity

---

## Direct Connect

AWS Direct Connect provides dedicated network connectivity between an organization's network and AWS.

A conceptual architecture is:

```text
Corporate Data Center
        |
        v
Direct Connect
        |
        v
AWS Direct Connect
        |
        v
Direct Connect Gateway
        |
        v
Transit Gateway
        |
        +---- Production VPC
        +---- Data VPC
        +---- Shared Services VPC
```

Direct Connect is useful when an organization requires sustained private connectivity and more predictable network characteristics than an Internet-based VPN can provide.

### When to Use Direct Connect

Typical use cases include:

- High-volume data transfer
- Long-term hybrid deployments
- Enterprise applications
- Large database integrations
- Predictable network performance requirements
- Dedicated connectivity requirements
- Large-scale migration programs

### Advantages

- Dedicated connectivity
- More predictable network characteristics
- Suitable for sustained traffic
- Reduces dependence on Internet routing
- Integrates with enterprise routing architectures

### Limitations

- More complex provisioning
- Physical connectivity dependencies
- Longer implementation time
- Higher operational requirements
- Requires explicit redundancy planning

---

## Direct Connect and VPN Together

Direct Connect and VPN are complementary technologies.

Direct Connect provides:

```text
Dedicated private connectivity
```

VPN provides:

```text
Encrypted IPsec connectivity
```

A resilient architecture can use Direct Connect as the primary path and VPN as a secondary path.

```mermaid
flowchart LR
    ONPREM["Corporate Network"]

    DX["Direct Connect"]
    VPN["Site-to-Site VPN"]

    TGW["Transit Gateway"]

    VPCS["AWS VPCs"]

    ONPREM --> DX
    ONPREM --> VPN

    DX --> TGW
    VPN --> TGW

    TGW --> VPCS
```

The failover behavior must be explicitly designed using routing policy and verified through testing.

Having both connections does not automatically guarantee the desired failover behavior.

---

## Transit Gateway as the Hybrid Hub

Transit Gateway provides a centralized routing layer for connecting multiple VPCs and external networks.

Without a central hub, an organization might create many independent connections:

```text
On-Prem
  |
  +---- VPC A
  +---- VPC B
  +---- VPC C
  +---- VPC D
```

As the number of networks increases, routing and security management become increasingly difficult.

Transit Gateway changes the topology:

```text
                 On-Premises
                      |
             +--------+--------+
             |                 |
          Direct Connect      VPN
             |                 |
             +--------+--------+
                      |
                      v
               Transit Gateway
                /     |      \
               v      v       v
            VPC A   VPC B    VPC C
```

Transit Gateway can become the central network boundary through which hybrid routes are controlled.

---

## Hybrid Connectivity Through Transit Gateway

A production architecture can look like:

```mermaid
flowchart TB
    ONPREM["On-Premises Network"]

    DX["Direct Connect"]
    VPN["Site-to-Site VPN"]

    TGW["Transit Gateway"]

    PROD["Production VPC"]
    DATA["Data VPC"]
    SHARED["Shared Services VPC"]

    ONPREM --> DX
    ONPREM --> VPN

    DX --> TGW
    VPN --> TGW

    TGW --> PROD
    TGW --> DATA
    TGW --> SHARED
```

The Transit Gateway route tables determine which networks can communicate.

This enables centralized control over:

- On-premises-to-VPC connectivity
- VPC-to-on-premises connectivity
- VPC-to-VPC connectivity
- Environment isolation
- Route propagation
- Inspection architectures
- Shared-services access

---

## Hybrid Request Lifecycle

Consider a Django application running in AWS that needs to access an on-premises PostgreSQL database.

The request path might be:

```text
Django
  |
  | TCP/5432
  v
VPC Route Table
  |
  v
Transit Gateway
  |
  v
Direct Connect
  |
  v
Corporate Router
  |
  v
On-Premises Firewall
  |
  v
PostgreSQL
```

The response follows the reverse path:

```text
PostgreSQL
  |
  v
Corporate Router
  |
  v
Direct Connect
  |
  v
Transit Gateway
  |
  v
AWS VPC
  |
  v
Django
```

Every boundary must have an appropriate route and security policy.

---

## Routing Is the Core of Hybrid Networking

Many hybrid connectivity incidents are routing incidents.

Suppose an AWS VPC uses:

```text
10.10.0.0/16
```

and the corporate network uses:

```text
172.16.0.0/16
```

A subnet route table may contain:

```text
Destination       Target
---------------------------------
10.10.0.0/16      local
172.16.0.0/16     tgw-xxxxxxxx
```

The Transit Gateway route table must provide a path toward:

```text
172.16.0.0/16
```

through the appropriate VPN or Direct Connect attachment.

The corporate network must also know how to reach:

```text
10.10.0.0/16
```

A complete path therefore requires:

```text
AWS route
   |
   v
Transit Gateway route
   |
   v
Hybrid attachment
   |
   v
Corporate route
   |
   v
Destination
```

The return path is equally important.

---

## BGP

Border Gateway Protocol (BGP) is commonly used to exchange routes dynamically between enterprise networks and AWS connectivity services.

Instead of manually maintaining every route:

```text
Corporate Router
       |
       | BGP
       v
AWS Connectivity
```

the networks can advertise reachable prefixes.

For example, the corporate network may advertise:

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

BGP becomes particularly useful as the network grows.

---

## Why BGP Matters

Dynamic routing becomes valuable when:

- Multiple VPCs exist.
- Multiple VPN tunnels exist.
- Direct Connect is redundant.
- Multiple Regions are connected.
- Network prefixes change frequently.
- Automatic route convergence is required.
- Network topology is too large for reliable manual route management.

A static routing architecture might be manageable for:

```text
1 VPC
1 data center
1 VPN
```

but becomes increasingly difficult to operate at enterprise scale.

BGP does not eliminate the need for route governance. Incorrect route advertisements can still create outages or unintended connectivity.

---

## BGP Failover

A redundant architecture may look like:

```text
              Corporate Network
               /             \
              /               \
             v                 v
       Direct Connect        VPN
             |                 |
             +-------+---------+
                     |
                     v
              Transit Gateway
```

When the preferred path becomes unavailable, routing can converge toward the backup path according to the configured routing policy.

Important considerations include:

- Route advertisement
- Route withdrawal
- BGP session health
- Prefix filtering
- Path preference
- Convergence time
- Asymmetric routing

Failover should be tested under real failure conditions.

---

## VPN Tunnel Redundancy

AWS Site-to-Site VPN connections are designed with two tunnels for high availability.

Conceptually:

```text
                 AWS
                  |
          +-------+-------+
          |               |
       Tunnel 1        Tunnel 2
          |               |
          +-------+-------+
                  |
          Customer Gateway
                  |
             On-Premises
```

However, two AWS tunnels do not automatically provide end-to-end redundancy.

For example:

```text
Tunnel 1 ----+
             |
Tunnel 2 ----+---- Single Customer Router
```

The customer router remains a single failure domain.

For critical systems, evaluate redundancy across:

- Customer routers
- Firewalls
- ISPs
- Physical links
- Data centers
- AWS connectivity locations

---

## Direct Connect Redundancy

A single Direct Connect connection creates a physical dependency.

A more resilient design may use independent connectivity paths:

```text
             Corporate Network
              /            \
             /              \
            v                v
       DX Location A     DX Location B
             |                |
             +-------+--------+
                     |
                     v
              AWS Network
```

Redundancy should be evaluated across actual failure domains rather than simply counting interfaces.

Consider independence across:

- Physical circuits
- Network devices
- Connectivity providers
- Direct Connect locations
- Power infrastructure
- Data centers
- AWS Regions

---

## Hybrid DNS

Network connectivity alone does not guarantee application connectivity.

Applications may need to resolve private names across both environments.

For example:

```text
AWS DNS
  |
  +---- service.aws.internal
  +---- database.aws.internal

Corporate DNS
  |
  +---- identity.corp.internal
  +---- legacy.corp.internal
```

AWS Route 53 Resolver supports hybrid DNS architectures through resolver endpoints and forwarding rules.

A typical architecture is:

```mermaid
flowchart LR
    APP["AWS Application"]

    OUT["Route 53 Resolver\nOutbound Endpoint"]
    CORPDNS["Corporate DNS"]

    IN["Route 53 Resolver\nInbound Endpoint"]
    AWSDNS["AWS Private DNS"]

    APP --> OUT
    OUT --> CORPDNS

    CORPDNS --> IN
    IN --> AWSDNS
```

The exact direction depends on which environment owns the requested DNS namespace.

---

## Hybrid DNS Failure Modes

DNS failures can look like network failures.

For example:

```text
Application
    |
    | resolve database.corp.internal
    v
DNS
    |
    X
Resolution failure
```

The application may report:

```text
connection timeout
```

even when the underlying network route is healthy.

Troubleshooting should therefore separate:

1. DNS resolution
2. Route availability
3. Network connectivity
4. Security filtering
5. Application availability

---

## Security Architecture

Hybrid connectivity crosses a significant trust boundary.

AWS workloads should not automatically trust the entire corporate network.

A controlled architecture may look like:

```text
AWS VPC
   |
   v
Transit Gateway
   |
   v
Inspection / Firewall
   |
   v
Direct Connect
   |
   v
Corporate Network
```

Potential controls include:

- Security Groups
- Network ACLs
- AWS Network Firewall
- Third-party firewalls
- On-premises firewalls
- TLS
- mTLS
- Application authorization
- Network segmentation
- Route isolation

These controls operate at different layers.

Routing determines:

```text
Can traffic reach the destination?
```

Security controls determine:

```text
Is the traffic allowed?
```

Application authorization determines:

```text
Is this request allowed to perform this operation?
```

Do not treat any one of these as a replacement for the others.

---

## Centralized Inspection

Organizations with strict security requirements may route hybrid traffic through a centralized inspection layer.

```text
AWS VPC
   |
   v
Transit Gateway
   |
   v
Inspection VPC
   |
   v
Firewall
   |
   v
Direct Connect
   |
   v
Corporate Network
```

This provides centralized policy enforcement.

However, stateful inspection introduces an important requirement: traffic should normally follow paths that preserve the firewall's state expectations.

Avoid architectures such as:

```text
Request:
AWS → Firewall → On-Prem

Response:
On-Prem → Direct Connect → AWS
```

when the response bypasses the stateful inspection path.

Routing symmetry must be part of the design.

---

## CIDR Planning

Overlapping CIDRs are one of the most damaging long-term problems in hybrid networking.

For example:

```text
AWS:
10.10.0.0/16

On-Premises:
10.10.0.0/16
```

The destination `10.10.x.x` is ambiguous.

A better approach is to allocate non-overlapping address spaces:

```text
AWS:
10.0.0.0/8

Corporate:
172.16.0.0/12
```

The exact allocation depends on the organization's overall address-management strategy.

CIDR planning should happen before large-scale migration.

---

## Overlapping CIDR Impact

Overlapping networks can affect:

- VPC Peering
- Transit Gateway connectivity
- VPN routing
- Direct Connect
- Kubernetes networking
- Service discovery
- Database connectivity
- Network security policies

When overlap cannot be eliminated, network translation or application-level architectures may be required.

The preferred solution is to prevent overlap through centralized IP address management.

---

## Hybrid Connectivity and Kubernetes

Kubernetes workloads frequently require access to enterprise services.

For example:

```text
EKS
 |
 +---- PostgreSQL on-premises
 +---- Corporate APIs
 +---- Enterprise Identity
 +---- Internal Artifact Registry
```

A network path may look like:

```text
EKS Pod
  |
  v
VPC Networking
  |
  v
Transit Gateway
  |
  v
Direct Connect
  |
  v
On-Premises Service
```

Kubernetes introduces additional address spaces:

- VPC CIDR
- Subnet CIDR
- Pod CIDR
- Service CIDR
- On-premises CIDRs

These must be planned together.

Overlapping pod or service networks can make hybrid routing significantly more difficult.

---

## Backend Engineering Example

Suppose a FastAPI service runs in AWS while PostgreSQL remains in an on-premises data center.

Architecture:

```text
                     AWS
                      |
                Application VPC
                      |
                   FastAPI
                      |
                      v
               Transit Gateway
                      |
                Direct Connect
                      |
                      v
               Corporate Router
                      |
                   Firewall
                      |
                      v
                  PostgreSQL
```

Application code should not need to know that PostgreSQL is on-premises.

For example:

```python
import os

import asyncpg


async def create_pool() -> asyncpg.Pool:
    return await asyncpg.create_pool(
        host=os.environ["DATABASE_HOST"],
        port=int(os.getenv("DATABASE_PORT", "5432")),
        user=os.environ["DATABASE_USER"],
        password=os.environ["DATABASE_PASSWORD"],
        database=os.environ["DATABASE_NAME"],
        min_size=5,
        max_size=20,
        command_timeout=10,
    )
```

The network architecture provides private connectivity, while the application must still account for hybrid-network characteristics.

Important application concerns include:

- Connection timeout
- Query timeout
- Connection pool size
- Retry behavior
- Circuit breakers
- Idempotency
- Latency
- Failure handling

---

## Latency Considerations

Hybrid communication generally has higher latency than communication within the same VPC or Availability Zone.

Consider:

```text
FastAPI
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
Corporate Network
   |
   v
PostgreSQL
```

A synchronous API that performs many sequential remote calls can become latency-sensitive.

Avoid:

```text
HTTP Request
   |
   +---- Remote DB call
   +---- Remote DB call
   +---- Remote DB call
   +---- Remote DB call
   +---- Remote DB call
```

Prefer:

- Fewer network round trips
- Efficient database queries
- Connection pooling
- Batch operations
- Caching
- Asynchronous processing
- Local replicas where appropriate
- Event-driven synchronization

---

## Distributed Systems Implications

Hybrid networking becomes part of the application's failure model.

A request may depend on:

```text
Application
   |
   v
AWS Network
   |
   v
Hybrid Connectivity
   |
   v
Corporate Network
   |
   v
Remote Service
```

Failure can occur at any layer:

- Route table
- Transit Gateway
- VPN
- Direct Connect
- Router
- Firewall
- DNS
- Database
- Remote application

Applications should therefore assume network dependencies can fail.

Useful resilience mechanisms include:

- Timeouts
- Retries
- Exponential backoff
- Circuit breakers
- Idempotency
- Caching
- Queue-based processing
- Dead-letter queues
- Graceful degradation

---

## Synchronous vs Asynchronous Integration

Hybrid systems often benefit from asynchronous communication.

Instead of:

```text
AWS Service
    |
    | synchronous request
    v
On-Premises Service
```

an event-driven architecture can decouple the systems:

```text
AWS Service
    |
    v
Kafka / Queue
    |
    v
On-Premises Consumer
    |
    v
Legacy System
```

This can reduce the application's dependence on continuous network availability.

Good candidates include:

- Data synchronization
- Batch processing
- Event propagation
- Reporting
- Long-running workflows
- Legacy-system integration

However, asynchronous processing changes consistency semantics and operational complexity. It should not be introduced merely to hide an unreliable network.

---

## MTU and Fragmentation

Hybrid paths can contain different MTU characteristics.

A path may include:

```text
EC2
 |
VPC
 |
Transit Gateway
 |
VPN / Direct Connect
 |
Firewall
 |
On-Premises Router
 |
Server
```

MTU mismatches can cause:

- Slow connections
- Packet fragmentation
- Retransmissions
- TLS failures
- Large-request failures
- Intermittent application errors
- gRPC communication problems

For production systems, validate the effective path MTU instead of assuming all network segments support the same packet size.

---

## gRPC Considerations

gRPC uses HTTP/2 and commonly maintains long-lived connections.

A hybrid gRPC path may be:

```text
AWS Service
    |
    | HTTP/2
    v
Transit Gateway
    |
    v
Direct Connect
    |
    v
On-Premises gRPC Service
```

Consider:

- Network latency
- Connection persistence
- Keepalive behavior
- Idle timeouts
- Load balancing
- TLS
- MTU
- Connection failure detection
- Reconnection behavior

Long-lived connections can behave differently from short-lived REST requests when routing paths or network devices change.

---

## High Availability Architecture

A production hybrid environment should eliminate unnecessary single points of failure.

A conceptual architecture is:

```mermaid
flowchart TB
    CORP["Corporate Network"]

    R1["Router A"]
    R2["Router B"]

    DX1["Direct Connect Path A"]
    DX2["Direct Connect Path B"]

    VPN1["VPN Path A"]
    VPN2["VPN Path B"]

    TGW["Transit Gateway"]

    VPC1["Production VPC"]
    VPC2["Data VPC"]

    CORP --> R1
    CORP --> R2

    R1 --> DX1
    R2 --> DX2

    R1 --> VPN1
    R2 --> VPN2

    DX1 --> TGW
    DX2 --> TGW
    VPN1 --> TGW
    VPN2 --> TGW

    TGW --> VPC1
    TGW --> VPC2
```

The exact topology depends on business requirements and the availability characteristics of the corporate network.

---

## Failure Domains

Redundancy should be evaluated based on shared dependencies.

For example:

```text
VPN Tunnel A ----+
                 |
VPN Tunnel B ----+---- Single Router
```

The tunnels are logically redundant but the router is not.

Likewise:

```text
DX Circuit A ----+
                 |
DX Circuit B ----+---- Same Physical Facility
```

may still share a significant physical failure domain.

Effective redundancy considers:

- Network devices
- Circuits
- Providers
- Facilities
- Power
- Connectivity locations
- AWS Regions
- Firewalls

The goal is to eliminate correlated failures, not simply increase the number of connections.

---

## Monitoring and Observability

Hybrid networking should be observable at several layers.

### AWS Layer

Monitor:

- Transit Gateway
- VPN tunnel health
- Direct Connect
- VPC Flow Logs
- Route changes
- CloudWatch metrics
- CloudTrail events

### Network Layer

Monitor:

- BGP sessions
- Packet loss
- Latency
- Interface utilization
- Tunnel state
- Router health
- Firewall health

### Application Layer

Monitor:

- Connection latency
- Timeout rate
- Retry rate
- Error rate
- Database connection pool saturation
- gRPC connection failures
- API latency

A useful observability model is:

```text
Network Metrics
      |
      v
Central Observability
      |
      +---- Metrics
      +---- Logs
      +---- Alerts
      +---- Distributed Tracing
```

---

## VPC Flow Logs

VPC Flow Logs help determine whether network traffic reaches expected network interfaces and whether traffic is accepted or rejected.

They can help answer:

- Which source generated traffic?
- Which destination was targeted?
- Which port was used?
- Was traffic accepted or rejected?
- How much traffic was transferred?

For example, if a Django application cannot reach an on-premises PostgreSQL database, flow logs can help distinguish:

```text
Application generated no traffic
```

from:

```text
Application generated traffic that was rejected
```

Flow Logs should be combined with Transit Gateway, VPN, Direct Connect, firewall, and application telemetry.

---

## Security Best Practices

Use least-privilege connectivity across the hybrid boundary.

Avoid broad access such as:

```text
AWS → Entire Corporate Network
```

when the actual requirement is:

```text
AWS → 172.16.20.0/24
TCP/5432
```

Prefer narrow routing and security policies where operationally practical.

Recommended practices include:

- Use TLS for sensitive application traffic.
- Restrict Security Groups.
- Restrict firewall policies.
- Separate production and non-production routing.
- Monitor route changes.
- Centralize network logging.
- Avoid unrestricted routes across trust boundaries.
- Document network ownership.
- Review route propagation regularly.
- Treat corporate networks as separate trust domains.

---

## Cost Considerations

Hybrid connectivity introduces costs at several layers.

| Component | Potential Cost Driver |
|---|---|
| Direct Connect | Ports and connectivity |
| VPN | Connection and data processing |
| Transit Gateway | Attachments and data processing |
| Cross-AZ traffic | Regional data transfer |
| Cross-Region traffic | Inter-Region data transfer |
| Network Firewall | Endpoint and traffic processing |
| Third-party firewall | Infrastructure and processing |
| Data transfer | Traffic volume and direction |

Centralized architectures can simplify network management while increasing data-processing or cross-AZ traffic costs.

For example:

```text
VPC A
  |
  v
Transit Gateway
  |
  v
Inspection VPC
  |
  v
Transit Gateway
  |
  v
VPC B
```

may introduce additional processing and transfer costs compared with architectures that keep traffic local.

Cost analysis should use expected traffic patterns rather than only infrastructure counts.

---

## Disaster Recovery

Hybrid connectivity should have an explicit disaster-recovery strategy.

A basic design may use:

```text
Primary:
Direct Connect

Secondary:
VPN
```

A mature design additionally considers failures of:

- AWS Region
- Transit Gateway
- Direct Connect path
- Direct Connect location
- Customer router
- Firewall
- Corporate data center
- DNS infrastructure

A multi-Region architecture might look like:

```text
                 Corporate Network
                  /             \
                 /               \
                v                 v
            AWS Region A      AWS Region B
                 |                 |
                TGW               TGW
                 |                 |
                VPCs              VPCs
```

Network failover alone is insufficient.

Application deployment, DNS, data replication, database recovery, and traffic management must also support the recovery strategy.

---

## Operational Ownership

Hybrid connectivity commonly crosses multiple teams.

```text
Cloud Team
    |
    +---- VPC
    +---- Transit Gateway
    +---- AWS Firewall

Network Team
    |
    +---- Routers
    +---- Direct Connect
    +---- VPN

Security Team
    |
    +---- Firewall Policies
    +---- Security Monitoring

Application Team
    |
    +---- Django / FastAPI
    +---- Database Clients
    +---- Retry Policies
```

For every connection, document:

- Source
- Destination
- CIDR
- Port
- Protocol
- Route owner
- Firewall owner
- Application owner
- Monitoring owner
- Incident escalation path

Clear ownership becomes especially important during network outages.

---

## Infrastructure as Code

AWS-side hybrid networking should be managed through Infrastructure as Code where practical.

For example, Terraform can define a VPN connection associated with a Transit Gateway:

```hcl
resource "aws_vpn_connection" "on_prem" {
  customer_gateway_id = aws_customer_gateway.on_prem.id
  transit_gateway_id  = aws_ec2_transit_gateway.main.id
  type                = "ipsec.1"

  tags = {
    Name = "on-prem-vpn"
  }
}
```

A complete implementation may additionally manage:

- Customer Gateway
- Transit Gateway
- VPN connection
- Transit Gateway route tables
- Route propagation
- VPC route tables
- Security Groups
- Network ACLs
- Firewall rules
- DNS forwarding
- Monitoring

Customer-side routers and firewalls may require separate automation systems.

Production changes should flow through reviewed CI/CD pipelines rather than ad-hoc console changes.

---

## AWS CLI Examples

Describe Transit Gateways:

```bash
aws ec2 describe-transit-gateways
```

Describe VPN connections:

```bash
aws ec2 describe-vpn-connections
```

Describe customer gateways:

```bash
aws ec2 describe-customer-gateways
```

Describe Direct Connect connections:

```bash
aws directconnect describe-connections
```

Describe Direct Connect virtual interfaces:

```bash
aws directconnect describe-virtual-interfaces
```

Describe Transit Gateway attachments:

```bash
aws ec2 describe-transit-gateway-attachments
```

Inspect VPC route tables:

```bash
aws ec2 describe-route-tables \
  --filters "Name=vpc-id,Values=vpc-xxxxxxxx"
```

These commands are useful for investigation and operational validation. Production changes should generally be performed through controlled Infrastructure as Code workflows.

---

## Troubleshooting Workflow

When an AWS workload cannot reach an on-premises service, trace the complete path systematically.

### Verify DNS

```bash
nslookup database.corp.internal
```

or:

```bash
dig database.corp.internal
```

Confirm that the hostname resolves to the expected private address.

### Verify the VPC Route

Confirm that the source subnet has a route for the destination CIDR:

```text
On-Premises CIDR → Transit Gateway
```

### Verify the Transit Gateway Route

Confirm that the Transit Gateway route table contains the destination network and the expected attachment.

### Verify the Hybrid Attachment

Check whether the Direct Connect or VPN attachment is healthy.

### Verify BGP

Confirm that expected prefixes are being advertised and received.

### Verify Corporate Routing

Confirm that the corporate router has a route back to the AWS VPC CIDR.

### Verify Firewalls

Check AWS-side and on-premises firewall policies.

### Verify Security Groups

Confirm that the destination workload permits the expected source CIDR and port.

### Verify the Return Path

Ensure the destination can route traffic back to the AWS source.

### Verify the Application

Only after network reachability has been established should application-level debugging become the primary focus.

---

## Common Failure Pattern

A typical incident may look like:

```text
Application
    |
    v
VPC Route
    |
    v
Transit Gateway
    |
    v
Direct Connect
    |
    v
Corporate Router
    |
    X
Firewall
```

The application may report:

```text
connection timeout
```

Changing application retries will not fix a firewall rejection.

The correct troubleshooting approach is to inspect every network boundary in the packet path.

---

## Common Mistakes

### Using VPN as the Only Path for Critical Systems

A single Internet-dependent path creates a significant availability dependency.

For critical workloads, evaluate Direct Connect plus VPN redundancy.

### Assuming Direct Connect Is Automatically Highly Available

A single Direct Connect circuit can fail.

Evaluate independent circuits, locations, providers, and devices.

### Forgetting Return Routes

Hybrid connectivity requires bidirectional routing.

A route from AWS to on-premises does not guarantee that the response can return to AWS.

### Using Overlapping CIDRs

Overlapping address spaces make normal routing ambiguous.

Prevent overlap through centralized IP address management.

### Treating BGP as Automatic Correctness

BGP dynamically exchanges routes, but incorrect advertisements can still create outages.

Use route filtering and explicit routing policies.

### Ignoring DNS

Applications can fail even when network connectivity is healthy if private DNS resolution is incorrect.

### Creating Stateful Inspection Without Symmetric Routing

Stateful firewalls can reject traffic when request and response paths do not match the expected inspection path.

### Granting Broad Corporate Access

Avoid exposing an entire corporate network when only a small set of services is required.

### Ignoring MTU

Hybrid paths can have different packet-size constraints.

Validate MTU behavior for protocols and traffic patterns that matter to the application.

### Ignoring Application Latency

Private connectivity does not make an on-premises database behave like a local database.

Design applications around actual round-trip latency.

### Assuming Two VPN Tunnels Provide End-to-End Redundancy

Two tunnels can still depend on one router, firewall, ISP, or physical facility.

Evaluate the complete failure domain.

---

## Production Architecture Checklist

Before deploying a hybrid architecture, verify:

- [ ] AWS and on-premises CIDRs do not overlap.
- [ ] Routing ownership is documented.
- [ ] Transit Gateway route tables are intentionally segmented.
- [ ] VPC route tables contain required hybrid routes.
- [ ] On-premises routers contain AWS return routes.
- [ ] BGP configuration is documented.
- [ ] Route advertisements are controlled.
- [ ] Direct Connect redundancy has been evaluated.
- [ ] VPN backup connectivity has been evaluated.
- [ ] Customer-side network devices are redundant where required.
- [ ] Firewall policies are explicitly defined.
- [ ] Security Groups allow only required traffic.
- [ ] DNS forwarding is designed and tested.
- [ ] MTU has been validated.
- [ ] Cross-AZ and cross-Region costs have been evaluated.
- [ ] VPC Flow Logs are enabled where appropriate.
- [ ] VPN and Direct Connect health is monitored.
- [ ] BGP failures generate alerts.
- [ ] Application timeouts reflect hybrid latency.
- [ ] Retry and circuit-breaker behavior is defined.
- [ ] Disaster recovery procedures are documented.
- [ ] AWS-side infrastructure is managed through IaC.
- [ ] Network ownership and escalation paths are documented.
- [ ] Failover has been tested rather than assumed.

---

## Interview Traps

### Is a VPN the Same as Direct Connect?

No.

VPN provides encrypted IPsec connectivity over the Internet. Direct Connect provides dedicated network connectivity into AWS.

### Should Direct Connect and VPN Be Used Together?

For critical hybrid architectures, they commonly complement each other. Direct Connect can provide the primary path while VPN provides backup connectivity.

### Does Direct Connect Encrypt Application Traffic Automatically?

Direct Connect provides private connectivity, but it should not be treated as application-layer encryption. Sensitive application traffic should use appropriate encryption such as TLS according to the security requirements.

### Why Is Transit Gateway Useful in Hybrid Architectures?

It provides a centralized routing hub for multiple VPCs and hybrid network attachments.

### Does BGP Encrypt Traffic?

No.

BGP is a routing protocol. Encryption is provided separately through mechanisms such as IPsec VPN or application-layer encryption.

### Why Is CIDR Planning Important?

Routing requires unambiguous destination networks. Overlapping CIDRs make normal network connectivity difficult or impossible.

### Can a Private AWS VPC Communicate With an On-Premises Database?

Yes, provided the required routes, connectivity attachments, DNS, firewall rules, Security Groups, NACLs, and return paths are correctly configured.

### Does Hybrid Connectivity Guarantee Application Availability?

No.

Network connectivity is only one dependency. Routers, DNS, firewalls, databases, applications, and AWS services can fail independently.

### Why Might Small Packets Work While Large Packets Fail?

MTU or fragmentation problems may exist somewhere along the hybrid path.

---

## Key Takeaways

- Hybrid connectivity connects AWS and external private networks, but production design requires coordinated routing, DNS, security, availability, observability, and failure management.
- Site-to-Site VPN provides encrypted IPsec connectivity, while Direct Connect provides dedicated connectivity; critical architectures commonly use both with deliberate routing and failover policies.
- Transit Gateway provides a scalable central routing layer for connecting multiple VPCs to on-premises networks through VPN and Direct Connect.
- Non-overlapping CIDRs, bidirectional routes, controlled BGP advertisements, hybrid DNS, firewall policy, and appropriate traffic symmetry are foundational requirements for reliable hybrid networking.
- Hybrid network failures become distributed-system failures, so backend applications should use appropriate timeouts, retries, circuit breakers, asynchronous processing, observability, and tested disaster-recovery procedures.