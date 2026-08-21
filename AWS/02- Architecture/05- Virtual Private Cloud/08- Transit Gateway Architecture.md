# 08- Transit Gateway Architecture

## Overview

AWS Transit Gateway (TGW) is a regional network transit hub that provides centralized connectivity between multiple VPCs, VPN connections, and other supported network attachments.

It addresses a fundamental limitation of large-scale VPC Peering architectures: point-to-point connectivity becomes increasingly difficult to manage as the number of VPCs and AWS accounts grows.

Instead of building a mesh:

```text
VPC A ───── VPC B
 │ \         / │
 │  \       /  │
 │   \     /   │
 │    \   /    │
 │     \ /     │
 VPC C ───── VPC D
```

Transit Gateway provides a hub-and-spoke model:

```text
                 VPC A
                   |
                   |
VPC B -------- Transit Gateway -------- VPC C
                   |
                   |
                 VPC D
```

The Transit Gateway becomes the central routing point.

This makes it possible to manage connectivity, segmentation, routing, and network boundaries centrally rather than maintaining large numbers of independent peering relationships.

For backend systems, Transit Gateway is particularly relevant when microservices, shared platforms, databases, security infrastructure, and workloads are distributed across multiple VPCs and AWS accounts.

---

## Why Transit Gateway Exists

VPCs are isolated by default. As organizations grow, they commonly create separate VPCs for:

- Production
- Staging
- Development
- Shared services
- Security tooling
- Data platforms
- Analytics
- Internal platforms
- Different business units
- Different AWS accounts
- Different Regions

A small environment might look like:

```text
Application VPC
       |
       | VPC Peering
       v
Shared Services VPC
```

This is manageable.

A larger environment can quickly become:

```text
10 VPCs
45 possible full-mesh peering connections
```

With 20 VPCs:

```text
190 possible full-mesh relationships
```

Transit Gateway changes the topology:

```text
VPC 1 ─┐
VPC 2 ─┤
VPC 3 ─┤
VPC 4 ─┤
VPC 5 ─┤
       ├── Transit Gateway
VPC 6 ─┤
VPC 7 ─┤
VPC 8 ─┤
VPC 9 ─┤
VPC 10 ─┘
```

The network becomes centralized without requiring every VPC to know about every other VPC's connectivity relationship.

---

## Core Concepts

A Transit Gateway architecture consists of several important components.

| Component | Purpose |
|---|---|
| Transit Gateway | Central routing hub |
| Attachment | Connects a network resource to the TGW |
| TGW Route Table | Controls how attached networks communicate |
| VPC Attachment | Connects a VPC to the TGW |
| VPN Attachment | Connects a Site-to-Site VPN |
| Direct Connect Gateway | Extends connectivity through Direct Connect |
| Peering Attachment | Connects Transit Gateways |
| Association | Determines which TGW route table an attachment uses |
| Propagation | Allows routes from an attachment to appear in a TGW route table |

Understanding **attachments, associations, and route propagation** is essential for designing and troubleshooting Transit Gateway.

---

## Transit Gateway Architecture

A simplified architecture is:

```mermaid
flowchart TB
    VPC1["Production VPC"]
    VPC2["Shared Services VPC"]
    VPC3["Data Platform VPC"]
    VPC4["Development VPC"]

    TGW["AWS Transit Gateway"]

    VPC1 --> TGW
    VPC2 --> TGW
    VPC3 --> TGW
    VPC4 --> TGW
```

The Transit Gateway receives traffic from an attached network and consults its route tables to determine the destination attachment.

The VPC route table must also contain a route directing the destination CIDR toward the Transit Gateway attachment.

Therefore, routing involves two layers:

```text
VPC Route Table
       |
       v
Transit Gateway
       |
       v
TGW Route Table
       |
       v
Destination Attachment
       |
       v
Destination VPC
```

---

## VPC Attachments

A VPC connects to Transit Gateway through a **VPC attachment**.

Conceptually:

```text
VPC
 |
 | VPC Attachment
 |
 v
Transit Gateway
```

The attachment is created at the VPC level, but subnet selection matters.

When creating a VPC attachment, subnets are selected in Availability Zones.

A production architecture normally selects one subnet in each relevant Availability Zone.

For example:

```text
VPC
├── AZ-a
│   └── TGW Attachment Subnet
│
├── AZ-b
│   └── TGW Attachment Subnet
│
└── AZ-c
    └── TGW Attachment Subnet
```

The selected subnets provide the network interfaces through which traffic reaches the Transit Gateway.

---

## Transit Gateway Route Tables

A Transit Gateway can have multiple route tables.

This is one of its most important architectural features.

A route table determines which attachments can communicate with which destinations.

For example:

```text
Production TGW Route Table

10.20.0.0/16 → Shared Services Attachment
10.30.0.0/16 → Data Platform Attachment
```

A separate development route table might contain:

```text
Development TGW Route Table

10.20.0.0/16 → Shared Services Attachment
```

This allows network segmentation without requiring separate Transit Gateways.

---

## Route Table Association

Each Transit Gateway attachment can be associated with a TGW route table.

Conceptually:

```text
Production VPC Attachment
          |
          v
Production TGW Route Table
```

and:

```text
Development VPC Attachment
          |
          v
Development TGW Route Table
```

The association determines which TGW route table is used for routing traffic arriving from that attachment.

This is different from route propagation.

---

## Route Propagation

Propagation controls which routes from an attachment are automatically inserted into a TGW route table.

For example:

```text
Production VPC
10.10.0.0/16
       |
       | Propagation
       v
Production TGW Route Table

10.10.0.0/16 → Production Attachment
```

Without propagation, routes can also be configured explicitly.

The distinction is important:

| Concept | Meaning |
|---|---|
| Association | Which TGW route table an attachment uses |
| Propagation | Which routes an attachment contributes to a TGW route table |
| Static route | Explicit route configured in a TGW route table |

A common troubleshooting error is confusing association with propagation.

---

## End-to-End Routing

Suppose:

```text
Application VPC
10.10.0.0/16

Database VPC
10.20.0.0/16
```

The application is:

```text
10.10.10.50
```

The database is:

```text
10.20.10.50
```

The application VPC route table needs:

```text
10.20.0.0/16 → Transit Gateway
```

The TGW route table needs:

```text
10.20.0.0/16 → Database VPC Attachment
```

The database VPC needs a return route:

```text
10.10.0.0/16 → Transit Gateway
```

The complete flow is:

```mermaid
sequenceDiagram
    participant App as Application VPC
    participant TGW as Transit Gateway
    participant DB as Database VPC

    App->>TGW: 10.20.10.50:5432
    TGW->>DB: Route to Database Attachment
    DB-->>TGW: Response
    TGW-->>App: Return traffic
```

The critical point is that Transit Gateway does not eliminate normal routing requirements.

It centralizes the transit decision; it does not remove the need for correct routes.

---

## VPC Route Tables

The VPC route table must direct remote traffic toward the Transit Gateway.

Example:

```text
Destination       Target
---------------------------------
10.20.0.0/16      tgw-xxxxxxxx
```

A production VPC may have:

```text
Destination       Target
---------------------------------
10.10.0.0/16      local
10.20.0.0/16      tgw-xxxxxxxx
10.30.0.0/16      tgw-xxxxxxxx
0.0.0.0/0         nat-xxxxxxxx
```

This means:

- Local traffic stays inside the VPC.
- Traffic destined for the database VPC goes to TGW.
- Traffic destined for the data platform goes to TGW.
- General Internet-bound traffic uses NAT.

---

## Transit Gateway Routing Model

A useful mental model is:

```text
Source Workload
      |
      v
VPC Route Table
      |
      v
Transit Gateway
      |
      v
TGW Route Table
      |
      v
Destination Attachment
      |
      v
Destination VPC Route Table
      |
      v
Destination Workload
```

A packet must successfully pass through each routing decision.

If any layer has no matching route, traffic fails.

---

## Network Segmentation

Transit Gateway becomes particularly powerful when used for network segmentation.

Consider:

```text
Production
Development
Shared Services
Security
```

A centralized architecture might use:

```text
                    Transit Gateway
                         |
        +----------------+----------------+
        |                |                |
        v                v                v
    Production       Development     Shared Services
    TGW Route        TGW Route       TGW Route
      Table             Table           Table
```

Production may communicate with:

```text
Shared Services
Data Platform
Security Inspection
```

Development might communicate only with:

```text
Shared Services
```

This prevents accidental broad connectivity.

---

## Production and Development Isolation

Suppose:

```text
Production VPC
10.10.0.0/16

Development VPC
10.20.0.0/16

Shared Services VPC
10.30.0.0/16
```

Desired policy:

```text
Production → Shared Services     ALLOW
Production → Development         DENY

Development → Shared Services    ALLOW
Development → Production         DENY
```

This can be implemented through separate TGW route tables and controlled route propagation.

The routing architecture becomes part of the security architecture.

---

## Shared Services Architecture

A common enterprise pattern is a centralized Shared Services VPC.

It may host:

- Internal DNS
- Monitoring
- Logging
- CI/CD services
- Artifact repositories
- Internal APIs
- Directory services
- Bastion or administrative services

Architecture:

```mermaid
flowchart TB
    PROD["Production VPC"]
    DEV["Development VPC"]
    DATA["Data VPC"]
    SHARED["Shared Services VPC"]

    TGW["Transit Gateway"]

    PROD --> TGW
    DEV --> TGW
    DATA --> TGW
    SHARED --> TGW
```

Instead of creating direct peering relationships between every workload VPC and Shared Services, Transit Gateway centralizes the routing.

---

## Centralized Inspection

Transit Gateway can also participate in architectures where traffic is routed through centralized security appliances.

For example:

```text
Application VPC
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
Destination
```

This pattern can provide centralized network inspection.

A common design uses:

- Transit Gateway
- Inspection VPC
- AWS Network Firewall or supported third-party appliances
- Separate TGW route tables

The exact routing design must be carefully validated because asymmetric routing can break stateful inspection.

---

## Centralized Egress

Transit Gateway can be used to centralize outbound network traffic.

For example:

```text
Application VPC
       |
       v
Transit Gateway
       |
       v
Egress VPC
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

This allows multiple VPCs to share a centralized egress architecture.

However, centralized egress introduces additional:

- Network dependencies
- Cross-AZ traffic
- Latency
- Cost
- Failure domains
- Operational complexity

The architecture should therefore be evaluated against the organization's security and cost requirements.

---

## Transit Gateway vs VPC Peering

| Characteristic | VPC Peering | Transit Gateway |
|---|---|---|
| Topology | Point-to-point | Hub-and-spoke |
| Transitive routing | No | Yes |
| Centralized routing | No | Yes |
| Multiple route tables | No central TGW model | Yes |
| Network segmentation | Limited | Strong |
| Large VPC environments | Poor fit | Strong fit |
| Operational model | Distributed | Centralized |
| Small environments | Simple | Potentially unnecessary |
| Shared networking platform | Limited | Excellent |
| Network inspection architecture | More complex | Better suited |

A practical rule:

> Peering is a connectivity primitive; Transit Gateway can become a network platform.

---

## Transit Gateway vs PrivateLink

Transit Gateway and AWS PrivateLink solve different problems.

Transit Gateway provides network-level connectivity:

```text
VPC A
  |
  v
TGW
  |
  v
VPC B
```

PrivateLink provides service-level access:

```text
Consumer VPC
      |
      v
Interface Endpoint
      |
      v
PrivateLink
      |
      v
Specific Service
```

Use Transit Gateway when networks need to communicate.

Use PrivateLink when a provider wants to expose a specific service without exposing the broader provider network.

---

## Transit Gateway vs NAT Gateway

These services are frequently confused.

| Service | Primary Purpose |
|---|---|
| Transit Gateway | Connect private networks |
| NAT Gateway | Allow private resources to initiate outbound IPv4 Internet connections |

Transit Gateway:

```text
VPC A → TGW → VPC B
```

NAT Gateway:

```text
Private Subnet → NAT Gateway → Internet Gateway → Internet
```

They can be used together.

---

## Transit Gateway vs Internet Gateway

An Internet Gateway provides VPC-level Internet connectivity.

Transit Gateway provides private network transit.

```text
Private VPC → TGW → Private VPC
```

versus:

```text
Public Subnet → Internet Gateway → Internet
```

Do not use Transit Gateway when the actual requirement is Internet access.

---

## Cross-Account Architecture

Transit Gateway is particularly useful in AWS Organizations with multiple accounts.

For example:

```text
AWS Organization
│
├── Production Account
│   └── Production VPC
│
├── Development Account
│   └── Development VPC
│
├── Data Account
│   └── Data VPC
│
└── Network Account
    └── Transit Gateway
```

A centralized networking account can own the Transit Gateway while workload accounts attach their VPCs to it.

This separates network governance from application ownership.

---

## Transit Gateway Resource Sharing

AWS Resource Access Manager (RAM) can be used to share a Transit Gateway with other AWS accounts.

This enables a centralized network account to provide TGW connectivity to workload accounts.

A common organizational model is:

```text
Network Account
      |
      v
Transit Gateway
      |
      +----------+
      |          |
      v          v
Prod Account   Data Account
```

This is useful for centralized governance, but account-level ownership and permissions must be carefully designed.

---

## Multi-Region Transit Gateway Architecture

Transit Gateway is regional.

A large multi-region architecture may use multiple Transit Gateways.

For example:

```text
Region A
   |
TGW-A
   |
   | TGW Peering
   |
TGW-B
   |
Region B
```

The individual regional Transit Gateways connect to their local VPCs.

Transit Gateway peering can provide connectivity between Transit Gateways.

```mermaid
flowchart LR
    VPC1["VPCs - Region A"]
    TGWA["Transit Gateway A"]
    TGWB["Transit Gateway B"]
    VPC2["VPCs - Region B"]

    VPC1 --> TGWA
    TGWA --> TGWB
    TGWB --> VPC2
```

Cross-region architecture requires additional consideration of:

- Latency
- Data transfer cost
- Regional isolation
- DNS
- Failure behavior
- Data residency
- Application consistency

---

## CIDR Planning

Transit Gateway does not eliminate the importance of IP address planning.

VPCs should use non-overlapping CIDRs.

Example:

```text
Production VPC       10.10.0.0/16
Development VPC      10.20.0.0/16
Data VPC             10.30.0.0/16
Shared Services      10.40.0.0/16
Security VPC         10.50.0.0/16
```

This provides clear routing boundaries.

Poor CIDR planning becomes particularly expensive after an organization has many connected VPCs.

Renumbering production networks later can require major migration work.

---

## Availability Zone Design

A production VPC attachment should generally use subnets in multiple Availability Zones.

Example:

```text
                 Transit Gateway
                       |
        +--------------+--------------+
        |              |              |
        v              v              v
       AZ-a           AZ-b           AZ-c
        |              |              |
       TGW            TGW            TGW
    subnet          subnet          subnet
```

This avoids unnecessarily making one Availability Zone the sole path to the Transit Gateway.

The application subnets themselves should also be distributed across multiple Availability Zones.

---

## Backend Architecture Example

Consider an enterprise backend platform:

```text
                         Transit Gateway
                               |
          +--------------------+--------------------+
          |                    |                    |
          v                    v                    v
   Application VPC         Data VPC          Shared Services
          |                    |                    |
     Django/FastAPI        PostgreSQL             Redis
     Celery Workers        Analytics              Kafka
```

A request might follow:

```text
Client
  |
  v
Application Load Balancer
  |
  v
Django / FastAPI
  |
  | Private network
  v
Transit Gateway
  |
  v
Data VPC
  |
  v
PostgreSQL
```

Similarly:

```text
Django
  |
  v
TGW
  |
  v
Shared Services
  |
  v
Kafka
```

The application remains private while still communicating with shared infrastructure.

---

## Microservices Architecture

A large organization may place different service domains in separate VPCs:

```text
Orders VPC
Payments VPC
Identity VPC
Data VPC
Observability VPC
```

Transit Gateway can provide controlled connectivity:

```mermaid
flowchart TB
    TGW["Transit Gateway"]

    ORDERS["Orders VPC"]
    PAYMENTS["Payments VPC"]
    IDENTITY["Identity VPC"]
    DATA["Data VPC"]
    OBS["Observability VPC"]

    ORDERS --> TGW
    PAYMENTS --> TGW
    IDENTITY --> TGW
    DATA --> TGW
    OBS --> TGW
```

However, network connectivity should not automatically mean unrestricted service connectivity.

Service-level authorization should still be enforced through:

- Security Groups
- Application authentication
- mTLS where appropriate
- IAM-based mechanisms
- Network segmentation
- Service discovery policies

---

## Security Considerations

Transit Gateway centralizes connectivity, so mistakes in its route tables can have broad impact.

A permissive TGW route table can accidentally create connectivity between environments that should be isolated.

For example, avoid an architecture where:

```text
Production
Development
Security
Data
```

all share unrestricted routes.

Instead, define explicit communication paths.

Example:

```text
Production
   |
   +----> Shared Services
   |
   +----> Data

Development
   |
   +----> Shared Services
```

No production-to-development route should exist unless explicitly required.

---

## Security Groups Still Apply

Transit Gateway does not replace Security Groups.

If:

```text
Application VPC
10.10.0.0/16
```

needs to access:

```text
PostgreSQL VPC
10.20.0.0/16
```

the PostgreSQL Security Group might allow:

```text
Protocol: TCP
Port: 5432
Source: 10.10.10.0/24
```

Routing determines whether packets can reach the destination.

Security controls determine whether the workload accepts them.

Both are required.

---

## Network ACLs

NACLs remain relevant because they operate at the subnet level and are stateless.

If NACLs are restrictive, both inbound and outbound traffic must be permitted appropriately.

A typical debugging sequence is:

```text
VPC Route
    ↓
TGW Route
    ↓
Destination Route
    ↓
Security Group
    ↓
NACL
    ↓
Host Firewall
    ↓
Application
```

Do not assume that a successful TGW route means the application connection will succeed.

---

## Route Table Isolation

A strong production design often uses multiple TGW route tables.

For example:

| TGW Route Table | Attachments | Intended Connectivity |
|---|---|---|
| Production | Prod, Shared, Data | Prod → Shared/Data |
| Development | Dev, Shared | Dev → Shared |
| Security | Inspection, Security | Controlled inspection paths |
| Egress | Egress VPC | Internet egress |

The exact design depends on the organization's security model.

The key principle is:

> Route tables should represent intentional trust and connectivity boundaries.

---

## Monitoring

Transit Gateway environments should be observable.

Useful mechanisms include:

- VPC Flow Logs
- Transit Gateway Flow Logs
- CloudWatch metrics
- CloudTrail
- AWS Config
- Network monitoring
- Centralized logging

Monitoring should answer:

- Which VPC generated traffic?
- Which attachment received it?
- Which destination was selected?
- Was traffic accepted?
- Was traffic rejected?
- Is an attachment unhealthy?
- Are route changes occurring unexpectedly?

---

## Troubleshooting

A structured troubleshooting process is more effective than changing random networking rules.

### Verify VPC Routing

Check the source subnet's route table.

Example:

```text
10.20.0.0/16 → tgw-xxxxxxxx
```

### Verify Attachment

Confirm the VPC attachment is available.

### Verify TGW Association

Determine which TGW route table is associated with the source attachment.

### Verify Route Propagation

Confirm that the destination route exists in the associated TGW route table.

### Verify Destination VPC

The destination VPC must have a return route:

```text
10.10.0.0/16 → tgw-xxxxxxxx
```

### Verify Security Groups

Check destination ports and source CIDRs.

### Verify NACLs

Check both directions.

### Verify DNS

If a hostname is being used, verify it resolves to the expected private address.

---

## CLI Examples

Create a Transit Gateway:

```bash
aws ec2 create-transit-gateway \
  --description "Production Network Transit Gateway"
```

Create a VPC attachment:

```bash
aws ec2 create-transit-gateway-vpc-attachment \
  --transit-gateway-id tgw-xxxxxxxx \
  --vpc-id vpc-xxxxxxxx \
  --subnet-ids subnet-aaaaaaa subnet-bbbbbbb
```

Describe Transit Gateways:

```bash
aws ec2 describe-transit-gateways
```

Describe VPC attachments:

```bash
aws ec2 describe-transit-gateway-vpc-attachments
```

Describe TGW route tables:

```bash
aws ec2 describe-transit-gateway-route-tables
```

Add a static TGW route:

```bash
aws ec2 create-transit-gateway-route \
  --transit-gateway-route-table-id tgw-rtb-xxxxxxxx \
  --destination-cidr-block 10.20.0.0/16 \
  --transit-gateway-attachment-id tgw-attach-xxxxxxxx
```

Associate an attachment with a route table:

```bash
aws ec2 associate-transit-gateway-route-table \
  --transit-gateway-route-table-id tgw-rtb-xxxxxxxx \
  --transit-gateway-attachment-id tgw-attach-xxxxxxxx
```

Enable route propagation:

```bash
aws ec2 enable-transit-gateway-route-table-propagation \
  --transit-gateway-route-table-id tgw-rtb-xxxxxxxx \
  --transit-gateway-attachment-id tgw-attach-xxxxxxxx
```

---

## Infrastructure as Code

Production Transit Gateway infrastructure should normally be managed through Infrastructure as Code.

A simplified Terraform example:

```hcl
resource "aws_ec2_transit_gateway" "main" {
  description = "Central production transit gateway"

  tags = {
    Name = "central-production-tgw"
  }
}

resource "aws_ec2_transit_gateway_vpc_attachment" "application" {
  transit_gateway_id = aws_ec2_transit_gateway.main.id
  vpc_id             = aws_vpc.application.id

  subnet_ids = [
    aws_subnet.tgw_a.id,
    aws_subnet.tgw_b.id,
  ]

  tags = {
    Name = "application-vpc-attachment"
  }
}

resource "aws_ec2_transit_gateway_route_table" "production" {
  transit_gateway_id = aws_ec2_transit_gateway.main.id

  tags = {
    Name = "production-routes"
  }
}

resource "aws_ec2_transit_gateway_route_table_association" "application" {
  transit_gateway_attachment_id  = aws_ec2_transit_gateway_vpc_attachment.application.id
  transit_gateway_route_table_id = aws_ec2_transit_gateway_route_table.production.id
}
```

In a mature environment, the Terraform architecture should also manage:

- VPC routes
- TGW route tables
- Route propagation
- Associations
- RAM sharing
- Security Groups
- Network ACLs
- Logging
- Monitoring

The goal is to make network topology reproducible and reviewable.

---

## Cost Considerations

Transit Gateway introduces additional networking costs.

Potential cost drivers include:

- Transit Gateway attachment usage
- Data processing
- Cross-AZ traffic
- Cross-region traffic
- Centralized inspection
- Centralized egress
- NAT Gateway usage

Centralization can simplify operations but may increase traffic concentration.

For example:

```text
Application VPC
      |
      v
     TGW
      |
      v
Central Egress
      |
      v
NAT Gateway
```

If workloads and egress resources are poorly placed across Availability Zones, unnecessary cross-AZ traffic can increase cost.

Network architecture should therefore evaluate:

```text
Security
+
Reliability
+
Latency
+
Operational Complexity
+
Cost
```

rather than optimizing for any single dimension.

---

## High Availability

A production Transit Gateway architecture should avoid unnecessary single-AZ dependencies.

Use VPC attachment subnets across multiple Availability Zones.

For example:

```text
              Transit Gateway
               /     |     \
              /      |      \
           AZ-a     AZ-b     AZ-c
            |        |        |
          TGW      TGW      TGW
        subnet   subnet   subnet
```

The connected workloads should also be distributed across Availability Zones.

For critical centralized services such as:

- Firewalls
- NAT
- Proxies
- DNS
- Inspection appliances

the availability design must account for their own failure modes.

---

## Disaster Recovery

Transit Gateway can be part of multi-region disaster recovery architectures.

For example:

```text
Region A
   |
TGW A
   |
   | TGW Peering
   |
TGW B
   |
Region B
```

However, TGW connectivity alone does not provide application disaster recovery.

The application must also address:

- Database replication
- State management
- DNS failover
- Service deployment
- Secrets
- Storage
- Queues
- Observability
- Traffic routing

Networking is only one part of a DR strategy.

---

## Common Mistakes

### Treating TGW as a Replacement for All Routing

Transit Gateway centralizes network transit but still requires correctly configured VPC and TGW route tables.

### Forgetting the Return Route

A route in the source VPC is not enough.

The destination VPC must have a valid return path.

### Confusing Association With Propagation

Association determines which TGW route table an attachment uses.

Propagation determines which routes an attachment contributes to that route table.

### Creating One Overly Permissive TGW Route Table

A single route table containing every VPC can unintentionally create broad network reachability.

Use segmentation when environments have different trust boundaries.

### Ignoring CIDR Planning

Overlapping networks can prevent routing and complicate future connectivity.

### Selecting Only One Availability Zone

Using only one attachment subnet can introduce unnecessary AZ dependency.

### Assuming TGW Provides Security

TGW provides routing, not application authorization.

Security Groups, NACLs, firewalls, and application-level controls remain important.

### Centralizing Everything Without Evaluating Cost

Centralized egress and inspection can create unnecessary cross-AZ traffic and processing costs.

### Using TGW for a Single Simple VPC Relationship

For two VPCs with a simple connectivity requirement, VPC Peering may be easier and cheaper operationally.

### Manually Modifying Production Routes

Manual networking changes create configuration drift and make incident recovery harder.

Use Infrastructure as Code and controlled change management.

---

## Production Design Patterns

### Shared Services Hub

```text
                 Transit Gateway
                       |
       +---------------+---------------+
       |               |               |
       v               v               v
   Production      Development      Shared Services
```

Use when multiple VPCs need access to centralized internal services.

### Centralized Inspection

```text
Application VPC
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
Destination
```

Use when security policy requires centralized traffic inspection.

### Centralized Egress

```text
Private VPCs
     |
     v
Transit Gateway
     |
     v
Egress VPC
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

Use when outbound Internet traffic must be centralized.

### Multi-Account Network Hub

```text
Network Account
       |
       v
Transit Gateway
   /    |    \
  /     |     \
Prod   Data    Dev
```

Use when AWS Organizations contains multiple workload accounts.

---

## Decision Framework

| Requirement | Recommended Approach |
|---|---|
| Two VPCs with simple direct connectivity | VPC Peering |
| Many VPCs need shared connectivity | Transit Gateway |
| Centralized network segmentation | Transit Gateway |
| Centralized routing | Transit Gateway |
| Expose one application/service privately | PrivateLink |
| Private outbound Internet access | NAT Gateway |
| Corporate network connectivity | VPN / Direct Connect |
| Multi-region network hub | Multiple TGWs + TGW Peering |
| Centralized security inspection | TGW + Inspection Architecture |

---

## Interview Traps

### Is Transit Gateway Regional?

Yes. A Transit Gateway is a regional networking resource.

### Does Transit Gateway Support Transitive Routing?

Yes. This is one of its major advantages over VPC Peering.

### Does Transit Gateway Automatically Route Traffic Between All VPCs?

No.

The route tables and attachment associations/propagation determine which networks can communicate.

### Does Creating a TGW Attachment Automatically Add VPC Routes?

No.

The VPC route tables still need routes pointing appropriate destination CIDRs to the Transit Gateway.

### What Is the Difference Between Association and Propagation?

Association determines which TGW route table an attachment uses.

Propagation determines which routes are inserted into a TGW route table from an attachment.

### Can Transit Gateway Connect Multiple AWS Accounts?

Yes.

AWS RAM can be used to share a Transit Gateway with other accounts.

### Can Transit Gateway Connect Multiple Regions?

Transit Gateways can be connected across Regions using Transit Gateway peering.

### Is Transit Gateway a Security Device?

No.

It is primarily a routing and connectivity service. Security controls must be implemented separately.

### Why Use Transit Gateway Instead of VPC Peering?

The primary architectural reason is scalability and centralized network management.

---

## Practical Architecture Review Checklist

Before approving a Transit Gateway architecture, verify:

- [ ] VPC CIDRs do not overlap.
- [ ] VPC route tables contain required TGW routes.
- [ ] TGW attachments exist in appropriate Availability Zones.
- [ ] TGW route table associations are intentional.
- [ ] Route propagation is intentional.
- [ ] Static routes are documented where used.
- [ ] Return routes exist.
- [ ] Production and development traffic are appropriately isolated.
- [ ] Security Groups allow only required ports and sources.
- [ ] NACLs have been evaluated.
- [ ] DNS resolution is designed.
- [ ] Flow Logs and relevant monitoring are enabled.
- [ ] Cross-AZ traffic has been considered.
- [ ] Cross-region traffic has been considered.
- [ ] Data processing and transfer costs have been evaluated.
- [ ] Network ownership is clearly defined.
- [ ] Infrastructure is managed through IaC.
- [ ] Failure and disaster recovery scenarios are documented.

---

## Key Takeaways

- AWS Transit Gateway provides a centralized regional network hub that scales better than large VPC Peering meshes.
- Correct connectivity requires coordination between VPC route tables, TGW attachments, TGW route table associations, route propagation or static routes, and destination return routes.
- Multiple TGW route tables can enforce meaningful network segmentation between production, development, shared services, data, and security environments.
- Transit Gateway is a networking primitive, not a security boundary; Security Groups, NACLs, firewalls, and application-level authorization remain necessary.
- Production TGW architectures should account for CIDR planning, Availability Zones, cross-account and multi-region connectivity, observability, cost, failure isolation, and Infrastructure as Code.