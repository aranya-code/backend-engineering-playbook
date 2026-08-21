# 01- VPC Network Architecture

## Overview

A production Amazon VPC is not simply a collection of subnets. It is a network architecture that determines how applications communicate with the internet, AWS services, databases, other VPCs, and external systems.

A well-designed VPC architecture should provide:

- Clear network boundaries
- Predictable routing
- Multi-AZ availability
- Private application workloads
- Controlled ingress and egress
- Least-privilege network access
- Private connectivity to AWS services where appropriate
- Address space that supports future growth
- Observable and troubleshootable traffic paths
- Infrastructure-as-Code management

A typical backend architecture separates workloads into public, private application, and private data tiers:

```text
                         Internet
                            |
                            v
                  Internet Gateway
                            |
                    Public Subnets
                            |
                 Application Load Balancer
                            |
              +-------------+-------------+
              |                           |
              v                           v
       Private App Subnet A       Private App Subnet B
              |                           |
        Django / FastAPI             Django / FastAPI
              |                           |
        +-----+------+              +-----+------+
        |            |              |            |
        v            v              v            v
   PostgreSQL      Redis       PostgreSQL      Redis
              \          \      /          /
               +----------+----+----------+
                          |
                   AWS Services
                          |
              +-----------+-----------+
              |                       |
              v                       v
       VPC Endpoints             NAT Gateway
              |                       |
              v                       v
        AWS Services              Internet
```

The architecture should be driven by traffic requirements rather than by simply following a fixed subnet template.

---

## Architecture Goals

A production VPC should answer several questions explicitly:

| Question | Architecture Concern |
|---|---|
| Where can users enter the system? | Ingress |
| Which resources are publicly reachable? | Exposure |
| How do private workloads reach the internet? | Egress |
| How do applications reach AWS services? | VPC endpoints / NAT |
| How do services communicate? | Security Groups / routing |
| How is traffic distributed across AZs? | Multi-AZ design |
| How are networks connected? | Peering / Transit Gateway / VPN / PrivateLink |
| How is IP space allocated? | CIDR planning |
| How are failures detected? | Monitoring / flow logs |
| How is the architecture recovered? | IaC / disaster recovery |

A senior-level VPC design starts with these questions before selecting individual AWS networking components.

---

## VPC Network Layers

A useful way to reason about the architecture is to separate it into layers.

```text
VPC
 |
 +-- Addressing
 |    |
 |    +-- CIDR
 |    +-- IP Allocation
 |
 +-- Segmentation
 |    |
 |    +-- Availability Zones
 |    +-- Subnets
 |
 +-- Routing
 |    |
 |    +-- Route Tables
 |    +-- Local Routes
 |    +-- Internet Gateway
 |    +-- NAT Gateway
 |    +-- VPC Endpoints
 |
 +-- Security
 |    |
 |    +-- Security Groups
 |    +-- Network ACLs
 |    +-- IAM
 |    +-- Endpoint Policies
 |
 +-- Connectivity
 |    |
 |    +-- Internet
 |    +-- Other VPCs
 |    +-- On-premises
 |    +-- AWS Services
 |
 +-- Observability
      |
      +-- VPC Flow Logs
      +-- CloudWatch
      +-- CloudTrail
      +-- Reachability Analyzer
```

This layered model makes troubleshooting considerably easier.

---

## Reference Production Architecture

A common multi-AZ backend architecture uses three subnet categories:

```text
VPC
 |
 +-- Availability Zone A
 |    |
 |    +-- Public Subnet
 |    +-- Private Application Subnet
 |    +-- Private Data Subnet
 |
 +-- Availability Zone B
      |
      +-- Public Subnet
      +-- Private Application Subnet
      +-- Private Data Subnet
```

The public subnets can contain components that require controlled internet connectivity:

- Application Load Balancers
- NAT Gateways
- Other intentionally public infrastructure

The private application subnets can contain:

- Django
- FastAPI
- REST APIs
- gRPC services
- Celery workers
- Microservices
- ECS tasks
- EKS workloads
- Internal services

The private data subnets can contain:

- PostgreSQL
- Redis
- Kafka
- Other stateful workloads

Managed AWS services may be accessed through private connectivity mechanisms where appropriate.

---

## Multi-AZ Architecture

Availability Zones provide independent failure domains within an AWS Region.

A production workload should generally distribute critical stateless components across multiple AZs.

```mermaid
flowchart TB
    CLIENT["Internet Clients"]
    ALB["Application Load Balancer"]

    subgraph VPC["Production VPC"]
        subgraph AZA["Availability Zone A"]
            PUBA["Public Subnet"]
            APPA["Private App Subnet"]
            DATAA["Private Data Subnet"]
            NAT_A["NAT Gateway"]
        end

        subgraph AZB["Availability Zone B"]
            PUBB["Public Subnet"]
            APPB["Private App Subnet"]
            DATAB["Private Data Subnet"]
            NAT_B["NAT Gateway"]
        end
    end

    CLIENT --> ALB
    ALB --> APPA
    ALB --> APPB

    APPA --> NAT_A
    APPB --> NAT_B

    APPA --> DATAA
    APPB --> DATAB
```

The exact placement of data services depends on the managed service or database architecture. The important principle is to avoid making one AZ an unnecessary dependency for the entire application.

---

## Availability Zone Locality

Where possible, traffic should remain within the same AZ when doing so improves availability, latency, or cost.

For example:

```text
AZ A Application
      |
      v
AZ A Dependency
```

is generally preferable to unnecessarily routing:

```text
AZ A Application
      |
      v
AZ B Dependency
```

However, locality should not override correct availability architecture.

For example, a highly available database may intentionally span multiple AZs even though this can introduce cross-AZ replication traffic.

The design should optimize the complete system rather than one individual network path.

---

## CIDR Architecture

The VPC CIDR determines the available private IPv4 address space.

Example:

```text
VPC
10.0.0.0/16
```

Possible subdivision:

```text
10.0.0.0/20   Public Subnets
10.0.16.0/20  Private Application
10.0.32.0/20  Private Data
10.0.48.0/20  Reserved
```

A production CIDR plan should reserve address space for future requirements.

Potential future consumers include:

- Additional AZs
- Kubernetes nodes and pods
- Databases
- Load balancers
- VPC endpoints
- Internal services
- Transit Gateway-connected networks
- Hybrid connectivity
- Additional environments

---

## CIDR Planning for Multiple Environments

Do not casually reuse the same CIDR ranges across networks that may eventually need connectivity.

A larger organization might use:

```text
Production VPC
10.10.0.0/16

Staging VPC
10.20.0.0/16

Development VPC
10.30.0.0/16

Shared Services VPC
10.40.0.0/16
```

This simplifies future connectivity through:

- Transit Gateway
- VPC Peering
- VPN
- Direct Connect
- Other network integration mechanisms

CIDR overlap is one of the most expensive networking design mistakes to discover after an environment has already grown.

---

## Subnet Architecture

A subnet is an IP range within a VPC associated with a single Availability Zone.

A typical production layout might be:

| Subnet Type | Example | Typical Workloads |
|---|---|---|
| Public | `10.10.0.0/20` | ALB, NAT Gateway |
| Private Application | `10.10.16.0/20` | Django, FastAPI, workers |
| Private Data | `10.10.32.0/20` | PostgreSQL, Redis |
| Reserved | `10.10.48.0/20` | Future expansion |

The exact ranges are architecture-specific.

Avoid creating tiny subnets simply because the current workload is small.

---

## Public and Private Subnets

The public/private distinction is primarily determined by routing.

A public subnet typically has a route toward an Internet Gateway:

```text
0.0.0.0/0
    |
    v
Internet Gateway
```

A private application subnet may instead have:

```text
0.0.0.0/0
    |
    v
NAT Gateway
```

A completely isolated subnet might have no default internet route.

```text
Private Application
        |
        +---- VPC local traffic
        |
        +---- VPC Endpoint
        |
        +---- No public internet route
```

Do not treat "private" as synonymous with "cannot communicate externally." Private resources can have controlled outbound connectivity.

---

## Route Table Architecture

Route tables determine the next hop for traffic.

Example public route table:

```text
Destination       Target
-----------       ------
10.10.0.0/16      local
0.0.0.0/0         igw-xxxxxxxx
```

Private application route table:

```text
Destination       Target
-----------       ------
10.10.0.0/16      local
0.0.0.0/0         nat-xxxxxxxx
```

A subnet's routing behavior is therefore determined by its associated route table.

---

## Longest Prefix Matching

AWS routing uses the most specific matching route.

For example:

```text
10.10.0.0/16    -> local
10.10.20.0/24   -> Transit Gateway
0.0.0.0/0       -> NAT Gateway
```

Traffic destined for:

```text
10.10.20.50
```

matches both:

```text
10.10.0.0/16
10.10.20.0/24
```

but the `/24` route is more specific and therefore takes precedence.

This is fundamental when troubleshooting complex VPC routing.

---

## Internet Gateway Architecture

An Internet Gateway provides connectivity between a VPC and the internet for appropriately configured resources.

Typical path:

```text
Public Application
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

For backend architectures, direct public access should generally be minimized.

A preferred architecture is:

```text
Internet
    |
    v
Application Load Balancer
    |
    v
Private Application
```

rather than exposing application servers directly.

---

## NAT Gateway Architecture

Private applications often require outbound access to public APIs.

Example:

```text
FastAPI
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
External API
```

NAT provides outbound connectivity without making the private workload directly reachable from the internet.

A multi-AZ production design commonly uses NAT Gateway resources per AZ when the availability and traffic architecture justify the additional cost.

---

## VPC Endpoint Architecture

AWS service traffic does not always need to traverse NAT.

For supported services, VPC endpoints can provide private connectivity.

```text
Private Application
       |
       +----> Gateway Endpoint ----> S3
       |
       +----> Interface Endpoint -> Secrets Manager
       |
       +----> Interface Endpoint -> SQS
       |
       +----> Interface Endpoint -> KMS
```

This can improve isolation and reduce unnecessary NAT dependency.

---

## Gateway Endpoints

Gateway endpoints are primarily used for supported AWS services such as:

- Amazon S3
- Amazon DynamoDB

They integrate with route tables.

Example:

```text
Private Subnet
      |
      v
Route Table
      |
      v
Gateway Endpoint
      |
      v
S3
```

They do not use interface endpoint ENIs.

---

## Interface Endpoints

Interface endpoints create ENIs in selected subnets.

Example:

```text
Private Application
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
AWS Service
```

They are commonly used for AWS services that support interface endpoints, such as:

- Secrets Manager
- SQS
- KMS
- CloudWatch Logs
- Systems Manager
- ECR-related APIs

The exact endpoint requirements depend on the AWS service and Region.

---

## Security Group Architecture

Security Groups should express workload relationships.

Example:

```text
Internet
   |
   v
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

This is preferable to broad CIDR-based rules when the relationship can be expressed using Security Group references.

For example:

```text
Database inbound:
TCP 5432
Source: sg-application
```

instead of:

```text
Database inbound:
TCP 5432
Source: 0.0.0.0/0
```

---

## Security Boundaries

A mature architecture combines multiple controls.

```text
                 Network Boundary
                        |
                        v
                    VPC / Subnet
                        |
                        v
                    Routing
                        |
                        v
                 Security Group
                        |
                        v
                   Application
                        |
                        v
              IAM / Application Auth
```

Different layers address different threats.

| Layer | Main Responsibility |
|---|---|
| VPC | Network isolation |
| Subnet | Network segmentation |
| Route Table | Traffic forwarding |
| Security Group | Stateful network filtering |
| NACL | Stateless subnet filtering |
| IAM | AWS API authorization |
| Application Authentication | User/service identity |
| Application Authorization | Business-level permissions |

No single layer should be expected to provide complete security.

---

## Ingress Architecture

For a public REST API:

```text
Client
  |
  v
DNS
  |
  v
Application Load Balancer
  |
  v
Private Application Subnet
  |
  v
Django / FastAPI
```

The application instances do not need public IP addresses.

This architecture provides a clear ingress boundary.

The ALB can handle:

- TLS termination
- HTTP routing
- Health checks
- Target distribution
- Availability Zone distribution

The application layer can focus on application processing.

---

## Internal Service Communication

Microservices may communicate privately:

```text
API Service
    |
    | HTTP / gRPC
    v
User Service
    |
    | HTTP / gRPC
    v
Payment Service
```

The services can remain private.

Security Groups should define which service-to-service connections are allowed.

For example:

```text
sg-api
  |
  | TCP 50051
  v
sg-payment
```

for a gRPC service listening on port `50051`.

---

## Database Architecture

Databases should generally not be directly reachable from the internet.

Typical architecture:

```text
Internet
    |
    v
ALB
    |
    v
Application
    |
    v
PostgreSQL
```

Security Group relationships:

```text
ALB SG
  |
  | 443
  v
Application SG
  |
  | 5432
  v
Database SG
```

The database should not require:

```text
0.0.0.0/0
```

for normal application connectivity.

---

## Redis Architecture

A Redis deployment follows the same principle.

```text
Django / FastAPI
       |
       | TCP 6379
       v
Redis
```

The Redis Security Group should allow access only from approved application Security Groups.

Avoid exposing Redis publicly.

Redis should not be treated as an internet-facing service.

---

## Kafka Architecture

Kafka introduces additional networking considerations because clients communicate with brokers and receive broker addresses in metadata.

A private Kafka architecture should therefore account for:

- Broker subnet placement
- Security Groups
- Advertised addresses
- DNS
- Client-to-broker ports
- Inter-broker communication
- Cross-AZ traffic

Conceptually:

```text
Application
     |
     | Kafka protocol
     v
Kafka Brokers
 /     |     \
AZ A  AZ B   AZ C
```

For high-throughput systems, network locality and cross-AZ traffic can materially affect cost and performance.

---

## Nginx in a VPC

Nginx can operate as:

- Reverse proxy
- Internal gateway
- Ingress component
- TLS termination layer
- Service routing layer

Example:

```text
ALB
 |
 v
Nginx
 |
 +---- Django
 |
 +---- FastAPI
 |
 +---- Internal APIs
```

Whether Nginx is required depends on the application and platform architecture.

Avoid adding Nginx merely because it is familiar if the ALB, ingress controller, or service mesh already provides the required functionality.

---

## Containerized Workloads

For ECS or EKS workloads, networking becomes more important because workload IP consumption can grow quickly.

A simplified EKS architecture:

```text
VPC
 |
 +-- Public Subnets
 |      |
 |      +-- Load Balancer
 |
 +-- Private Subnets
        |
        +-- Kubernetes Nodes
        +-- Pods
        +-- VPC Endpoints
        +-- NAT
```

Depending on the CNI and networking configuration, pods may consume VPC IP addresses directly.

This makes CIDR planning particularly important for Kubernetes.

---

## VPC and CI/CD

CI/CD systems may need access to private resources.

For example:

```text
GitHub Actions
      |
      v
Deployment Mechanism
      |
      v
Private AWS Environment
      |
      +-- ECS
      +-- EKS
      +-- Database
      +-- Internal APIs
```

Avoid exposing private databases or internal services simply to make CI/CD easier.

Prefer controlled deployment mechanisms such as:

- AWS-native deployment services
- Self-hosted runners where justified
- Private connectivity
- IAM roles and short-lived credentials

---

## Service-to-Service Architecture

A typical backend system may look like:

```mermaid
flowchart LR
    CLIENT["Clients"]
    ALB["Public ALB"]

    subgraph VPC["VPC"]
        API["API Service"]
        USER["User Service"]
        PAYMENT["Payment Service"]
        WORKER["Celery Workers"]
        REDIS["Redis"]
        DB["PostgreSQL"]
        KAFKA["Kafka"]
    end

    CLIENT --> ALB
    ALB --> API

    API --> USER
    API --> PAYMENT
    API --> REDIS
    API --> DB
    API --> KAFKA

    WORKER --> KAFKA
    WORKER --> DB
    WORKER --> REDIS
```

The network architecture should make these relationships explicit.

---

## VPC Connectivity Options

Different connectivity mechanisms solve different problems.

| Requirement | Typical AWS Mechanism |
|---|---|
| Internet access from public resources | Internet Gateway |
| Internet egress from private resources | NAT Gateway |
| S3 private connectivity | Gateway Endpoint |
| DynamoDB private connectivity | Gateway Endpoint |
| AWS service private connectivity | Interface Endpoint |
| Service exposure to other VPCs/accounts | PrivateLink |
| VPC-to-VPC connectivity | VPC Peering |
| Many-VPC centralized connectivity | Transit Gateway |
| On-premises connectivity | VPN / Direct Connect |
| Public application ingress | ALB / other load balancer |

Selecting the correct connectivity primitive is an architectural decision.

---

## VPC Peering vs PrivateLink

These mechanisms should not be treated as interchangeable.

### VPC Peering

```text
VPC A
  |
  | Network connectivity
  v
VPC B
```

### PrivateLink

```text
VPC A
  |
  | Service connectivity
  v
Specific Service in VPC B
```

Use VPC peering when broader network connectivity is required.

Use PrivateLink when consumers should access a specific service without broad network access to the provider network.

---

## VPC Peering vs Transit Gateway

For a small number of VPCs:

```text
VPC A <----> VPC B
```

may be sufficient.

As the number of VPCs grows, direct peering can become difficult to manage.

```text
VPC A
 |\ 
 | \
 |  \ 
 VPC B VPC C
 |      |
 VPC D VPC E
```

A Transit Gateway can provide centralized connectivity:

```text
              Transit Gateway
             /       |       \
            /        |        \
         VPC A      VPC B      VPC C
```

The correct choice depends on traffic patterns, routing requirements, organizational boundaries, and scale.

---

## Hybrid Connectivity

A production organization may need connectivity between AWS and on-premises infrastructure.

```text
On-Premises
     |
     | VPN / Direct Connect
     v
AWS Connectivity Layer
     |
     v
Transit Gateway
     |
 +---+---+
 |       |
VPC A   VPC B
```

CIDR planning becomes critical because overlapping address spaces can complicate hybrid routing.

---

## DNS Architecture

DNS is a fundamental part of VPC networking.

Typical flow:

```text
Application
    |
    v
VPC DNS Resolver
    |
    +---- AWS service hostname
    |
    +---- Internal service
    |
    +---- Public hostname
```

DNS determines which IP address the application attempts to reach.

In private architectures, DNS may also determine whether traffic reaches:

- An interface endpoint
- An internal load balancer
- A private service
- A public endpoint

Therefore, DNS failures can look like routing failures.

---

## Observability Architecture

Network observability should cover multiple layers.

```text
                    VPC
                     |
        +------------+-------------+
        |            |             |
        v            v             v
   VPC Flow Logs  CloudTrail   DNS Logs
        |            |             |
        +------------+-------------+
                     |
                     v
               Monitoring
                     |
                     v
              Alerting / SIEM
```

Useful signals include:

- Rejected network flows
- Unexpected source IPs
- Unexpected destination IPs
- NAT traffic volume
- Cross-AZ traffic
- Endpoint usage
- DNS failures
- Load balancer failures
- Application connection timeouts

---

## VPC Flow Logs

VPC Flow Logs can help answer:

```text
Who attempted to connect?
Where?
On which port?
Was the traffic accepted or rejected?
```

Example conceptual record:

```text
Source:      10.10.16.25
Destination: 10.10.32.15
Port:        5432
Protocol:    TCP
Action:      ACCEPT
```

Flow Logs are particularly useful when debugging Security Group, NACL, and routing issues.

They should be integrated into the organization's logging and retention strategy.

---

## Troubleshooting Methodology

When an application cannot reach a destination, avoid randomly modifying infrastructure.

Follow the packet.

### Identify the Source

```text
Source workload
Source IP
Source subnet
Source AZ
```

### Identify the Destination

```text
Destination hostname
Resolved IP
Destination subnet
Destination service
```

### Verify DNS

```bash
dig example.internal
```

### Inspect Routes

Determine which route table is associated with the source subnet.

### Identify the Next Hop

Possible targets include:

```text
local
igw
nat
vpce
tgw
pcx
vgw
```

### Check Security Groups

Verify:

```text
Source SG
Destination SG
Port
Protocol
```

### Check NACLs

Remember that NACLs are stateless.

### Check Application Behavior

A successful TCP connection does not guarantee that the application protocol will succeed.

---

## Common Architecture Mistakes

### Single-AZ Application Architecture

Placing all application infrastructure in one AZ creates an avoidable failure domain.

### One NAT Gateway for Everything

A single NAT Gateway may create:

- Single-AZ dependency
- Cross-AZ traffic
- Availability concerns
- Concentrated bandwidth

Evaluate NAT placement against cost and availability requirements.

### Overlapping CIDRs

This can become a major problem when networks need to communicate later.

### Public Application Servers

Directly exposing application servers increases the attack surface.

### Broad Security Group Rules

Rules such as:

```text
TCP 5432
0.0.0.0/0
```

are rarely appropriate for a production PostgreSQL database.

### Treating NACLs as the Primary Application Firewall

Security Groups are usually easier to reason about for stateful application relationships.

### Ignoring Cross-AZ Traffic

Cross-AZ communication can affect:

- Latency
- Cost
- Architecture
- Failure behavior

### Using NAT for Everything

AWS service traffic may be better served through VPC endpoints.

### Creating Too Many Endpoints

Interface endpoints introduce additional cost and operational resources.

### Ignoring DNS

Private architectures frequently depend on correct DNS behavior.

---

## Scalability Considerations

VPC architecture must scale with both infrastructure and traffic.

Consider:

### IP Capacity

Large-scale systems can exhaust subnet addresses.

### Number of AZs

More AZs improve resilience but increase networking resources.

### Endpoint Count

Each interface endpoint can consume subnet IP capacity.

### NAT Throughput

High-volume workloads may require careful NAT architecture.

### Cross-AZ Traffic

Large service-to-service traffic flows can become expensive.

### Kubernetes

Pod networking can consume substantial VPC IP capacity.

### Microservices

A growing number of services increases Security Group, DNS, routing, and observability complexity.

---

## Reliability Considerations

A reliable VPC architecture should avoid unnecessary single points of failure.

Typical design:

```text
                    ALB
                 /       \
                /         \
              AZ A        AZ B
               |            |
          App Instances App Instances
               |            |
           NAT A          NAT B
               |            |
               +-----+------+
                     |
                  Services
```

For stateful systems, use the availability mechanisms provided by the relevant AWS service or database architecture.

Do not assume that simply placing two instances in two AZs automatically creates a highly available database.

---

## Disaster Recovery

VPC infrastructure should be reproducible.

Store definitions for:

- VPC
- Subnets
- Route Tables
- Internet Gateways
- NAT Gateways
- VPC Endpoints
- Security Groups
- NACLs
- Load Balancers
- DNS configuration
- Connectivity infrastructure

using Infrastructure as Code.

A disaster recovery environment should have explicitly documented:

```text
CIDR plan
+
Subnet plan
+
Routing
+
Security controls
+
DNS
+
External connectivity
+
AWS service endpoints
```

The objective is not merely to recreate a VPC, but to recreate the complete traffic architecture.

---

## Infrastructure as Code

A production VPC should generally be managed through:

- Terraform
- AWS CloudFormation
- AWS CDK

Example Terraform structure:

```text
terraform/
├── modules/
│   ├── vpc/
│   ├── security-groups/
│   ├── endpoints/
│   └── networking/
│
├── environments/
│   ├── dev/
│   ├── staging/
│   └── production/
│
└── main.tf
```

Network changes should go through the same review process as application changes.

---

## Cost Optimization

Cost optimization should consider the entire traffic path.

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

may be replaced with:

```text
Application
    |
    v
VPC Endpoint
    |
    v
AWS Service
```

where supported and economically justified.

But endpoint costs must also be evaluated.

Consider:

```text
NAT hourly cost
+
NAT data processing
+
Endpoint hourly cost
+
Endpoint data processing
+
Cross-AZ traffic
+
Operational complexity
```

Optimize the architecture rather than one component in isolation.

---

## Production Review Checklist

Before approving a VPC architecture, verify:

```text
[ ] CIDR space supports future growth
[ ] CIDRs do not overlap with connected networks
[ ] Critical workloads span appropriate AZs
[ ] Public resources are intentionally exposed
[ ] Application workloads are private where possible
[ ] Route tables are explicitly documented
[ ] Internet Gateway usage is intentional
[ ] NAT Gateway architecture is understood
[ ] VPC endpoint requirements are evaluated
[ ] Security Groups follow least privilege
[ ] NACLs are intentionally configured
[ ] DNS architecture is documented
[ ] Cross-AZ traffic is understood
[ ] Network observability is enabled where required
[ ] Infrastructure is managed through IaC
[ ] Disaster recovery networking is reproducible
[ ] AWS service dependencies are documented
[ ] Cost implications are understood
```

---

## Interview Traps

### Is a VPC itself public or private?

A VPC is a network boundary. Public or private behavior is determined by the resources, subnet routing, addressing, and connectivity configuration inside it.

### What makes a subnet public?

A subnet is generally considered public when its route table provides a path through an Internet Gateway.

### Does a private subnet mean no internet access?

No. A private subnet can have controlled outbound internet access through a NAT Gateway.

### Does NAT allow inbound internet connections?

A NAT Gateway provides outbound connectivity for private resources. It is not a general inbound access mechanism.

### Why use multiple AZs?

To reduce the impact of an Availability Zone failure and distribute workloads across independent failure domains.

### Why keep application servers private?

To reduce direct internet exposure and force inbound traffic through controlled entry points such as load balancers.

### Why plan CIDRs carefully?

Because overlapping address ranges can prevent or complicate future connectivity between VPCs, on-premises networks, and other environments.

### VPC Peering vs PrivateLink?

VPC peering provides network-level connectivity between VPCs. PrivateLink provides service-level connectivity to a specific exposed service.

### NAT Gateway vs VPC Endpoint?

NAT Gateway is primarily for outbound connectivity to public destinations. VPC endpoints provide private connectivity to supported AWS services.

### Security Group vs NACL?

Security Groups are stateful and associated with network interfaces/resources. NACLs are stateless and associated with subnets.

---

## Senior-Level Architecture Principles

A senior engineer should evaluate a VPC in terms of **traffic flows**, not isolated AWS services.

For every major dependency, identify:

```text
Source
  |
  v
DNS
  |
  v
Route
  |
  v
Network Control
  |
  v
Next Hop
  |
  v
Destination
```

Then evaluate:

```text
Security
Availability
Latency
Cost
Scalability
Observability
Operational Complexity
Disaster Recovery
```

For example, for a FastAPI service calling PostgreSQL:

```text
FastAPI
  |
  | DNS
  v
PostgreSQL Endpoint
  |
  v
Route
  |
  v
Security Group
  |
  v
PostgreSQL
```

For a Celery worker calling a public third-party API:

```text
Celery Worker
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
Third-Party API
```

For a service reading a secret:

```text
Django
  |
  v
AWS SDK
  |
  v
Private DNS
  |
  v
Interface Endpoint
  |
  v
Secrets Manager
```

Being able to explain these paths precisely is more valuable than memorizing isolated definitions.

## Key Takeaways

- A production VPC should be designed around explicit traffic flows, failure domains, address planning, security boundaries, and operational requirements rather than simply creating public and private subnets.
- Multi-AZ application architecture, deliberate routing, private workloads, controlled ingress, and controlled egress form the foundation of a resilient backend network.
- NAT Gateways, VPC endpoints, Internet Gateways, Transit Gateway, VPC Peering, and PrivateLink solve different connectivity problems and should be selected based on the actual traffic requirement.
- CIDR planning, DNS, Security Groups, route tables, and cross-AZ traffic become increasingly important as systems scale into microservices, Kubernetes, hybrid networking, and multi-account architectures.
- The strongest VPC design and troubleshooting skill is the ability to trace a request from source through DNS, routing, security controls, and network hops to its destination while evaluating security, availability, performance, cost, and operability.