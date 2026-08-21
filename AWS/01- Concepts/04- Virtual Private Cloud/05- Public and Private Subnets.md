# 05- Public and Private Subnets

## Overview

Public and private subnets are logical network segments within an Amazon VPC that differ primarily in their routing behavior and intended exposure.

A **public subnet** has a route to an Internet Gateway. A **private subnet** does not have a direct route to an Internet Gateway for normal internet connectivity. Private workloads can still reach external destinations through controlled mechanisms such as a NAT Gateway or access AWS services privately through VPC endpoints.

This distinction is fundamental to production backend architecture because it determines where internet-facing components, application services, workers, databases, caches, and other infrastructure should run.

A common production topology is:

```text
                         Internet
                            |
                            v
                   Internet Gateway
                            |
                +-----------+-----------+
                |                       |
                v                       v
          Public Subnet A         Public Subnet B
                |                       |
                +-----------+-----------+
                            |
                   Load Balancer
                            |
                +-----------+-----------+
                |                       |
                v                       v
        Private App Subnet A    Private App Subnet B
                |                       |
                +-----------+-----------+
                            |
                +-----------+-----------+
                |                       |
                v                       v
        Private Data Subnet A   Private Data Subnet B
```

The core principle is:

> Public or private is primarily a property of the subnet's routing architecture, not simply a property of the resources placed inside it.

---

## Public and Private Subnets

### Public Subnet

A subnet is generally considered public when its associated route table contains a route to an Internet Gateway.

For example:

```text
Destination       Target

10.0.0.0/16       local
0.0.0.0/0         igw-xxxxxxxx
```

This gives resources in the subnet a network path toward the Internet Gateway.

A resource still requires appropriate public addressing and security configuration to be directly reachable from the internet.

### Private Subnet

A private subnet does not have a direct route to an Internet Gateway.

A common private application subnet might use:

```text
Destination       Target

10.0.0.0/16       local
0.0.0.0/0         nat-xxxxxxxx
```

The NAT Gateway provides controlled outbound internet connectivity without giving the private resource a direct inbound internet path through the NAT connection.

A highly isolated data subnet may have:

```text
Destination       Target

10.0.0.0/16       local
```

with no default internet route at all.

---

## Why the Distinction Matters

Public and private subnet separation provides a straightforward network architecture for backend systems.

For example:

```text
Internet
    |
    v
Public Load Balancer
    |
    v
Private API
    |
    +----> PostgreSQL
    |
    +----> Redis
    |
    +----> Kafka
```

The public component accepts internet traffic.

The application remains private.

The database and infrastructure services remain further isolated.

This reduces unnecessary exposure and creates explicit network boundaries.

---

## Public Subnet Routing

A typical public subnet route table contains:

```text
Destination       Target
10.0.0.0/16       local
0.0.0.0/0         Internet Gateway
```

Traffic destined for an address outside the VPC follows the default route toward the Internet Gateway.

Conceptually:

```text
Resource
   |
   v
Public Subnet
   |
   v
Route Table
   |
   v
Internet Gateway
   |
   v
Internet
```

The Internet Gateway is therefore part of the routing path, but it does not independently make every resource public.

---

## Private Subnet Routing

A private application subnet commonly uses:

```text
Destination       Target
10.0.0.0/16       local
0.0.0.0/0         NAT Gateway
```

The traffic flow becomes:

```text
Private Application
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

The application can initiate outbound connections while remaining without a direct route from the internet to its private address.

---

## Private Subnets Without Internet Access

Not every private workload needs outbound internet connectivity.

A database subnet might use:

```text
Destination       Target
10.0.0.0/16       local
```

The database can communicate with resources inside the VPC while having no default route to the internet.

For example:

```text
Private Application
        |
        | TCP 5432
        v
Private PostgreSQL
```

The database does not need to download packages, call external APIs, or access arbitrary internet destinations during normal operation.

Removing unnecessary routes is an important security and operational practice.

---

## Public Does Not Mean Insecure

A public subnet provides a path toward an Internet Gateway, but it does not automatically expose every resource.

Effective internet accessibility depends on several factors:

```text
Public subnet
      +
Route to Internet Gateway
      +
Public IPv4 addressing where required
      +
Security Group rules
      +
Network ACL rules
      +
Application behavior
```

For example, an internet-facing Application Load Balancer can be public while its backend targets remain private.

```text
Internet
   |
   v
Public ALB
   |
   v
Private API
```

This is generally preferable to giving every API instance its own public IP address.

---

## Private Does Not Mean Automatically Secure

A private subnet reduces direct internet exposure, but it is not a complete security boundary.

A private application can still have:

- Overly permissive Security Groups
- Weak application authentication
- Unrestricted internal access
- Vulnerable dependencies
- Excessive outbound access
- Compromised credentials
- Misconfigured NACLs

Security should therefore be layered:

```text
Network segmentation
        +
Security Groups
        +
NACLs where appropriate
        +
IAM
        +
TLS
        +
Application authentication
        +
Authorization
        +
Secrets management
        +
Monitoring
```

---

## Public Subnet Use Cases

Public subnets are commonly appropriate for resources that intentionally require public connectivity.

Typical examples include:

| Resource | Typical placement | Reason |
|---|---|---|
| Internet-facing ALB | Public | Accept internet traffic |
| Internet-facing NLB | Public | Accept internet traffic |
| NAT Gateway | Public | Provide outbound path for private workloads |
| Network appliance | Depends on architecture | Controlled ingress/egress |
| Bastion host | Public when used | Administrative access, although alternatives are often preferable |

The exact placement depends on the service and architecture.

---

## Private Subnet Use Cases

Private subnets are commonly used for workloads that should not be directly reachable from the public internet.

Examples:

| Workload | Typical placement |
|---|---|
| Django API | Private |
| FastAPI service | Private |
| gRPC service | Private |
| Celery worker | Private |
| ECS tasks | Private |
| EKS nodes | Private |
| PostgreSQL | Private |
| Redis | Private |
| Kafka | Private |
| Internal microservices | Private |

The goal is to minimize direct exposure and force communication through controlled network paths.

---

## Typical Three-Tier Architecture

A common backend architecture uses three logical tiers:

```text
Public Tier
    |
    +-- Load Balancer
    +-- NAT Gateway

Application Tier
    |
    +-- Django
    +-- FastAPI
    +-- gRPC
    +-- Celery
    +-- Internal Services

Data Tier
    |
    +-- PostgreSQL
    +-- Redis
    +-- Kafka
```

The corresponding VPC structure might be:

```text
VPC
|
+-- AZ A
|   |
|   +-- Public Subnet
|   +-- Private App Subnet
|   +-- Private Data Subnet
|
+-- AZ B
    |
    +-- Public Subnet
    +-- Private App Subnet
    +-- Private Data Subnet
```

This provides both segmentation and Availability Zone distribution.

---

## Production Architecture

A production API architecture can be represented as:

```mermaid
flowchart TB
    Internet["Internet"]

    subgraph VPC["Amazon VPC"]
        subgraph Public["Public Subnets"]
            ALB["Application Load Balancer"]
            NAT_A["NAT Gateway A"]
            NAT_B["NAT Gateway B"]
        end

        subgraph App["Private Application Subnets"]
            API_A["Django / FastAPI A"]
            API_B["Django / FastAPI B"]
            WORKER_A["Celery Worker A"]
            WORKER_B["Celery Worker B"]
        end

        subgraph Data["Private Data Subnets"]
            DB["PostgreSQL"]
            REDIS["Redis"]
            KAFKA["Kafka"]
        end

        ENDPOINTS["VPC Endpoints"]
    end

    Internet --> ALB

    ALB --> API_A
    ALB --> API_B

    API_A --> DB
    API_B --> DB

    API_A --> REDIS
    API_B --> REDIS

    WORKER_A --> DB
    WORKER_B --> DB

    API_A --> KAFKA
    API_B --> KAFKA

    API_A --> NAT_A
    API_B --> NAT_B

    API_A --> ENDPOINTS
    API_B --> ENDPOINTS
```

This architecture separates public ingress from private application execution and private data services.

---

## Public Load Balancer With Private Applications

One of the most important patterns is:

```text
Internet
    |
    v
Public Application Load Balancer
    |
    +-------------------+
    |                   |
    v                   v
Private API A       Private API B
```

The load balancer handles internet-facing connectivity.

The application instances or containers do not need public IP addresses.

This provides several advantages:

- Smaller public attack surface
- Centralized TLS termination where appropriate
- Centralized routing
- Easier horizontal scaling
- Better workload isolation
- Simpler Security Group design

A common Security Group relationship is:

```text
ALB Security Group
        |
        | TCP 443
        v
Application Security Group
```

The application Security Group can allow traffic from the ALB Security Group rather than allowing arbitrary internet CIDRs.

---

## NAT Gateway and Private Subnets

Private application workloads frequently need outbound internet access.

For example, a FastAPI service may need to call:

```text
https://api.example.com
```

The flow can be:

```text
FastAPI
   |
   v
Private App Subnet
   |
   v
Route Table
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

The external service sees the NAT Gateway's public address rather than the application's private IP.

This is useful for third-party allowlisting.

---

## NAT Gateway High Availability

A production design should consider NAT Gateway placement across Availability Zones.

A centralized architecture may look like:

```text
AZ A App
    |
    +------+
           |
           v
        NAT A
           |
           v
        Internet

AZ B App
    |
    +------+
           |
           v
        NAT A
```

This can create a cross-AZ dependency for AZ B.

A more AZ-isolated architecture is:

```text
AZ A App
    |
    v
NAT A
    |
    v
Internet

AZ B App
    |
    v
NAT B
    |
    v
Internet
```

The second architecture generally improves AZ isolation but introduces additional NAT Gateway cost.

The appropriate choice depends on:

- Availability requirements
- Outbound traffic volume
- Cost
- Failure behavior
- Operational simplicity

---

## VPC Endpoints and Private Subnets

Private workloads may need to communicate with AWS services.

For example:

```text
Django
   |
   v
S3
```

Instead of routing that traffic through a NAT Gateway, a supported VPC endpoint can provide private access.

```text
Private Django
       |
       v
VPC Endpoint
       |
       v
Amazon S3
```

This can provide:

- Private service connectivity
- Reduced dependence on NAT
- More explicit network controls
- Potential cost savings

VPC endpoints should be evaluated based on actual service requirements and traffic patterns.

---

## Private Data Subnets

Database and stateful infrastructure should generally remain private.

Example:

```text
Private App Subnet
       |
       | TCP 5432
       v
Private Data Subnet
       |
       v
PostgreSQL
```

The database Security Group should permit access only from the required application Security Group.

For example:

```text
Database Security Group

Inbound:
TCP 5432
Source: application-sg
```

Avoid:

```text
TCP 5432
Source: 0.0.0.0/0
```

The latter unnecessarily exposes the database to public networks when the database does not require public access.

---

## Security Group Design

A public/private subnet architecture works best when Security Groups represent application relationships.

For example:

```text
Internet
    |
    v
ALB
    |
    | HTTPS
    v
API
    |
    +---- TCP 5432 ----> PostgreSQL
    |
    +---- TCP 6379 ----> Redis
    |
    +---- Kafka --------> Kafka
```

Security Groups can represent:

```text
alb-sg
    |
    v
api-sg
    |
    +---> db-sg
    |
    +---> redis-sg
    |
    +---> kafka-sg
```

This is generally more maintainable than allowing entire VPC CIDR ranges between all tiers.

---

## Network ACLs

NACLs operate at the subnet level.

A production design may therefore have:

```text
Public Subnet
    |
    +-- Public NACL

Private Application Subnet
    |
    +-- Application NACL

Private Data Subnet
    |
    +-- Data NACL
```

NACLs are stateless.

This means both directions must be considered.

For example:

```text
Application
   |
   | TCP request
   v
Database
   |
   | TCP response
   v
Application
```

The relevant NACL rules must permit the necessary traffic in both directions.

Do not introduce complicated NACL rules without testing the complete traffic flow.

---

## Route Table Design

A clean architecture often uses separate route tables for different subnet tiers.

```text
Public Route Table
    |
    +-- Public Subnet A
    +-- Public Subnet B

Private App Route Table A
    |
    +-- App Subnet A

Private App Route Table B
    |
    +-- App Subnet B

Private Data Route Table
    |
    +-- Data Subnet A
    +-- Data Subnet B
```

For high-availability NAT architecture, separate application route tables per AZ can be useful:

```text
App Route Table A
0.0.0.0/0 -> NAT A

App Route Table B
0.0.0.0/0 -> NAT B
```

This keeps each application subnet on its local NAT path.

---

## Public and Private Subnet Traffic Flows

### Internet Ingress

```text
Internet
   |
   v
Internet Gateway
   |
   v
Public Subnet
   |
   v
Load Balancer
   |
   v
Private Application
```

### Private Application to Database

```text
Private Application
   |
   v
Local VPC Route
   |
   v
Private Data Subnet
   |
   v
Database
```

### Private Application to Internet

```text
Private Application
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

### Private Application to AWS Service

```text
Private Application
   |
   v
VPC Endpoint
   |
   v
AWS Service
```

These four flows cover many production backend networking scenarios.

---

## Public vs Private Subnet Comparison

| Characteristic | Public Subnet | Private Subnet |
|---|---|---|
| Route to Internet Gateway | Typically yes | No direct internet route |
| Typical purpose | Public ingress/egress infrastructure | Internal workloads |
| Internet-facing ALB | Yes | No, for an internet-facing ALB |
| Django/FastAPI | Usually no | Yes |
| PostgreSQL | Usually no | Yes |
| Redis | Usually no | Yes |
| Celery | Usually no | Yes |
| NAT Gateway | Yes | No |
| Direct public addressing | Possible | Generally avoided |
| Outbound internet | Through IGW | Commonly through NAT |
| AWS service access | Internet/NAT or endpoint | Endpoint or NAT |
| Exposure | Higher | Lower |

These are typical patterns rather than absolute service-placement rules.

---

## Public and Private Subnets in Kubernetes

EKS commonly uses public and private subnets together.

A common architecture is:

```text
Public Subnets
    |
    +-- AWS Load Balancers

Private Subnets
    |
    +-- EKS Nodes
    +-- Pods
```

For example:

```text
Internet
    |
    v
Public Load Balancer
    |
    v
Private EKS Service
    |
    v
Pod
```

Private worker nodes can use NAT for outbound access or VPC endpoints for supported AWS services.

Subnet IP capacity is particularly important because Kubernetes can consume large numbers of addresses.

---

## Public and Private Subnets With ECS

A typical ECS architecture is:

```text
Public Subnets
    |
    +-- Application Load Balancer

Private Subnets
    |
    +-- ECS Tasks
    +-- Workers
```

Traffic:

```text
Client
   |
   v
ALB
   |
   v
ECS Task
```

The ECS tasks remain private.

If tasks need outbound internet access:

```text
ECS Task
   |
   v
NAT Gateway
   |
   v
Internet
```

This is a common production pattern for containerized APIs.

---

## Public and Private Subnets With Django

A production Django application could use:

```text
Internet
   |
   v
Application Load Balancer
   |
   v
Private Django instances
   |
   +----> RDS PostgreSQL
   |
   +----> ElastiCache Redis
   |
   +----> Celery workers
```

The Django application should not need a public IP simply because users access the application from the internet.

The load balancer provides the public entry point.

---

## Public and Private Subnets With gRPC

Internal gRPC services are often appropriate for private subnets.

For example:

```text
REST API
   |
   | gRPC
   v
Internal Service
```

Both services can remain private.

A public load balancer may handle external HTTPS traffic while an internal load balancer or service-discovery mechanism handles internal service communication.

This provides a clean separation:

```text
External traffic
    |
    v
Public Load Balancer
    |
    v
Private API

Internal traffic
    |
    v
Private Service
```

---

## Subnet Isolation vs Application Isolation

Subnet separation should not be confused with application isolation.

For example:

```text
Private Application Subnet
    |
    +-- Service A
    +-- Service B
    +-- Service C
```

All three services may still communicate if their routing and Security Groups allow it.

If stronger isolation is required, combine:

- Security Groups
- Network policies where applicable
- IAM
- Service authorization
- Separate subnets when justified
- Separate VPCs when required

Subnet boundaries are one layer of architecture, not the complete security model.

---

## Common Mistake: Putting the API in a Public Subnet

A common early design is:

```text
Internet
   |
   v
EC2
Django
Public IP
```

This works, but exposes the application host directly.

A production architecture can instead use:

```text
Internet
   |
   v
Public ALB
   |
   v
Private Django
```

The public surface becomes smaller and traffic management becomes centralized.

---

## Common Mistake: Putting the Database in a Public Subnet

This is usually unnecessary.

The application can communicate with a private database over the VPC's internal routing.

```text
Application
    |
    v
Private Data Subnet
    |
    v
PostgreSQL
```

A database does not need a public route simply because the application is internet-facing.

---

## Common Mistake: Assuming NAT Provides Inbound Access

A NAT Gateway is designed primarily for outbound connectivity from private resources.

It should not be treated as:

```text
Internet
   |
   v
NAT Gateway
   |
   v
Private Server
```

for exposing private servers.

Use a load balancer or another deliberate ingress architecture instead.

---

## Common Mistake: One NAT Gateway for Everything

A single NAT Gateway may be simple and inexpensive for small environments, but it creates an AZ dependency and can introduce cross-AZ traffic.

For production environments with significant availability requirements, evaluate per-AZ NAT architecture.

---

## Common Mistake: Making Everything Private Without an Egress Plan

Private workloads frequently still need to access:

- External APIs
- Package repositories
- AWS services
- Container registries
- Monitoring endpoints

A private subnet without an appropriate egress architecture can cause deployment and runtime failures.

Before moving a workload to a private subnet, identify its outbound dependencies.

---

## Common Mistake: Allowing Entire VPC CIDR Ranges

A rule such as:

```text
10.0.0.0/16 -> TCP 5432
```

may allow every workload in the VPC to reach PostgreSQL.

Prefer a specific Security Group relationship when possible:

```text
api-sg -> db-sg
TCP 5432
```

This better represents the intended dependency.

---

## Security Architecture

A strong production design can be represented as:

```mermaid
flowchart LR
    Internet["Internet"]

    IGW["Internet Gateway"]

    ALB["Public ALB"]

    APP["Private Application"]

    DB["Private Database"]

    SG1["ALB Security Group"]
    SG2["Application Security Group"]
    SG3["Database Security Group"]

    Internet --> IGW
    IGW --> ALB
    ALB --> APP
    APP --> DB

    SG1 -.-> ALB
    SG2 -.-> APP
    SG3 -.-> DB
```

The network controls should reflect the actual application dependency graph.

For example:

```text
Internet -> ALB
ALB -> API
API -> Database
API -> Redis
```

not:

```text
Internet -> Everything
```

---

## Monitoring

Public/private subnet architecture should be observable.

Useful monitoring signals include:

- VPC Flow Logs
- NAT Gateway traffic
- NAT Gateway errors
- Subnet IP availability
- Load balancer health
- Network interface usage
- Security Group changes
- NACL changes
- Route table changes
- Cross-AZ traffic

For example, a sudden increase in NAT traffic may indicate:

```text
Unexpected outbound dependency
        |
        v
Higher NAT cost
        |
        v
Potential security concern
```

Monitoring should therefore cover both reliability and security.

---

## Cost Considerations

Public/private subnet architecture itself does not directly create a major subnet charge.

The associated components can create significant costs.

Important considerations include:

- NAT Gateway hourly charges
- NAT Gateway data processing
- Cross-AZ data transfer
- VPC endpoint costs
- Load balancer costs
- Transit Gateway traffic
- Network appliance processing

A centralized NAT architecture may be cheaper in some low-volume environments:

```text
AZ A App ----+
             |
AZ B App ----+--> NAT Gateway
             |
AZ C App ----+
```

but may introduce cross-AZ traffic and a larger failure domain.

A per-AZ design:

```text
AZ A App --> NAT A
AZ B App --> NAT B
AZ C App --> NAT C
```

usually provides better AZ isolation at greater cost.

---

## Reliability Considerations

Public and private subnet design should support the desired application failure model.

For a multi-AZ application:

```text
AZ A
|
+-- Public Subnet
+-- Private App Subnet
+-- Private Data Subnet

AZ B
|
+-- Public Subnet
+-- Private App Subnet
+-- Private Data Subnet
```

Application traffic can continue if one AZ becomes unavailable, provided the load balancer, application capacity, database architecture, and other dependencies are also designed for that failure.

Subnet redundancy alone does not guarantee application high availability.

---

## Disaster Recovery Considerations

A DR environment should preserve the intended public/private separation.

For example:

```text
Primary Region
|
+-- Public Subnets
+-- Private App Subnets
+-- Private Data Subnets

DR Region
|
+-- Public Subnets
+-- Private App Subnets
+-- Private Data Subnets
```

The DR network should also have:

- Sufficient IP capacity
- Required route tables
- Required NAT or endpoint architecture
- Security Groups
- NACLs where applicable
- DNS configuration
- Connectivity to dependent services

A DR application that cannot reach its database or external dependencies is not operationally useful.

---

## AWS CLI Inspection

List subnets:

```bash
aws ec2 describe-subnets
```

Filter subnets for a VPC:

```bash
aws ec2 describe-subnets \
    --filters Name=vpc-id,Values=vpc-xxxxxxxx
```

Inspect route tables:

```bash
aws ec2 describe-route-tables \
    --filters Name=vpc-id,Values=vpc-xxxxxxxx
```

Inspect Internet Gateways:

```bash
aws ec2 describe-internet-gateways \
    --filters Name=attachment.vpc-id,Values=vpc-xxxxxxxx
```

Inspect NAT Gateways:

```bash
aws ec2 describe-nat-gateways \
    --filter Name=vpc-id,Values=vpc-xxxxxxxx
```

Inspect subnet capacity:

```bash
aws ec2 describe-subnets \
    --subnet-ids subnet-xxxxxxxx \
    --query 'Subnets[].{Subnet:SubnetId,CIDR:CidrBlock,AZ:AvailabilityZone,AvailableIPs:AvailableIpAddressCount}'
```

Inspect Network ACLs:

```bash
aws ec2 describe-network-acls \
    --filters Name=vpc-id,Values=vpc-xxxxxxxx
```

These commands are useful when determining whether a subnet is actually public/private and diagnosing connectivity problems.

---

## Troubleshooting Public Subnet Connectivity

If a resource expected to be internet-accessible cannot receive traffic, check:

```text
Resource
   |
   v
Public Subnet
   |
   +-- Route Table
   |      |
   |      +-- 0.0.0.0/0 -> IGW
   |
   +-- Network ACL
   |
   +-- Security Group
   |
   +-- Public IPv4 / Elastic IP
   |
   v
Internet Gateway
```

Verify each layer.

A route to the Internet Gateway alone does not guarantee successful connectivity.

---

## Troubleshooting Private Subnet Outbound Connectivity

For a private application that cannot reach the internet:

```text
Application
    |
    v
Private Subnet
    |
    v
Route Table
    |
    v
NAT Gateway
    |
    v
Public Subnet
    |
    v
Internet Gateway
    |
    v
Internet
```

Check:

1. The private subnet's route table.
2. The default route.
3. The NAT Gateway state.
4. The NAT Gateway's subnet.
5. The public subnet route to the Internet Gateway.
6. NAT Gateway networking and address configuration.
7. Security Groups.
8. NACL rules.
9. DNS resolution.
10. The destination service.

Do not immediately modify Security Groups without first verifying the route.

---

## Troubleshooting Private Application to Database

For:

```text
API -> PostgreSQL
```

identify:

```text
API IP
API subnet
API route table
API Security Group
API NACL

Database IP
Database subnet
Database route table
Database Security Group
Database NACL
```

The expected path is usually:

```text
API
 |
 v
VPC local route
 |
 v
Database subnet
 |
 v
Database ENI
 |
 v
Database Security Group
 |
 v
PostgreSQL
```

A NAT Gateway should not be required for normal communication between resources in the same VPC.

---

## Infrastructure as Code

Public and private subnet definitions should generally be managed through Infrastructure as Code.

A simplified Terraform example:

```hcl
resource "aws_subnet" "public_a" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "ap-south-1a"
  map_public_ip_on_launch = true

  tags = {
    Name = "public-a"
    Tier = "public"
  }
}

resource "aws_subnet" "private_app_a" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.11.0/20"
  availability_zone = "ap-south-1a"

  tags = {
    Name = "private-app-a"
    Tier = "application"
  }
}
```

`map_public_ip_on_launch` influences whether public IPv4 addresses are automatically assigned to eligible instances launched into the subnet. It does not by itself make the subnet public.

The route table association and Internet Gateway route remain fundamental to public subnet behavior.

---

## Senior-Level Design Perspective

At an intermediate level, the distinction is:

```text
Public = route to Internet Gateway
Private = no direct route to Internet Gateway
```

At a senior level, the question becomes:

> Which workloads should be reachable from the internet, which workloads require outbound connectivity, and which network paths should exist between each tier?

A senior engineer should reason about the complete dependency graph:

```text
Internet
    |
    v
Public Ingress
    |
    v
Private Application
    |
    +----> Private Database
    |
    +----> Private Cache
    |
    +----> Private Kafka
    |
    +----> VPC Endpoint
    |
    +----> NAT Gateway
```

Each path should have an explicit purpose.

For every connection, evaluate:

- Source
- Destination
- Protocol
- Port
- Route
- Security Group
- NACL
- DNS
- Availability
- Cost
- Failure behavior

This turns public/private subnet design from a memorized AWS concept into an architectural discipline.

---

## Interview Traps

### What makes a subnet public?

A subnet is generally public when its route table has a route to an Internet Gateway.

### Does assigning a public IP make a subnet public?

No. Public subnet behavior primarily depends on routing. Public addressing is another requirement for direct public IPv4 communication.

### Can a private subnet access the internet?

Yes. A private subnet can use a NAT Gateway for outbound connectivity.

### Can a private subnet access AWS services without NAT?

Yes, where an appropriate VPC endpoint is available and configured.

### Should databases normally be in public subnets?

No. Databases generally belong in private data subnets unless a specific architecture requires otherwise.

### Can a public ALB send traffic to private instances?

Yes. This is a common production architecture.

### Does NAT Gateway provide inbound access to private instances?

No. NAT Gateway is primarily used for outbound connectivity initiated by private resources.

### Why might a private subnet still need a route table?

Every subnet uses a route table to determine traffic paths, even when the subnet has no internet route.

### Why deploy public and private subnets across multiple AZs?

To distribute workloads across failure domains and improve availability.

### Why can centralized NAT be problematic?

It can introduce cross-AZ traffic, additional latency/cost, and an AZ dependency.

### Is a private subnet a complete security boundary?

No. Private routing reduces exposure but does not replace Security Groups, NACLs, IAM, encryption, or application-level authorization.

## Key Takeaways

- Public and private subnet behavior is primarily determined by routing: public subnets have a path to an Internet Gateway, while private subnets do not have a direct internet route.
- A common production architecture places load balancers and NAT Gateways in public subnets while keeping APIs, workers, databases, caches, and internal services in private subnets.
- Private workloads can obtain controlled outbound access through NAT Gateways or private AWS service access through VPC endpoints without becoming directly internet-facing.
- High-availability subnet architecture requires multiple Availability Zones, sufficient IP capacity, deliberate NAT placement, consistent routing, and carefully scoped Security Groups.
- Public/private subnet design should be based on explicit traffic flows and dependency requirements rather than simply classifying resources as "public" or "private."