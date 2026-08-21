# 05- Private-Only VPC Architecture

## Overview

A private-only VPC architecture is a network design in which workloads do not require publicly routable IP addresses and there is no direct Internet ingress to application resources.

The architecture is useful for systems where external access is unnecessary or should be mediated through private connectivity mechanisms. Typical workloads include:

- Internal microservices
- Backend processing platforms
- Data-processing systems
- Internal APIs
- Corporate applications
- Private Kubernetes clusters
- Batch and asynchronous workloads
- Systems accessed through VPN or AWS Direct Connect
- Multi-account AWS environments using centralized networking

A private-only VPC does **not** necessarily mean the workloads have no external connectivity. Private workloads can still communicate with AWS services, corporate networks, and selected external systems through mechanisms such as:

- VPC endpoints
- NAT Gateways
- AWS Transit Gateway
- Site-to-Site VPN
- AWS Direct Connect
- PrivateLink
- Internal load balancers

The key design principle is:

> Do not provide public network exposure when the workload does not require it.

---

## What Makes a VPC Private-Only?

A VPC becomes effectively private-only when application workloads are not directly reachable from the public Internet.

A typical architecture looks like:

```text
                    Corporate Network
                           |
                     VPN / Direct Connect
                           |
                           v
                    +-------------+
                    |     VPC     |
                    |             |
                    | Private     |
                    | Subnets     |
                    |             |
                    |  Services   |
                    |  Databases  |
                    +-------------+
                           |
                    VPC Endpoints
                           |
                           v
                     AWS Services
```

There may be no:

- Internet Gateway used for workload Internet access
- Public IPv4 addresses
- Public load balancers
- Public application endpoints

Instead, access is provided through controlled private paths.

---

## Why Use a Private-Only Architecture?

Public networking introduces additional attack surface and operational requirements.

A public workload may require:

- Public IP addressing
- Internet-facing load balancers
- Public DNS
- Internet-facing Security Group rules
- TLS certificates
- DDoS considerations
- Public authentication
- Internet exposure monitoring

A private architecture removes many of these requirements from internal workloads.

The result is a smaller externally reachable attack surface.

### Typical Use Cases

| Workload | Private-Only Suitable? | Reason |
|---|---|---|
| Internal REST API | Yes | Consumers can use private connectivity |
| Internal gRPC service | Yes | Private service-to-service communication |
| PostgreSQL | Yes | Database should not be Internet-facing |
| Redis | Yes | Cache should remain private |
| Celery workers | Yes | Usually no public ingress |
| Kafka | Yes | Brokers generally remain private |
| Internal Kubernetes cluster | Yes | Worker nodes can remain private |
| Public website | Usually no | Requires public ingress |
| Public API | Usually no | Requires controlled Internet ingress |

---

## Public vs Private-Only Architecture

| Characteristic | Public/Private VPC | Private-Only VPC |
|---|---|---|
| Internet-facing load balancer | Common | Not required |
| Public application IPs | Possible | Avoided |
| Internet Gateway | Often required | Not required for workload access |
| NAT Gateway | Common | Optional |
| VPC endpoints | Recommended | Often important |
| VPN / Direct Connect | Optional | Common |
| Public DNS | Common | Usually unnecessary |
| Internal DNS | Important | Critical |
| External user access | Direct | Through controlled private connectivity |

Private-only does not mean "no routing." It means routing is deliberately restricted to trusted networks and services.

---

## Reference Architecture

A production private-only VPC commonly spans multiple Availability Zones.

```mermaid
flowchart TB
    USERS["Corporate Users / Private Clients"]
    VPN["VPN / Direct Connect"]
    TGW["Transit Gateway"]

    subgraph VPC["Private VPC"]
        subgraph AZA["Availability Zone A"]
            APPA["Private App Subnet A"]
            DATAA["Private Data Subnet A"]
            APPA_NODE["Application A"]
        end

        subgraph AZB["Availability Zone B"]
            APPB["Private App Subnet B"]
            DATAB["Private Data Subnet B"]
            APPB_NODE["Application B"]
        end

        RDS["Private PostgreSQL"]
        REDIS["Private Redis"]
        VPCE["VPC Endpoints"]
    end

    USERS --> VPN
    VPN --> TGW
    TGW --> APPA
    TGW --> APPB

    APPA_NODE --> RDS
    APPB_NODE --> RDS

    APPA_NODE --> REDIS
    APPB_NODE --> REDIS

    APPA_NODE --> VPCE
    APPB_NODE --> VPCE
```

The exact topology depends on whether the environment connects to a corporate network, other VPCs, AWS services, or selected external systems.

---

## Private Subnets

Private-only architectures normally use private subnets for all application workloads.

Example:

```text
VPC: 10.20.0.0/16

AZ A
├── Private Application Subnet A
└── Private Data Subnet A

AZ B
├── Private Application Subnet B
└── Private Data Subnet B
```

Example CIDR allocation:

| AZ | Tier | CIDR |
|---|---|---|
| AZ A | Application | `10.20.0.0/20` |
| AZ A | Data | `10.20.16.0/20` |
| AZ B | Application | `10.20.32.0/20` |
| AZ B | Data | `10.20.48.0/20` |

The CIDRs are illustrative. Production subnet sizing should account for:

- Autoscaling
- Container workloads
- Kubernetes pod addressing
- Future services
- AWS-reserved addresses
- Additional AZs
- Network growth

---

## Route Tables

A private-only application subnet may use a route table similar to:

```text
Destination       Target
--------------------------------
10.20.0.0/16      local
```

This provides VPC-local connectivity.

Additional routes can provide access to trusted networks:

```text
Destination       Target
--------------------------------
10.20.0.0/16      local
10.30.0.0/16      tgw-xxxxxxxx
10.40.0.0/16      tgw-xxxxxxxx
```

The routes could represent:

- Corporate network
- Shared-services VPC
- Security VPC
- Database VPC
- Other application VPCs

The important distinction is that the default route does not need to point to an Internet Gateway.

---

## No Internet Gateway Requirement

An Internet Gateway is required for Internet connectivity from a VPC.

A private-only VPC can operate without an Internet Gateway when workloads do not need direct Internet connectivity.

Conceptually:

```text
Private Application
       |
       X
   No Internet
```

Instead:

```text
Private Application
       |
       +---- VPC Endpoint ----> AWS Service
       |
       +---- Transit Gateway --> Corporate Network
       |
       +---- PrivateLink ------> Private Service
```

This produces a much more controlled network boundary.

---

## VPC Endpoints

VPC endpoints are particularly important in private-only environments because applications often need to communicate with AWS services.

Common examples include:

- Amazon S3
- DynamoDB
- Secrets Manager
- Systems Manager
- ECR
- STS
- CloudWatch-related services

Without appropriate private connectivity, a workload may be unable to reach required AWS APIs.

The architecture becomes:

```text
Private Application
       |
       v
VPC Endpoint
       |
       v
AWS Service
```

The application does not need a public IP for this communication.

---

## Gateway Endpoints

Gateway endpoints are available for:

- Amazon S3
- DynamoDB

They integrate with route tables.

Example:

```text
Destination             Target
---------------------------------------
10.20.0.0/16            local
pl-xxxxxxxx             vpce
```

The route directs matching traffic through the endpoint.

Gateway endpoints are useful for private application workloads that need S3 or DynamoDB access without relying on NAT.

---

## Interface Endpoints

Interface endpoints use Elastic Network Interfaces inside the VPC.

Conceptually:

```text
Private Application
       |
       v
Private ENI
       |
       v
AWS PrivateLink
       |
       v
AWS Service
```

They are commonly used for AWS services that support interface endpoints.

Because the endpoint is represented inside the VPC, Security Groups can control access to it.

For example:

```text
Application SG
      |
      | TCP 443
      v
Endpoint SG
```

This makes interface endpoints particularly useful in tightly controlled environments.

---

## PrivateLink

AWS PrivateLink provides private connectivity between consumers and supported services.

A private-only architecture can consume services without exposing them to the public Internet.

Example:

```text
Consumer VPC
     |
     v
Interface Endpoint
     |
     v
AWS PrivateLink
     |
     v
Service VPC
```

This is useful for:

- Internal platform services
- Shared services
- SaaS integrations supporting PrivateLink
- Cross-account service exposure
- Organization-wide internal APIs

---

## Internal Load Balancers

Private applications can still use load balancing.

Instead of:

```text
Internet
   |
   v
Internet-facing ALB
```

use:

```text
Private Client
   |
   v
Internal ALB
   |
   v
Private Application
```

An internal Application Load Balancer provides a stable private entry point for services.

This is useful for:

- Internal REST APIs
- Internal HTTP services
- Private administrative applications
- Microservices
- Service-to-service communication

---

## Private REST API Architecture

An internal Django or FastAPI API can be deployed entirely privately.

```text
Corporate User
      |
      v
VPN
      |
      v
Internal ALB
      |
      v
Django / FastAPI
      |
      +---- PostgreSQL
      |
      +---- Redis
```

The API has no public endpoint.

Access can be controlled through:

- Corporate identity
- VPN authentication
- Security Groups
- Private DNS
- Application authentication
- IAM where applicable

---

## Private gRPC Architecture

gRPC is particularly well suited to private service-to-service communication.

```text
Service A
   |
   | gRPC
   v
Internal Load Balancer
   |
   v
Service B
```

The service does not need a public IP.

A private DNS name can provide a stable endpoint:

```text
orders.internal.example.com
```

Service A resolves the private address and connects through the VPC network.

---

## Private DNS

Private-only architectures depend heavily on DNS.

A common pattern is:

```text
orders.internal.example.com
payments.internal.example.com
users.internal.example.com
```

These names resolve to private addresses.

Private DNS can be implemented using:

- Amazon Route 53 Private Hosted Zones
- Service discovery
- Kubernetes DNS
- Internal load balancer DNS names

The objective is to avoid hardcoding private IP addresses.

---

## Route 53 Private Hosted Zones

A private hosted zone can provide internal DNS resolution.

Example:

```text
internal.example.com

api.internal.example.com
orders.internal.example.com
payments.internal.example.com
```

The records resolve only from associated VPCs or connected networks with appropriate DNS configuration.

This is useful for internal APIs and microservices.

---

## Corporate Network Connectivity

A private-only VPC often needs to communicate with an organization's network.

Two common mechanisms are:

### Site-to-Site VPN

```text
Corporate Network
       |
       | Encrypted VPN
       v
AWS VPC
```

### Direct Connect

```text
Corporate Network
       |
       | Dedicated connectivity
       v
AWS
       |
       v
VPC
```

The choice depends on:

- Latency requirements
- Throughput
- Reliability
- Cost
- Existing network infrastructure
- Compliance requirements

---

## Transit Gateway

Transit Gateway simplifies connectivity between multiple VPCs and on-premises networks.

Without centralized routing:

```text
VPC A <----> VPC B
VPC A <----> VPC C
VPC B <----> VPC C
```

As the number of networks grows, routing becomes difficult to maintain.

With Transit Gateway:

```text
              VPC A
                |
                |
VPC B ---- Transit Gateway ---- VPC C
                |
                |
          Corporate Network
```

This is especially useful in multi-account AWS environments.

---

## Shared Services Architecture

A private-only environment can centralize common infrastructure.

```mermaid
flowchart LR
    APP1["Application VPC"]
    APP2["Application VPC"]
    APP3["Application VPC"]
    TGW["Transit Gateway"]
    SHARED["Shared Services VPC"]

    APP1 --> TGW
    APP2 --> TGW
    APP3 --> TGW
    TGW --> SHARED

    SHARED --> DNS["Private DNS"]
    SHARED --> LOG["Logging"]
    SHARED --> SEC["Security Services"]
```

Shared services may include:

- DNS
- Monitoring
- Logging
- Security tooling
- Artifact repositories
- Internal APIs
- CI/CD services

This architecture is common in larger AWS organizations.

---

## Security Group Design

Security Groups should express workload relationships.

Example:

```text
Corporate Network
        |
        v
Internal ALB SG
        |
        v
Application SG
        |
        +---- Database SG
        |
        +---- Redis SG
        |
        +---- Endpoint SG
```

Example rules:

| Security Group | Source | Port | Purpose |
|---|---|---:|---|
| Internal ALB SG | Corporate network | 443 | Private HTTPS |
| App SG | Internal ALB SG | 8000 | Application traffic |
| DB SG | App SG | 5432 | PostgreSQL |
| Redis SG | App SG | 6379 | Redis |
| Endpoint SG | App SG | 443 | AWS service access |

Avoid broad rules such as:

```text
0.0.0.0/0
```

when a private security-group relationship can be used.

---

## Network ACLs

Network ACLs operate at the subnet boundary and are stateless.

For private-only architectures, keep NACLs simple unless there is a specific requirement for subnet-level filtering.

Overly restrictive NACLs can break:

- Application traffic
- Database connections
- DNS
- Endpoint communication
- Return traffic

Security Groups should generally provide the primary workload-level access control.

---

## NAT Gateway in a Private-Only VPC

A private-only architecture does not automatically mean NAT is forbidden.

There are two distinct designs.

### Strictly Private AWS Connectivity

```text
Application
   |
   +---- VPC Endpoint ----> AWS Services
   |
   +---- Transit Gateway --> Internal Networks
```

No general Internet egress exists.

### Private Workloads With Controlled Internet Egress

```text
Application
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

The application remains private and does not receive unsolicited Internet traffic.

However, the VPC is no longer completely isolated from the Internet.

Therefore, distinguish between:

- **Private workloads**
- **No public inbound access**
- **No Internet egress**
- **Fully isolated networking**

These are not identical concepts.

---

## Strictly Isolated VPC

A highly restricted environment may use:

```text
Private Application
       |
       +---- AWS VPC Endpoints
       |
       +---- Private Services
       |
       +---- Corporate Network
```

with no:

- Internet Gateway
- NAT Gateway
- Public IP addresses
- Internet-facing load balancers
- Public routes

This is useful for workloads with strict security or compliance requirements.

Examples include:

- Sensitive internal systems
- Regulated workloads
- Security tooling
- Internal data processing
- Controlled enterprise applications

---

## External API Access

A common design question is:

> How does a private application call an external API?

If the environment allows Internet egress:

```text
Private Application
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

If Internet access is prohibited, the external dependency needs an alternative private connectivity mechanism, such as:

- PrivateLink
- VPN
- Direct Connect
- Private interconnect
- A controlled proxy architecture

The network design must match the external service's connectivity model.

---

## AWS Service Access Without NAT

Suppose a private Django service needs to upload objects to S3.

A NAT-based architecture could be:

```text
Django
  |
  v
NAT Gateway
  |
  v
Internet Gateway
  |
  v
S3
```

A private architecture can instead use:

```text
Django
  |
  v
S3 VPC Endpoint
  |
  v
S3
```

This reduces dependency on Internet egress and can improve network control.

---

## ECR and Container Workloads

Private ECS or EKS workloads may need to pull container images from Amazon ECR.

A private architecture should provide the required private connectivity to the relevant AWS services.

Conceptually:

```text
Private ECS/EKS
      |
      +---- ECR Endpoint
      |
      +---- S3 Endpoint
      |
      +---- Other Required AWS Endpoints
```

The exact endpoint requirements depend on the container runtime, AWS services being used, and deployment architecture.

Missing required endpoints can cause private container workloads to fail during image pulls or runtime operations.

---

## Secrets Management

Private workloads often retrieve secrets dynamically.

For example:

```text
Django
  |
  | HTTPS
  v
Secrets Manager Endpoint
  |
  v
Secret
```

The application does not need public Internet access to retrieve the secret when the required private endpoint connectivity is configured.

This supports:

- Credential rotation
- Reduced secret exposure
- Centralized access control
- Auditing

---

## Systems Manager

AWS Systems Manager can provide operational access to private workloads without requiring public SSH exposure.

A common pattern is:

```text
Engineer
   |
   v
AWS Console / CLI
   |
   v
Systems Manager
   |
   v
Private Instance
```

This is preferable to:

```text
Internet
   |
   v
Public IP
   |
   v
SSH
```

for environments where public administrative access is unnecessary.

---

## Kubernetes Private Networking

A private EKS architecture commonly uses:

```text
                    VPC
                     |
        +------------+------------+
        |                         |
 Private Subnet A          Private Subnet B
        |                         |
    EKS Nodes                EKS Nodes
        |                         |
    Pods                      Pods
        |                         |
        +------------+------------+
                     |
              Private Services
```

The Kubernetes control plane and workload networking require careful consideration of:

- VPC CIDR
- Pod addressing
- Service CIDR
- Private endpoints
- AWS API access
- ECR access
- DNS
- Load balancers
- Security Groups

Subnet IP exhaustion is a common scaling problem in large Kubernetes deployments.

---

## Docker and ECS

Private ECS tasks can operate without public IP addresses.

```text
Internal ALB
     |
     v
ECS Service
     |
     +---- PostgreSQL
     +---- Redis
     +---- S3
     +---- Secrets Manager
```

AWS service access can be provided through VPC endpoints, while controlled external egress can use NAT where required.

---

## Data Tier Isolation

A private-only architecture should generally isolate data workloads further.

Example:

```text
Application Subnet
        |
        | 5432
        v
Database Subnet
```

The database route table should not provide unnecessary Internet connectivity.

Similarly:

```text
Application Subnet
        |
        | 6379
        v
Redis Subnet
```

Access should be restricted using Security Groups.

---

## Multi-AZ Design

Private-only does not mean single-AZ.

Production workloads should normally use multiple AZs where availability requirements justify it.

```text
                    Private Clients
                          |
                    Internal ALB
                    /          \
                   /            \
              AZ A              AZ B
               |                  |
          App Instances       App Instances
               |                  |
               +--------+---------+
                        |
                  Private Data
```

This protects against individual AZ failures.

---

## Failure Scenario

Consider an application deployed only in AZ A:

```text
Internal ALB
     |
     v
App A
     |
     v
Database
```

If AZ A becomes unavailable, the application is unavailable even if the database remains healthy.

A Multi-AZ architecture provides:

```text
Internal ALB
   |
   +---- App A
   |
   +---- App B
```

The application should have enough remaining capacity to serve traffic after an AZ failure.

---

## High Availability of Network Dependencies

A private architecture has additional network dependencies that must also be considered.

For example:

```text
Application
    |
    v
VPC Endpoint
    |
    v
AWS Service
```

or:

```text
Application
    |
    v
NAT Gateway
```

or:

```text
Application
    |
    v
Transit Gateway
    |
    v
Corporate Network
```

Availability planning must include these dependencies.

For Multi-AZ applications, avoid unnecessary dependence on a single-AZ network component.

---

## Observability

Private-only systems require strong network observability because failures may otherwise appear as generic connection errors.

Monitor:

### Network

- VPC Flow Logs
- Route propagation
- Transit Gateway metrics
- NAT Gateway metrics where used
- VPC endpoint health and usage
- DNS resolution

### Application

- HTTP latency
- Connection failures
- DNS errors
- Timeout rates
- Retry counts

### Database

- Connection counts
- Query latency
- CPU
- Storage
- Failover state

### Kubernetes/ECS

- Task or pod health
- Network errors
- IP utilization
- Container startup failures
- Image pull failures

---

## Troubleshooting Connectivity

When a private workload cannot reach another service, inspect the path systematically.

### Verify DNS

```bash
nslookup api.internal.example.com
```

or:

```bash
dig api.internal.example.com
```

Confirm the hostname resolves to the expected private address.

### Verify Routing

Check:

- Subnet route table
- Destination CIDR
- Transit Gateway route
- VPC peering route
- Endpoint route
- Return route

### Verify Security Groups

Check both:

- Source workload Security Group
- Destination Security Group

### Verify Network ACLs

Confirm that the subnet-level rules allow the required traffic and return traffic.

### Verify Application Listening Port

For example:

```bash
ss -lntp
```

Confirm the application is actually listening on the expected interface and port.

### Verify Flow Logs

VPC Flow Logs can help determine whether traffic is:

- Accepted
- Rejected

They are particularly useful when the application only reports a timeout.

---

## Common Mistakes

### Assuming Private Means Isolated

A private subnet can still have:

- NAT-based Internet access
- Transit Gateway connectivity
- VPC peering
- PrivateLink
- VPN connectivity

Private does not automatically mean isolated.

### Removing Internet Access Without Replacing AWS Service Connectivity

A workload may need:

- ECR
- S3
- Secrets Manager
- Systems Manager
- STS
- Other AWS APIs

Removing NAT without providing appropriate endpoints can break production workloads.

### Giving Private Workloads Public IPs

If the workload does not require public access, do not assign a public address simply because it makes connectivity easier.

### Using Public DNS for Internal Services

Prefer private DNS names for internal APIs and services.

### Hardcoding Private IP Addresses

Private IPs can change.

Use:

- Route 53 Private Hosted Zones
- Service discovery
- Internal load balancers
- Kubernetes DNS

### Exposing Internal Services Through Public Load Balancers

Not every API needs to be Internet-facing.

### Creating Excessively Broad Security Groups

Avoid:

```text
Source: VPC CIDR
Port: All
```

when specific service-to-service rules are possible.

### Forgetting Return Routes

Routing is bidirectional.

A forward route without a valid return path can still produce connection failures.

### Ignoring IP Exhaustion

Private-only architectures often contain large numbers of:

- ECS tasks
- EKS pods
- ENIs
- Interface endpoints

Subnet capacity must be planned accordingly.

---

## Production Pitfalls

### Endpoint Sprawl

Large environments may accumulate many interface endpoints.

Each endpoint should have:

- Ownership
- Security Group rules
- DNS configuration
- Cost awareness
- Lifecycle management

### Cross-AZ Traffic

A private architecture can accidentally introduce cross-AZ traffic.

For example:

```text
AZ A Application
      |
      v
AZ B Dependency
```

This may introduce:

- Additional latency
- Additional data-transfer cost
- Cross-AZ dependency

Design for locality where appropriate, but do not sacrifice reliability merely to eliminate every cross-AZ flow.

### Centralized Egress

A centralized NAT or inspection architecture can simplify governance but introduce:

- Additional latency
- Cross-AZ traffic
- Single points of failure if poorly designed
- More complex routing

Centralization should be an intentional architecture decision.

---

## Security Architecture

A strong private-only design uses multiple layers of control.

```text
Identity
   |
   v
Private Network
   |
   v
Route Tables
   |
   v
Security Groups
   |
   v
Application Authentication
   |
   v
Authorization
```

Network isolation is not a substitute for application-level authorization.

For example, an internal API should still authenticate and authorize callers even if the API is unreachable from the public Internet.

---

## Zero-Trust Considerations

A private network should not be treated as inherently trusted.

For example:

```text
Service A
    |
    | Private network
    v
Service B
```

Private connectivity does not prove that Service A should be allowed to perform every operation on Service B.

Use:

- Authentication
- Authorization
- Encryption
- Least-privilege Security Groups
- IAM
- Service identities
- Audit logging

The network boundary should complement, not replace, application security.

---

## Disaster Recovery

Private-only architectures should include network recovery planning.

Consider:

- VPC recreation through Infrastructure as Code
- Route table definitions
- Security Groups
- Endpoint configuration
- Private DNS zones
- Transit Gateway attachments
- VPN configuration
- Database recovery
- Cross-region connectivity

Infrastructure as Code is particularly important because private network configuration can be extensive.

A recovery process should be able to reconstruct the network without manually recreating dozens of console resources.

---

## Cost Considerations

Private-only networking can reduce some costs but increase others.

Potential costs include:

- Interface VPC endpoints
- NAT Gateways if Internet egress is required
- Transit Gateway
- VPN
- Direct Connect
- Internal load balancers
- Cross-AZ data transfer

Cost optimization should not simply remove private connectivity.

Instead, understand traffic patterns.

For example:

```text
Application
   |
   v
NAT Gateway
   |
   v
AWS Service
```

may be less appropriate than:

```text
Application
   |
   v
VPC Endpoint
   |
   v
AWS Service
```

when the service supports the required endpoint type.

---

## When to Use a Private-Only VPC

Use a private-only architecture when:

- Workloads are internal.
- Public Internet ingress is unnecessary.
- Corporate users access services through private connectivity.
- Security requirements favor reduced public exposure.
- Services communicate through private networking.
- AWS services can be accessed through endpoints.
- External connectivity can be provided through controlled private paths.
- Compliance requirements require stronger network isolation.

It is particularly useful for:

- Enterprise backend platforms
- Internal APIs
- Data processing
- Private microservices
- EKS/ECS workloads
- Shared services
- Regulated environments

---

## When Not to Use It

A fully private architecture may be inappropriate when the workload fundamentally requires direct public Internet access.

Examples:

- Public websites
- Public APIs
- Consumer-facing applications
- Public webhook receivers
- Public SaaS endpoints

Even these systems can still keep their backend and data tiers private.

The usual compromise is:

```text
Internet
   |
   v
Public Edge
   |
   v
Private Backend
   |
   v
Private Data
```

---

## Private-Only vs Three-Tier Public/Private Architecture

| Concern | Private-Only | Public + Private |
|---|---|---|
| Public ingress | No | Yes |
| Internal APIs | Excellent fit | Excellent fit |
| Public APIs | Requires edge outside/private integration | Natural fit |
| Internet Gateway | Not required for workload access | Common |
| NAT | Optional | Common |
| VPC endpoints | Important | Important |
| Corporate access | Common | Optional |
| External users | Through controlled private paths | Directly supported |
| Attack surface | Smaller | Larger |
| Network complexity | Higher for external access | Lower for public applications |

The correct choice depends on the application's connectivity requirements.

---

## Architecture Decision Checklist

Before choosing a private-only design, answer:

```text
[ ] Who needs to access the application?
[ ] Are all consumers inside trusted networks?
[ ] Does the application need Internet egress?
[ ] Which AWS services does the workload consume?
[ ] Which VPC endpoints are required?
[ ] Are external APIs required?
[ ] Can those external APIs be reached privately?
[ ] Is VPN or Direct Connect required?
[ ] Will multiple VPCs communicate?
[ ] Is Transit Gateway required?
[ ] Does the workload require private DNS?
[ ] Are internal load balancers required?
[ ] How will administrators access instances?
[ ] Is Systems Manager available?
[ ] Are application workloads deployed across multiple AZs?
[ ] Is subnet IP capacity sufficient?
[ ] Are Security Groups least-privilege?
[ ] Are route tables intentionally scoped?
[ ] Are VPC Flow Logs enabled where required?
[ ] Can the network be recreated through IaC?
[ ] Have AZ and dependency failure scenarios been tested?
```

---

## Example Backend Platform

A private backend platform might look like:

```text
                    Corporate Network
                           |
                    VPN / Direct Connect
                           |
                           v
                  Internal Load Balancer
                           |
              +------------+------------+
              |                         |
         Django API                FastAPI API
              |                         |
              +------------+------------+
                           |
                    Private Services
                     /      |      \
                    /       |       \
             PostgreSQL   Redis    Kafka
                    |
              VPC Endpoints
                    |
        +-----------+------------+
        |           |            |
       S3      Secrets Manager  ECR
```

No application server needs a public IP.

External connectivity is explicitly designed rather than being provided implicitly through public routing.

---

## Key Takeaways

- A private-only VPC keeps workloads off the public Internet while still allowing controlled access to AWS services, corporate networks, and private services.
- Private-only does not automatically mean zero Internet egress; NAT, Transit Gateway, VPN, Direct Connect, PrivateLink, and VPC endpoints provide different connectivity models.
- VPC endpoints, private DNS, internal load balancers, and least-privilege Security Groups are core building blocks for production private architectures.
- Removing Internet access without replacing required AWS service connectivity can break ECR, S3, Secrets Manager, Systems Manager, and other application dependencies.
- High availability requires Multi-AZ workloads and resilient network dependencies, while Infrastructure as Code should make the complete private network reproducible.