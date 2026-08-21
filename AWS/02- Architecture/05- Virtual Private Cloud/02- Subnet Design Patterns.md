# 02- Subnet Design Patterns

## Overview

Subnet design is the mechanism used to segment a VPC into distinct network zones with different routing, security, availability, and workload responsibilities.

A good subnet architecture does more than divide a CIDR range. It establishes boundaries around application tiers, failure domains, network exposure, and future capacity.

For production backend systems, subnet design should answer:

- Which workloads need public connectivity?
- Which workloads must remain private?
- Which resources require outbound internet access?
- Which resources should communicate only inside the VPC?
- How should workloads be distributed across Availability Zones?
- How much IP capacity is required today and in the future?
- Which AWS services require private endpoints?
- How will Kubernetes, ECS, databases, and load balancers consume addresses?
- How will routing and security policies differ between workload classes?

A common production pattern is:

```text
                         Internet
                            |
                            v
                    Internet Gateway
                            |
              +-------------+-------------+
              |                           |
        Public Subnet A             Public Subnet B
              |                           |
              |                       NAT Gateway
              |                           |
              +-------------+-------------+
                            |
                  Application Load Balancer
                            |
              +-------------+-------------+
              |                           |
      Private App Subnet A        Private App Subnet B
              |                           |
        Django / FastAPI             Django / FastAPI
        Celery / Workers             Celery / Workers
              |                           |
              +-------------+-------------+
                            |
              +-------------+-------------+
              |                           |
       Private Data A              Private Data B
              |                           |
        PostgreSQL / Redis        PostgreSQL / Redis
```

The exact design depends on the workload. There is no universally correct number of subnet tiers.

---

## Subnet Design Principles

A production subnet strategy should follow several principles.

### Separate by Network Responsibility

Resources with materially different network requirements should not automatically share the same subnet.

For example:

```text
Public
  |
  +-- Load Balancers

Private Application
  |
  +-- Django
  +-- FastAPI
  +-- Celery
  +-- Microservices

Private Data
  |
  +-- PostgreSQL
  +-- Redis
  +-- Kafka
```

This creates clearer routing and security boundaries.

### Design Around Availability Zones

Subnets exist within a single Availability Zone.

A subnet cannot span multiple AZs.

Therefore, high-availability architectures normally create corresponding subnet sets in multiple AZs.

```text
VPC
 |
 +-- AZ A
 |    |
 |    +-- Public
 |    +-- Private App
 |    +-- Private Data
 |
 +-- AZ B
      |
      +-- Public
      +-- Private App
      +-- Private Data
```

### Preserve Future Capacity

Subnet CIDRs are difficult to change casually after production workloads are deployed.

Leave enough address space for:

- Application scaling
- Additional instances
- Load balancers
- VPC endpoints
- ECS tasks
- Kubernetes pods
- NAT-related infrastructure
- Future services
- Additional AZs
- Migration projects

---

## Public and Private Subnet Pattern

The most common backend architecture uses public and private subnets.

### Public Subnet

A public subnet has a route to an Internet Gateway.

Example:

```text
Destination       Target
10.0.0.0/16      local
0.0.0.0/0        Internet Gateway
```

Resources placed there can potentially communicate with the internet when they also have suitable public addressing and security configuration.

Typical workloads include:

- Application Load Balancers
- Network Load Balancers when public exposure is required
- NAT Gateways

### Private Subnet

A private subnet does not have a direct route to an Internet Gateway for general outbound internet access.

It may instead use:

```text
0.0.0.0/0 -> NAT Gateway
```

Typical workloads include:

- Django applications
- FastAPI services
- gRPC services
- Celery workers
- ECS tasks
- EKS nodes
- Internal services

The distinction is therefore primarily about routing, not the name assigned to the subnet.

---

## Three-Tier Subnet Pattern

A three-tier network separates public, application, and data workloads.

```text
                    Internet
                       |
                       v
                Public Subnets
                       |
                       v
             Application Subnets
                       |
                       v
                 Data Subnets
```

Example:

| Tier | Example CIDR | Typical Workloads | Internet Exposure |
|---|---|---|---|
| Public | `10.0.0.0/20` | ALB, NAT | Controlled |
| Application | `10.0.16.0/20` | Django, FastAPI, workers | Private |
| Data | `10.0.32.0/20` | PostgreSQL, Redis | Private |
| Reserved | `10.0.48.0/20` | Future workloads | None |

The CIDRs are examples rather than mandatory values.

---

## Two-Tier Subnet Pattern

Not every application needs a dedicated data subnet.

A smaller architecture may use:

```text
Public
  |
  +-- Load Balancer

Private
  |
  +-- Application
  +-- Database
  +-- Redis
```

This reduces operational complexity but provides less network segmentation.

A two-tier design can be appropriate for:

- Small internal applications
- Development environments
- Low-complexity systems
- Early-stage services

For mature production environments, stronger segmentation may be justified.

---

## Four-Tier and Specialized Patterns

Large systems may require more segmentation.

Example:

```text
Public
  |
  +-- Load Balancers

Ingress
  |
  +-- Reverse Proxies
  +-- API Gateways

Application
  |
  +-- REST APIs
  +-- gRPC Services
  +-- Workers

Data
  |
  +-- PostgreSQL
  +-- Redis
  +-- Kafka

Management
  |
  +-- Administrative Services
  +-- Bastion / Access Infrastructure
```

However, subnet proliferation should be avoided unless each subnet has a meaningful architectural purpose.

More subnets increase:

- Route table management
- Security policy complexity
- IP allocation requirements
- Troubleshooting effort
- Infrastructure-as-Code complexity

---

## Availability Zone Subnet Pattern

A production application should normally distribute stateless workloads across multiple AZs.

Example:

```text
VPC: 10.0.0.0/16

AZ A
├── Public A       10.0.0.0/20
├── App A          10.0.16.0/20
└── Data A         10.0.32.0/20

AZ B
├── Public B       10.0.48.0/20
├── App B          10.0.64.0/20
└── Data B         10.0.80.0/20
```

This allows application infrastructure to survive an AZ-level failure when the application and dependent services are designed appropriately.

---

## Why Subnets Are AZ-Scoped

An AWS subnet belongs to exactly one Availability Zone.

This has an important architectural consequence:

```text
Subnet A
   |
   +-- AZ A

Subnet B
   |
   +-- AZ B
```

You cannot create:

```text
Subnet A
   |
   +-- AZ A
   +-- AZ B
```

Therefore, "multi-AZ subnet architecture" actually means multiple corresponding subnets, one or more in each AZ.

---

## Symmetric Subnet Layout

A common production pattern is to keep the subnet structure symmetric across AZs.

```text
              VPC
               |
       +-------+-------+
       |               |
      AZ A            AZ B
       |               |
   +---+---+       +---+---+
   |   |   |       |   |   |
  PUB APP DATA    PUB APP DATA
```

Symmetry makes:

- Routing easier to understand
- Terraform modules easier to maintain
- Failover more predictable
- Operational troubleshooting simpler
- Resource placement more consistent

For example, if application subnet A uses a NAT Gateway in AZ A, application subnet B can use a corresponding NAT Gateway in AZ B.

---

## NAT-Aware Subnet Design

Private application subnets often need outbound internet access.

A common architecture is:

```text
AZ A
Private App A
    |
    v
NAT Gateway A
    |
    v
Internet Gateway

AZ B
Private App B
    |
    v
NAT Gateway B
    |
    v
Internet Gateway
```

This avoids making AZ B dependent on NAT infrastructure in AZ A.

An alternative is:

```text
Private App A ----+
                  |
                  v
              NAT Gateway A
                  |
                  v
              Internet Gateway
                  ^
                  |
              NAT Gateway B
                  |
Private App B ----+
```

The choice involves an availability-versus-cost tradeoff.

---

## Single NAT Gateway Pattern

A cost-sensitive environment may use one NAT Gateway:

```text
Private A ----+
              |
              v
          NAT Gateway
              |
              v
        Internet Gateway
              ^
              |
Private B ----+
```

### Advantages

- Lower NAT hourly cost
- Simpler architecture
- Fewer NAT resources

### Limitations

- Creates a concentrated dependency
- Can cause cross-AZ traffic
- AZ failure can affect private subnet egress
- May increase cross-AZ data transfer costs

This pattern can be acceptable for development or environments where reduced availability is an explicit tradeoff.

---

## NAT Gateway per AZ Pattern

For production workloads where AZ isolation matters:

```text
             Internet Gateway
              /            \
             /              \
          NAT A            NAT B
            |                |
         App A             App B
```

Each private subnet uses the NAT Gateway in its own AZ.

### Advantages

- Better AZ isolation
- Reduced dependency on another AZ
- Lower cross-AZ NAT traffic
- More predictable failure behavior

### Limitations

- Higher hourly cost
- More infrastructure
- More route tables or routes to manage

This is often the preferred architecture for critical production systems.

---

## Isolated Subnet Pattern

Some workloads should have no internet route at all.

Example:

```text
Application
    |
    v
Private Data Subnet
    |
    +-- Local VPC traffic
    +-- Required private endpoints
```

Typical candidates include:

- Databases
- Sensitive internal services
- Internal control-plane workloads
- Some stateful systems

An isolated subnet should not automatically be given:

```text
0.0.0.0/0 -> NAT Gateway
```

just because another private subnet uses one.

Give each subnet only the connectivity its workloads require.

---

## Application and Data Subnet Separation

Separating application and data workloads provides a clear security boundary.

```text
Application SG
      |
      | TCP 5432
      v
Database SG
```

The database subnet does not need to be directly accessible from:

- The internet
- Public subnets
- Unrelated application services

A typical route architecture is:

```text
Application Subnet
       |
       +---- local VPC route ----> Database Subnet
```

The Security Group determines whether the specific connection is allowed.

---

## Database Subnet Groups

Managed AWS database services commonly use subnet groups.

For example, a production database architecture may select private subnets across multiple AZs:

```text
DB Subnet Group
 |
 +-- Private Data A
 |
 +-- Private Data B
 |
 +-- Private Data C
```

The database service can then use the selected subnets according to its availability architecture.

Do not confuse a DB subnet group with a subnet itself.

A DB subnet group is a collection of subnets used by a managed database service.

---

## Load Balancer Subnet Pattern

Public Application Load Balancers should generally use subnets across multiple AZs.

```text
                   Internet
                      |
                      v
                    ALB
                 /       \
                /         \
          Public A       Public B
```

The ALB then routes to private application targets:

```text
ALB
 |
 +----> App A
 |
 +----> App B
```

This avoids requiring the application instances themselves to have public IP addresses.

---

## Internal Load Balancer Pattern

Internal services can use internal load balancers.

```text
Service A
    |
    v
Internal ALB
    |
 +--+--+
 |     |
 v     v
Svc B  Svc C
```

This is useful for:

- Internal REST APIs
- gRPC services
- Microservices
- Private administrative APIs

The load balancer remains reachable only through private network paths.

---

## Microservice Subnet Strategy

Do not create one subnet per microservice by default.

For example, this is usually unnecessary:

```text
Subnet A -> User Service
Subnet B -> Payment Service
Subnet C -> Order Service
Subnet D -> Inventory Service
```

Security Groups can often provide sufficient service-level isolation.

A more scalable design is:

```text
Private Application Subnets
 |
 +-- User Service
 +-- Payment Service
 +-- Order Service
 +-- Inventory Service
```

with Security Groups defining allowed relationships.

Use dedicated subnets when there is a genuine network-level requirement.

---

## Security Group-Oriented Segmentation

Subnet segmentation and Security Group segmentation solve different problems.

Example:

```text
                 Private App Subnet
                        |
          +-------------+-------------+
          |             |             |
       API SG        Worker SG     Admin SG
          |             |             |
          v             v             v
       API Pods       Workers       Admin
```

The subnet provides a network placement boundary.

The Security Group controls traffic to individual network interfaces.

A production architecture usually needs both.

---

## Kubernetes Subnet Design

Kubernetes can dramatically increase IP consumption.

A simplified EKS architecture:

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
        +-- Pods
```

Depending on the networking model, pods may consume VPC IP addresses.

Therefore, subnet capacity must account for:

```text
Nodes
+
Pods
+
DaemonSets
+
Load Balancers
+
VPC Endpoints
+
Scaling Headroom
```

This is one reason Kubernetes VPC planning should happen before the cluster reaches production scale.

---

## ECS Subnet Design

ECS tasks using VPC networking can also consume subnet IP addresses.

For example:

```text
Private App Subnet
 |
 +-- ECS Task
 +-- ECS Task
 +-- ECS Task
 +-- ECS Task
```

As the service scales horizontally, IP consumption increases.

If a subnet has insufficient available addresses, ECS task placement can fail even when CPU and memory capacity remain available.

Therefore, subnet capacity is an infrastructure scaling constraint.

---

## VPC Endpoint Impact

Interface VPC endpoints create Elastic Network Interfaces in selected subnets.

For example:

```text
Private App Subnet
 |
 +-- Application ENIs
 +-- Endpoint ENI
 +-- Endpoint ENI
 +-- Endpoint ENI
```

Large endpoint deployments can therefore consume meaningful subnet IP capacity.

When planning subnets, account for:

- Interface endpoints
- Load balancer ENIs
- ECS tasks
- EKS pods
- Application instances

---

## Shared Services Subnet Pattern

Organizations sometimes maintain shared infrastructure:

```text
Shared Services VPC
 |
 +-- DNS
 +-- Monitoring
 +-- Security Services
 +-- Internal Tooling
```

Application VPCs may connect through:

```text
Transit Gateway
```

or service-specific connectivity such as:

```text
PrivateLink
```

Shared services should have explicit network boundaries and routing policies.

Do not allow unrestricted connectivity simply because workloads belong to the same organization.

---

## Management Subnet Pattern

Administrative workloads may require controlled private access.

Example:

```text
Corporate Network
       |
       v
VPN / Direct Connect
       |
       v
Management Subnet
       |
       +-- Administrative Access
       +-- Management Tools
```

Avoid using a publicly accessible bastion host as the default solution when AWS-native private access mechanisms can provide a better security model.

Management access should be:

- Audited
- Restricted
- Short-lived where possible
- Centrally controlled

---

## Reserved Subnet Pattern

Reserve part of the VPC address space for future requirements.

Example:

```text
10.0.0.0/16

10.0.0.0/20    Public
10.0.16.0/20   Application
10.0.32.0/20   Data
10.0.48.0/20   Reserved
10.0.64.0/20   Reserved
...
```

Reserved capacity can support:

- New AZs
- New services
- Migration workloads
- Kubernetes growth
- New environments
- Network appliances

Unused address space is not necessarily wasted address space.

---

## Environment-Specific Subnet Patterns

Development and production should not necessarily have identical capacity.

Example:

```text
Production
10.10.0.0/16

Staging
10.20.0.0/16

Development
10.30.0.0/16
```

Within production:

```text
Public A       10.10.0.0/20
Public B       10.10.48.0/20

App A          10.10.16.0/20
App B          10.10.64.0/20

Data A         10.10.32.0/20
Data B         10.10.80.0/20
```

Consistent patterns make automation and troubleshooting easier.

---

## IPv4 Capacity Planning

For an IPv4 subnet:

```text
CIDR size = 2^(32 - prefix length)
```

For example:

```text
/24 = 256 addresses
/20 = 4096 addresses
/16 = 65536 addresses
```

AWS reserves five IP addresses in each subnet, so the usable address count is lower than the mathematical total.

Example:

```text
/24
256 total
-5 AWS-reserved
=251 usable
```

Always plan using usable capacity rather than raw CIDR size.

---

## Subnet Sizing Strategy

Avoid sizing subnets solely around current instance counts.

Instead estimate:

```text
Current capacity
+
Expected growth
+
Scaling burst
+
Infrastructure overhead
+
Reserved capacity
```

For example:

```text
Current:
200 application IPs

Expected:
400 IPs

Burst:
200 IPs

Infrastructure:
100 IPs

Target:
900+ IP capacity
```

The exact sizing model depends on the workload.

---

## Subnet Sizing for High-Churn Workloads

Systems that frequently create and destroy network interfaces require additional headroom.

Examples include:

- ECS tasks
- EKS pods
- Lambda functions attached to VPC subnets
- Auto Scaling Groups
- Short-lived workers

A subnet that appears sufficiently large based on average utilization can still fail during scaling bursts.

Monitor available IP addresses as a capacity metric.

---

## Routing Patterns

Subnet design and route tables must be designed together.

Example:

```text
Public Route Table
------------------
10.0.0.0/16 -> local
0.0.0.0/0   -> Internet Gateway
```

Application Route Table:

```text
Private App Route Table
-----------------------
10.0.0.0/16 -> local
0.0.0.0/0   -> NAT Gateway
```

Data Route Table:

```text
Private Data Route Table
------------------------
10.0.0.0/16 -> local
```

The data subnet has no general internet route.

---

## Separate Route Tables by Behavior

Do not automatically assign one route table to every subnet.

If subnet traffic requirements differ, use separate route tables.

For example:

```text
Public Route Table
       |
       +-- Public A
       +-- Public B

App Route Table A
       |
       +-- App A

App Route Table B
       |
       +-- App B

Data Route Table
       |
       +-- Data A
       +-- Data B
```

This allows routing behavior to evolve independently.

---

## AZ-Specific Route Tables

AZ-specific route tables are particularly useful when NAT Gateways are deployed per AZ.

```text
App A
 |
 v
Route Table A
 |
 v
NAT A

App B
 |
 v
Route Table B
 |
 v
NAT B
```

This avoids routing private application traffic through another AZ merely to reach its NAT Gateway.

---

## Security Considerations

Subnet architecture should enforce network least privilege.

### Public Exposure

Keep public subnets limited to resources that genuinely require public connectivity.

### Database Isolation

Database subnets should not have direct internet ingress.

### Security Groups

Use Security Group references for application relationships where appropriate.

### NACLs

Use NACLs for subnet-level stateless controls when there is a clear requirement.

### VPC Endpoints

Use endpoint policies and Security Groups appropriately for interface endpoints.

### Management Access

Avoid exposing administrative services publicly.

### Logging

Enable appropriate network and audit logging.

---

## Production Pitfalls

### Making Every Subnet Public

This increases the potential attack surface and makes network intent unclear.

### Creating One Giant Private Subnet

This can simplify initial deployment but becomes difficult to segment as the system grows.

### Creating Too Many Tiny Subnets

Small CIDRs can create scaling failures long before the VPC runs out of overall address space.

### Ignoring Interface Endpoint IP Consumption

Endpoint ENIs consume addresses.

### Ignoring Kubernetes IP Requirements

Pod density can exhaust subnet capacity.

### Using One Route Table Everywhere

Different workload classes often require different routing behavior.

### Designing Only for Average Traffic

Auto Scaling and burst workloads require capacity headroom.

### Ignoring AZ Failure

A subnet is AZ-specific. A single-subnet workload is therefore tied to one failure domain.

---

## Production Design Example

Consider a production Django platform with:

- Public REST API
- Celery workers
- PostgreSQL
- Redis
- S3
- Secrets Manager
- External payment API

A suitable architecture could be:

```mermaid
flowchart TB
    INTERNET["Internet"]

    subgraph VPC["10.10.0.0/16"]
        subgraph AZA["AZ A"]
            PUBA["Public Subnet"]
            APPA["Private App Subnet"]
            DATAA["Private Data Subnet"]
            NATA["NAT Gateway"]
        end

        subgraph AZB["AZ B"]
            PUBB["Public Subnet"]
            APPB["Private App Subnet"]
            DATAB["Private Data Subnet"]
            NATB["NAT Gateway"]
        end

        ALB["Application Load Balancer"]
        S3EP["S3 Gateway Endpoint"]
        SECRET["Secrets Manager Interface Endpoint"]
        DB["PostgreSQL"]
        REDIS["Redis"]
    end

    INTERNET --> ALB

    ALB --> APPA
    ALB --> APPB

    APPA --> DATAA
    APPB --> DATAB

    APPA --> NATA
    APPB --> NATB

    APPA --> S3EP
    APPB --> S3EP

    APPA --> SECRET
    APPB --> SECRET

    APPA --> DB
    APPB --> DB

    APPA --> REDIS
    APPB --> REDIS

    NATA --> INTERNET
    NATB --> INTERNET
```

Traffic behavior:

| Traffic | Path |
|---|---|
| User → API | Internet → ALB → Private App |
| App → PostgreSQL | Private App → Private Data |
| App → Redis | Private App → Private Data |
| App → S3 | Private App → Gateway Endpoint |
| App → Secrets Manager | Private App → Interface Endpoint |
| App → Payment API | Private App → NAT Gateway → Internet |
| Internal service → internal service | Private VPC routing + Security Groups |

This architecture keeps application workloads private while allowing controlled access to required external dependencies.

---

## Subnet Design for Backend Services

For Django or FastAPI:

```text
ALB
 |
 v
Private App Subnet
 |
 +-- API
 +-- Workers
 |
 +-- PostgreSQL
 +-- Redis
```

For gRPC:

```text
Internal ALB / NLB
 |
 v
Private App Subnets
 |
 +-- gRPC Service A
 +-- gRPC Service B
```

For Kafka:

```text
Private Kafka Subnets
 |
 +-- Broker A
 +-- Broker B
 +-- Broker C
```

For Kubernetes:

```text
Private Kubernetes Subnets
 |
 +-- Nodes
 +-- Pods
 +-- Load Balancer ENIs
 +-- VPC Endpoint ENIs
```

The subnet design should follow the networking requirements of the platform rather than the programming framework itself.

---

## Monitoring and Capacity Management

Monitor subnet-level capacity continuously.

Important metrics include:

- Available IPv4 addresses
- Network interface count
- NAT traffic
- NAT connection counts
- Cross-AZ traffic
- VPC endpoint traffic
- Rejected flows
- Load balancer health
- DNS resolution failures

A useful operational question is:

> Can this subnet support the application's maximum expected scaling event?

Not merely:

> Does the subnet have enough addresses right now?

---

## Infrastructure as Code

Subnet layouts should be defined declaratively.

A conceptual Terraform structure:

```text
networking/
├── vpc.tf
├── subnets.tf
├── route_tables.tf
├── nat.tf
├── endpoints.tf
├── security_groups.tf
└── variables.tf
```

Use variables for environment-specific CIDRs while preserving a consistent topology.

Example:

```hcl
variable "vpc_cidr" {
  type        = string
  description = "CIDR block allocated to the VPC"
}

variable "availability_zones" {
  type        = list(string)
  description = "Availability Zones used by the environment"
}
```

Subnet changes should be reviewed carefully because modifying production network topology can affect many dependent resources.

---

## Design Review Checklist

Before approving a subnet design, verify:

```text
[ ] Every subnet belongs to the intended AZ
[ ] CIDRs do not overlap
[ ] CIDRs leave sufficient growth capacity
[ ] Public subnets contain only intentionally public infrastructure
[ ] Application workloads are private where possible
[ ] Data workloads are isolated appropriately
[ ] Route tables match subnet responsibilities
[ ] NAT architecture matches availability requirements
[ ] VPC endpoints are accounted for
[ ] ECS/EKS IP consumption is estimated
[ ] Load balancer placement is multi-AZ where required
[ ] Database subnet groups use appropriate private subnets
[ ] Security Groups enforce workload relationships
[ ] Cross-AZ traffic is understood
[ ] Monitoring tracks available IP capacity
[ ] Disaster recovery requirements are reflected in the design
[ ] Terraform/CloudFormation/CDK can reproduce the topology
```

---

## Interview Traps

### Can a subnet span multiple Availability Zones?

No. A subnet belongs to exactly one AZ.

### Does a public subnet automatically make every resource public?

No. Public routing alone does not automatically expose a resource. Public addressing, security controls, and the resource's networking configuration also matter.

### Why create separate application and database subnets?

To establish clearer network segmentation and make routing and security policies easier to control.

### Why use multiple subnets across AZs?

To distribute resources across independent failure domains.

### Should every microservice have its own subnet?

Usually not. Security Groups and application-level controls can provide service isolation without subnet proliferation.

### Why can an application fail to scale even when CPU is available?

The subnet may have exhausted available IP addresses.

### Why does Kubernetes require careful subnet planning?

Pods and nodes can consume VPC IP capacity depending on the networking configuration.

### Why use separate route tables for application subnets?

Different application subnets may need different egress paths, especially when using AZ-local NAT Gateways.

### Is a private subnet always isolated from the internet?

No. A private subnet can have outbound internet access through a NAT Gateway.

### Does subnet separation replace Security Groups?

No. Subnets provide network placement and routing boundaries; Security Groups provide stateful resource-level traffic controls.

---

## Key Takeaways

- Subnet design is fundamentally about segmentation, Availability Zone isolation, routing behavior, security boundaries, and future IP capacity.
- Production architectures commonly distribute equivalent public, application, and data subnet roles across multiple Availability Zones.
- Private subnet sizing must account for application scaling, ECS/EKS networking, VPC endpoints, load balancers, and burst capacity rather than current utilization alone.
- Route tables, NAT architecture, Security Groups, and subnet placement must be designed together as one traffic architecture.
- Good subnet design minimizes unnecessary exposure and operational complexity while preserving enough capacity and network flexibility for future growth.