# 04- Subnets

## Overview

A subnet is a logical network segment within an Amazon VPC. It allocates a portion of the VPC's CIDR block to resources in a specific Availability Zone and provides the boundary at which route-table associations and subnet-level networking controls are applied.

For backend infrastructure, subnet design determines where workloads run, which traffic paths are available, how resources are isolated, how much IP capacity is available, and how the architecture behaves during scaling or Availability Zone failures.

A production VPC commonly separates workloads into logical subnet tiers:

```text
VPC
10.0.0.0/16
|
+-- Availability Zone A
|   |
|   +-- Public Subnet
|   +-- Private Application Subnet
|   +-- Private Data Subnet
|
+-- Availability Zone B
    |
    +-- Public Subnet
    +-- Private Application Subnet
    +-- Private Data Subnet
```

The important distinction is that a subnet is not inherently public or private. Its effective network behavior is primarily determined by its route table and the gateways or other network targets reachable through those routes.

---

## What Is a Subnet?

A subnet is a subdivision of a VPC's IP address space.

Suppose a VPC uses:

```text
10.0.0.0/16
```

The address space can be divided into smaller subnet CIDRs:

```text
10.0.1.0/24
10.0.2.0/24
10.0.3.0/24
```

Each subnet belongs to one Availability Zone.

For example:

```text
VPC: 10.0.0.0/16

AZ A:
    10.0.1.0/24

AZ B:
    10.0.2.0/24

AZ C:
    10.0.3.0/24
```

Subnets therefore provide both:

- **Address segmentation**
- **Availability Zone placement**

This makes them a fundamental building block for production architecture.

---

## Why Subnets Exist

Subnets provide a way to organize workloads into separate network segments with different routing and security requirements.

For example:

```text
Internet-facing workloads
        |
        v
Public Subnets

Application workloads
        |
        v
Private Application Subnets

Database workloads
        |
        v
Private Data Subnets
```

This separation makes it possible to implement different network paths.

For example:

```text
Public Subnet
    |
    +-- Internet Gateway

Private Application Subnet
    |
    +-- NAT Gateway

Private Data Subnet
    |
    +-- No direct internet route
```

Subnet segmentation is therefore useful for:

- Network isolation
- Routing control
- Security architecture
- IP capacity planning
- Availability Zone distribution
- Operational organization

---

## Subnet and Availability Zone Relationship

Every subnet exists in a single Availability Zone.

A subnet cannot span multiple Availability Zones.

For example:

```text
VPC
|
+-- AZ A
|   |
|   +-- subnet-a
|
+-- AZ B
|   |
|   +-- subnet-b
|
+-- AZ C
    |
    +-- subnet-c
```

This relationship is important for high availability.

A production application should generally distribute capacity across multiple Availability Zones rather than putting all application resources into one subnet in one AZ.

---

## Multi-AZ Subnet Architecture

A common production structure is:

```mermaid
flowchart TB
    VPC["VPC 10.0.0.0/16"]

    subgraph AZ1["Availability Zone A"]
        PUB1["Public Subnet"]
        APP1["Private Application Subnet"]
        DB1["Private Data Subnet"]
    end

    subgraph AZ2["Availability Zone B"]
        PUB2["Public Subnet"]
        APP2["Private Application Subnet"]
        DB2["Private Data Subnet"]
    end

    VPC --> AZ1
    VPC --> AZ2

    AZ1 --> PUB1
    AZ1 --> APP1
    AZ1 --> DB1

    AZ2 --> PUB2
    AZ2 --> APP2
    AZ2 --> DB2
```

The application tier can then distribute instances or tasks across:

```text
APP1
APP2
```

If one Availability Zone becomes unavailable, the remaining AZ can continue serving traffic if the application and its dependencies are designed for that failure mode.

---

## Subnet CIDR

Every subnet receives a CIDR block from the VPC address space.

Example:

```text
VPC:
10.0.0.0/16

Subnet:
10.0.10.0/24
```

The subnet CIDR determines its IP capacity.

A `/24` contains:

```text
256 total IPv4 addresses
```

AWS reserves five IPv4 addresses in each subnet, leaving:

```text
251 usable IPv4 addresses
```

The actual available capacity at runtime can be lower because addresses are allocated to resources and AWS-managed networking components.

For production planning, use AWS's reported available IP count rather than relying only on mathematical calculations.

---

## Subnet Size Planning

Subnet size should be determined from expected workload capacity.

Consider:

```text
Current workload
+
Expected growth
+
Autoscaling
+
AZ failure redistribution
+
AWS-managed network interfaces
+
Future services
```

For example, an application subnet intended to support:

- EC2 instances
- ECS tasks
- EKS pods
- Load balancers
- VPC endpoints

may need substantially more capacity than a subnet containing a few static EC2 instances.

### Poor Planning

```text
Application Subnet
10.0.1.0/28
```

A very small subnet may become an operational constraint during scaling.

### Better Planning

Use a larger subnet when workload growth and IP consumption justify it.

The exact size should be determined through capacity planning rather than a universal `/24` recommendation.

---

## Public Subnets

A public subnet is generally a subnet whose route table contains a route to an Internet Gateway.

For example:

```text
Destination       Target
10.0.0.0/16       local
0.0.0.0/0         igw-xxxxxxxx
```

This creates a route from the subnet toward the internet gateway.

Resources in the subnet still require appropriate public addressing and security configuration to be directly reachable from the internet.

### Typical Public Workloads

Public subnets commonly contain resources such as:

- Internet-facing load balancers
- NAT Gateways
- Certain network appliances
- Other infrastructure that intentionally requires public connectivity

Application servers and databases generally do not need to be placed in public subnets simply because the application is internet-facing.

---

## Private Subnets

A private subnet does not have a direct route to an Internet Gateway for normal outbound internet access.

A common architecture is:

```text
Private Subnet
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

Another private subnet may have no internet path at all:

```text
Private Data Subnet
    |
    +-- VPC local routes
    +-- Internal services
```

Private subnets are commonly used for:

- Django applications
- FastAPI applications
- gRPC services
- Celery workers
- Databases
- Redis
- Kafka
- Internal microservices
- EKS workloads

---

## Public vs Private Subnets

| Characteristic | Public Subnet | Private Subnet |
|---|---|---|
| Direct route to IGW | Typically yes | Typically no |
| Typical workload | Load balancers, NAT | APIs, workers, databases |
| Direct internet ingress | Possible with required addressing/security | Not through an IGW route |
| Outbound internet | Through IGW | Commonly through NAT |
| Typical exposure | Internet-facing | Internal |
| Security posture | Higher exposure | Reduced direct exposure |

The terms describe routing architecture rather than an inherent security classification.

A private subnet is not automatically secure, and a public subnet is not automatically insecure.

---

## Route Tables and Subnets

A subnet is associated with a route table.

The route table determines where traffic from resources in that subnet is directed.

Example public subnet:

```text
Subnet
10.0.1.0/24
     |
     v
Public Route Table
     |
     +-- 10.0.0.0/16 -> local
     +-- 0.0.0.0/0  -> Internet Gateway
```

Private application subnet:

```text
Subnet
10.0.11.0/24
     |
     v
Private Route Table
     |
     +-- 10.0.0.0/16 -> local
     +-- 0.0.0.0/0  -> NAT Gateway
```

Private data subnet:

```text
Subnet
10.0.21.0/24
     |
     v
Data Route Table
     |
     +-- 10.0.0.0/16 -> local
```

The third example intentionally has no default route to the internet.

---

## Route Table Association

A subnet can be associated with one route table at a time.

A route table can be associated with multiple subnets.

This makes it possible to create routing tiers.

For example:

```text
Public Route Table
    |
    +-- Public Subnet A
    +-- Public Subnet B

Private App Route Table
    |
    +-- App Subnet A
    +-- App Subnet B

Private Data Route Table
    |
    +-- Data Subnet A
    +-- Data Subnet B
```

This is generally preferable to creating a unique route table for every subnet without a specific reason.

---

## Main Route Table

Every VPC has a main route table.

If a subnet is not explicitly associated with another route table, it uses the VPC's main route table.

In production environments, explicit subnet-to-route-table associations are often easier to reason about because the routing behavior becomes visible from the infrastructure definition.

For infrastructure-as-code, explicitly declaring associations can reduce accidental changes caused by assumptions about the main route table.

---

## Local VPC Routing

VPC route tables contain a local route for the VPC's CIDR.

For example:

```text
Destination       Target
10.0.0.0/16       local
```

This allows communication between resources using addresses within the VPC address space, subject to applicable network security controls.

A resource in:

```text
10.0.1.10
```

can therefore potentially communicate with:

```text
10.0.21.20
```

through the VPC's local routing.

Security Groups and NACLs still determine whether the traffic is permitted.

---

## Subnet-Level Security

Subnets interact with two major network security mechanisms:

- Security Groups
- Network ACLs

Security Groups are associated with network interfaces.

Network ACLs are associated with subnets.

Conceptually:

```text
VPC
 |
 +-- Subnet
      |
      +-- Network ACL
      |
      +-- Network Interfaces
              |
              +-- Security Groups
```

This distinction matters when troubleshooting.

If an application cannot connect to PostgreSQL, inspect both:

```text
Application ENI
    |
    +-- Security Group

Application Subnet
    |
    +-- NACL

Database Subnet
    |
    +-- NACL

Database ENI
    |
    +-- Security Group
```

---

## Network ACLs at the Subnet Boundary

NACLs provide stateless filtering at the subnet boundary.

For example:

```text
Internet
   |
   v
Subnet NACL
   |
   v
Application
```

Because NACLs are stateless, both directions of traffic must be considered.

For example:

```text
Client
  |
  | TCP request
  v
Application
  |
  | TCP response
  v
Client
```

The NACL configuration must permit the necessary traffic in both directions.

This is one reason overly restrictive NACLs can cause difficult-to-diagnose connectivity failures.

---

## Subnets and Network Interfaces

Resources receive network connectivity through network interfaces.

For example:

```text
Subnet
10.0.11.0/24
    |
    +-- ENI
    |    |
    |    +-- Private IP
    |    +-- Security Groups
    |
    +-- ENI
         |
         +-- Private IP
         +-- Security Groups
```

Different AWS services manage network interfaces differently, but subnet capacity remains important because network interfaces consume IP addresses.

---

## Subnets and EC2

An EC2 instance is launched into a subnet.

For example:

```text
EC2 Instance
    |
    v
Subnet
10.0.11.0/24
    |
    v
Availability Zone A
```

The instance receives a private IPv4 address from the subnet.

If it requires public internet access, the surrounding architecture must provide:

- Appropriate route
- Internet Gateway
- Public IPv4 or Elastic IP where required
- Security Group rules
- NACL rules where applicable

For production application servers, private subnet placement is usually preferable.

---

## Subnets and ECS

ECS tasks using `awsvpc` networking receive network interfaces and IP addresses from the VPC networking environment.

A simplified architecture is:

```text
Private Subnet
|
+-- ECS Task
|     |
|     +-- ENI
|     +-- Private IP
|
+-- ECS Task
      |
      +-- ENI
      +-- Private IP
```

This makes subnet IP capacity important for ECS services that scale horizontally.

For high task counts, a small subnet can become a bottleneck even when the underlying compute resources are available.

---

## Subnets and EKS

EKS introduces particularly important subnet-capacity considerations.

A simplified model is:

```text
Private Subnet
|
+-- EKS Node
|    |
|    +-- ENI
|    +-- Pod IPs
|
+-- EKS Node
     |
     +-- ENI
     +-- Pod IPs
```

Depending on the networking model, pods can consume VPC IP addresses.

Large Kubernetes clusters should therefore plan subnet capacity around:

- Node count
- Pod count
- Instance type
- ENI limits
- IP allocation behavior
- Autoscaling
- Availability Zone distribution

IP exhaustion can prevent pods from being scheduled even when CPU and memory are available.

---

## Subnets and Load Balancers

Internet-facing load balancers are commonly deployed across multiple public subnets in different Availability Zones.

For example:

```text
Internet
    |
    v
Application Load Balancer
    |
    +-- Public Subnet A
    |
    +-- Public Subnet B
            |
            v
       Private App Subnets
```

The application targets can remain private.

This creates a clear network boundary:

```text
Internet
    |
    v
Public Load Balancer
    |
    v
Private Application
```

It also reduces the need to assign public addresses to individual application instances.

---

## Subnets and Databases

Databases such as Amazon RDS are commonly placed into private subnets.

A database subnet group typically spans multiple Availability Zones.

For example:

```text
Private Data Subnet A
        |
        +-- RDS

Private Data Subnet B
        |
        +-- RDS
```

The database should generally not have a route that makes direct internet access necessary.

Application connectivity should instead be controlled through:

```text
Application Security Group
        |
        v
Database Security Group
        |
        v
Database
```

Subnet isolation and Security Group controls complement each other.

---

## Subnet Tiers

A common VPC architecture uses logical subnet tiers.

```text
Public Tier
    |
    +-- Load Balancers
    +-- NAT Gateways

Application Tier
    |
    +-- APIs
    +-- Workers
    +-- Internal Services

Data Tier
    |
    +-- PostgreSQL
    +-- Redis
    +-- Kafka
```

Each tier can use separate route tables and security policies.

This does not mean every service must have its own subnet.

Subnet boundaries should represent meaningful network or operational boundaries.

---

## Three-Tier VPC Architecture

A typical backend platform might look like:

```mermaid
flowchart TB
    Internet["Internet"]

    subgraph VPC["Amazon VPC"]
        subgraph Public["Public Subnets"]
            ALB["Application Load Balancer"]
            NAT["NAT Gateway"]
        end

        subgraph App["Private Application Subnets"]
            API1["Django / FastAPI"]
            API2["Django / FastAPI"]
            WORKER["Celery Workers"]
        end

        subgraph Data["Private Data Subnets"]
            DB["PostgreSQL"]
            REDIS["Redis"]
            KAFKA["Kafka"]
        end
    end

    Internet --> ALB

    ALB --> API1
    ALB --> API2

    API1 --> DB
    API2 --> DB

    API1 --> REDIS
    API2 --> REDIS

    WORKER --> DB
    WORKER --> REDIS
    WORKER --> KAFKA

    API1 --> NAT
    API2 --> NAT
```

This pattern is common because it provides a straightforward separation between public ingress, application processing, and persistent data.

---

## Subnet Design Across Availability Zones

A production architecture should generally mirror logical subnet tiers across multiple Availability Zones.

For example:

```text
VPC
10.0.0.0/16

AZ A
|
+-- Public A
+-- App A
+-- Data A

AZ B
|
+-- Public B
+-- App B
+-- Data B

AZ C
|
+-- Public C
+-- App C
+-- Data C
```

This gives the application multiple failure domains.

The subnet ranges should be planned so that each AZ has sufficient capacity.

---

## Symmetric Subnet Design

Symmetry makes infrastructure easier to reason about.

For example:

```text
AZ A:
Public    10.0.1.0/24
App       10.0.11.0/20
Data      10.0.21.0/24

AZ B:
Public    10.0.2.0/24
App       10.0.12.0/20
Data      10.0.22.0/24

AZ C:
Public    10.0.3.0/24
App       10.0.13.0/20
Data      10.0.23.0/24
```

The exact CIDRs are examples only.

The benefit of symmetry is operational predictability.

When troubleshooting:

```text
App A -> App B
```

the network engineer can immediately understand the expected topology.

---

## One Subnet Per Service?

Generally, no.

A common beginner design is:

```text
Subnet A -> Django
Subnet B -> FastAPI
Subnet C -> Redis
Subnet D -> Celery
Subnet E -> Kafka
```

This can create unnecessary complexity.

Subnets should usually represent meaningful network boundaries rather than every application component.

A more practical design may be:

```text
Private Application Subnet
    |
    +-- Django
    +-- FastAPI
    +-- Celery
    +-- Internal Services

Private Data Subnet
    |
    +-- PostgreSQL
    +-- Redis
    +-- Kafka
```

Separate subnets may still be appropriate when different workloads have different:

- Routing requirements
- Security requirements
- IP capacity requirements
- Compliance boundaries
- Operational ownership

---

## Dedicated Subnets for Infrastructure

Some architectures use dedicated subnets for specific infrastructure.

Examples include:

- Network inspection appliances
- Firewall infrastructure
- Transit Gateway attachments
- PrivateLink endpoint interfaces
- Specialized workloads

This should be driven by the architecture rather than by a blanket rule that every resource requires its own subnet.

---

## Private Subnets With No Internet Access

Not every private subnet needs NAT.

For example, a database subnet may use:

```text
Destination       Target

10.0.0.0/16       local
```

and nothing else.

This creates a stronger network boundary.

Application subnets may use:

```text
10.0.0.0/16       local
0.0.0.0/0         NAT Gateway
```

This difference is intentional.

```text
Application:
Needs controlled outbound access

Database:
Does not need internet access
```

Avoid adding default routes simply because they are available.

---

## Private Subnets With VPC Endpoints

Private workloads that need AWS service access can use VPC endpoints.

For example:

```text
Private Application
        |
        v
VPC Endpoint
        |
        v
Amazon S3
```

This can avoid unnecessary paths through a NAT Gateway.

A private subnet can therefore provide:

```text
Private application
    |
    +-- Database
    |
    +-- Redis
    |
    +-- VPC Endpoint
    |
    +-- NAT Gateway
```

where each path serves a different purpose.

---

## Subnet Routing Patterns

### Public Subnet

```text
10.0.0.0/16 -> local
0.0.0.0/0   -> Internet Gateway
```

### Private Application Subnet

```text
10.0.0.0/16 -> local
0.0.0.0/0   -> NAT Gateway
```

### Private Data Subnet

```text
10.0.0.0/16 -> local
```

### Private AWS Service Access

Depending on endpoint type and service:

```text
Application
    |
    v
VPC Endpoint
    |
    v
AWS Service
```

The important engineering principle is to provide only the routes required by the workload.

---

## Subnet Route Tables and Availability Zones

NAT Gateway architecture requires particular attention to Availability Zones.

Consider:

```text
AZ A Application
       |
       v
NAT Gateway in AZ A
       |
       v
Internet Gateway
```

and:

```text
AZ B Application
       |
       v
NAT Gateway in AZ A
       |
       v
Internet Gateway
```

The second design introduces cross-AZ traffic for outbound connectivity.

A more resilient architecture may use:

```text
AZ A App -> NAT A -> IGW
AZ B App -> NAT B -> IGW
```

This can improve AZ isolation and avoid unnecessary cross-AZ traffic, although it introduces additional NAT Gateway cost.

The decision should consider:

- Availability requirements
- Traffic volume
- Cross-AZ costs
- Failure behavior
- Operational simplicity

---

## Subnet IP Capacity Monitoring

Subnet capacity should be monitored as an infrastructure metric.

AWS exposes available IPv4 capacity for subnets.

Example:

```bash
aws ec2 describe-subnets \
    --subnet-ids subnet-xxxxxxxx \
    --query 'Subnets[].{SubnetId:SubnetId,CIDR:CidrBlock,AvailableIPs:AvailableIpAddressCount}'
```

A production monitoring strategy should establish thresholds appropriate for workload growth.

For example:

```text
Healthy:
High available IP capacity

Warning:
Capacity declining rapidly

Critical:
Insufficient addresses for expected scaling
```

The exact thresholds should be based on workload behavior rather than a universal percentage.

---

## IP Exhaustion

Subnet IP exhaustion occurs when there are not enough available addresses for new network interfaces or other required allocations.

Symptoms may include:

- EC2 launch failures
- ECS task placement failures
- EKS pod scheduling failures
- Load balancer provisioning issues
- Lambda networking issues
- Infrastructure deployment failures

A typical investigation is:

```text
Deployment failure
       |
       v
Identify subnet
       |
       v
Check AvailableIpAddressCount
       |
       v
Identify major IP consumers
       |
       v
Review workload scaling
       |
       v
Expand or redesign subnet capacity
```

Do not wait for complete exhaustion before planning remediation.

---

## Subnet and Autoscaling

Autoscaling can turn a seemingly adequate subnet into a capacity bottleneck.

For example:

```text
Normal:
20 application instances

Peak:
150 application instances
```

If every instance requires a private IP, subnet capacity must accommodate the peak.

Container platforms can amplify this effect because a single node or task architecture may consume multiple network addresses.

Capacity planning should therefore use expected **peak** resource counts, not average counts.

---

## Subnet and Disaster Recovery

DR architectures should have equivalent network capacity.

For example:

```text
Primary Region
|
+-- Public Subnets
+-- Application Subnets
+-- Data Subnets

DR Region
|
+-- Public Subnets
+-- Application Subnets
+-- Data Subnets
```

The DR environment should have enough IP capacity to run the intended recovery workload.

A common mistake is provisioning a DR VPC with tiny subnets because the environment is normally inactive.

If the recovery plan requires full production capacity, the network must support that capacity.

---

## Security Considerations

Subnet isolation should support, but not replace, fine-grained security controls.

A typical security architecture is:

```text
Internet
   |
   v
Public Subnet
   |
   v
Load Balancer
   |
   v
Private Application Subnet
   |
   v
Private Data Subnet
```

Additional controls include:

- Security Groups
- Network ACLs
- IAM
- TLS
- Application authentication
- Secrets management
- VPC Flow Logs
- VPC endpoint policies

Do not assume that putting a database into a private subnet automatically makes it secure.

A private subnet reduces direct exposure, but access still needs to be controlled.

---

## Monitoring and Observability

Useful subnet-level operational signals include:

- Available IP addresses
- Network traffic
- Flow Log accept/reject records
- Route changes
- Resource placement failures
- NAT Gateway traffic
- Cross-AZ traffic
- Load balancer health
- Network interface consumption

VPC Flow Logs can help investigate traffic entering or leaving network interfaces associated with subnet resources.

A production network should make subnet capacity and connectivity observable before they become incident causes.

---

## Cost Considerations

Subnets themselves are not typically a major direct cost.

However, subnet architecture can influence other costs.

Examples:

- NAT Gateway data processing
- Cross-AZ data transfer
- Network appliance traffic
- Transit Gateway traffic
- VPC endpoint costs
- Load balancer costs

For example, sending traffic from:

```text
AZ B Application
       |
       v
NAT Gateway in AZ A
```

may introduce cross-AZ data transfer.

The lowest-cost subnet architecture is not necessarily the most reliable architecture.

Evaluate:

```text
Availability
+
Performance
+
Security
+
Operational simplicity
+
Cost
```

together.

---

## Reliability Considerations

For production applications:

- Use multiple Availability Zones.
- Distribute application capacity across AZs.
- Provide sufficient IP capacity in each AZ.
- Avoid single-AZ network dependencies where availability requirements prohibit them.
- Keep routing consistent across equivalent subnet tiers.
- Monitor subnet capacity.
- Test failure scenarios.
- Plan subnet capacity for scaling events.

A common failure scenario is:

```text
AZ A fails
   |
   v
Workloads move to AZ B
   |
   v
AZ B subnet lacks IP capacity
   |
   v
Recovery capacity cannot launch
```

Therefore, subnet capacity is part of the application's high-availability design.

---

## Common Mistakes

### Making Every Subnet Public

An internet-facing application does not require every application component to be public.

Prefer:

```text
Internet
   |
   v
Public Load Balancer
   |
   v
Private Application
```

### Creating One Subnet Per Service

This often creates unnecessary routing and operational complexity.

Use subnet boundaries where they provide meaningful network isolation or operational value.

### Making Private Data Subnets Internet-Routable

Databases and other sensitive services often do not need outbound internet access.

Avoid unnecessary default routes.

### Using Tiny Subnets

Small subnets may work during development but fail during production scaling.

### Ignoring AZ Capacity Balance

One AZ can become IP-constrained while another has abundant capacity.

### Assuming Private Means Secure

Private routing reduces exposure but does not replace Security Groups, NACLs, IAM, encryption, or application authorization.

### Ignoring Cross-AZ Traffic

Centralized NAT or network appliances can cause unnecessary cross-AZ traffic.

### Forgetting AWS-Reserved Addresses

The theoretical CIDR capacity is larger than the number of IPv4 addresses available to workloads.

### Hard-Coding Private IPs

Infrastructure is dynamic.

Use DNS and service discovery instead of depending on individual resource addresses.

---

## Practical Backend Example

Consider a Django API with PostgreSQL, Redis, and Celery.

A practical VPC design might be:

```text
VPC: 10.0.0.0/16

AZ A
|
+-- Public Subnet
|     |
|     +-- ALB
|     +-- NAT Gateway
|
+-- Private Application Subnet
|     |
|     +-- Django
|     +-- Celery
|
+-- Private Data Subnet
      |
      +-- PostgreSQL
      +-- Redis

AZ B
|
+-- Public Subnet
|     |
|     +-- ALB
|     +-- NAT Gateway
|
+-- Private Application Subnet
|     |
|     +-- Django
|     +-- Celery
|
+-- Private Data Subnet
      |
      +-- PostgreSQL
      +-- Redis
```

Traffic flows:

```text
Client
   |
   v
ALB
   |
   v
Django
   |
   +----> PostgreSQL
   |
   +----> Redis
   |
   +----> Celery
```

Outbound traffic:

```text
Django
   |
   v
Private Route Table
   |
   v
NAT Gateway
   |
   v
Internet
```

The application remains private while still supporting external integrations.

---

## AWS CLI Operations

List all subnets:

```bash
aws ec2 describe-subnets
```

List subnets for a VPC:

```bash
aws ec2 describe-subnets \
    --filters Name=vpc-id,Values=vpc-xxxxxxxx
```

Display subnet IDs, CIDRs, AZs, and available addresses:

```bash
aws ec2 describe-subnets \
    --filters Name=vpc-id,Values=vpc-xxxxxxxx \
    --query 'Subnets[].{SubnetId:SubnetId,CIDR:CidrBlock,AZ:AvailabilityZone,AvailableIPs:AvailableIpAddressCount}'
```

Inspect a specific subnet:

```bash
aws ec2 describe-subnets \
    --subnet-ids subnet-xxxxxxxx
```

List route tables associated with a VPC:

```bash
aws ec2 describe-route-tables \
    --filters Name=vpc-id,Values=vpc-xxxxxxxx
```

List network ACLs:

```bash
aws ec2 describe-network-acls \
    --filters Name=vpc-id,Values=vpc-xxxxxxxx
```

These commands are useful during infrastructure validation and connectivity troubleshooting.

---

## Infrastructure as Code Considerations

Subnet definitions should normally be managed through Infrastructure as Code rather than manually created and modified in production.

A simplified Terraform example:

```hcl
resource "aws_subnet" "private_app_a" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.11.0/20"
  availability_zone = "ap-south-1a"

  tags = {
    Name = "private-app-a"
    Tier = "application"
  }
}

resource "aws_subnet" "private_app_b" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.12.0/20"
  availability_zone = "ap-south-1b"

  tags = {
    Name = "private-app-b"
    Tier = "application"
  }
}
```

Production infrastructure should additionally standardize:

- Naming
- Tags
- Environment
- Cost allocation
- Ownership
- Availability Zone mapping
- CIDR allocation
- Route table associations

The goal is to make the network topology reproducible and auditable.

---

## Troubleshooting Subnet Connectivity

When a workload cannot communicate with another resource, identify the subnet on both sides.

For example:

```text
Source:
10.0.11.25
Subnet:
10.0.11.0/24

Destination:
10.0.21.30
Subnet:
10.0.21.0/24
```

Then inspect:

```text
Source Subnet
    |
    +-- Route Table
    +-- NACL

Source ENI
    |
    +-- Security Group

Destination Subnet
    |
    +-- Route Table
    +-- NACL

Destination ENI
    |
    +-- Security Group
```

For internet connectivity:

```text
Private Subnet
    |
    +-- Route Table
    |
    +-- NAT Gateway
    |
    +-- Internet Gateway
    |
    +-- External Destination
```

For AWS service access:

```text
Private Subnet
    |
    +-- Route / DNS
    |
    +-- VPC Endpoint
    |
    +-- AWS Service
```

A deterministic flow-based approach is more reliable than changing security rules randomly.

---

## Interview Traps

### Can a subnet span multiple Availability Zones?

No. Each subnet belongs to one Availability Zone.

### Does every subnet need its own route table?

No. Multiple subnets can share a route table.

### What makes a subnet public?

Typically, a route table associated with the subnet contains a route to an Internet Gateway.

### Does a private subnet mean no internet connectivity is possible?

No. A private subnet can have outbound internet access through a NAT Gateway.

### Does a private subnet automatically make a database secure?

No. Security Groups, NACLs, IAM, encryption, authentication, and other controls still matter.

### Why use multiple subnets across Availability Zones?

To distribute workloads across failure domains and improve availability.

### Why can subnet IP exhaustion break autoscaling?

New resources require IP addresses. If the subnet has insufficient capacity, scaling cannot create the required network interfaces or workloads.

### Why might two equivalent application subnets have different available IP counts?

Different workloads, ENIs, tasks, pods, or AWS-managed resources may have consumed different amounts of address capacity.

### Should every microservice have its own subnet?

No. Subnets should represent meaningful network boundaries rather than application naming boundaries.

### Why can a centralized NAT Gateway create cross-AZ traffic?

A workload in one AZ sending traffic through a NAT Gateway located in another AZ crosses the AZ boundary before reaching the NAT infrastructure.

## Key Takeaways

- A subnet is an Availability Zone-scoped network segment whose CIDR, route table, and security controls determine how workloads communicate.
- Public and private subnet behavior is primarily a routing concept; private workloads can still obtain controlled outbound connectivity through NAT or private AWS service access through VPC endpoints.
- Production subnet design should use multiple Availability Zones, predictable tiers, and enough IP capacity for current workloads, autoscaling, and failure redistribution.
- Subnet boundaries should represent meaningful network, security, routing, or operational requirements rather than creating a separate subnet for every service.
- Subnet capacity, routing, and AZ distribution are part of application reliability and should be managed, monitored, and tested as production infrastructure.