# 07- VPC Architecture and Design Questions

## Overview

VPC architecture and design interview questions evaluate whether you can design a network around application requirements rather than simply configure individual AWS networking components.

A strong answer should connect:

- CIDR planning.
- Subnet topology.
- Availability Zones.
- Route tables.
- Internet and NAT connectivity.
- Security boundaries.
- VPC endpoints.
- VPC peering.
- Transit Gateway.
- VPN and Direct Connect.
- DNS.
- Network inspection.
- Observability.
- Multi-account architecture.
- High availability.
- Disaster recovery.
- Cost and operational complexity.

The central design principle is to treat the VPC as a **network architecture and failure-domain design problem**, not merely as a collection of subnets and route tables.

For senior-level interviews, explain both the architecture and the trade-offs. A technically valid design can still be poor if it introduces unnecessary network hops, excessive cost, overlapping CIDRs, a large blast radius, or difficult operational dependencies.

## Core VPC Architecture

A common production architecture for a backend application is:

```mermaid
flowchart TB
    Internet((Internet))
    IGW[Internet Gateway]

    subgraph VPC[VPC]
        subgraph Public[Public Subnets]
            ALB[Application Load Balancer]
            NAT[NAT Gateway]
        end

        subgraph Private[Private Application Subnets]
            API1[Django / FastAPI]
            API2[Django / FastAPI]
            Worker[Celery Workers]
        end

        subgraph Data[Private Data Subnets]
            DB[(PostgreSQL)]
            Redis[(Redis)]
        end
    end

    Internet --> IGW
    IGW --> ALB
    ALB --> API1
    ALB --> API2
    API1 --> DB
    API2 --> DB
    Worker --> Redis
    API1 --> NAT
    API2 --> NAT
    Worker --> NAT
```

The exact architecture depends on workload requirements, but the common pattern is:

- Internet-facing entry points in public subnets.
- Application workloads in private subnets.
- Databases and caches in isolated or private data subnets.
- Explicit Security Group relationships between tiers.
- Multi-AZ deployment for critical workloads.
- NAT or VPC endpoints for required outbound connectivity.

## CIDR Planning Questions

### Interview Question: How Would You Choose a VPC CIDR?

Start with the network relationships the VPC may need throughout its lifetime.

Consider:

- Number of Availability Zones.
- Number of subnet tiers.
- Expected workload growth.
- Future VPCs.
- VPC peering.
- Transit Gateway.
- On-premises networks.
- Kubernetes networking.
- Other AWS accounts.
- Corporate IP addressing standards.
- Future mergers or network integrations.

For example:

```text
VPC
10.0.0.0/16

Public:
10.0.1.0/24
10.0.2.0/24
10.0.3.0/24

Application:
10.0.11.0/24
10.0.12.0/24
10.0.13.0/24

Database:
10.0.21.0/24
10.0.22.0/24
10.0.23.0/24
```

The important point is not the exact CIDR size. It is ensuring that the address space is sufficiently large, structured, and non-overlapping with networks that may need to communicate later.

### Interview Question: Why Is CIDR Overlap a Problem?

Consider:

```text
VPC A
10.0.0.0/16

VPC B
10.0.0.0/16
```

Both networks claim the same destination range.

When the networks need to communicate through peering, Transit Gateway, VPN, or other routing mechanisms, the overlapping addresses create ambiguous or impossible routing relationships.

CIDR planning should therefore happen at an organizational level rather than independently for every VPC.

## Subnet Design

A production VPC commonly divides subnets by workload role and Availability Zone.

```text
VPC: 10.0.0.0/16

AZ-a
├── Public:   10.0.1.0/24
├── App:      10.0.11.0/24
└── Data:     10.0.21.0/24

AZ-b
├── Public:   10.0.2.0/24
├── App:      10.0.12.0/24
└── Data:     10.0.22.0/24

AZ-c
├── Public:   10.0.3.0/24
├── App:      10.0.13.0/24
└── Data:     10.0.23.0/24
```

This provides:

- Failure-domain separation.
- Clear routing boundaries.
- Easier security policy design.
- Better operational visibility.
- Room for horizontal scaling.

### Interview Question: Why Have Separate Application and Database Subnets?

Subnet separation creates an additional network boundary and allows different routing policies.

For example:

```text
Internet
   |
   v
Public ALB
   |
   v
Application Subnets
   |
   v
Database Subnets
```

The database tier should not require Internet access.

This does not replace Security Groups. Instead, routing and security controls work together.

## Public vs Private Subnets

A subnet is generally considered public when its route table provides a path to an Internet Gateway.

Example:

```text
Destination       Target
10.0.0.0/16       local
0.0.0.0/0         igw-xxxx
```

A private subnet does not have a direct Internet Gateway route.

For outbound Internet access, it can use:

```text
Private Workload
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

A private subnet therefore does not mean "no outbound connectivity." It means the workload does not have direct Internet routing.

## Interview Question: Does a Security Group Make a Subnet Private?

No.

These are separate concepts.

```text
Route Table
    |
    +--> Determines where packets can go

Security Group
    |
    +--> Determines which traffic is allowed
```

A subnet can have restrictive Security Groups and still be publicly routed.

Likewise, a subnet without an Internet route can still allow broad internal traffic.

## Internet Gateway vs NAT Gateway

| Component | Primary Role | Direct Internet Ingress | Outbound Internet |
|---|---|---:|---:|
| Internet Gateway | Connect VPC to Internet | Yes | Yes |
| NAT Gateway | Provide outbound connectivity for private resources | No unsolicited inbound | Yes |

An Internet Gateway is associated with the VPC.

A NAT Gateway is deployed into a subnet and requires appropriate routing.

## NAT Gateway Architecture

For high availability, a common architecture is one NAT Gateway per Availability Zone:

```text
AZ-a                    AZ-b
 |                       |
Private-a             Private-b
 |                       |
NAT-a                  NAT-b
 |                       |
IGW                    IGW
```

This keeps outbound traffic within the same AZ where practical.

### Interview Question: Why Not Use One NAT Gateway?

One NAT Gateway may reduce infrastructure cost but introduces a shared dependency.

For example:

```text
Private-a ----+
Private-b ----+---- NAT-a
Private-c ----+
```

If the NAT Gateway or its Availability Zone becomes unavailable, private workloads in other AZs may lose outbound connectivity if their routes depend on it.

A per-AZ NAT architecture improves failure isolation but increases cost.

### Cost Trade-Off

Consider:

- NAT Gateway hourly cost.
- NAT data processing cost.
- Cross-AZ traffic.
- Application traffic volume.
- Availability requirements.
- VPC endpoint alternatives.

For high-volume AWS service traffic, VPC endpoints may reduce unnecessary NAT dependency.

## Route Table Design

Routing is one of the most important parts of VPC architecture.

A public route table might contain:

```text
Destination       Target
10.0.0.0/16       local
0.0.0.0/0         igw-xxxx
```

A private application route table might contain:

```text
Destination       Target
10.0.0.0/16       local
0.0.0.0/0         nat-xxxx
```

An isolated database route table might contain:

```text
Destination       Target
10.0.0.0/16       local
```

The route table should reflect the intended communication model.

## Route Evaluation

When a packet is sent, AWS evaluates routes using the most specific matching destination.

For example:

```text
10.0.0.0/16  -> local
10.0.20.0/24 -> specific target
0.0.0.0/0    -> default target
```

Traffic destined for `10.0.20.10` matches the `/24` route rather than the `/16` route.

This becomes particularly important in complex architectures involving:

- Transit Gateway.
- VPC peering.
- VPN.
- Direct Connect.
- Inspection appliances.
- Centralized egress.

## Security Group Architecture

A strong design uses Security Groups to express application relationships.

For example:

```text
Internet
   |
   v
ALB-SG
   |
   | TCP 443
   v
API-SG
   |
   | TCP 5432
   v
DB-SG
```

The database Security Group can allow PostgreSQL only from the application Security Group.

Conceptually:

```text
DB-SG
Inbound:
TCP 5432
Source: API-SG
```

This is generally preferable to allowing:

```text
TCP 5432
Source: 10.0.0.0/16
```

when the application Security Group expresses the intended trust boundary more precisely.

## Security Groups vs Network ACLs

| Characteristic | Security Group | Network ACL |
|---|---|---|
| Scope | Network interface/resource | Subnet |
| State | Stateful | Stateless |
| Rules | Allow | Allow and deny |
| Return traffic | Automatically tracked | Must be explicitly allowed |
| Typical role | Workload-level access | Subnet-level filtering |

Security Groups should usually be the primary workload access-control mechanism.

NACLs can be useful for subnet-level controls, but overly restrictive NACLs frequently introduce operational complexity.

A common mistake is forgetting that NACLs are stateless and therefore require both directions of traffic to be permitted.

## Interview Question: When Would You Use a NACL?

Potential use cases include:

- Broad subnet-level deny policies.
- Explicit subnet boundary controls.
- Compliance requirements.
- Blocking known network ranges.

Do not add complex NACL rules simply because "more security" sounds better.

Complex NACLs can make troubleshooting substantially harder.

## VPC Endpoints

VPC endpoints provide private connectivity to supported AWS services.

For example:

```text
Private EC2
    |
    v
VPC Endpoint
    |
    v
Amazon S3
```

This avoids unnecessarily routing supported AWS service traffic through a NAT Gateway.

Endpoint categories include:

- Gateway endpoints.
- Interface endpoints.

Gateway endpoints are commonly used for services such as S3 and DynamoDB.

Interface endpoints use AWS PrivateLink and provide connectivity through network interfaces in the VPC.

## Interview Question: Why Use VPC Endpoints?

Advantages include:

- Private connectivity to supported AWS services.
- Reduced dependence on NAT.
- Reduced Internet exposure.
- Potential cost savings.
- Better network isolation.

Production considerations include:

- Endpoint policies.
- DNS behavior.
- Security Groups for interface endpoints.
- Availability across required AZs.
- Service support.
- Endpoint operating cost.

## DNS Architecture

DNS is an important part of VPC design, especially in hybrid environments.

A simplified architecture is:

```text
Application
    |
    v
VPC Resolver
    |
    +---- AWS DNS
    |
    +---- On-Premises DNS
```

For hybrid environments, Route 53 Resolver endpoints and forwarding rules can provide controlled DNS integration.

Common problems include:

- Incorrect resolver configuration.
- Missing forwarding rules.
- Security controls blocking DNS.
- Incorrect private hosted zones.
- Applications using hard-coded IP addresses.

A senior-level design treats DNS as part of the network architecture rather than an afterthought.

## VPC Peering

VPC peering provides private connectivity between two VPCs.

```text
VPC A
10.10.0.0/16
    |
    | VPC Peering
    |
VPC B
10.20.0.0/16
```

The CIDRs must be compatible for the intended communication.

### Interview Question: Is VPC Peering Transitive?

No.

Consider:

```text
VPC A <--> VPC B <--> VPC C
```

VPC A cannot automatically use VPC B as a transit path to reach VPC C.

Each required network relationship must be explicitly established.

## Transit Gateway

Transit Gateway provides centralized connectivity between multiple VPCs and external networks.

```mermaid
flowchart LR
    VPC1[VPC A]
    VPC2[VPC B]
    VPC3[VPC C]
    VPN[Site-to-Site VPN]
    DX[Direct Connect]
    TGW[Transit Gateway]

    VPC1 --> TGW
    VPC2 --> TGW
    VPC3 --> TGW
    VPN --> TGW
    DX --> TGW
```

Transit Gateway is particularly useful when networking grows beyond a small number of direct relationships.

## VPC Peering vs Transit Gateway

| Characteristic | VPC Peering | Transit Gateway |
|---|---|---|
| Topology | Point-to-point | Hub-and-spoke |
| Transitive routing | No | Supported through TGW routing |
| Central routing | No | Yes |
| Large-scale networking | Less suitable | Well suited |
| Operational model | Distributed | Centralized |
| Typical use | Simple VPC relationships | Multi-VPC enterprise networks |

The important interview answer is not "Transit Gateway is better."

The correct answer is to explain the topology, scale, routing requirements, and operational trade-offs.

## Multi-Account VPC Architecture

Large AWS environments commonly use multiple accounts.

```text
AWS Organization
│
├── Production Account
│   ├── VPC A
│   └── VPC B
│
├── Development Account
│   └── VPC C
│
├── Security Account
│   └── Inspection VPC
│
└── Networking Account
    └── Transit Gateway
```

This can provide stronger isolation and governance than placing every environment into one account.

Potential benefits include:

- Smaller blast radius.
- Independent IAM boundaries.
- Environment isolation.
- Centralized networking.
- Better cost allocation.
- Independent operational ownership.

## Hub-and-Spoke Networking

A common enterprise model is:

```text
                   Transit Gateway
                  /      |       \
                 /       |        \
              VPC A    VPC B     VPC C
```

However, attaching every VPC to a Transit Gateway does not automatically mean every VPC should communicate with every other VPC.

Transit Gateway route tables can create separate routing domains.

For example:

```text
TGW Route Table: Production
    |
    +---- Production VPCs

TGW Route Table: Development
    |
    +---- Development VPCs

TGW Route Table: Shared Services
    |
    +---- Shared Services VPC
```

This allows centralized connectivity while preserving segmentation.

## Centralized Inspection Architecture

Some organizations require traffic inspection between network segments.

A simplified architecture is:

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
Network Firewall / Appliance
      |
      v
Transit Gateway
      |
      v
Destination VPC
```

This architecture can provide:

- Centralized inspection.
- Consistent security policy.
- Centralized monitoring.

However, it also introduces:

- Additional routing complexity.
- More network hops.
- Potential throughput constraints.
- Appliance scaling requirements.
- Additional failure dependencies.

The inspection layer should therefore be introduced because of a concrete security or compliance requirement, not simply because centralized architecture appears cleaner.

## Centralized Egress

A centralized egress architecture can provide controlled Internet access:

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

Advantages:

- Centralized outbound policy.
- Centralized inspection.
- Centralized Internet egress.
- Easier organization-wide controls.

Trade-offs:

- Additional routing complexity.
- Cross-AZ or cross-VPC traffic.
- Additional data-transfer costs.
- Larger shared blast radius.
- More operational dependencies.

For smaller environments, per-VPC NAT may be simpler.

## High Availability Design

A VPC is not highly available merely because it contains multiple subnets.

Critical workloads must be deployed across independent Availability Zones.

Example:

```text
                    ALB
                 /       \
               AZ-a      AZ-b
                |          |
              API-a      API-b
                |          |
              DB-a       DB-b
```

The exact database architecture depends on the selected database service.

For stateless Django or FastAPI services:

```text
ALB
 |
 +---- API AZ-a
 |
 +---- API AZ-b
 |
 +---- API AZ-c
```

This allows traffic to continue through healthy Availability Zones if one AZ fails.

## Availability vs Scalability

These are related but different architectural properties.

### Availability

The system remains operational despite component or failure-domain failures.

### Scalability

The system can handle increased workload.

For example:

```text
3 API instances across 3 AZs
```

primarily addresses availability and baseline redundancy.

Increasing to:

```text
20 API instances across 3 AZs
```

also provides greater capacity.

A strong architecture evaluates both independently.

## Stateless Backend Architecture

Django and FastAPI applications commonly benefit from horizontal scaling.

A typical design is:

```text
             ALB
              |
      +-------+-------+
      |       |       |
    API-a   API-b   API-c
      |       |       |
      +-------+-------+
              |
       +------+------+
       |             |
    PostgreSQL      Redis
```

Application instances should avoid relying on local state for data that must survive instance replacement.

Redis can provide:

- Caching.
- Shared application state where appropriate.
- Celery broker/backend functionality depending on the architecture.

PostgreSQL typically remains the durable relational data store.

## Kubernetes VPC Design

Kubernetes introduces additional network-planning requirements.

Depending on the architecture, address space may be needed for:

- Nodes.
- Pods.
- Services.
- Load balancers.
- Cluster networking.
- External integrations.

A simplified design is:

```text
Internet
   |
Load Balancer
   |
Kubernetes Cluster
   |
+--+----------------+
|                   |
Node A             Node B
|                   |
Pods               Pods
|                   |
+---------+---------+
          |
       Database
```

CIDR planning becomes especially important because Kubernetes networking can consume significant address space.

Avoid choosing a VPC CIDR without considering the cluster's networking model and future cluster expansion.

## Hybrid Connectivity

A common enterprise architecture is:

```mermaid
flowchart TB
    OnPrem[Corporate Network]

    DX[Direct Connect]
    VPN[Site-to-Site VPN]
    TGW[Transit Gateway]

    Prod[Production VPC]
    Dev[Development VPC]
    Shared[Shared Services VPC]
    Inspect[Inspection VPC]

    OnPrem --> DX
    OnPrem --> VPN

    DX --> TGW
    VPN --> TGW

    TGW --> Prod
    TGW --> Dev
    TGW --> Shared
    TGW --> Inspect
```

Direct Connect and Site-to-Site VPN can serve different roles.

A common production design uses one as primary connectivity and another as a backup path, depending on business and availability requirements.

The important architectural consideration is redundancy across the entire path rather than merely provisioning multiple logical connections.

## Disaster Recovery Architecture

Multi-AZ architecture and multi-Region disaster recovery solve different problems.

Multi-AZ primarily addresses Availability Zone failures.

Multi-Region architectures can address regional failure scenarios.

Example:

```text
Region A
+-------------------+
| Production VPC    |
+-------------------+
          |
       Replication
          |
          v
Region B
+-------------------+
| DR VPC            |
+-------------------+
```

A complete DR architecture must consider:

- RTO.
- RPO.
- Data replication.
- DNS failover.
- Infrastructure automation.
- Secrets.
- Application deployment.
- Network connectivity.
- Dependency recovery.

Creating a second VPC without synchronized data and application recovery mechanisms is not a complete disaster recovery solution.

## Backend API VPC Design

Consider a production Django or FastAPI API requiring PostgreSQL and Redis.

A reasonable architecture is:

```text
                     Internet
                        |
                        v
                   Public ALB
                  /          \
                 /            \
          Private AZ-a    Private AZ-b
              |                |
          Django API       Django API
              |                |
              +-------+--------+
                      |
             +--------+--------+
             |                 |
        PostgreSQL           Redis
```

Workers can operate separately:

```text
Celery Workers
      |
      +---- PostgreSQL
      |
      +---- Redis
      |
      +---- External APIs
```

The API instances and workers can use NAT Gateway for required outbound Internet access, while VPC endpoints can provide private connectivity to supported AWS services.

## Microservices VPC Design

Do not automatically create one VPC for every microservice.

A common architecture can host multiple services within a VPC:

```text
VPC
 |
 +-- Service A
 +-- Service B
 +-- Service C
 +-- Shared Services
 +-- Database
 +-- Redis
```

The correct network boundary depends on:

- Security isolation.
- Compliance.
- Organizational ownership.
- Blast radius.
- Network scale.
- Operational independence.

A VPC is a network boundary, not necessarily a microservice boundary.

## Network Observability

A production VPC should have multiple diagnostic layers.

Useful tools include:

- VPC Flow Logs.
- CloudWatch.
- Reachability Analyzer.
- CloudTrail.
- Transit Gateway metrics.
- VPN tunnel metrics.
- Direct Connect telemetry.
- Route inspection.
- Application logs.

For example:

```text
HTTP 504
   |
   v
Application timeout
   |
   v
Connection failure
   |
   v
VPC Flow Logs
   |
   v
Rejected traffic
   |
   v
Security Group / NACL / Route
```

Network troubleshooting is most effective when application symptoms can be correlated with network-level evidence.

## Common Architecture Mistakes

### Using One Flat Network

A single broad network with unrestricted internal connectivity increases the blast radius of configuration mistakes and compromised workloads.

Use meaningful segmentation.

### Choosing an Undersized CIDR

A VPC may work initially but become difficult to expand.

Plan address space based on expected growth and future connectivity.

### Overlapping CIDRs

Overlapping CIDRs become problematic when networks must communicate.

Plan organizational address space before creating many VPCs.

### One NAT Gateway for Everything

This can create a shared dependency and introduce cross-AZ traffic.

Evaluate per-AZ NAT versus centralized egress based on availability and cost requirements.

### Public IPs on Application Servers

Application instances generally do not need public addresses when an ALB provides Internet-facing ingress.

Private application subnets reduce direct exposure.

### Using Security Groups as the Only Security Boundary

Security Groups are critical but do not replace:

- Routing.
- IAM.
- Encryption.
- Application authentication.
- Network segmentation.
- Logging.
- Threat detection.

### Excessive VPC Peering

A large peering mesh becomes increasingly difficult to manage.

Transit Gateway may provide a more scalable routing topology.

### Centralizing Everything

Centralization can simplify governance but can also increase blast radius.

Evaluate:

- Shared dependencies.
- Failure modes.
- Throughput.
- Latency.
- Routing complexity.
- Cost.

### Overly Complex NACLs

Restrictive NACLs can introduce subtle failures because they are stateless.

Use them deliberately and understand ephemeral ports and return traffic.

## Interview Scenario: Design a Highly Available Web Application

### Requirements

Design a Django API that:

- Handles Internet traffic.
- Uses PostgreSQL.
- Uses Redis.
- Runs across multiple Availability Zones.
- Does not expose application instances directly to the Internet.

### Strong Architecture

```text
                     Internet
                        |
                        v
                  Public ALB
                  /        \
                 /          \
          Private AZ-a    Private AZ-b
              |                |
          Django API       Django API
              |                |
              +-------+--------+
                      |
             +--------+--------+
             |                 |
        PostgreSQL           Redis
```

Key decisions:

- ALB is deployed in public subnets.
- Application instances run in private subnets.
- Database resources are isolated from Internet access.
- Redis is not publicly exposed.
- Security Groups define explicit tier-to-tier access.
- Application workloads span multiple AZs.
- NAT provides required outbound connectivity.
- VPC endpoints are considered for supported AWS service traffic.

## Interview Scenario: Design Networking for 100 VPCs

For a large number of VPCs, a point-to-point peering mesh becomes operationally difficult.

A scalable topology is:

```text
                         Transit Gateway
                  /    /    |    \    \
                 /    /     |     \    \
              VPC 1 VPC 2  VPC 3  VPC 4 ... VPC N
```

Add:

- TGW route-table segmentation.
- Centralized network ownership.
- AWS Organizations.
- Automated VPC provisioning.
- Centralized logging.
- Controlled inspection.
- Hybrid connectivity.
- Documented IP allocation.

The design should prevent development networks from automatically gaining unrestricted access to production networks.

## Interview Scenario: Isolate Production and Development

A simple requirement is:

```text
Production
    X
Development
```

Potential controls include:

- Separate AWS accounts.
- Separate VPCs.
- Separate Transit Gateway route tables.
- Security Groups.
- IAM boundaries.
- Separate deployment pipelines.
- Controlled shared-service access.

For strong isolation requirements, separate AWS accounts generally provide a stronger administrative boundary than simply using separate subnets.

## Interview Scenario: Private Access to S3

Suppose application servers in private subnets need S3.

A NAT-based design is:

```text
EC2
 |
NAT Gateway
 |
Internet Gateway
 |
S3
```

Where supported, a VPC endpoint can provide a private service path:

```text
EC2
 |
VPC Endpoint
 |
S3
```

The design should also consider endpoint policies, route configuration, and the required DNS behavior.

## Interview Scenario: Centralized Network Inspection

Suppose an organization requires inspection between multiple VPCs.

A possible design is:

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
Firewall
  |
  v
Transit Gateway
  |
  v
VPC B
```

The critical interview point is that centralized inspection is not simply a matter of inserting a firewall.

You must design:

- Forward routing.
- Return routing.
- Route-table associations.
- Route propagation.
- Appliance scaling.
- Failure handling.
- Symmetric traffic paths where required.
- Monitoring.

Incorrect routing can cause asymmetric traffic or blackholes.

## Interview Scenario: Hybrid Network

Suppose a company has an on-premises PostgreSQL system that AWS applications must access.

A production design might be:

```text
AWS Application VPC
        |
        v
Transit Gateway
        |
        +------ Direct Connect
        |
        +------ VPN Backup
        |
        v
Corporate Network
        |
        v
PostgreSQL
```

The design should account for:

- Routing in both directions.
- CIDR compatibility.
- DNS resolution.
- Security controls.
- Connection failure.
- Failover behavior.
- Latency.
- Monitoring.

A connection that works in one direction is not sufficient.

## Architecture Decision Framework

When designing a VPC, evaluate:

| Area | Design Questions |
|---|---|
| Addressing | Is the CIDR large enough and non-overlapping? |
| Availability | How many AZs are required? |
| Routing | Which networks must communicate? |
| Security | Where are the trust boundaries? |
| Internet | Which workloads require ingress or egress? |
| AWS Services | Can endpoints reduce NAT/Internet dependency? |
| Hybrid | Is VPN or Direct Connect required? |
| Multi-VPC | Is Transit Gateway appropriate? |
| DNS | How will internal and hybrid DNS work? |
| Inspection | Does traffic require centralized inspection? |
| Observability | Can network failures be diagnosed quickly? |
| Cost | Are NAT, TGW, endpoints, and cross-AZ traffic justified? |
| DR | What happens when an AZ or Region fails? |

## Senior-Level Design Principles

### Design for Failure

Assume that:

- An Availability Zone can fail.
- A NAT Gateway can fail.
- A VPN tunnel can fail.
- A route can be misconfigured.
- A network appliance can fail.
- A deployment can introduce an incorrect rule.
- A shared networking component can become unavailable.

Design redundancy around actual failure domains.

### Minimize Blast Radius

Separate:

- Production and development.
- Internet-facing and internal workloads.
- Application and database tiers.
- High-trust and low-trust environments.
- Shared infrastructure and application workloads.

### Prefer Explicit Connectivity

Do not allow communication simply because two workloads happen to reside inside the same broad network.

Important communication paths should be intentional and documented.

### Avoid Unnecessary Network Hops

Every additional hop can introduce:

- Latency.
- Cost.
- Failure points.
- Troubleshooting complexity.

Centralized inspection and egress are useful when required, but they should not be introduced without understanding the trade-offs.

### Automate Network Infrastructure

Critical VPC infrastructure should generally be managed through Infrastructure as Code.

Common options include:

- Terraform.
- AWS CloudFormation.
- AWS CDK.

A production network should avoid uncontrolled manual changes to:

- Route tables.
- Security Groups.
- NACLs.
- Transit Gateway routes.
- VPC endpoints.

Infrastructure changes should be reviewed and deployed through a controlled CI/CD process.

## Infrastructure as Code Structure

A reasonable Terraform organization might look like:

```text
terraform/
├── modules/
│   ├── vpc/
│   ├── security-group/
│   └── transit-gateway/
│
├── environments/
│   ├── production/
│   └── development/
│
└── README.md
```

Network modules should expose meaningful configuration while keeping environment-specific values outside reusable modules.

## Production Review Checklist

Before deploying a production VPC architecture, verify:

- CIDRs do not overlap with connected networks.
- CIDRs provide enough capacity for future growth.
- Critical subnets span the required Availability Zones.
- Public and private route tables are intentional.
- Internet Gateway routes are limited to workloads that need them.
- NAT Gateway architecture matches availability requirements.
- Security Groups follow least privilege.
- NACLs do not unintentionally block return traffic.
- Database subnets have no unnecessary Internet path.
- VPC endpoints are used where they provide meaningful value.
- DNS resolution works for internal and hybrid workloads.
- Transit Gateway route tables provide intentional connectivity.
- VPN and Direct Connect paths have appropriate redundancy.
- Inspection paths support both forward and return traffic.
- Flow Logs and diagnostic tooling are available.
- NAT, Transit Gateway, endpoint, and cross-AZ costs are understood.
- Network infrastructure is reproducible through Infrastructure as Code.
- Disaster recovery requirements are explicitly documented.

## Key Takeaways

- **VPC architecture is a network design problem involving addressing, routing, security, availability, connectivity, observability, and operational ownership.**
- **CIDR planning must account for future VPCs, hybrid networks, Transit Gateway, Kubernetes, and organizational growth because overlapping address ranges can become difficult to remediate.**
- **High availability requires more than multiple subnets: critical workloads, network paths, and shared dependencies must be distributed across meaningful failure domains.**
- **Transit Gateway, VPC peering, VPC endpoints, VPN, and Direct Connect solve different connectivity problems and should be selected according to topology, scale, security, and operational requirements.**
- **Senior-level VPC design balances security, reliability, scalability, observability, simplicity, and cost instead of optimizing for only one networking property.**