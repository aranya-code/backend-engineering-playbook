# 01- Introduction to Amazon VPC

## Overview

Amazon Virtual Private Cloud (VPC) is the foundational networking boundary for workloads running in AWS. It provides an isolated, logically defined network in which backend services, databases, caches, load balancers, and other AWS resources can communicate according to explicitly configured routing and security rules.

For backend engineering, a VPC is more than an AWS networking feature. It determines how an application reaches the internet, how services communicate internally, how databases remain private, how microservices cross availability zones, and how production traffic is controlled and observed.

A typical production backend may contain:

- Public-facing load balancers
- Private application servers
- Private databases
- Redis clusters
- Internal microservices
- NAT gateways for controlled outbound internet access
- VPC endpoints for private access to AWS services
- Security groups and network ACLs
- Route tables controlling packet paths
- VPC Flow Logs for network visibility

A simplified architecture looks like this:

```mermaid
flowchart TB
    Internet["Internet"]
    IGW["Internet Gateway"]
    Public["Public Subnet"]
    Private["Private Application Subnet"]
    DB["Private Database Subnet"]
    NAT["NAT Gateway"]
    VPC["Amazon VPC"]

    Internet --> IGW
    IGW --> Public
    Public --> Private
    Private --> DB
    Private --> NAT
    NAT --> IGW

    subgraph VPC
        Public
        Private
        DB
        NAT
    end
```

The key engineering principle is that **being inside the same VPC does not automatically mean resources can communicate**. Connectivity depends on subnet routing, security controls, network interfaces, and the destination involved.

---

## What Is a VPC?

A VPC is a logically isolated virtual network dedicated to an AWS account and Region. Within a VPC, you define the network address space and configure how resources communicate with each other and with networks outside the VPC.

A VPC provides the networking foundation for services such as:

- Amazon EC2
- Amazon RDS
- Amazon ElastiCache
- Amazon ECS
- Amazon EKS
- Application Load Balancers
- Network Load Balancers
- AWS Lambda functions configured for VPC access
- Internal microservices
- Self-managed databases
- Private service endpoints

A VPC typically contains several interconnected networking components:

| Component | Primary responsibility |
|---|---|
| VPC CIDR | Defines the IP address space |
| Subnet | Divides the VPC into smaller network segments |
| Route table | Determines where network traffic is sent |
| Internet Gateway | Provides internet connectivity for eligible resources |
| NAT Gateway | Provides controlled outbound internet access from private subnets |
| Security Group | Stateful traffic filtering at the resource/network-interface level |
| Network ACL | Stateless filtering at the subnet boundary |
| VPC Endpoint | Enables private connectivity to supported AWS services |
| VPC Peering | Connects two VPCs privately |
| Transit Gateway | Provides centralized connectivity between multiple networks |
| VPC Flow Logs | Captures metadata about network traffic |

---

## Why VPC Exists

Without network isolation, backend infrastructure would have limited control over:

- Which services can communicate
- Which resources are reachable from the internet
- How application servers reach databases
- How outbound traffic leaves private networks
- How different environments are isolated
- How AWS services are accessed privately
- How networks are connected across accounts or Regions

VPC provides explicit network boundaries.

For example, consider a Django API:

```text
Client
  |
  v
Application Load Balancer
  |
  v
Django / FastAPI application
  |
  +------> PostgreSQL
  |
  +------> Redis
  |
  +------> AWS services
```

A production design should normally avoid exposing PostgreSQL or Redis directly to the public internet.

Instead:

```text
Internet
   |
   v
Public Load Balancer
   |
   v
Private Application Subnets
   |
   +----> Private Database Subnets
   |
   +----> Private Cache
   |
   +----> VPC Endpoint / NAT Gateway
```

The VPC provides the network structure required to implement this architecture.

---

## VPC Scope and Regional Boundaries

A VPC is associated with a single AWS Region.

For example:

```text
VPC
└── Region: ap-south-1
```

A VPC does not inherently span multiple AWS Regions.

A multi-Region architecture therefore requires separate VPCs:

```text
Region: ap-south-1
    |
    +-- VPC A

Region: ap-southeast-1
    |
    +-- VPC B
```

Connectivity between these environments requires an appropriate inter-Region networking architecture.

This distinction matters when designing disaster recovery or active-active systems.

---

## VPC CIDR Block

Every VPC requires an IPv4 CIDR block.

For example:

```text
10.0.0.0/16
```

This represents the VPC's primary IPv4 address space.

The CIDR determines the range of private IP addresses available for resources inside the VPC.

A `/16` provides 65,536 IPv4 addresses mathematically, although AWS reserves some addresses within each subnet.

A common production design might start with:

```text
VPC
10.0.0.0/16

    Public Subnets
    10.0.1.0/24
    10.0.2.0/24

    Application Subnets
    10.0.11.0/24
    10.0.12.0/24

    Database Subnets
    10.0.21.0/24
    10.0.22.0/24
```

The exact CIDR strategy should be designed before production deployment because changing network address architecture later can be disruptive.

### CIDR Planning Considerations

When choosing CIDR ranges, consider:

- Current workload size
- Future growth
- Number of subnets
- Availability Zones
- VPC peering
- Transit Gateway connectivity
- Hybrid connectivity
- On-premises networks
- Other AWS accounts
- Kubernetes networking requirements
- Future acquisitions or organizational network integration

A common mistake is choosing an address range without considering future network connectivity.

For example:

```text
VPC A: 10.0.0.0/16
VPC B: 10.0.0.0/16
```

Overlapping CIDRs can make direct private connectivity between these networks problematic.

---

## Subnets

A subnet is a subdivision of a VPC CIDR block.

For example:

```text
VPC
10.0.0.0/16

    Subnet A
    10.0.1.0/24

    Subnet B
    10.0.2.0/24

    Subnet C
    10.0.3.0/24
```

Subnets are associated with a single Availability Zone.

A production VPC commonly distributes subnets across multiple Availability Zones:

```mermaid
flowchart TB
    VPC["VPC 10.0.0.0/16"]

    AZ1["Availability Zone A"]
    AZ2["Availability Zone B"]

    PUB1["Public Subnet"]
    APP1["Private App Subnet"]
    DB1["Private DB Subnet"]

    PUB2["Public Subnet"]
    APP2["Private App Subnet"]
    DB2["Private DB Subnet"]

    VPC --> AZ1
    VPC --> AZ2

    AZ1 --> PUB1
    AZ1 --> APP1
    AZ1 --> DB1

    AZ2 --> PUB2
    AZ2 --> APP2
    AZ2 --> DB2
```

Subnets are therefore an important mechanism for both **network segmentation** and **availability architecture**.

---

## Public and Private Subnets

The terms public and private describe routing behavior.

A subnet is generally considered public when its route table provides a route to an Internet Gateway.

For example:

```text
Destination       Target
0.0.0.0/0         igw-xxxxxxxx
```

A private subnet does not have a direct route to an Internet Gateway.

For example:

```text
Destination       Target
0.0.0.0/0         nat-xxxxxxxx
```

The NAT Gateway allows resources in the private subnet to initiate outbound connections without directly accepting unsolicited inbound internet connections through the NAT path.

This distinction is extremely important:

> A subnet is not public merely because an EC2 instance has a public IP address. Public accessibility depends on the overall routing and security configuration.

---

## Route Tables

A route table determines where traffic leaving a subnet should be sent.

A simplified public route table might look like:

```text
Destination       Target
10.0.0.0/16       local
0.0.0.0/0         igw-xxxxxxxx
```

The `local` route allows communication within the VPC CIDR.

A private application route table might look like:

```text
Destination       Target
10.0.0.0/16       local
0.0.0.0/0         nat-xxxxxxxx
```

The important distinction is:

```text
Public subnet
    |
    +-- 0.0.0.0/0 --> Internet Gateway

Private subnet
    |
    +-- 0.0.0.0/0 --> NAT Gateway
```

Routing and security are separate concerns.

A route allowing traffic does not mean the traffic will be accepted. Security Groups and Network ACLs can still block it.

---

## Internet Gateway

An Internet Gateway (IGW) provides a VPC with a path to the public internet.

A simplified public traffic flow is:

```text
Client
   |
   v
Internet
   |
   v
Internet Gateway
   |
   v
Public Subnet
   |
   v
Resource
```

For a resource to communicate directly with the internet, the architecture must satisfy the relevant routing, addressing, and security requirements.

The Internet Gateway is horizontally scaled and managed by AWS. You do not provision individual gateway servers.

### Important Distinction

An Internet Gateway does not make every resource in the VPC publicly accessible.

Public accessibility depends on several components working together:

```text
Public IP / addressing
        +
Route table
        +
Internet Gateway
        +
Security Group
        +
Network ACL
```

If any required component is incorrectly configured, connectivity can fail.

---

## NAT Gateway

A NAT Gateway allows resources in private subnets to initiate outbound connections to external destinations.

Typical example:

```text
Private EC2
    |
    v
Private Route Table
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

This is useful when application servers need to:

- Download operating-system packages
- Call external APIs
- Access package repositories
- Retrieve public dependencies
- Communicate with third-party services

The application instances remain in private subnets.

### NAT Gateway Is Not an Inbound Gateway

A NAT Gateway is primarily used for outbound connectivity initiated by private resources.

It should not be treated as a mechanism for exposing private application servers to the internet.

---

## Security Groups

Security Groups provide stateful network access control.

For example, an application server might allow:

```text
Inbound:
TCP 443 from Load Balancer Security Group

Outbound:
Required application traffic
```

A PostgreSQL database might allow:

```text
Inbound:
TCP 5432 from Application Security Group
```

This is preferable to allowing:

```text
TCP 5432 from 0.0.0.0/0
```

Security Groups can reference other Security Groups, which makes them particularly useful for service-to-service authorization.

For example:

```text
ALB Security Group
        |
        | TCP 443
        v
Application Security Group
        |
        | TCP 5432
        v
Database Security Group
```

This expresses the architecture more accurately than maintaining large lists of IP addresses.

---

## Network ACLs

Network Access Control Lists (NACLs) provide stateless traffic filtering at the subnet level.

Unlike Security Groups, NACLs are stateless.

This means inbound and outbound traffic must be explicitly permitted where required.

Conceptually:

```text
Internet
   |
   v
Network ACL
   |
   v
Subnet
   |
   v
Resource
   |
   v
Network ACL
   |
   v
Internet
```

NACLs are useful as an additional subnet-level security boundary, but they should not be used as a replacement for carefully designed Security Groups.

A common operational mistake is introducing restrictive NACL rules without accounting for return traffic and ephemeral ports.

---

## VPC Endpoints

VPC endpoints allow supported AWS services to be accessed privately from a VPC.

This can reduce the need to send AWS service traffic through public internet paths or NAT infrastructure.

Common use cases include private access to:

- Amazon S3
- Amazon DynamoDB
- Amazon ECR
- AWS Secrets Manager
- Amazon CloudWatch
- AWS Systems Manager

For example:

```text
Private Application
       |
       v
VPC Endpoint
       |
       v
AWS Service
```

This can improve security posture and, depending on the service and architecture, reduce NAT Gateway traffic and associated costs.

---

## VPC Peering

VPC Peering provides private connectivity between two VPCs.

For example:

```text
VPC A
10.0.0.0/16
    |
    | VPC Peering
    |
VPC B
10.1.0.0/16
```

Routing must be configured appropriately in both VPCs.

VPC peering is useful for relatively simple connectivity requirements, but a large number of point-to-point peerings can become difficult to manage.

This is one reason larger organizations often use AWS Transit Gateway.

---

## Transit Gateway

AWS Transit Gateway provides a centralized network connectivity model.

Instead of maintaining many individual VPC-to-VPC connections:

```text
VPC A <----> VPC B
VPC A <----> VPC C
VPC B <----> VPC C
VPC B <----> VPC D
...
```

a centralized architecture can be used:

```text
              VPC A
                |
                |
VPC B ---- Transit Gateway ---- VPC C
                |
                |
              VPC D
```

This is particularly useful for:

- Multi-account environments
- Centralized networking
- Hybrid connectivity
- Large numbers of VPCs
- Shared services architectures

The trade-off is increased architectural complexity and the need for disciplined route management.

---

## VPC and Backend Application Architecture

A typical production Django or FastAPI architecture might look like:

```mermaid
flowchart LR
    Client["Client"]
    ALB["Application Load Balancer"]

    subgraph VPC["Amazon VPC"]
        subgraph Public["Public Subnets"]
            ALB
            NAT["NAT Gateway"]
        end

        subgraph App["Private Application Subnets"]
            API1["Django / FastAPI"]
            API2["Django / FastAPI"]
            Worker["Celery Workers"]
        end

        subgraph Data["Private Data Subnets"]
            DB["PostgreSQL / RDS"]
            Redis["Redis"]
        end
    end

    Client --> ALB
    ALB --> API1
    ALB --> API2

    API1 --> DB
    API2 --> DB

    API1 --> Redis
    API2 --> Redis

    Worker --> DB
    Worker --> Redis

    API1 --> NAT
    API2 --> NAT
```

The VPC is responsible for the network foundation, while application-level concerns remain in the application architecture.

For example:

- Django handles HTTP request processing.
- FastAPI handles API routing and validation.
- Celery handles asynchronous work.
- PostgreSQL stores persistent data.
- Redis provides caching or messaging support.
- Kafka can provide event streaming.
- Nginx or an AWS load balancer can handle traffic distribution.
- The VPC controls how these components communicate at the network layer.

---

## Request and Network Flow

Consider a client calling a production REST API.

```text
Client
  |
  | HTTPS
  v
Application Load Balancer
  |
  | HTTP/HTTPS
  v
Private Application Subnet
  |
  | TCP 5432
  v
Private PostgreSQL
```

A request can therefore cross multiple network boundaries before application code executes.

At a high level:

```mermaid
sequenceDiagram
    participant C as Client
    participant ALB as Load Balancer
    participant API as Application
    participant DB as PostgreSQL

    C->>ALB: HTTPS request
    ALB->>API: Forward request
    API->>DB: SQL query
    DB-->>API: Query result
    API-->>ALB: HTTP response
    ALB-->>C: HTTPS response
```

At each stage, the network configuration must permit the required traffic.

For example:

```text
Client
  |
  +--> ALB: TCP 443
          |
          +--> API: TCP 8000/443
                    |
                    +--> PostgreSQL: TCP 5432
```

The exact ports depend on the implementation.

---

## VPC and Microservices

In a microservices architecture, VPC design becomes particularly important because the number of network flows increases.

For example:

```text
API Gateway / ALB
       |
       v
User Service
       |
       +----> Order Service
       |
       +----> Payment Service
       |
       +----> Notification Service
                     |
                     +----> Kafka
                     |
                     +----> Redis
```

The network architecture should not blindly allow every service to communicate with every other service.

Instead, access should reflect application dependencies.

For example:

| Source | Destination | Port | Reason |
|---|---|---:|---|
| ALB | API | 443 | HTTPS traffic |
| API | PostgreSQL | 5432 | Database access |
| API | Redis | 6379 | Cache access |
| API | Kafka | 9092/9093 | Event streaming |
| Worker | PostgreSQL | 5432 | Background processing |

This creates a network-level representation of the application's dependency graph.

---

## VPC Availability and Fault Domains

A production VPC should generally distribute workloads across multiple Availability Zones.

For example:

```text
Region
|
+-- Availability Zone A
|      |
|      +-- Public Subnet
|      +-- Private App Subnet
|      +-- Private Data Subnet
|
+-- Availability Zone B
       |
       +-- Public Subnet
       +-- Private App Subnet
       +-- Private Data Subnet
```

This protects against the failure of a single Availability Zone.

For stateless application services, this commonly means running multiple instances or tasks across multiple AZs.

For stateful services, use the service's supported high-availability architecture rather than assuming that simply placing resources in separate subnets makes the application highly available.

---

## VPC and Kubernetes

Amazon EKS workloads also depend heavily on VPC networking.

A simplified architecture is:

```text
VPC
|
+-- Public Subnets
|      |
|      +-- Load Balancers
|
+-- Private Subnets
       |
       +-- EKS Nodes
       |     |
       |     +-- Pods
       |
       +-- Databases
```

Kubernetes networking introduces additional considerations such as:

- Pod IP allocation
- Node IP allocation
- Subnet capacity
- Security Groups
- Load balancer integration
- Network policies
- NAT requirements
- VPC CNI behavior
- IP exhaustion

Therefore, VPC CIDR planning becomes especially important for large EKS environments.

---

## VPC and Serverless Applications

AWS Lambda functions can be configured to access resources inside a VPC.

This is commonly required when a Lambda function needs to access private resources such as:

```text
Lambda
   |
   +----> RDS
   |
   +----> ElastiCache
   |
   +----> Internal service
```

However, putting a Lambda function inside a VPC should not be treated as an automatic security improvement.

It introduces networking considerations such as:

- Subnet selection
- Security Groups
- Outbound routing
- NAT Gateway requirements
- VPC endpoint usage
- IP address consumption

The networking design should be driven by the resources the function actually needs to access.

---

## Security Model

A production VPC should use multiple layers of network control.

A simplified model is:

```text
Internet
   |
   v
Internet Gateway
   |
   v
Route Table
   |
   v
Subnet
   |
   v
Network ACL
   |
   v
Security Group
   |
   v
Network Interface
   |
   v
Application
```

These components solve different problems.

| Layer | Responsibility |
|---|---|
| Route table | Determines traffic destination |
| Network ACL | Stateless subnet-level filtering |
| Security Group | Stateful resource-level traffic filtering |
| Application authentication | Determines application identity/permissions |
| TLS | Protects data in transit |
| IAM | Controls AWS API/resource permissions |

A common mistake is assuming that network access control replaces application authorization.

It does not.

For example, allowing TCP 443 to an API does not determine whether a user is allowed to access `/admin`.

Network security and application security are separate layers.

---

## Monitoring and Observability

Network failures can be difficult to diagnose without visibility.

VPC Flow Logs can provide metadata about traffic flowing through supported network interfaces and resources.

They can help investigate questions such as:

- Was traffic accepted?
- Was traffic rejected?
- Which source attempted the connection?
- Which destination was targeted?
- Which port was involved?
- Which network interface handled the traffic?

A typical troubleshooting process is:

```text
Application failure
      |
      v
Check application logs
      |
      v
Check DNS resolution
      |
      v
Check route tables
      |
      v
Check Security Groups
      |
      v
Check Network ACLs
      |
      v
Check VPC Flow Logs
      |
      v
Check destination service
```

VPC networking should therefore be treated as part of the application's observability architecture rather than as infrastructure that can be ignored after deployment.

---

## Production Design Considerations

### CIDR Planning

Choose address ranges with future connectivity in mind.

Avoid unnecessarily small CIDRs for environments expected to grow.

Also avoid overlapping address spaces when VPCs may eventually need to communicate.

### Availability Zones

Distribute critical workloads across multiple Availability Zones.

Do not create a production architecture where all application capacity or a critical network component exists in only one AZ without a deliberate reason.

### Private Application Workloads

Keep databases, caches, internal services, and other non-public workloads private whenever possible.

Typical architecture:

```text
Internet
   |
   v
Public Load Balancer
   |
   v
Private Application
   |
   +----> Private Database
   |
   +----> Private Redis
```

### Outbound Internet Access

Do not expose private application instances simply because they need outbound internet connectivity.

Use an appropriate outbound architecture such as:

```text
Private Subnet
    |
    v
NAT Gateway
    |
    v
Internet Gateway
```

or use VPC endpoints when the destination is a supported AWS service.

### Security Group Design

Prefer service-oriented Security Groups.

For example:

```text
alb-sg
    |
    v
api-sg
    |
    v
db-sg
```

This is usually easier to reason about than broad CIDR-based rules.

### Network Segmentation

Use subnet boundaries to create meaningful network zones.

A common pattern is:

```text
Public
    |
    +-- Load Balancers

Private Application
    |
    +-- APIs
    +-- Workers
    +-- Internal Services

Private Data
    |
    +-- Databases
    +-- Caches
```

Network segmentation should reflect security and operational requirements rather than creating subnets simply because more subnets appear more secure.

---

## Cost Considerations

VPC networking itself is not necessarily expensive, but several networking components can introduce significant costs.

Common cost areas include:

- NAT Gateway processing
- NAT Gateway hourly charges
- Transit Gateway processing
- VPC endpoint usage
- Cross-AZ data transfer
- Cross-Region data transfer
- VPN connections
- Direct Connect
- Network Firewall

NAT Gateway architecture deserves particular attention in high-volume systems.

For example:

```text
Thousands of private workloads
          |
          v
     NAT Gateway
          |
          v
      Internet
```

If a large amount of AWS service traffic can instead use appropriate VPC endpoints, the architecture may reduce unnecessary NAT traffic and improve network isolation.

Cost optimization must not compromise required security or availability.

---

## Reliability Considerations

For production systems, avoid treating the VPC as a single flat network.

Design for:

- Multiple Availability Zones
- Redundant application capacity
- Redundant network paths where required
- Controlled failure domains
- Appropriate NAT architecture
- Reliable DNS
- Observability
- Documented routing
- Tested recovery procedures

A highly available application requires more than two subnets.

You must consider the entire dependency chain:

```text
Client
  |
  v
Load Balancer
  |
  v
Application
  |
  +----> Database
  |
  +----> Cache
  |
  +----> Queue / Kafka
  |
  +----> External APIs
```

Every dependency needs an appropriate availability and failure strategy.

---

## Common Mistakes and Pitfalls

### Treating a VPC as a Security Boundary by Itself

A VPC provides network isolation, but it does not automatically secure applications.

**Better approach:** combine network controls with IAM, application authorization, encryption, secrets management, and monitoring.

### Using Overly Broad Security Group Rules

A rule such as:

```text
0.0.0.0/0 -> TCP 5432
```

can expose a database to the internet.

**Better approach:** restrict access to the required Security Group or trusted network range.

### Confusing Security Groups with Network ACLs

Security Groups are stateful; NACLs are stateless.

Treating them as interchangeable commonly causes connectivity failures.

### Using Public Subnets for Everything

Putting application servers and databases into public subnets simply because they need outbound connectivity increases the attack surface.

**Better approach:** keep internal workloads private and provide controlled outbound access.

### Ignoring CIDR Growth

A VPC that works today can become difficult to extend when its address space is poorly planned.

**Better approach:** plan for growth and future VPC connectivity before deployment.

### Ignoring Overlapping CIDRs

Overlapping networks can make VPC peering, Transit Gateway connectivity, VPN integration, or hybrid networking difficult or impossible.

### Assuming a Route Means Connectivity

A route table only determines where traffic is sent.

Connectivity also depends on:

- Security Groups
- Network ACLs
- Destination configuration
- DNS
- Network interfaces
- Service-level policies

### Forgetting Return Paths

A packet may reach its destination while the response cannot return.

Always reason about both directions of a network flow.

### Ignoring Cross-AZ Traffic

A distributed architecture can introduce cross-AZ traffic and corresponding latency and data-transfer costs.

Network placement should therefore consider both availability and traffic patterns.

---

## Practical Backend Example

Consider a FastAPI service running on EC2 or ECS.

The desired architecture is:

```text
                     Internet
                        |
                        v
              Application Load Balancer
                        |
             +----------+----------+
             |                     |
             v                     v
        App Subnet A          App Subnet B
             |                     |
             +----------+----------+
                        |
              +---------+---------+
              |                   |
              v                   v
         PostgreSQL             Redis
        Private Subnets       Private Subnets
```

Security Groups could model the relationships:

```text
alb-sg
  |
  +-- HTTPS --> api-sg

api-sg
  |
  +-- PostgreSQL --> db-sg
  |
  +-- Redis --> redis-sg
```

The application does not need direct public access.

For outbound access:

```text
api-sg resources
       |
       v
Private Route Table
       |
       v
NAT Gateway
       |
       v
Internet Gateway
       |
       v
External API
```

For AWS services that support private endpoints:

```text
Private Application
       |
       v
VPC Endpoint
       |
       v
AWS Service
```

This architecture provides clear separation between public ingress, private application execution, private data services, and controlled outbound traffic.

---

## Basic AWS CLI Inspection

The AWS CLI can be used to inspect the VPC networking configuration.

List VPCs:

```bash
aws ec2 describe-vpcs
```

List subnets:

```bash
aws ec2 describe-subnets
```

List route tables:

```bash
aws ec2 describe-route-tables
```

List Internet Gateways:

```bash
aws ec2 describe-internet-gateways
```

List NAT Gateways:

```bash
aws ec2 describe-nat-gateways
```

List Security Groups:

```bash
aws ec2 describe-security-groups
```

List Network ACLs:

```bash
aws ec2 describe-network-acls
```

List VPC endpoints:

```bash
aws ec2 describe-vpc-endpoints
```

For production troubleshooting, filtering these commands by VPC ID, subnet ID, or resource ID is preferable to inspecting large unfiltered outputs.

For example:

```bash
aws ec2 describe-subnets \
    --filters Name=vpc-id,Values=vpc-xxxxxxxx
```

---

## Engineering Mental Model

When debugging or designing a VPC, reason about a connection as a sequence:

```text
Source
  |
  v
Source Network Interface
  |
  v
Subnet
  |
  v
Route Table
  |
  v
Network Path
  |
  v
Destination Network Interface
  |
  v
Security Controls
  |
  v
Destination Service
```

For an external destination:

```text
Private Resource
      |
      v
Private Route Table
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

For an internal resource:

```text
Application
      |
      v
VPC Local Route
      |
      v
Destination Subnet
      |
      v
Destination Resource
```

For an AWS service accessed through an endpoint:

```text
Private Application
      |
      v
VPC Endpoint
      |
      v
AWS Service
```

This mental model is more useful in production than memorizing isolated AWS networking components.

---

## Senior-Level Design Perspective

At an intermediate level, VPC knowledge means understanding:

- CIDRs
- Subnets
- Route tables
- Internet Gateways
- NAT Gateways
- Security Groups
- NACLs

At a senior level, the problem becomes architectural.

You need to reason about:

- IP address planning
- Availability Zones
- Failure domains
- Network segmentation
- Cross-account networking
- Hybrid connectivity
- Transit Gateway
- Private AWS service access
- Security boundaries
- Traffic inspection
- Observability
- Cross-AZ traffic
- Cost
- Disaster recovery
- Organizational network topology

The important question is no longer:

> "What is a NAT Gateway?"

It becomes:

> "Which workloads require outbound internet access, which can use private AWS endpoints, where should NAT infrastructure live, and what happens if the associated Availability Zone fails?"

Similarly, instead of asking:

> "What is a Security Group?"

ask:

> "What are the legitimate communication paths between services, and how can the network policy enforce those dependencies without creating excessive coupling or operational complexity?"

That shift from component knowledge to **network architecture reasoning** is what makes VPC knowledge useful for senior backend engineering and system design.

## Key Takeaways

- Amazon VPC provides the foundational network boundary for AWS backend workloads, defining address space, segmentation, routing, and connectivity.
- Production VPCs should normally separate public ingress from private application and data workloads while distributing critical resources across multiple Availability Zones.
- Routing, Security Groups, Network ACLs, addressing, and destination configuration are separate concerns; successful connectivity requires the entire path to be valid.
- CIDR planning, private connectivity, outbound traffic architecture, and cross-VPC networking should be considered early because they become increasingly difficult to change after production adoption.
- Senior-level VPC design is primarily about reasoning over traffic flows, security boundaries, failure domains, scalability, observability, and cost rather than memorizing individual AWS networking components.