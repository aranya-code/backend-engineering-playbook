# 14- Production VPC Design

## Overview

A production VPC is not simply a collection of subnets, route tables, and security groups. It is a network architecture that establishes the connectivity, isolation, failure boundaries, security controls, and operational model for backend workloads running in AWS.

A production VPC should be designed around several independent concerns:

- Network segmentation
- Availability Zones
- Internet ingress and egress
- Private service connectivity
- Routing
- Security boundaries
- Hybrid connectivity
- Multi-account connectivity
- Observability
- Scalability
- Failure recovery
- Cost control

For a typical backend platform, the desired traffic model is:

```text
Internet
   |
   v
Route 53
   |
   v
CloudFront / WAF
   |
   v
Application Load Balancer
   |
   v
Private Application Subnets
   |
   +---------> PostgreSQL
   |
   +---------> Redis
   |
   +---------> Kafka
   |
   +---------> AWS Services
```

The application should generally not require public IP addresses for ordinary application servers, databases, caches, workers, or internal services.

A useful production principle is:

> Public connectivity should terminate at controlled ingress or egress points; application workloads should remain private unless there is a specific architectural reason to expose them.

---

## Production VPC Design Goals

A production VPC should satisfy several goals simultaneously.

| Goal | Design implication |
|---|---|
| High availability | Distribute workloads across multiple AZs |
| Security | Minimize public exposure and enforce least privilege |
| Scalability | Leave sufficient CIDR capacity and subnet IP capacity |
| Reliability | Avoid single-AZ and single-device dependencies |
| Operability | Centralize logs, metrics, and network visibility |
| Cost efficiency | Control NAT Gateway, data transfer, and inspection costs |
| Isolation | Separate workloads by trust and operational boundaries |
| Hybrid connectivity | Design for Direct Connect, VPN, or Transit Gateway |
| Disaster recovery | Ensure another AZ/Region/account can host workloads when required |

The design should be driven by workload requirements rather than by copying a generic diagram.

---

## Reference Production Architecture

A common production VPC uses multiple Availability Zones with separate public, application, and data subnets.

```mermaid
flowchart TB
    INTERNET["Internet"]

    IGW["Internet Gateway"]
    ALB["Application Load Balancer"]

    subgraph VPC["Production VPC"]
        subgraph AZ1["Availability Zone A"]
            PUB1["Public Subnet"]
            APP1["Private App Subnet"]
            DATA1["Private Data Subnet"]
        end

        subgraph AZ2["Availability Zone B"]
            PUB2["Public Subnet"]
            APP2["Private App Subnet"]
            DATA2["Private Data Subnet"]
        end

        subgraph AZ3["Availability Zone C"]
            PUB3["Public Subnet"]
            APP3["Private App Subnet"]
            DATA3["Private Data Subnet"]
        end

        NAT1["NAT Gateway A"]
        NAT2["NAT Gateway B"]
        NAT3["NAT Gateway C"]

        RDS["Multi-AZ Database"]
        REDIS["Redis"]
    end

    INTERNET --> IGW
    IGW --> ALB

    ALB --> APP1
    ALB --> APP2
    ALB --> APP3

    APP1 --> NAT1
    APP2 --> NAT2
    APP3 --> NAT3

    APP1 --> RDS
    APP2 --> RDS
    APP3 --> RDS

    APP1 --> REDIS
    APP2 --> REDIS
    APP3 --> REDIS

    NAT1 --> IGW
    NAT2 --> IGW
    NAT3 --> IGW
```

The exact architecture can vary, but the important property is that a failure in one Availability Zone should not unnecessarily take down the entire application.

---

## CIDR Planning

CIDR planning is one of the most important decisions because changing network addressing later can be expensive and operationally disruptive.

A VPC might start with:

```text
10.0.0.0/16
```

providing 65,536 IPv4 addresses before AWS subnet reservations and other constraints.

Example subdivision:

```text
VPC
10.0.0.0/16

├── AZ-A
│   ├── Public     10.0.0.0/20
│   ├── App        10.0.16.0/20
│   └── Data       10.0.32.0/20
│
├── AZ-B
│   ├── Public     10.0.64.0/20
│   ├── App        10.0.80.0/20
│   └── Data       10.0.96.0/20
│
└── AZ-C
    ├── Public     10.0.128.0/20
    ├── App        10.0.144.0/20
    └── Data       10.0.160.0/20
```

The specific CIDRs are examples, not universal recommendations.

---

## CIDR Design Principles

### Avoid Overly Small VPCs

A `/24` VPC may appear sufficient for a small application, but production growth can quickly exhaust the address space.

Potential consumers include:

- EC2
- ECS
- EKS
- Load balancers
- RDS
- ElastiCache
- Interface endpoints
- Network appliances
- Future subnets
- Additional environments

Address exhaustion is much harder to fix than capacity exhaustion in many other infrastructure resources.

### Avoid Overly Large Subnets Without Reason

Large subnets can simplify capacity planning but may reduce segmentation and make IP utilization harder to reason about.

Design subnet sizes according to:

- Expected workload count
- Scaling limits
- Pod density
- Interface endpoint requirements
- Load balancer requirements
- Future growth
- Multi-account connectivity

---

## CIDR Overlap

CIDR overlap becomes particularly problematic when networks need to communicate.

For example:

```text
VPC A
10.0.0.0/16

VPC B
10.0.0.0/16
```

Connecting these networks creates routing ambiguity.

This becomes especially painful with:

- VPC Peering
- Transit Gateway
- Direct Connect
- Site-to-Site VPN
- Multi-account architectures
- Mergers and acquisitions
- Corporate data centers

A production organization should maintain a centralized IP address management strategy.

---

## Subnet Design

Subnets should represent meaningful network boundaries rather than simply being containers for arbitrary resources.

Common categories include:

| Subnet | Typical resources | Internet exposure |
|---|---|---|
| Public | ALB, NAT Gateway, controlled ingress | Route to IGW |
| Private application | ECS, EKS nodes, EC2, application workloads | No direct inbound Internet |
| Private data | Databases, caches, internal data services | No direct Internet |
| Inspection | Network Firewall / appliances | Controlled |
| Transit | Specialized routing components | Controlled |

A common three-tier model is:

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

The tiers are logical security and routing boundaries, not merely different folders for resources.

---

## Public vs Private Subnets

A subnet is considered public when its route table provides a route to an Internet Gateway and the resource has the necessary public addressing configuration.

Example public route:

```text
0.0.0.0/0
    |
    v
Internet Gateway
```

A private application subnet commonly uses:

```text
0.0.0.0/0
    |
    v
NAT Gateway
    |
    v
Internet Gateway
```

This allows outbound Internet access without allowing unsolicited inbound Internet connections directly to the application workload.

---

## Route Table Design

Routing should be intentionally designed.

Example application subnet route table:

```text
Destination          Target
--------------------------------
10.0.0.0/16          local
0.0.0.0/0            NAT Gateway
```

Example data subnet:

```text
Destination          Target
--------------------------------
10.0.0.0/16          local
```

The data subnet therefore does not require general Internet egress.

Additional routes may exist for:

- Transit Gateway
- VPC Peering
- Virtual Private Gateway
- Direct Connect Gateway
- Interface endpoints
- Network inspection paths

---

## NAT Gateway Strategy

NAT Gateway design is one of the most important production cost and availability decisions.

A common mistake is:

```text
AZ-A App
   |
   v
NAT Gateway in AZ-A
   ^
   |
AZ-B App
```

This creates a cross-AZ dependency.

A more resilient design is:

```text
AZ-A App --> NAT-A
AZ-B App --> NAT-B
AZ-C App --> NAT-C
```

Each Availability Zone uses its local NAT Gateway where practical.

### Why This Matters

If AZ-A experiences a failure, applications in AZ-B and AZ-C should not depend on infrastructure located in AZ-A for normal Internet egress.

The trade-off is cost.

Multiple NAT Gateways increase:

- Hourly NAT Gateway cost
- Data processing cost

But they reduce cross-AZ dependency and improve fault isolation.

---

## NAT Gateway Cost Optimization

Not all private workloads require Internet-based egress.

For AWS services, consider VPC endpoints.

Examples include:

- Amazon S3
- Amazon DynamoDB
- Amazon ECR
- AWS Systems Manager
- AWS Secrets Manager
- CloudWatch
- STS

The exact endpoint architecture depends on the service and workload.

For example:

```text
Application
    |
    v
S3 Gateway Endpoint
    |
    v
S3
```

instead of:

```text
Application
    |
    v
NAT Gateway
    |
    v
Internet
    |
    v
S3
```

This can reduce NAT traffic and keep supported service traffic on AWS networking paths.

---

## VPC Endpoints

VPC endpoints allow private connectivity to supported AWS services.

Two major categories are:

| Endpoint | Typical use |
|---|---|
| Gateway endpoint | S3 and DynamoDB |
| Interface endpoint | Many AWS services through PrivateLink |

A production architecture should evaluate endpoint usage based on:

- Security requirements
- NAT costs
- Traffic volume
- Service support
- DNS behavior
- Availability requirements

---

## Security Group Architecture

Security Groups should represent application communication requirements.

Example:

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

The database should not allow:

```text
0.0.0.0/0 : 5432
```

Instead, allow access from the application Security Group where the architecture supports Security Group referencing.

Conceptually:

```text
Internet
   |
   v
ALB-SG
   |
   v
APP-SG
   |
   v
DB-SG
```

This creates an explicit trust chain.

---

## Security Group Design Principles

Prefer:

- Least privilege
- Application-specific rules
- Referencing Security Groups where appropriate
- Minimal inbound rules
- Explicit outbound requirements for sensitive environments

Avoid:

- Broad `0.0.0.0/0` inbound access
- Opening database ports publicly
- Reusing one Security Group for every workload
- Treating Security Groups as the only security boundary

---

## Network ACLs

Network ACLs operate at the subnet boundary and are stateless.

Security Groups are stateful.

| Feature | Security Group | Network ACL |
|---|---|---|
| Scope | ENI/resource | Subnet |
| Stateful | Yes | No |
| Rule evaluation | Allow rules | Allow and deny |
| Return traffic | Automatically handled | Must be explicitly permitted |
| Typical use | Workload-level access | Subnet-level boundary |

A common production strategy is:

```text
Network ACL
    |
    v
Coarse subnet boundary

Security Group
    |
    v
Fine-grained workload access
```

Avoid creating extremely complex NACL configurations unless there is a clear security requirement. Complexity increases troubleshooting cost.

---

## Internet Ingress Architecture

A production backend should normally avoid exposing application servers directly.

Prefer:

```text
Internet
   |
   v
CloudFront
   |
   v
AWS WAF
   |
   v
Application Load Balancer
   |
   v
Private Application Workloads
```

The application workloads remain private.

For APIs:

```text
Client
  |
HTTPS
  |
CloudFront / ALB
  |
Private API
```

This is generally preferable to:

```text
Client
  |
Internet
  |
EC2 public IP
```

---

## Load Balancer Placement

An Application Load Balancer is commonly deployed across multiple Availability Zones.

```text
             ALB
          /       \
         /         \
      AZ-A         AZ-B
       |             |
      App           App
```

The load balancer distributes traffic to healthy targets.

Health checks should be designed around application readiness rather than merely checking whether a process is listening on a port.

---

## Application Tier

The application tier may contain:

- Django
- FastAPI
- Node.js
- Java
- Go
- ECS tasks
- EKS workloads
- EC2 instances

Example:

```text
Private Application Subnets

AZ-A:
    Django API
    Celery Worker

AZ-B:
    Django API
    Celery Worker

AZ-C:
    Django API
    Celery Worker
```

Applications should be designed to tolerate instance and Availability Zone failures.

---

## Kubernetes and EKS Considerations

EKS adds additional networking considerations.

Pods may consume IP addresses depending on the networking model and configuration.

Therefore, subnet capacity should account for:

- Nodes
- Pods
- Load balancer interfaces
- ENIs
- Scaling operations
- Infrastructure components

A subnet that appears sufficiently large for EC2 instances may be inadequate for a high-density Kubernetes cluster.

For EKS, IP planning should be performed before cluster deployment rather than after address exhaustion occurs.

---

## ECS Considerations

For ECS tasks using `awsvpc` networking, tasks receive network interfaces and private IP addresses.

Therefore:

```text
More ECS Tasks
       |
       v
More ENIs / IP consumption
       |
       v
More subnet capacity required
```

Autoscaling design should include subnet IP capacity.

---

## Database Tier

Databases should normally reside in private subnets.

Example:

```text
Application
    |
    | 5432
    v
PostgreSQL
```

The database Security Group should only allow required application sources.

For managed databases such as Amazon RDS or Aurora, use multiple Availability Zones where the service and workload require high availability.

Do not expose PostgreSQL directly to the Internet merely because a developer needs administrative access.

Prefer controlled access through:

- VPN
- Direct Connect
- Bastion alternatives
- Systems Manager
- Approved administrative tooling

---

## Redis and Cache Architecture

Redis or ElastiCache should normally remain private.

Example:

```text
Django / FastAPI
      |
      | Redis protocol
      v
ElastiCache
```

Application Security Groups should control access.

Avoid:

```text
0.0.0.0/0 -> Redis
```

A cache often contains sensitive session data, tokens, or application state and should be treated as an internal service.

---

## Kafka Architecture

Kafka deployments require careful network planning because clients must be able to reach brokers and advertised addresses.

A production architecture might be:

```text
Private Applications
       |
       v
Kafka Security Group
       |
       v
Kafka Brokers
```

For cross-VPC or hybrid Kafka architectures, validate:

- Broker advertised addresses
- DNS resolution
- Routing
- Security Groups
- TLS
- Authentication
- MTU
- Latency
- Cross-AZ data transfer

Kafka is particularly sensitive to network topology because consumers and producers maintain persistent connections.

---

## Egress Architecture

Private applications often need outbound connectivity for:

- Package repositories
- External APIs
- AWS APIs
- Container registries
- Monitoring
- Authentication providers

Do not automatically route every destination through the NAT Gateway.

Classify traffic:

```text
Application
    |
    +--> AWS service --> VPC Endpoint
    |
    +--> Internal service --> Private routing
    |
    +--> External API --> NAT / controlled egress
```

This improves security and can reduce cost.

---

## Centralized Egress

Large organizations may centralize egress through a shared network architecture.

For example:

```text
Spoke VPC A
      |
Spoke VPC B
      |
Spoke VPC C
      |
      v
Transit Gateway
      |
      v
Inspection / Egress VPC
      |
      v
Firewall / NAT
      |
      v
Internet
```

Advantages include:

- Centralized security controls
- Consistent egress policies
- Centralized logging
- Reduced duplicated infrastructure

Limitations include:

- More routing complexity
- Potential bottlenecks
- Cross-AZ or cross-VPC data transfer
- Larger blast radius
- More difficult troubleshooting

Centralization should be justified by organizational requirements rather than used automatically.

---

## Transit Gateway Integration

For organizations with many VPCs, Transit Gateway often becomes the central routing layer.

```mermaid
flowchart LR
    VPC1["Production VPC"]
    VPC2["Staging VPC"]
    VPC3["Shared Services VPC"]
    VPC4["Security VPC"]

    TGW["Transit Gateway"]

    VPC1 --> TGW
    VPC2 --> TGW
    VPC3 --> TGW
    VPC4 --> TGW

    TGW --> CORP["Corporate Network"]
```

This avoids building a large mesh of VPC Peering connections.

Routing must still be explicitly controlled.

---

## Multi-Account Architecture

Production environments often use separate AWS accounts for isolation.

Example:

```text
AWS Organization
       |
       +-- Security Account
       |
       +-- Network Account
       |
       +-- Production Account
       |
       +-- Staging Account
       |
       +-- Development Account
       |
       +-- Shared Services Account
```

A centralized networking account may own:

- Transit Gateway
- Direct Connect Gateway
- Centralized inspection
- Shared DNS infrastructure
- Network logging

Application accounts can then consume approved network services.

---

## Multi-Region Architecture

For critical workloads, multiple AWS Regions may be required.

```text
             Global DNS
                 |
        +--------+--------+
        |                 |
        v                 v
   Region A           Region B
      |                  |
    VPC A              VPC B
      |                  |
   Backend            Backend
      |                  |
   Database           Database
```

The network architecture should consider:

- Inter-Region connectivity
- DNS failover
- Data replication
- Route propagation
- Regional service availability
- Disaster recovery requirements

Do not assume multi-Region automatically means disaster recovery. Data, identity, deployment, secrets, and operational processes must also support the failover model.

---

## Availability Zone Design

At minimum, production workloads that require high availability should normally span multiple Availability Zones.

Example:

```text
Region
 |
 +-- AZ-A
 |    +-- ALB
 |    +-- App
 |    +-- NAT
 |
 +-- AZ-B
 |    +-- ALB
 |    +-- App
 |    +-- NAT
 |
 +-- AZ-C
      +-- ALB
      +-- App
      +-- NAT
```

The key principle is:

> Do not allow a single Availability Zone to become an accidental dependency for the entire application.

---

## Failure Domain Analysis

For every major component, ask:

> What happens if this component disappears?

| Component | Failure question |
|---|---|
| AZ | Can traffic move to another AZ? |
| NAT Gateway | Can application egress continue? |
| ALB target | Is another target healthy? |
| Route table | Is routing still correct? |
| Transit Gateway attachment | Is another path available? |
| VPN tunnel | Is another tunnel/path available? |
| Direct Connect | Does VPN provide backup? |
| Database | Is failover supported? |
| Redis | Is cache loss tolerated? |
| Kafka broker | Can clients continue operating? |

This approach produces more useful designs than simply labeling components "highly available."

---

## DNS Architecture

DNS is part of the production network design.

A typical public architecture may be:

```text
Client
   |
   v
Route 53
   |
   v
CloudFront / ALB
```

Internal services may use private DNS:

```text
service.internal.example.com
             |
             v
        Private DNS
             |
             v
       Internal Service
```

For hybrid environments, DNS forwarding may connect AWS and corporate namespaces.

Production DNS design should consider:

- Private hosted zones
- Resolver endpoints
- Forwarding rules
- Split-horizon DNS
- TTLs
- Failover
- Health checks
- Service discovery

---

## VPC Flow Logs

VPC Flow Logs provide visibility into network traffic metadata.

They are useful for investigating:

- Unexpected connections
- Rejected traffic
- Security Group behavior
- Network paths
- Traffic patterns
- Security incidents

A useful operational workflow is:

```text
Application failure
       |
       v
DNS check
       |
       v
Route check
       |
       v
Security Group check
       |
       v
VPC Flow Logs
       |
       v
Identify accept/reject behavior
```

Flow Logs do not replace application logs or packet-level debugging.

---

## Monitoring Strategy

Production VPC monitoring should cover multiple layers.

| Layer | Examples |
|---|---|
| Connectivity | VPN, Direct Connect, Transit Gateway |
| Routing | BGP, route propagation, route tables |
| Security | Flow Logs, firewall logs |
| Capacity | Subnet IP utilization |
| NAT | Connections, bytes, errors |
| Load balancing | Healthy targets, latency, errors |
| Application | Request latency, 5xx |
| Database | Connections, CPU, storage |
| DNS | Resolution failures, latency |

The most important metrics are those that allow operators to distinguish:

```text
Application failure
```

from:

```text
Network failure
```

from:

```text
Security policy failure
```

---

## Subnet IP Capacity Monitoring

IP exhaustion is an operational problem that is frequently overlooked.

Monitor:

- Available IP addresses
- ECS task density
- EKS pod density
- ENI consumption
- Interface endpoint consumption
- Scaling trends

A service may have enough CPU and memory to scale but still fail because the subnet has no available addresses.

This is especially important for:

- EKS
- ECS
- High-scale EC2 fleets
- Serverless networking patterns
- Interface-heavy architectures

---

## Security Architecture

A production VPC should use multiple independent security controls.

```text
                Internet
                   |
                WAF
                   |
             Load Balancer
                   |
            Security Group
                   |
            Private App Tier
                   |
            Security Group
                   |
              Data Tier
                   |
             Private Storage
```

Additional controls may include:

- IAM
- AWS Organizations SCPs
- Network Firewall
- GuardDuty
- VPC Flow Logs
- CloudTrail
- KMS
- Secrets Manager
- TLS
- mTLS
- Endpoint policies

Security should be layered rather than concentrated in a single mechanism.

---

## Network Firewall and Inspection

Some environments require centralized traffic inspection.

A simplified design:

```text
Spoke VPC
    |
    v
Transit Gateway
    |
    v
Inspection VPC
    |
    v
AWS Network Firewall
    |
    v
Destination
```

Inspection can enforce:

- Domain policies
- Network policies
- Threat detection
- Egress restrictions
- Segmentation requirements

However, inserting inspection into every path increases complexity and latency.

Use inspection where the threat model and compliance requirements justify it.

---

## Private-Only Workloads

A strong production pattern is to keep most workloads private.

```text
Public:
    ALB
    NAT Gateway

Private:
    Django
    FastAPI
    Celery
    ECS
    EKS
    Redis
    PostgreSQL
    Kafka
```

This reduces the number of resources directly exposed to the Internet.

A private workload can still communicate externally through controlled egress.

---

## Administrative Access

Avoid exposing SSH or RDP directly to the Internet.

Instead consider:

```text
Engineer
   |
   v
VPN / Zero-Trust Access / SSM
   |
   v
Private Resource
```

For AWS-managed environments, Systems Manager can often eliminate the need for publicly reachable SSH endpoints.

This reduces attack surface and simplifies access auditing.

---

## Bastion Hosts

Traditional bastion hosts can still be used where appropriate:

```text
Engineer
   |
   v
Bastion
   |
   v
Private Instance
```

However, a bastion adds:

- Another host to patch
- Another access boundary
- Another Security Group
- Another audit requirement

Prefer managed access mechanisms when they meet operational requirements.

---

## Encryption

Network privacy and encryption should be treated separately.

Production applications should use:

- TLS for APIs
- TLS for databases where supported and required
- mTLS for sensitive service-to-service communication
- IPsec for VPN connectivity
- Appropriate Direct Connect link encryption where required

A private subnet is not equivalent to encrypted application communication.

---

## High Availability

High availability requires eliminating unnecessary single points of failure.

Weak design:

```text
                NAT
                 |
AZ-A -----------+
                 |
AZ-B -----------+
```

Improved design:

```text
AZ-A --> NAT-A
AZ-B --> NAT-B
AZ-C --> NAT-C
```

Similarly:

```text
AZ-A --> App A --> DB
AZ-B --> App B --> DB
AZ-C --> App C --> DB
```

The database itself must provide an appropriate HA mechanism rather than merely being deployed in a private subnet.

---

## Disaster Recovery

A VPC design should align with the application's RTO and RPO.

| Requirement | Possible architecture |
|---|---|
| Basic HA | Multi-AZ |
| Regional resilience | Multi-Region |
| Account isolation | Multi-account |
| Hybrid resilience | Direct Connect + VPN |
| Database resilience | Multi-AZ / replication |
| Infrastructure recovery | IaC |
| Fast restoration | Automated deployment + backups |

Disaster recovery is not simply:

```text
Take a VPC backup
```

Instead, recovery may involve reconstructing:

- VPC
- Subnets
- Routes
- Security Groups
- IAM
- Compute
- Databases
- Secrets
- DNS
- Observability
- External integrations

Infrastructure as code is therefore an important component of recoverability.

---

## Infrastructure as Code

Production VPCs should generally be reproducible through tools such as:

- Terraform
- AWS CloudFormation
- AWS CDK

A conceptual Terraform structure might be:

```text
infrastructure/
├── modules/
│   ├── vpc/
│   ├── security-groups/
│   ├── transit-gateway/
│   └── endpoints/
│
├── environments/
│   ├── production/
│   ├── staging/
│   └── development/
│
└── main.tf
```

Separate reusable modules from environment-specific configuration.

---

## CI/CD for Network Infrastructure

Network infrastructure should have the same engineering discipline as application code.

A typical pipeline:

```text
Pull Request
     |
     v
Terraform fmt
     |
     v
Terraform validate
     |
     v
Security checks
     |
     v
Terraform plan
     |
     v
Review
     |
     v
Terraform apply
```

Production network changes should generally require controlled approval.

A routing mistake can affect:

- Entire applications
- Multiple accounts
- Hybrid connectivity
- Security boundaries
- Production traffic

Therefore, network infrastructure should be treated as high-impact code.

---

## Change Management

Before modifying production networking, document:

- Current topology
- Intended change
- Affected routes
- Affected Security Groups
- Expected traffic flow
- Rollback plan
- Failure modes
- Monitoring plan

For example:

```text
Change:
Add new private subnet

Validate:
CIDR does not overlap
Route table correct
NACL correct
Security Groups correct
IP capacity sufficient

Rollback:
Remove subnet association
Restore route configuration
```

---

## Cost Considerations

Production networking can become a significant cost center.

Common contributors include:

- NAT Gateway hourly charges
- NAT data processing
- Cross-AZ data transfer
- Inter-Region data transfer
- Transit Gateway processing
- Network Firewall processing
- VPN
- Direct Connect
- VPC endpoints
- Load balancers

A useful optimization strategy is:

```text
High-volume AWS traffic
        |
        v
VPC Endpoint

High-volume external traffic
        |
        v
Controlled NAT / egress

High-volume internal traffic
        |
        v
Private routing
```

Do not optimize purely for the lowest infrastructure bill. A cheaper topology that creates cross-AZ dependencies or weakens isolation may be more expensive operationally.

---

## Cross-AZ Traffic

Cross-AZ communication may incur data transfer costs and adds network dependencies.

Example:

```text
AZ-A Application
      |
      v
AZ-B NAT Gateway
```

This may be operationally and financially inferior to:

```text
AZ-A Application
      |
      v
AZ-A NAT Gateway
```

Similarly, applications should understand whether high-volume traffic to databases, caches, or Kafka brokers crosses Availability Zones.

Cross-AZ traffic is not inherently wrong. It should be intentional.

---

## Performance Considerations

VPC architecture can affect application latency.

Potential contributors include:

- Cross-AZ traffic
- NAT processing
- Network inspection
- VPN encryption
- Transit Gateway routing
- Cross-Region communication
- DNS resolution
- Load balancer hops

For latency-sensitive services:

```text
Application
    |
    v
Closest appropriate dependency
```

is generally preferable to unnecessarily routing through centralized infrastructure.

---

## Production VPC Anti-Patterns

### Public EC2 Application Servers

```text
Internet
   |
   v
EC2 Public IP
```

Prefer:

```text
Internet
   |
   v
ALB
   |
   v
Private EC2
```

### Public Database

```text
Internet
   |
   v
PostgreSQL
```

Avoid this architecture for normal production workloads.

### One NAT Gateway for Every AZ

A centralized NAT Gateway can create a cross-AZ dependency.

Use per-AZ NAT where the availability and traffic profile justify it.

### One Giant Security Group

A single Security Group containing every application creates weak segmentation.

Use Security Groups aligned with workload responsibilities.

### Overlapping CIDRs

This makes future connectivity difficult.

Plan IP space before creating interconnected networks.

### No IP Capacity Monitoring

A subnet can fail to scale even when CPU and memory are available.

### Direct SSH From the Internet

Use controlled administrative access instead.

### Routing Everything Through Inspection

Centralized inspection can be useful, but unnecessary inspection paths add latency, cost, and complexity.

### Treating NAT as a Firewall

NAT controls address translation and outbound connectivity; it should not be treated as a comprehensive security control.

### Using NACLs as the Primary Application Firewall

Security Groups are generally better suited for workload-level stateful access control.

### Assuming Multi-AZ Means Highly Available

Multi-AZ infrastructure is only useful if the application, database, routing, DNS, and operational processes can actually tolerate an AZ failure.

---

## Production Design Checklist

### Network

- [ ] VPC CIDR has sufficient growth capacity.
- [ ] CIDRs do not overlap with connected networks.
- [ ] Subnets span multiple Availability Zones.
- [ ] Public and private routing boundaries are intentional.
- [ ] Route tables are minimal and understandable.
- [ ] IP capacity is monitored.
- [ ] DNS architecture is documented.

### Security

- [ ] Application workloads are private where practical.
- [ ] Databases are not publicly reachable.
- [ ] Security Groups follow least privilege.
- [ ] NACLs are intentionally configured.
- [ ] Administrative access is controlled.
- [ ] TLS is enabled where required.
- [ ] Network inspection is used where justified.
- [ ] Flow Logs and audit logging are enabled according to requirements.

### Availability

- [ ] Application workloads span multiple AZs.
- [ ] Load balancers span multiple AZs.
- [ ] NAT strategy avoids unnecessary single-AZ dependencies.
- [ ] Database HA is configured where required.
- [ ] Hybrid connectivity has redundancy.
- [ ] DNS failover is tested where applicable.
- [ ] Failure scenarios have been tested.

### Connectivity

- [ ] Transit Gateway architecture is documented where applicable.
- [ ] VPC Peering dependencies are documented.
- [ ] Direct Connect redundancy is considered.
- [ ] VPN backup is considered.
- [ ] Route advertisements are controlled.
- [ ] Hybrid CIDRs do not overlap.
- [ ] Cross-account routes are explicitly managed.

### Operations

- [ ] Infrastructure is managed through IaC.
- [ ] Network changes are reviewed.
- [ ] Production changes have rollback plans.
- [ ] Monitoring covers connectivity and routing.
- [ ] Alerts distinguish network and application failures.
- [ ] Cost drivers are monitored.
- [ ] Disaster recovery procedures are documented.
- [ ] Recovery procedures have been tested.

---

## Reference Architecture for a Backend Platform

A mature backend platform could use the following topology:

```mermaid
flowchart TB
    USER["Users / Clients"]
    R53["Route 53"]
    CF["CloudFront"]
    WAF["AWS WAF"]
    ALB["Application Load Balancer"]

    subgraph PROD["Production VPC"]
        subgraph AZ1["AZ-A"]
            APP1["Django / FastAPI"]
            CELERY1["Celery"]
            NAT1["NAT Gateway"]
        end

        subgraph AZ2["AZ-B"]
            APP2["Django / FastAPI"]
            CELERY2["Celery"]
            NAT2["NAT Gateway"]
        end

        subgraph AZ3["AZ-C"]
            APP3["Django / FastAPI"]
            CELERY3["Celery"]
            NAT3["NAT Gateway"]
        end

        DB["PostgreSQL / RDS"]
        REDIS["Redis / ElastiCache"]
        KAFKA["Kafka"]
        EP["VPC Endpoints"]
        TGW["Transit Gateway"]
    end

    USER --> R53
    R53 --> CF
    CF --> WAF
    WAF --> ALB

    ALB --> APP1
    ALB --> APP2
    ALB --> APP3

    APP1 --> DB
    APP2 --> DB
    APP3 --> DB

    APP1 --> REDIS
    APP2 --> REDIS
    APP3 --> REDIS

    APP1 --> KAFKA
    APP2 --> KAFKA
    APP3 --> KAFKA

    APP1 --> EP
    APP2 --> EP
    APP3 --> EP

    APP1 --> NAT1
    APP2 --> NAT2
    APP3 --> NAT3

    TGW --> CORP["Corporate / Other VPCs"]
```

The architecture separates:

```text
Ingress
   |
Application
   |
Data
   |
AWS Service Access
   |
External Egress
   |
Hybrid Connectivity
```

Each path can then be independently secured, monitored, scaled, and tested.

---

## Production Review Questions

Before approving a VPC architecture, ask:

### Network Capacity

- Can the VPC support expected growth?
- Are connected CIDRs guaranteed not to overlap?
- Can EKS/ECS scaling exhaust subnet IPs?

### Availability

- What happens if one AZ disappears?
- What happens if one NAT Gateway fails?
- What happens if Direct Connect fails?
- What happens if VPN fails?
- What happens if a database node fails?

### Security

- Which resources are publicly reachable?
- Why do they need to be public?
- Which Security Group allows database access?
- How is administrative access performed?
- Where is encryption applied?

### Routing

- Can every required destination be reached?
- Are any routes unnecessarily broad?
- Are there asymmetric routing risks?
- Are centralized inspection paths creating dependencies?

### Operations

- Can the network be recreated from code?
- Are routing changes audited?
- Can operators diagnose rejected traffic?
- Is IP exhaustion monitored?

### Cost

- How much traffic crosses AZ boundaries?
- How much traffic traverses NAT?
- Would VPC endpoints reduce NAT usage?
- Is centralized networking actually cheaper at the expected scale?

### Disaster Recovery

- Can the environment be rebuilt?
- Are CIDRs compatible with the DR environment?
- Does DNS support the recovery strategy?
- Are connectivity and security controls reproduced automatically?

---

## Key Takeaways

- A production VPC should be designed around **availability, isolation, routing, security, scalability, observability, and failure domains**, not merely subnet creation.
- Keep application and data workloads private where practical, expose controlled ingress through load balancers, and use deliberate egress paths for external communication.
- Plan CIDRs and subnet capacity before deployment; overlapping networks and IP exhaustion are difficult production problems to correct later.
- High availability requires eliminating unnecessary single-AZ dependencies across compute, NAT, databases, routing, DNS, and hybrid connectivity.
- Treat VPC infrastructure as production code: manage it with IaC, review network changes, monitor traffic and capacity, control costs, and continuously test failure and recovery scenarios.