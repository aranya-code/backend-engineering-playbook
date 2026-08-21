# 04- Three-Tier VPC Architecture

## Overview

A three-tier VPC architecture separates an application into distinct network tiers with different exposure and security requirements:

- **Presentation tier** — public-facing entry points such as load balancers.
- **Application tier** — private backend services such as Django, FastAPI, gRPC, ECS tasks, EKS workloads, or EC2 instances.
- **Data tier** — private stateful systems such as PostgreSQL, Redis, and other databases.

The primary purpose is **network isolation**. A component should only be able to communicate with the components it actually needs.

A typical production architecture is:

```text
                           Internet
                              |
                              v
                     Internet Gateway
                              |
                     Public Subnets
                    +---------+---------+
                    |                   |
                 ALB A               ALB B
                    |                   |
                    +---------+---------+
                              |
                       Private App Tier
                    +---------+---------+
                    |                   |
                 App A               App B
                    |                   |
                    +---------+---------+
                              |
                       Private Data Tier
                    +---------+---------+
                    |                   |
              Database A           Database B
```

The architecture is normally implemented across multiple Availability Zones so that the tiers do not depend on a single AZ.

A three-tier design is not a requirement for every workload. It is most useful when the application has clear trust boundaries and the operational benefits of network isolation outweigh the additional infrastructure complexity.

---

## Why Three Tiers Exist

The main reason to separate tiers is to reduce the blast radius of network compromise and configuration errors.

Without segmentation:

```text
Internet
   |
   v
Application
   |
   +---- Database
   +---- Redis
   +---- Internal services
```

If the application host is compromised, the attacker may have unnecessary network access to internal systems.

With tier separation:

```text
Internet
   |
   v
Public Load Balancer
   |
   v
Application Tier
   |
   v
Data Tier
```

The Security Groups and route configuration can enforce the intended communication paths.

For example:

```text
Internet
   |
   | HTTPS
   v
ALB
   |
   | HTTP/HTTPS
   v
Application
   |
   | PostgreSQL
   v
Database
```

The database does not need to accept traffic directly from the Internet.

---

## Three-Tier Model

| Tier | Typical Location | Examples | Internet Inbound |
|---|---|---|---|
| Presentation | Public subnet | ALB, public reverse proxy | Controlled |
| Application | Private subnet | Django, FastAPI, gRPC, ECS, EKS | No |
| Data | Private subnet | PostgreSQL, Redis, databases | No |

The exact AWS resources can vary, but the security principle remains:

> Put resources with similar exposure and trust requirements into the same network tier.

---

## Presentation Tier

The presentation tier is the controlled entry point into the application.

Typical components include:

- Application Load Balancer
- Network Load Balancer
- Reverse proxy
- Public-facing ingress infrastructure

A common architecture is:

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
Application Load Balancer
```

The public subnet contains the load balancer rather than the application servers themselves.

This allows the application tier to remain private.

### Why Use a Load Balancer?

A load balancer provides:

- Traffic distribution
- Health checking
- TLS termination
- Target registration
- High availability across AZs
- Integration with autoscaling

For a backend API:

```text
Client
  |
  | HTTPS
  v
ALB
  |
  +---- App A
  |
  +---- App B
```

The client does not need to know the private IP addresses of application instances.

---

## Application Tier

The application tier contains the backend compute responsible for executing business logic.

Examples include:

- Django
- Django REST Framework
- FastAPI
- gRPC services
- Celery workers
- ECS tasks
- EKS pods
- EC2 application instances

The application tier should generally be private.

```text
Private Application Subnet
 |
 +-- Django API
 +-- FastAPI API
 +-- gRPC services
 +-- Celery workers
```

The application instances can initiate outbound connections when required, but they should not accept arbitrary Internet traffic.

---

## Data Tier

The data tier contains persistent or shared state.

Examples:

- PostgreSQL
- MySQL
- Redis
- Managed database services
- Kafka infrastructure
- Other stateful services

A database should normally be reachable only by the application workloads that require it.

For example:

```text
Application Security Group
          |
          | TCP 5432
          v
Database Security Group
```

The database Security Group should not contain:

```text
0.0.0.0/0
```

for PostgreSQL access.

Instead, access should be based on the appropriate application Security Group.

---

## Reference Architecture

A production-oriented three-tier architecture across two AZs can be represented as:

```mermaid
flowchart TB
    USER["Internet Clients"]
    IGW["Internet Gateway"]

    subgraph VPC["Production VPC"]
        subgraph AZA["Availability Zone A"]
            PUBA["Public Subnet A"]
            APPA["Private App Subnet A"]
            DATAA["Private Data Subnet A"]
            ALBA["ALB Node"]
            APPA_NODE["Application A"]
        end

        subgraph AZB["Availability Zone B"]
            PUBB["Public Subnet B"]
            APPB["Private App Subnet B"]
            DATAB["Private Data Subnet B"]
            ALBB["ALB Node"]
            APPB_NODE["Application B"]
        end

        DB["PostgreSQL HA"]
        REDIS["Redis HA"]
        NAT_A["NAT Gateway A"]
        NAT_B["NAT Gateway B"]
    end

    USER --> IGW
    IGW --> ALBA
    IGW --> ALBB

    ALBA --> APPA_NODE
    ALBB --> APPB_NODE

    APPA_NODE --> DB
    APPB_NODE --> DB

    APPA_NODE --> REDIS
    APPB_NODE --> REDIS

    APPA_NODE --> NAT_A
    APPB_NODE --> NAT_B
```

The diagram represents the logical architecture. Actual AWS service placement and routing depend on the selected services.

---

## Subnet Design

A common subnet structure is:

```text
VPC: 10.10.0.0/16

AZ A
├── Public A
├── Private App A
└── Private Data A

AZ B
├── Public B
├── Private App B
└── Private Data B
```

Example CIDR allocation:

| AZ | Tier | Example CIDR |
|---|---|---|
| AZ A | Public | `10.10.0.0/20` |
| AZ A | Application | `10.10.16.0/20` |
| AZ A | Data | `10.10.32.0/20` |
| AZ B | Public | `10.10.48.0/20` |
| AZ B | Application | `10.10.64.0/20` |
| AZ B | Data | `10.10.80.0/20` |

The ranges are illustrative.

Subnet sizing should account for:

- Current workloads
- Autoscaling
- Kubernetes pod networking
- ECS task density
- AWS-reserved addresses
- Future expansion
- Additional services

Avoid allocating extremely small private subnets simply because current instance counts are low.

---

## Public Subnet Routing

A public subnet normally has a default route through an Internet Gateway.

```text
Destination       Target
--------------------------------
10.10.0.0/16      local
0.0.0.0/0         igw-xxxxxxxx
```

Resources placed in the subnet can have public connectivity when the resource and security configuration also permit it.

The presence of an Internet Gateway route does not automatically make every resource publicly accessible.

---

## Private Application Subnet Routing

An application subnet typically has:

```text
Destination       Target
--------------------------------
10.10.0.0/16      local
0.0.0.0/0         nat-xxxxxxxx
```

This allows private workloads to initiate outbound Internet connections through a NAT Gateway.

For example:

```text
FastAPI
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

The external service sees the NAT Gateway's public IP rather than the application's private IP.

---

## Private Data Subnet Routing

The data tier generally does not need Internet access.

Its route table may contain only:

```text
Destination       Target
--------------------------------
10.10.0.0/16      local
```

This provides VPC-local communication without providing a default Internet route.

This is an important security boundary.

Do not add a NAT Gateway to a database subnet merely because the database software may occasionally need package updates.

Prefer service-specific mechanisms, managed maintenance, or controlled operational paths instead.

---

## Route Table Separation

Separate route tables can reinforce tier boundaries.

Example:

```text
Public Route Table
    |
    +-- Public subnets

Application Route Table
    |
    +-- App subnets

Data Route Table
    |
    +-- Data subnets
```

The routing policy should reflect the intended architecture.

However, route tables are not a replacement for Security Groups.

Routing determines whether a path exists.

Security Groups determine whether traffic is permitted.

---

## Security Group Architecture

Security Groups should represent application relationships.

A common structure is:

```text
Internet
   |
   | TCP 443
   v
ALB Security Group
   |
   | TCP 8000
   v
Application Security Group
   |
   | TCP 5432
   v
Database Security Group
```

For example:

| Security Group | Inbound Source | Port | Purpose |
|---|---|---:|---|
| ALB SG | Internet | 443 | HTTPS |
| App SG | ALB SG | 8000 | Backend traffic |
| DB SG | App SG | 5432 | PostgreSQL |
| Redis SG | App SG | 6379 | Redis |

This is preferable to broad CIDR-based rules when the relationship is between AWS resources.

---

## Security Group Referencing

Instead of:

```text
Database SG
Source: 10.10.0.0/16
Port: 5432
```

prefer:

```text
Database SG
Source: Application SG
Port: 5432
```

This expresses the security relationship directly.

It also avoids granting database access to every resource in the VPC.

The application Security Group can then be attached to the required application workloads.

---

## Network ACL Considerations

Network ACLs operate at the subnet boundary and are stateless.

Security Groups are stateful and operate at the network interface level.

For most application architectures:

```text
Primary workload access control
    -> Security Groups

Additional subnet-level controls
    -> Network ACLs
```

Do not introduce complex Network ACL rules without a clear security requirement.

Overly restrictive NACLs can cause difficult-to-diagnose failures because return traffic must be explicitly permitted.

---

## Request Flow

A typical HTTPS request follows:

```mermaid
sequenceDiagram
    participant C as Client
    participant ALB as Public ALB
    participant APP as Private Application
    participant DB as Private Database
    participant EXT as External API

    C->>ALB: HTTPS request
    ALB->>APP: Forward request
    APP->>DB: Query
    DB-->>APP: Result
    APP->>EXT: Optional outbound request
    EXT-->>APP: Response
    APP-->>ALB: HTTP response
    ALB-->>C: HTTPS response
```

The client never needs direct network access to the application or database subnet.

---

## Internet Ingress vs Egress

A key distinction in a three-tier design is:

### Ingress

Traffic entering the application:

```text
Internet
   |
   v
IGW
   |
   v
ALB
   |
   v
Application
```

### Egress

Traffic initiated by the application:

```text
Application
   |
   v
NAT Gateway
   |
   v
IGW
   |
   v
Internet
```

These are different traffic flows and should be designed independently.

---

## NAT Gateway Design

For production Multi-AZ systems, a common architecture is:

```text
App A --> NAT A --> IGW
App B --> NAT B --> IGW
```

This avoids making App A dependent on NAT B for ordinary outbound traffic.

For lower-cost environments:

```text
App A --+
        |
        +--> NAT --> IGW
        |
App B --+
```

may be acceptable.

The decision should be based on:

- Availability requirements
- Traffic volume
- Cost
- Failure tolerance
- Operational requirements

---

## VPC Endpoints

Applications frequently communicate with AWS services such as:

- S3
- DynamoDB
- Secrets Manager
- Systems Manager
- CloudWatch-related services
- ECR
- STS

Where supported, VPC endpoints can keep traffic on AWS-managed private networking paths instead of sending it through a NAT Gateway.

Conceptually:

```text
Application
   |
   +---- VPC Endpoint ----> AWS Service
   |
   +---- NAT Gateway -----> Internet
```

This can improve network control and may reduce NAT data-processing costs for suitable traffic patterns.

Endpoint types and supported services vary, so they should be selected based on actual application dependencies.

---

## Application Tier Examples

### Django

A common deployment:

```text
ALB
 |
 v
Django / Gunicorn
 |
 +-- PostgreSQL
 +-- Redis
 +-- Celery
```

Django workers should not require public IP addresses.

### FastAPI

```text
ALB
 |
 v
FastAPI / Uvicorn
 |
 +-- PostgreSQL
 +-- Redis
 +-- External APIs
```

The same private-subnet model applies.

### gRPC

Internal gRPC services can communicate privately:

```text
Service A
   |
   | gRPC
   v
Service B
```

A private load balancer or service-discovery mechanism can provide stable connectivity without exposing the service publicly.

---

## Celery Workers

Celery workers are usually application-tier workloads.

A common architecture is:

```text
Django / FastAPI
       |
       v
Redis / Broker
       |
       v
Celery Workers
       |
       v
Database
```

Workers generally do not need inbound Internet access.

They may require outbound connectivity for:

- External APIs
- Package repositories
- AWS services

Such egress should use NAT Gateways or VPC endpoints as appropriate.

---

## PostgreSQL Data Tier

A production PostgreSQL deployment should remain private.

Example:

```text
Application SG
      |
      | TCP 5432
      v
PostgreSQL
```

For managed PostgreSQL, use the database service's supported high-availability capabilities when required.

Do not expose PostgreSQL directly to the Internet simply to make application development easier.

---

## Redis Data Tier

Redis should similarly remain private.

```text
Application SG
      |
      | TCP 6379
      v
Redis
```

Do not expose Redis publicly.

An exposed Redis endpoint can become a serious security vulnerability.

---

## Kafka Data Tier

Kafka can be placed in private networking.

```text
Application
    |
    v
Private Kafka Cluster
```

The cluster should use appropriate replication and AZ distribution when availability is important.

Kafka clients should not require public Internet exposure merely to communicate with brokers.

---

## Three-Tier vs Two-Tier Architecture

Not every system needs three distinct tiers.

| Architecture | Characteristics | Suitable For |
|---|---|---|
| Two-tier | App + data | Smaller services |
| Three-tier | Presentation + app + data | Traditional production APIs |
| Service-oriented | Multiple private services | Microservices |
| Serverless | Managed service boundaries | Event-driven/serverless systems |

A three-tier model is useful when the separation provides a meaningful security or operational boundary.

Do not create additional tiers merely to make the architecture diagram look sophisticated.

---

## Three-Tier vs Microservices

A three-tier architecture describes **network and application boundaries**.

Microservices describe **service decomposition**.

They are not mutually exclusive.

For example:

```text
Presentation Tier
       |
       v
Application Tier
       |
       +-- Orders Service
       +-- Payments Service
       +-- Users Service
       +-- Notifications Service
       |
       v
Data Tier
```

A microservices system can still use a three-tier network architecture.

---

## Service-to-Service Communication

Internal services should generally use private networking.

Example:

```text
Public ALB
   |
   v
API Service
   |
   | gRPC
   v
Orders Service
   |
   | PostgreSQL
   v
Database
```

Do not expose every microservice through a public load balancer.

Public exposure increases:

- Attack surface
- Authentication complexity
- Operational complexity
- Monitoring requirements
- Cost

Use private service discovery and internal load balancing where appropriate.

---

## High Availability

A production three-tier architecture should normally span multiple AZs.

```text
                 Public ALB
                 /       \
                /         \
            AZ A           AZ B
             |               |
          App A            App B
             |               |
             +-------+-------+
                     |
                 Data Tier
```

For critical workloads, consider:

- Multi-AZ application capacity
- Multi-AZ load balancing
- AZ-local NAT Gateways
- Highly available databases
- Highly available cache
- Replicated messaging systems

The exact configuration depends on the availability requirements.

---

## Failure Scenario: Application AZ Failure

Suppose AZ A fails.

Before:

```text
ALB
 |
 +-- App A
 +-- App B
```

After:

```text
ALB
 |
 +-- App B
```

The architecture should continue operating if:

- App B has enough capacity.
- The ALB detects App A failure.
- The database remains available.
- Redis remains available.
- Required outbound connectivity remains available.
- The application can handle the increased traffic.

This is why Multi-AZ capacity planning is as important as subnet placement.

---

## Failure Scenario: Database Failure

If the application tier is healthy but the database is unavailable:

```text
ALB
 |
 +-- App A
 +-- App B
      |
      X
      |
   Database
```

Adding another application instance does not solve the problem.

This demonstrates an important principle:

> Availability must be designed across dependency chains, not only at the compute layer.

The database, cache, message broker, and external dependencies all influence end-to-end availability.

---

## Availability Dependency Chain

A request may depend on:

```text
Client
  |
  v
DNS
  |
  v
ALB
  |
  v
Application
  |
  +--> PostgreSQL
  |
  +--> Redis
  |
  +--> Kafka
  |
  +--> External API
```

If any critical dependency is unavailable, the request may fail.

A senior architecture review therefore asks:

> What happens when each dependency fails?

rather than only:

> Are the application servers distributed across AZs?

---

## Observability

Monitor each tier independently.

### Presentation Tier

Monitor:

- Request count
- HTTP status codes
- Target health
- Latency
- TLS errors
- Connection errors

### Application Tier

Monitor:

- CPU
- Memory
- Request latency
- Error rate
- Worker utilization
- Container restarts
- Application logs

### Data Tier

Monitor:

- Database connections
- CPU
- Memory
- Storage
- Query latency
- Cache hit rate
- Replication/failover state

### Network Layer

Monitor:

- NAT Gateway traffic
- NAT errors
- VPC Flow Logs
- Subnet IP utilization
- Endpoint usage
- Cross-AZ traffic

---

## Security Considerations

A three-tier architecture should enforce least privilege at multiple layers.

### Internet Exposure

Only required public endpoints should be exposed.

Typical:

```text
Internet -> ALB
```

Not:

```text
Internet -> PostgreSQL
Internet -> Redis
Internet -> Internal gRPC service
```

### Security Groups

Prefer resource-based relationships:

```text
ALB SG -> App SG -> DB SG
```

### Data Encryption

Use encryption for:

- HTTPS traffic
- Database storage
- Redis where supported
- S3 objects
- Secrets
- Message systems where required

### Secrets

Do not store database credentials directly in:

- Source code
- Docker images
- Git repositories
- AMIs
- Terraform source files

Use appropriate secret-management mechanisms such as AWS Secrets Manager or Systems Manager Parameter Store according to the use case.

---

## Scalability Considerations

Three-tier architecture supports independent scaling.

For example:

```text
Presentation Tier
       |
       v
Scale ALB capacity as needed

Application Tier
       |
       v
Scale API instances/tasks

Data Tier
       |
       v
Scale database/cache independently
```

The application tier is generally easiest to scale horizontally.

The data tier is often the scaling bottleneck.

For example:

```text
100 API instances
       |
       v
Single PostgreSQL instance
```

may simply move the bottleneck to PostgreSQL.

Architecture must therefore consider:

- Connection pooling
- Read replicas
- Caching
- Partitioning
- Query optimization
- Queue-based processing
- Database scaling strategies

---

## Database Connection Management

A highly scaled backend can exhaust database connections.

For example:

```text
50 application instances
x
10 database connections
=
500 connections
```

If PostgreSQL cannot support the resulting connection load, adding more application instances can make the problem worse.

Use appropriate connection pooling and carefully size application workers and database connections.

For Django and other Python services, consider:

- Worker count
- Thread/process model
- Database connection reuse
- Pool sizing
- Request concurrency

---

## Performance Considerations

Network isolation introduces additional hops in some architectures.

For example:

```text
Client
  |
  v
ALB
  |
  v
Application
  |
  v
Database
```

The additional network components are normally acceptable, but high-throughput systems should measure:

- Latency
- Throughput
- Cross-AZ traffic
- NAT processing
- Database round trips
- Service-to-service calls

Avoid excessive synchronous network calls.

A microservice request path such as:

```text
API
 -> Auth
 -> Orders
 -> Pricing
 -> Inventory
 -> Payments
```

can accumulate latency and failure points even when the VPC is correctly designed.

---

## Cost Considerations

Three-tier architectures can introduce additional costs from:

- NAT Gateways
- Load balancers
- Cross-AZ traffic
- Additional compute
- Managed databases
- Redis
- Kafka
- VPC endpoints

Cost optimization should focus on unnecessary traffic and resources rather than removing security boundaries.

For example:

```text
Application
    |
    v
NAT Gateway
    |
    v
S3
```

may be replaced with:

```text
Application
    |
    v
S3 VPC Endpoint
    |
    v
S3
```

when appropriate.

This can improve network isolation and reduce unnecessary NAT processing for supported service traffic.

---

## Common Mistakes

### Putting Application Servers in Public Subnets

A backend server does not need a public IP simply because users access the application.

Prefer:

```text
Internet -> ALB -> Private App
```

### Exposing the Database

Avoid:

```text
0.0.0.0/0 -> TCP 5432
```

Use private subnets and restrictive Security Groups.

### Treating Route Tables as Security Controls

Routes determine reachability, but they are not a replacement for Security Groups.

### One Security Group for Everything

Using one broad Security Group makes least-privilege enforcement difficult.

Prefer separate roles:

```text
ALB SG
App SG
DB SG
Redis SG
```

### Putting the Data Tier Behind NAT

A database generally does not need outbound Internet access.

### Forgetting NAT Failure

If private applications require Internet egress, NAT architecture becomes part of application availability.

### Insufficient Subnet Capacity

Autoscaling may fail because the subnet has no available private IP addresses.

### Making Every Service Public

Internal services should not automatically receive public load balancers or public IPs.

### Confusing Three Tiers with Three Subnets

A tier is a logical architectural boundary. A production implementation usually has corresponding subnets across multiple AZs.

### Overengineering the Architecture

Three tiers are useful when they solve a real isolation or operational problem.

Do not create unnecessary network layers that increase routing and operational complexity.

---

## Interview Traps

### Does a three-tier architecture require exactly three subnets?

No. A production architecture commonly has multiple subnets per tier across multiple AZs.

### Should application servers be in public subnets?

Usually no. A public load balancer can provide Internet ingress while application workloads remain private.

### Does a private subnet mean it cannot access the Internet?

No. A private subnet can have outbound Internet access through a NAT Gateway while remaining inaccessible to unsolicited Internet connections.

### Are route tables enough to secure the database?

No. Security Groups and other controls are required.

### Why have a data subnet if the database is managed?

Managed databases still require network placement and access controls. Database subnet groups commonly place database resources into private subnets.

### Is a three-tier architecture automatically highly available?

No. High availability requires redundancy across failure domains and resilient dependencies.

### Can microservices use a three-tier architecture?

Yes. Three-tier architecture and microservice decomposition address different architectural concerns.

### Why not put everything in public subnets?

It unnecessarily increases the attack surface and makes least-privilege network design harder.

### Why does the application tier need NAT?

Only when private workloads need outbound Internet access. AWS service communication may instead use VPC endpoints where supported.

### Why is the data tier usually not given a default route?

Because databases and other stateful systems generally should not require general Internet connectivity.

---

## Production Checklist

Before deploying a three-tier VPC architecture, verify:

```text
[ ] VPC CIDR is large enough for expected growth
[ ] Each tier has appropriate subnets
[ ] Critical tiers span multiple AZs
[ ] Public subnets contain only intentionally public resources
[ ] Application workloads are private
[ ] Data workloads are private
[ ] ALB is deployed across required AZs
[ ] Application Security Group accepts traffic only from ALB
[ ] Database Security Group accepts traffic only from required clients
[ ] Redis access is restricted
[ ] Internal services are not publicly exposed unnecessarily
[ ] NAT architecture matches availability requirements
[ ] VPC endpoints are used where appropriate
[ ] Route tables are intentionally separated
[ ] NACL configuration does not accidentally block return traffic
[ ] Subnet IP capacity supports autoscaling
[ ] Database failover requirements are addressed
[ ] Redis/messaging availability requirements are addressed
[ ] Application state is externalized
[ ] Secrets are managed securely
[ ] Monitoring exists for every tier
[ ] Cross-AZ traffic is understood
[ ] Failure scenarios have been tested
[ ] Infrastructure is managed through IaC
```

---

## Example Infrastructure Layout

A maintainable Infrastructure as Code repository might separate networking concerns:

```text
infrastructure/
├── networking/
│   ├── vpc.tf
│   ├── subnets.tf
│   ├── route-tables.tf
│   ├── internet-gateway.tf
│   ├── nat-gateways.tf
│   ├── endpoints.tf
│   └── security-groups.tf
│
├── load-balancing/
│   └── alb.tf
│
├── application/
│   ├── ecs.tf
│   └── autoscaling.tf
│
├── database/
│   └── postgres.tf
│
└── cache/
    └── redis.tf
```

This separation keeps the network foundation independent from application deployment logic.

---

## Key Takeaways

- A three-tier VPC separates public ingress, private application workloads, and private stateful systems to establish clear security and trust boundaries.
- The presentation tier should normally expose only controlled entry points such as an ALB, while Django, FastAPI, gRPC, Celery, and similar workloads remain in private subnets.
- Security Groups should model application relationships such as `ALB → App → Database`, while route tables provide network reachability rather than acting as the primary security mechanism.
- Production three-tier architectures should account for Multi-AZ capacity, NAT availability, database failover, subnet IP capacity, dependency failures, and cross-AZ traffic.
- Three-tier architecture is a logical design pattern rather than a fixed number of subnets; use it when the resulting isolation and operational benefits justify the additional complexity.