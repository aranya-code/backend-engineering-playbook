# 07- VPC Peering

## Overview

VPC Peering provides private network connectivity between two Virtual Private Clouds using private IPv4 or IPv6 addresses.

The connection is direct: traffic between the VPCs does not require an Internet Gateway, NAT Gateway, VPN, or Transit Gateway. Once peering is established, each VPC must have explicit routes for the remote VPC's CIDR, and the relevant security controls must allow the traffic.

The basic model is:

```text
VPC A
10.10.0.0/16
    |
    | VPC Peering
    |
    v
VPC B
10.20.0.0/16
```

VPC Peering can operate:

- Within the same AWS account
- Across AWS accounts
- Across AWS Regions

It is most useful for relatively simple, intentional VPC-to-VPC connectivity. For large environments containing many VPCs, Transit Gateway is generally a better architectural foundation because peering creates point-to-point relationships that become increasingly difficult to operate at scale.

---

## Why VPC Peering Exists

A VPC is logically isolated from other VPCs by default.

Suppose an organization has:

```text
Development VPC
10.10.0.0/16

Production VPC
10.20.0.0/16
```

An application in Development cannot simply connect to a private IP address in Production.

VPC Peering provides a private network path between them.

Typical use cases include:

- Connecting two VPCs owned by the same application platform
- Sharing a small number of services between VPCs
- Connecting VPCs belonging to different AWS accounts
- Connecting VPCs across Regions
- Migrating workloads between VPCs
- Supporting temporary or tightly scoped network dependencies

The important architectural property is that peering creates **direct VPC-to-VPC connectivity**, not a centralized routing hub.

---

## Core Architecture

A peering connection has two sides:

- **Requester VPC**
- **Accepter VPC**

The requester initiates the peering request.

The accepter must accept it before the connection becomes active.

```mermaid
flowchart LR
    A["VPC A<br/>10.10.0.0/16"]
    P["VPC Peering Connection"]
    B["VPC B<br/>10.20.0.0/16"]

    A --> P
    P --> B
```

The peering connection itself does not automatically modify route tables.

Both VPCs need appropriate routes.

---

## How VPC Peering Works

Assume:

```text
VPC A = 10.10.0.0/16
VPC B = 10.20.0.0/16
```

A workload in VPC A:

```text
10.10.1.25
```

needs to reach:

```text
10.20.1.40
```

The traffic path is:

```text
Application
10.10.1.25
     |
     v
VPC A Route Table
10.20.0.0/16
     |
     v
VPC Peering
     |
     v
VPC B Route Table
     |
     v
10.20.1.40
```

The return path must also exist:

```text
10.20.1.40
     |
     v
VPC B Route Table
10.10.0.0/16
     |
     v
VPC Peering
     |
     v
VPC A
     |
     v
10.10.1.25
```

This is a critical networking principle:

> Connectivity requires a valid forward path and a valid return path.

---

## Route Tables

Creating the peering connection does not automatically create routes.

For VPC A:

```text
Destination       Target
--------------------------------
10.20.0.0/16      pcx-xxxxxxxx
```

For VPC B:

```text
Destination       Target
--------------------------------
10.10.0.0/16      pcx-xxxxxxxx
```

The routes should be added to the route tables associated with the subnets that need connectivity.

For example:

```text
VPC A
│
├── Public Subnet
│
├── Private App Subnet
│       └── Route: 10.20.0.0/16 → pcx-xxxx
│
└── Private Database Subnet
        └── Route: 10.20.0.0/16 → pcx-xxxx
```

Do not automatically add the peering route to every route table. Routing should reflect the intended trust and connectivity model.

---

## Route Table Selection Matters

A common troubleshooting mistake is verifying that a route exists in the VPC but not checking whether the relevant subnet actually uses that route table.

For example:

```text
VPC A
│
├── App Subnet
│   └── Route Table A
│       └── 10.20.0.0/16 → pcx-1234
│
└── Worker Subnet
    └── Route Table B
        └── No peering route
```

The application subnet can reach VPC B, while the worker subnet cannot.

Always verify:

1. Source subnet
2. Associated route table
3. Destination route
4. Peering connection state
5. Destination route table
6. Security controls

---

## CIDR Requirements

The VPCs should use non-overlapping IP address ranges for normal routed connectivity.

For example:

```text
VPC A
10.10.0.0/16

VPC B
10.20.0.0/16
```

is a good starting point.

This is problematic:

```text
VPC A
10.10.0.0/16

VPC B
10.10.0.0/16
```

because the same destination IP space exists in both networks.

AWS does not support establishing a standard VPC peering connection between VPCs with overlapping IPv4 or IPv6 CIDR blocks.

CIDR planning should therefore happen before VPC provisioning.

---

## CIDR Planning for Production

If an organization expects multiple VPCs, allocate address ranges systematically.

For example:

```text
10.0.0.0/8
│
├── 10.10.0.0/16  Development
├── 10.20.0.0/16  Staging
├── 10.30.0.0/16  Production
├── 10.40.0.0/16  Shared Services
└── 10.50.0.0/16  Data Platform
```

This makes future routing easier.

For larger environments, allocate larger address blocks to environments or regions and subdivide them into VPC-specific ranges.

---

## Security Groups

VPC Peering does not bypass Security Groups.

Suppose:

```text
Application VPC
10.10.0.0/16

Database VPC
10.20.0.0/16
```

The database Security Group might allow:

```text
Protocol: TCP
Port: 5432
Source: 10.10.0.0/16
```

This allows PostgreSQL traffic from the application VPC.

A more restrictive rule could use a specific source CIDR:

```text
10.10.10.0/24
```

rather than the entire VPC.

The principle should be:

> Allow only the source networks and ports that the application actually requires.

---

## Network ACLs

Network ACLs apply at the subnet level.

If NACLs are configured restrictively, traffic must satisfy both directions of the NACL rules.

For example:

```text
Application Subnet
        |
        | outbound
        v
    Peering
        |
        v
Database Subnet
        |
        | inbound
        v
   Database
```

Return traffic must also be permitted.

Because NACLs are stateless, both inbound and outbound rules must be considered.

Security Groups are stateful, while NACLs are stateless.

---

## VPC Peering Is Not Transitive

This is one of the most important VPC Peering concepts.

Suppose:

```text
VPC A
  |
  | Peering
  |
VPC B
  |
  | Peering
  |
VPC C
```

You might expect:

```text
VPC A → VPC B → VPC C
```

to allow:

```text
VPC A → VPC C
```

It does not.

VPC Peering does not provide transitive routing.

```text
A <----> B <----> C

A -X-> C
```

If A needs direct connectivity to C, an explicit connectivity mechanism is required.

This is one of the major reasons large networks often use Transit Gateway instead of creating extensive peering meshes.

---

## Example of Non-Transitive Routing

Consider:

```text
Application VPC
     |
     | Peering
     v
Shared Services VPC
     |
     | Peering
     v
Database VPC
```

The application cannot use the Shared Services VPC as a router to reach the Database VPC.

The Shared Services VPC cannot simply forward the packet on behalf of the Application VPC.

If the application requires direct access to the database VPC, the architecture must explicitly provide an appropriate connectivity mechanism.

---

## VPC Peering vs Transit Gateway

These technologies solve related but different networking problems.

| Feature | VPC Peering | Transit Gateway |
|---|---|---|
| Connectivity model | Point-to-point | Hub-and-spoke |
| Transitive routing | No | Yes through TGW routing |
| Small number of VPCs | Excellent | Often unnecessary |
| Large VPC estates | Operationally difficult | Better suited |
| Central routing | No | Yes |
| Route segmentation | Limited | Strong |
| Cross-account | Supported | Supported |
| Cross-region | Supported | Supported |
| Network hub | No | Yes |
| Operational complexity | Grows with peers | More centralized |

A useful rule is:

> Use VPC Peering for focused point-to-point connectivity; use Transit Gateway when network connectivity itself needs to become a shared platform.

---

## Full-Mesh Scaling Problem

Assume an organization has:

```text
VPC A
VPC B
VPC C
VPC D
VPC E
```

A full mesh requires:

```text
A ↔ B
A ↔ C
A ↔ D
A ↔ E
B ↔ C
B ↔ D
B ↔ E
C ↔ D
C ↔ E
D ↔ E
```

The number of point-to-point relationships grows according to:

```text
N × (N - 1) / 2
```

| VPC Count | Potential Peering Connections |
|---:|---:|
| 2 | 1 |
| 5 | 10 |
| 10 | 45 |
| 20 | 190 |
| 50 | 1,225 |

The problem is not only the number of connections.

Every connection can introduce:

- Route management
- Security review
- Ownership questions
- Monitoring requirements
- CIDR dependencies
- Troubleshooting paths
- Infrastructure-as-Code state
- Lifecycle management

This is why peering should be treated as an architectural decision rather than simply a connectivity feature.

---

## Cross-Account VPC Peering

VPC Peering can connect VPCs belonging to different AWS accounts.

Example:

```text
Account A
Development
    |
    |
    v
VPC Peering
    |
    |
    v
Account B
Shared Services
```

The accounts must coordinate the peering request and acceptance.

Cross-account connectivity should also be governed by:

- IAM
- Security Groups
- Route tables
- Network ACLs
- Organizational policies
- Change management

AWS account ownership does not automatically establish trust.

---

## Cross-Region VPC Peering

VPC Peering can also provide private connectivity between VPCs in different AWS Regions.

Example:

```text
Region A                         Region B

VPC A                            VPC B
10.10.0.0/16                     10.20.0.0/16
   |                                  |
   +-------- Inter-Region ------------+
                 Peering
```

This can be useful for:

- Regional service dependencies
- Migration
- Disaster recovery architectures
- Multi-region applications
- Controlled replication paths

However, cross-region traffic introduces additional considerations around:

- Latency
- Data transfer costs
- Regional failure
- Application consistency
- DNS
- Data residency

---

## DNS Resolution

VPC Peering can be used with private DNS resolution, but DNS configuration must be deliberately designed.

For example:

```text
api.internal.example.com
        |
        v
Private DNS
        |
        v
Private IP in another VPC
```

Applications should generally consume stable DNS names rather than hard-coded private IP addresses.

For multi-VPC environments, Route 53 private hosted zones and Resolver can provide a more maintainable DNS architecture.

---

## Application Example

Consider a Django application in one VPC and PostgreSQL in another.

```text
Application VPC
10.10.0.0/16
│
├── Django
│   10.10.10.20
│
└── Private Subnet
       |
       | Route:
       | 10.20.0.0/16 → pcx-xxxx
       |
       v
   VPC Peering
       |
       v
Database VPC
10.20.0.0/16
│
└── PostgreSQL
    10.20.10.50:5432
```

The Django application can use:

```text
postgresql://db.internal.example.com:5432/application
```

provided that:

- DNS resolves correctly
- The application subnet has a route to the database VPC
- The database subnet has a return route
- The PostgreSQL Security Group allows the application traffic
- NACLs permit the traffic
- The peering connection is active

The application does not need to expose PostgreSQL publicly.

---

## Backend Service-to-Service Communication

VPC Peering can support private communication between microservices hosted in different VPCs.

For example:

```text
Orders VPC
    |
    | HTTPS :443
    v
VPC Peering
    |
    v
Payments VPC
```

An internal REST or gRPC service can remain private.

However, if many microservices across many VPCs need connectivity, a centralized networking model or service-level connectivity mechanism may be easier to operate.

---

## VPC Peering and Kubernetes

If Kubernetes workloads are distributed across VPCs, peering can provide network reachability between the underlying VPC address spaces.

However, Kubernetes networking introduces another layer:

```text
Pod Network
     |
     v
Node Network
     |
     v
VPC Network
     |
     v
VPC Peering
     |
     v
Remote VPC
```

Do not assume that VPC-level connectivity automatically solves Kubernetes-level service discovery or routing requirements.

The Kubernetes CNI, pod addressing, service discovery, NetworkPolicies, and AWS routing model must all be considered.

---

## VPC Peering and AWS PrivateLink

PrivateLink and VPC Peering are often confused because both provide private connectivity.

The architectural difference is significant.

### VPC Peering

Provides network-level connectivity:

```text
Consumer VPC
      |
      v
Provider VPC
```

The consumer can potentially reach multiple resources in the provider VPC, subject to routing and security controls.

### PrivateLink

Provides service-level connectivity:

```text
Consumer
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

PrivateLink is often preferable when the provider wants to expose one service without exposing its broader network.

---

## Comparison With Other Connectivity Options

| Requirement | VPC Peering | Transit Gateway | PrivateLink |
|---|---|---|---|
| Direct VPC connectivity | Yes | Yes | Service-specific |
| Point-to-point | Yes | No | Service-oriented |
| Transitive routing | No | Yes | Not applicable |
| Centralized routing | No | Yes | No |
| Expose one service | Possible but broad | Possible but broad | Excellent |
| Large network | Less suitable | Excellent | Complementary |
| Consumer/provider model | Less explicit | Network-oriented | Excellent |
| Cross-account | Yes | Yes | Yes |
| Cross-region | Yes | Supported architecture | Supported where applicable |

---

## Routing Constraints

VPC Peering does not function as a general-purpose router.

A peered VPC cannot be used to provide arbitrary third-party routing through the peering connection.

For example:

```text
VPC A
   |
   | Peering
   v
VPC B
   |
   v
Internet
```

VPC A should not be treated as though VPC B were a general-purpose gateway to the Internet.

Similarly, peering is not a replacement for:

- Transit Gateway
- Site-to-Site VPN
- Direct Connect
- NAT Gateway
- Internet Gateway

Each solves a different networking problem.

---

## Security Architecture

A secure peering design should use multiple controls.

```text
              Route Table
                  |
                  v
             VPC Peering
                  |
        +---------+---------+
        |                   |
 Security Group          NACL
        |                   |
        +---------+---------+
                  |
                  v
              Workload
```

Security should be based on the minimum required communication.

For example, if an application needs PostgreSQL:

```text
Source:
10.10.10.0/24

Destination:
10.20.10.50

Protocol:
TCP

Port:
5432
```

Avoid broad rules such as:

```text
0.0.0.0/0
```

when a specific private CIDR is sufficient.

---

## Monitoring

VPC Flow Logs are useful for troubleshooting peering traffic.

They can help answer:

- Did traffic reach the source ENI?
- Was the traffic accepted or rejected?
- Which source IP was used?
- Which destination IP was targeted?
- Which port was used?

A practical troubleshooting path is:

```text
Application
   |
   v
DNS
   |
   v
Route Table
   |
   v
Peering State
   |
   v
Remote Route Table
   |
   v
Security Group
   |
   v
NACL
   |
   v
Destination
```

Do not immediately change Security Groups when the actual problem is a missing route.

---

## Troubleshooting Checklist

When a connection fails, check the following in order.

### Peering State

Confirm:

```text
Active
```

rather than:

```text
Pending Acceptance
```

or another inactive state.

### CIDR

Verify the VPC CIDRs do not overlap.

### Source Route Table

Check:

```text
Destination = Remote VPC CIDR
Target = pcx-xxxxxxxx
```

### Destination Route Table

Verify the remote VPC has a return route.

### Security Group

Check that the destination allows the required protocol and port.

### Network ACL

Check both directions because NACLs are stateless.

### DNS

Verify that the hostname resolves to the expected private IP.

### Operating System Firewall

If applicable, check host-level firewall rules.

### Application

Finally verify:

- Listening port
- Application binding
- TLS configuration
- Credentials
- Service health

---

## CLI Examples

Create a VPC peering connection:

```bash
aws ec2 create-vpc-peering-connection \
  --vpc-id vpc-aaaaaaaa \
  --peer-vpc-id vpc-bbbbbbbb
```

For a cross-account or cross-region request, additional parameters may be required.

Accept a peering connection:

```bash
aws ec2 accept-vpc-peering-connection \
  --vpc-peering-connection-id pcx-xxxxxxxx
```

Describe peering connections:

```bash
aws ec2 describe-vpc-peering-connections \
  --vpc-peering-connection-ids pcx-xxxxxxxx
```

Add a route to a route table:

```bash
aws ec2 create-route \
  --route-table-id rtb-aaaaaaaa \
  --destination-cidr-block 10.20.0.0/16 \
  --vpc-peering-connection-id pcx-xxxxxxxx
```

Add the corresponding return route:

```bash
aws ec2 create-route \
  --route-table-id rtb-bbbbbbbb \
  --destination-cidr-block 10.10.0.0/16 \
  --vpc-peering-connection-id pcx-xxxxxxxx
```

Delete a peering connection:

```bash
aws ec2 delete-vpc-peering-connection \
  --vpc-peering-connection-id pcx-xxxxxxxx
```

Before deleting a connection, remove or update dependent routes and confirm that no production workloads still depend on it.

---

## Infrastructure as Code

Peering should generally be managed through Infrastructure as Code in production.

A simplified Terraform example:

```hcl
resource "aws_vpc_peering_connection" "application_to_shared" {
  vpc_id      = aws_vpc.application.id
  peer_vpc_id = aws_vpc.shared_services.id
  auto_accept = true

  tags = {
    Name = "application-to-shared-services"
  }
}

resource "aws_route" "application_to_shared" {
  route_table_id            = aws_route_table.application_private.id
  destination_cidr_block    = aws_vpc.shared_services.cidr_block
  vpc_peering_connection_id = aws_vpc_peering_connection.application_to_shared.id
}

resource "aws_route" "shared_to_application" {
  route_table_id            = aws_route_table.shared_private.id
  destination_cidr_block    = aws_vpc.application.cidr_block
  vpc_peering_connection_id = aws_vpc_peering_connection.application_to_shared.id
}
```

Cross-account configurations generally require provider aliases and separate ownership considerations.

The important production principle is that the peering connection, routes, and security rules should be managed as one dependency graph.

---

## Production Considerations

### High Availability

VPC Peering itself is a managed AWS networking capability, but the workloads on both sides still need to be designed for availability.

Avoid making a single instance or Availability Zone the only usable endpoint.

### Failure Isolation

If VPC A depends on VPC B for a critical database or service, VPC B becomes part of the application's failure domain.

Consider:

- Service redundancy
- Regional strategy
- Database replication
- Failover
- DNS behavior

### Dependency Management

Document every production peering relationship.

A useful inventory includes:

| Field | Example |
|---|---|
| Source VPC | Orders |
| Destination VPC | Payments |
| Account | Shared Services |
| Region | `ap-south-1` |
| Purpose | Payment API |
| Ports | `443` |
| Owner | Platform Team |
| Criticality | High |

This becomes valuable during incident response and architecture reviews.

### Lifecycle Management

Peering connections should have an owner and documented reason for existence.

Remove obsolete connections rather than allowing them to accumulate indefinitely.

---

## Cost Considerations

VPC Peering does not require a NAT Gateway or Internet Gateway for the peering path.

However, data transfer charges can still apply depending on the traffic pattern, especially for cross-AZ and cross-region communication.

Consider:

```text
Application
    |
    v
AZ-A
    |
    v
Peering
    |
    v
AZ-B
```

Cross-AZ traffic can create additional cost and latency.

Architecture decisions should therefore consider both network reachability and workload placement.

---

## Common Mistakes

### Assuming Peering Automatically Creates Routes

It does not.

The required routes must be configured.

### Forgetting the Return Route

Forward traffic may leave the source VPC but never return.

### Using Overlapping CIDRs

Overlapping address spaces prevent normal routed connectivity.

### Expecting Transitive Routing

```text
A ↔ B ↔ C
```

does not mean:

```text
A ↔ C
```

### Allowing Excessive Security Group Access

Do not open entire VPCs when only one service and port are required.

### Ignoring NACLs

Restrictive NACLs can silently block otherwise valid traffic.

### Hard-Coding IP Addresses

Use private DNS names where practical.

### Creating Too Many Peering Connections

A large peering mesh becomes difficult to understand and operate.

### Managing Production Peering Manually

Manual changes are difficult to audit, reproduce, and review.

### Treating Peering as a Security Boundary

Peering creates connectivity; it does not replace authorization controls.

---

## When VPC Peering Is a Good Choice

Use VPC Peering when:

- Only a small number of VPCs need direct connectivity.
- The relationship is explicit and stable.
- CIDRs are non-overlapping.
- Centralized routing is unnecessary.
- The traffic relationship is relatively simple.
- Direct VPC-to-VPC communication is desired.

Example:

```text
Application VPC
       |
       | Peering
       v
Dedicated Data VPC
```

This can be reasonable when the dependency is tightly scoped.

---

## When VPC Peering Is a Poor Choice

Avoid using it as the primary network architecture when:

- Dozens of VPCs require interconnected routing.
- Connectivity relationships change frequently.
- Centralized inspection is required.
- Centralized routing policies are required.
- Network segmentation needs to be managed centrally.
- The organization has many AWS accounts and Regions.

In those environments, Transit Gateway is often a better foundation.

---

## Interview Traps

### Is VPC Peering Transitive?

No.

Each required VPC-to-VPC path must be explicitly established.

### Does Creating Peering Automatically Update Route Tables?

No.

Routes must be configured on both sides.

### Can Peered VPCs Have Overlapping CIDRs?

No, not for a standard VPC peering connection.

### Can VPC Peering Work Across AWS Accounts?

Yes.

It can be used for cross-account VPC connectivity.

### Can VPC Peering Work Across Regions?

Yes.

Inter-Region VPC Peering provides private connectivity between supported VPCs in different Regions.

### Does Peering Replace Security Groups?

No.

Security Groups remain part of the traffic authorization model.

### Does Peering Provide Internet Access?

No.

It provides private connectivity between the peered VPCs. It does not make one VPC an Internet gateway for another.

### When Should Transit Gateway Be Preferred?

When the network contains enough VPCs or connectivity relationships that point-to-point peering becomes difficult to operate.

---

## Reference Architecture

A small production environment might look like:

```mermaid
flowchart TB
    APP["Application VPC<br/>10.10.0.0/16"]
    DATA["Data VPC<br/>10.20.0.0/16"]
    PEER["VPC Peering"]

    APP --> PEER
    PEER --> DATA

    APP --> APPRT["Application Route Table"]
    DATA --> DATART["Data Route Table"]

    APPRT --> PEER
    DATART --> PEER
```

For example:

```text
Application VPC
10.10.0.0/16
│
├── Private App Subnet
│   └── Django / FastAPI
│
└── Worker Subnet
    └── Celery Workers

        |
        | VPC Peering
        |

Data VPC
10.20.0.0/16
│
├── PostgreSQL
│
└── Redis
```

Only the required application traffic should be permitted across the connection.

---

## VPC Peering Decision Framework

Before creating a peering connection, answer:

| Question | Decision |
|---|---|
| Are the CIDRs non-overlapping? | Required |
| Is direct VPC connectivity needed? | Required |
| Is the number of VPCs small? | Preferable |
| Is transitive routing required? | Use another architecture |
| Is centralized routing required? | Consider Transit Gateway |
| Is only one service being exposed? | Consider PrivateLink |
| Is the connection temporary? | Document lifecycle |
| Is production involved? | Use IaC and change management |
| Are security rules narrowly scoped? | Required |
| Is DNS designed? | Strongly recommended |

---

## Key Takeaways

- VPC Peering provides direct private connectivity between two VPCs, but both sides require explicit routing and appropriate security controls.
- Peering is non-transitive, so `VPC A ↔ VPC B ↔ VPC C` does not provide connectivity between A and C.
- Non-overlapping CIDRs, correct forward and return routes, Security Groups, NACLs, and DNS are all important when troubleshooting peering connectivity.
- VPC Peering is well suited to small, explicit point-to-point relationships; large multi-VPC environments generally benefit from Transit Gateway or service-level PrivateLink architectures.
- Production peering should be treated as infrastructure: manage it through IaC, document ownership and dependencies, monitor traffic, and remove obsolete connections.