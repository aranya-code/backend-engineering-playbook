# README

## Overview

This folder contains the core networking concepts required to design, operate, and troubleshoot an Amazon VPC at production scale.

The material progresses from the VPC itself through IP addressing, subnet architecture, routing, internet connectivity, private egress, and VPC endpoints. The emphasis is on understanding **how traffic actually moves through a VPC** rather than memorizing individual AWS features.

The concepts covered here form the networking foundation for backend systems deployed with:

- Django and FastAPI
- REST and gRPC services
- Microservices
- Docker and Kubernetes
- PostgreSQL
- Redis
- Kafka
- Celery
- Nginx
- EC2
- ECS and EKS
- CI/CD workloads
- AWS managed services

The most important mental model is:

```text
VPC
 |
 +-- CIDR / IP Addressing
 |
 +-- Subnets
 |    |
 |    +-- Public Subnets
 |    +-- Private Subnets
 |
 +-- Route Tables
 |    |
 |    +-- Local Routing
 |    +-- Internet Gateway
 |    +-- NAT Gateway
 |    +-- VPC Endpoints
 |
 +-- Security Controls
      |
      +-- Security Groups
      +-- Network ACLs
```

---

## Quick Navigation

| # | Topic | Coverage |
|---|---|---|
| 01 | [Introduction to Amazon VPC](01-%20Introduction%20to%20Amazon%20VPC.md) | Amazon VPC fundamentals and the foundational AWS networking boundary. |
| 02 | [VPC Components](02-%20VPC%20Components.md) | Major components that make up a VPC and VPC architecture. |
| 03 | [VPC CIDR Blocks and IP Addressing](03-%20VPC%20CIDR%20Blocks%20and%20IP%20Addressing.md) | VPC address space design, CIDR blocks, and IP allocation. |
| 04 | [Subnets](04-%20Subnets.md) | Subnet boundaries, Availability Zone placement, and IP allocation. |
| 05 | [Public and Private Subnets](05-%20Public%20and%20Private%20Subnets.md) | How subnet routing determines internet accessibility. |
| 06 | [Route Tables and Routing](06-%20Route%20Tables%20and%20Routing.md) | How AWS determines the next hop for network traffic. |
| 07 | [Internet Gateway](07-%20Internet%20Gateway.md) | Public subnet internet access and IGW routing. |
| 08 | [NAT Gateway](08-%20NAT%20Gateway.md) | Private workload egress without accepting inbound connections. |
| 09 | [VPC Endpoints](09-%20VPC%20Endpoints.md) | VPC endpoint model and private AWS service connectivity. |
| 10 | [Gateway Endpoints](10-%20Gateway%20Endpoints.md) | Private S3 and DynamoDB connectivity through route tables. |
| 11 | [Interface Endpoints and AWS PrivateLink](11-%20Interface%20Endpoints%20and%20AWS%20PrivateLink.md) | ENI-based private service connectivity and service-level network exposure. |

---

## Recommended Reading Order

The files are intentionally numbered in dependency order.

```text
VPC
 |
 v
VPC Components
 |
 v
CIDR / IP Addressing
 |
 v
Subnets
 |
 v
Public vs Private Subnets
 |
 v
Route Tables
 |
 +----> Internet Gateway
 |
 +----> NAT Gateway
 |
 +----> VPC Endpoints
          |
          +----> Gateway Endpoints
          |
          +----> Interface Endpoints / PrivateLink
```

A strong understanding of routing should come before attempting to reason about NAT Gateways or VPC endpoints.

---

## Core Architecture Model

A typical production backend VPC can be structured around multiple Availability Zones:

```mermaid
flowchart TB
    VPC["Production VPC"]

    subgraph AZ1["Availability Zone A"]
        PUB1["Public Subnet"]
        PRIV1["Private Application Subnet"]
        DB1["Private Data Subnet"]
    end

    subgraph AZ2["Availability Zone B"]
        PUB2["Public Subnet"]
        PRIV2["Private Application Subnet"]
        DB2["Private Data Subnet"]
    end

    IGW["Internet Gateway"]
    NAT1["NAT Gateway"]
    NAT2["NAT Gateway"]
    VPCE["VPC Endpoints"]

    INTERNET["Internet"]

    VPC --> AZ1
    VPC --> AZ2

    PUB1 --> IGW
    PUB2 --> IGW

    PRIV1 --> NAT1
    PRIV2 --> NAT2

    PRIV1 --> VPCE
    PRIV2 --> VPCE

    IGW --> INTERNET
```

The important design principle is that different traffic destinations can use different paths.

```text
Public Internet
    -> Internet Gateway / NAT Gateway

AWS services supporting endpoints
    -> VPC Endpoint

Local VPC resources
    -> Local VPC routing

Other networks
    -> Peering / Transit Gateway / VPN / Direct Connect
```

---

## Traffic Flow Mental Model

When troubleshooting VPC networking, follow the packet.

For every request, ask:

```text
1. What is the source IP?
2. What is the destination IP?
3. Which subnet contains the source?
4. Which route table is associated with that subnet?
5. What is the most specific matching route?
6. What is the next hop?
7. Does the next component allow the traffic?
8. Does the destination allow the traffic?
```

For a private application calling a public API:

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
Internet Gateway
    |
    v
Internet
    |
    v
Public API
```

For a private application calling S3 through a gateway endpoint:

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
S3 Gateway Endpoint
    |
    v
Amazon S3
```

For a private application calling Secrets Manager through an interface endpoint:

```text
Application
    |
    v
Private DNS
    |
    v
Interface Endpoint ENI
    |
    v
AWS PrivateLink
    |
    v
Secrets Manager
```

---

## Public and Private Networking

The distinction between public and private subnets is fundamentally a **routing property**.

A subnet is commonly considered public when its route table provides a route toward an Internet Gateway.

```text
0.0.0.0/0
    |
    v
Internet Gateway
```

A private subnet typically does not have a direct route to the Internet Gateway.

It may instead use:

```text
0.0.0.0/0
    |
    v
NAT Gateway
```

for outbound internet access.

This distinction is more precise than simply saying:

> "Public subnet = internet-facing."

The actual traffic behavior is determined by routing, addressing, and security controls.

---

## Typical Backend Architecture

A production Django or FastAPI application might use:

```text
                    Internet
                       |
                       v
               Application Load Balancer
                       |
                       v
              Private Application Subnets
                /                  \
               /                    \
          Django/FastAPI        Django/FastAPI
               |                    |
               +---------+----------+
                         |
          +--------------+--------------+
          |              |              |
          v              v              v
      PostgreSQL       Redis           Kafka
          |
          |
     AWS Services
          |
    +-----+----------------+
    |     |        |       |
    v     v        v       v
   S3   SQS   Secrets   CloudWatch
```

The application layer generally belongs in private subnets.

Public exposure should normally be limited to the components that actually require it, such as:

- Application Load Balancers
- NAT Gateways
- Bastion infrastructure where explicitly justified
- Other intentionally public services

---

## Core Components

| Component | Primary Responsibility |
|---|---|
| VPC | Network isolation and addressing boundary |
| CIDR Block | Defines the VPC IP address space |
| Subnet | Segments the VPC IP space |
| Route Table | Determines packet forwarding |
| Internet Gateway | Enables internet connectivity for public resources |
| NAT Gateway | Provides outbound internet access for private resources |
| Gateway Endpoint | Private access to supported services such as S3 and DynamoDB |
| Interface Endpoint | Private access to supported services through ENIs |
| PrivateLink | Service-level private connectivity |
| Security Group | Stateful resource-level traffic filtering |
| Network ACL | Stateless subnet-level traffic filtering |

---

## Public vs Private Traffic Paths

| Destination | Typical Path |
|---|---|
| Another resource in the same VPC | Local route |
| Internet from public resource | Internet Gateway |
| Internet from private resource | NAT Gateway → Internet Gateway |
| S3 through gateway endpoint | Gateway Endpoint |
| DynamoDB through gateway endpoint | Gateway Endpoint |
| Secrets Manager | Interface Endpoint where configured |
| SQS | Interface Endpoint where configured |
| KMS | Interface Endpoint where configured |
| Third-party public API | NAT Gateway |
| Another VPC | VPC Peering, Transit Gateway, PrivateLink, or other connectivity mechanism |

---

## High Availability Principles

A production VPC should generally be designed around Availability Zones rather than a single subnet.

A common architecture is:

```text
                 VPC
                  |
        +---------+---------+
        |                   |
       AZ A                AZ B
        |                   |
   Public Subnet       Public Subnet
        |                   |
   Private Subnet      Private Subnet
        |                   |
   Data Subnet         Data Subnet
```

For application workloads:

```text
AZ A
 |
 +-- Application
 +-- NAT Gateway
 +-- Interface Endpoints

AZ B
 |
 +-- Application
 +-- NAT Gateway
 +-- Interface Endpoints
```

The exact design depends on workload requirements and cost constraints, but production systems should avoid accidental single-AZ dependencies.

---

## Security Model

VPC networking should be treated as multiple security layers.

```text
                    Request
                       |
                       v
                Network Routing
                       |
                       v
                 Security Group
                       |
                       v
                  Network ACL
                       |
                       v
                 AWS Service
                       |
                       v
                IAM / Policies
```

The layers solve different problems.

### Security Groups

Use Security Groups for stateful resource-level traffic controls.

Typical examples:

```text
ALB
 |
 | TCP 443
 v
Application
 |
 | TCP 5432
 v
PostgreSQL
```

### Network ACLs

NACLs operate at the subnet level and are stateless.

They are useful for explicit subnet-level network controls but are generally more difficult to manage than Security Groups for application relationships.

### IAM

IAM controls authorization to AWS APIs.

A successful network connection does not imply permission to perform an AWS operation.

---

## Production Design Principles

### Design IP Space Before Deployment

CIDR planning becomes difficult to change later.

Consider:

- Current workload size
- Future subnet requirements
- Multi-AZ expansion
- VPC peering
- Transit Gateway
- Hybrid networking
- Kubernetes
- Shared services
- Organizational address allocation

Avoid selecting a CIDR simply because it is convenient for a small development environment.

---

### Separate Workload Responsibilities

A common production model is:

```text
Public Subnets
    |
    +-- Load Balancers
    +-- NAT Gateways

Private Application Subnets
    |
    +-- Django
    +-- FastAPI
    +-- Workers
    +-- Microservices

Private Data Subnets
    |
    +-- PostgreSQL
    +-- Redis
    +-- Other data services
```

The exact subnet strategy varies by architecture, but separating responsibilities improves security and operational clarity.

---

### Keep Application Servers Private

Backend workloads generally should not require public IP addresses.

Prefer:

```text
Internet
   |
   v
Load Balancer
   |
   v
Private Application
```

rather than:

```text
Internet
   |
   v
Public Application Server
```

This reduces the direct attack surface.

---

### Use Least-Connectivity Design

Do not connect networks simply because connectivity is technically possible.

Prefer:

```text
Application
    |
    +-- PostgreSQL
    |
    +-- Redis
    |
    +-- SQS
```

over:

```text
Application
    |
    +-- Entire VPC
```

Service-specific connectivity is particularly valuable with PrivateLink.

---

## Cost Considerations

VPC design has cost implications.

Common cost areas include:

- NAT Gateway hourly charges
- NAT Gateway data processing
- Interface endpoint hourly charges
- Interface endpoint data processing
- Cross-AZ traffic
- Transit Gateway usage
- Public IPv4 addresses
- Load Balancers
- VPN or Direct Connect

A useful optimization strategy is to understand traffic before optimizing infrastructure.

For example:

```text
Large AWS service traffic
        |
        v
Evaluate VPC Endpoint

Public internet traffic
        |
        v
Evaluate NAT Gateway
```

Do not introduce architecture purely to reduce one line item while increasing another significantly.

---

## Monitoring and Troubleshooting

VPC troubleshooting should be systematic.

Useful tools and services include:

- VPC Flow Logs
- Reachability Analyzer
- CloudWatch
- CloudTrail
- Route 53 Resolver logs
- AWS CLI
- EC2 network inspection
- Load Balancer logs
- Application logs

A useful troubleshooting sequence is:

```text
DNS
 |
 v
IP Address
 |
 v
Subnet
 |
 v
Route Table
 |
 v
Next Hop
 |
 v
Security Group
 |
 v
NACL
 |
 v
Destination
 |
 v
Application
```

Avoid immediately modifying multiple networking resources at once.

Change one variable, test, and identify which layer caused the failure.

---

## Common Mistakes

### Treating Public and Private as Security Labels

A public subnet is not automatically insecure, and a private subnet is not automatically secure.

Routing determines internet reachability; Security Groups, NACLs, IAM, authentication, and application controls determine additional security boundaries.

### Giving Applications Public IPs Unnecessarily

Backend workloads generally do not need direct internet exposure.

Use load balancers or other controlled ingress mechanisms.

### Ignoring CIDR Overlap

Overlapping CIDRs can prevent or complicate connectivity between networks.

This becomes particularly problematic with:

- VPC peering
- Transit Gateway
- VPN
- Direct Connect
- Multi-account architectures

### Using One NAT Gateway Without Considering AZ Failure

A single NAT Gateway can become a cross-AZ dependency and availability concern.

### Assuming Security Groups Control Everything

Security Groups do not replace:

- IAM
- NACLs
- Endpoint policies
- Resource policies
- Application authentication

### Ignoring DNS

Many apparently network-related AWS problems are actually DNS problems.

### Using NAT for AWS Services Without Evaluating Endpoints

Supported AWS services may be reachable privately through VPC endpoints.

Evaluate the traffic path and cost before routing everything through NAT.

---

## Interview Traps

### What makes a subnet public?

A route table associated with the subnet has a route that provides connectivity to an Internet Gateway, together with the addressing and security configuration required for internet communication.

### Does assigning a public IP automatically make a subnet public?

No.

Public connectivity requires appropriate routing through an Internet Gateway.

### Can private subnets access the internet?

Yes, typically through a NAT Gateway or another appropriate egress mechanism.

### Can a private subnet receive unsolicited internet traffic through NAT?

A NAT Gateway provides outbound connectivity for private resources; it is not a general inbound internet gateway for those resources.

### What determines where a packet goes?

The route table associated with the source subnet, using the most specific matching route.

### Gateway Endpoint vs Interface Endpoint?

Gateway endpoints integrate with route tables and are used for supported services such as S3 and DynamoDB. Interface endpoints use ENIs and AWS PrivateLink.

### Does a VPC isolate applications from each other?

A VPC provides network isolation, but applications still require appropriate Security Groups, routing, IAM, authentication, and authorization controls.

---

## Practical Backend Engineering Checklist

Before deploying a production backend into a VPC, verify:

```text
[ ] VPC CIDR is planned for future growth
[ ] CIDRs do not conflict with connected networks
[ ] Multiple AZs are used where required
[ ] Application workloads are private
[ ] Public ingress is intentionally controlled
[ ] Route tables are explicitly understood
[ ] NAT requirements are documented
[ ] NAT placement is highly available where required
[ ] S3/DynamoDB endpoint requirements are evaluated
[ ] Interface endpoint requirements are evaluated
[ ] Security Groups follow least privilege
[ ] NACLs are understood and tested
[ ] DNS behavior is verified
[ ] VPC Flow Logs are considered
[ ] Cross-AZ traffic is understood
[ ] Endpoint and NAT costs are understood
[ ] Disaster recovery networking is documented
[ ] Infrastructure is managed through IaC
```

---

## Infrastructure as Code

For production environments, prefer Infrastructure as Code over manually creating networking components.

Common options include:

- Terraform
- AWS CloudFormation
- AWS CDK

A VPC should generally be treated as a version-controlled infrastructure boundary.

Changes to:

- CIDRs
- Subnets
- Route Tables
- NAT Gateways
- Endpoints
- Security Groups
- NACLs

should be reviewed like application code.

---

## Final Architecture Mental Model

The entire section can be reduced to one traffic model:

```text
                         Internet
                            |
                            v
                    Internet Gateway
                            |
             +--------------+--------------+
             |                             |
        Public Subnet                 Public Subnet
             |                             |
        Load Balancer                Load Balancer
             |                             |
             +--------------+--------------+
                            |
                     Private Subnets
                     /             \
                    /               \
              Application        Application
                    |               |
          +---------+-------+-------+---------+
          |         |       |       |         |
          v         v       v       v         v
       PostgreSQL Redis   Kafka   AWS APIs   S3
                                      |       |
                                      v       v
                              Interface EP  Gateway EP
                                      |
                                      v
                                  PrivateLink

Private Applications
        |
        v
   NAT Gateway
        |
        v
      Internet
```

The key engineering skill is not memorizing each AWS networking component independently. It is being able to look at a source, destination, route table, and security configuration and explain **exactly how the packet moves through the architecture**.

## Key Takeaways

- A VPC is the foundational AWS networking boundary, with CIDRs, subnets, routing, gateways, endpoints, and security controls working together to determine traffic behavior.
- Public and private subnet behavior is primarily a routing concern; security requires additional controls such as Security Groups, NACLs, IAM, and application-level authorization.
- Production backend workloads should generally remain private and use controlled ingress, deliberate outbound paths, and multi-AZ architecture where availability requires it.
- NAT Gateways, gateway endpoints, interface endpoints, and PrivateLink solve different connectivity problems and should be selected according to destination, security requirements, availability, and cost.
- The most important VPC troubleshooting skill is tracing the complete traffic path from DNS and source subnet through routing and security controls to the destination.