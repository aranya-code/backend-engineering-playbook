# 07- Internet Gateway

## Overview

An Internet Gateway (IGW) is a horizontally scaled, redundant VPC component that provides a path between resources in an Amazon VPC and the public internet.

An Internet Gateway does not independently make a subnet or resource public. Public internet connectivity requires the correct combination of:

- An Internet Gateway attached to the VPC
- A route from the subnet's route table to the Internet Gateway
- Appropriate public IPv4 or IPv6 addressing
- Permitted Security Group rules
- Permitted Network ACL rules
- Correct application and operating-system configuration

The fundamental public-subnet path is:

```text
Internet
    |
    v
Internet Gateway
    |
    v
VPC Route Table
    |
    v
Public Subnet
    |
    v
Resource
```

For outbound traffic from a public IPv4 resource, the reverse path is:

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

For a production backend architecture, the Internet Gateway is commonly used at the VPC edge while application workloads remain in private subnets:

```text
Internet
    |
    v
Internet Gateway
    |
    v
Public Load Balancer
    |
    v
Private Application
    |
    +----> PostgreSQL
    +----> Redis
    +----> Kafka
```

This separation is one of the fundamental building blocks of secure AWS networking.

---

## What Is an Internet Gateway?

An Internet Gateway is an AWS-managed VPC component that enables communication between a VPC and the internet.

It performs two important architectural roles:

1. Provides a logical connection between the VPC and the public internet.
2. Supports one-to-one network address translation for instances using public IPv4 addresses.

For IPv6, addresses are globally routable and do not require NAT in the same way IPv4 private addresses do.

An Internet Gateway is attached to a VPC rather than directly to an individual subnet or EC2 instance.

```text
VPC
 |
 +-- Internet Gateway
 |
 +-- Public Subnet
 |      |
 |      +-- Load Balancer
 |
 +-- Private Subnet
        |
        +-- Application
```

The route table determines which subnet traffic uses the Internet Gateway.

---

## Why Internet Gateways Exist

A VPC is logically isolated from other networks by default.

To provide internet connectivity, AWS needs a VPC-level internet gateway and appropriate routing.

The Internet Gateway allows architectures such as:

```text
Client on Internet
        |
        v
Internet-facing ALB
        |
        v
Private API
```

or:

```text
Public EC2
    |
    v
Internet Gateway
    |
    v
Internet
```

Without an Internet Gateway, a route table cannot provide normal direct internet connectivity through an IGW.

---

## Internet Gateway Architecture

A simplified architecture is:

```mermaid
flowchart LR
    Internet["Internet"]

    IGW["Internet Gateway"]

    subgraph VPC["Amazon VPC"]
        RT["Public Route Table"]
        Subnet["Public Subnet"]
        Resource["Internet-Facing Resource"]
    end

    Internet <--> IGW
    IGW <--> RT
    RT --> Subnet
    Subnet --> Resource
```

The route table contains a route such as:

```text
Destination       Target

10.0.0.0/16       local
0.0.0.0/0         igw-xxxxxxxx
```

The `0.0.0.0/0` route directs destinations outside the VPC toward the Internet Gateway.

---

## Internet Gateway vs Public Subnet

An Internet Gateway does not automatically make every subnet public.

Consider:

```text
VPC
 |
 +-- Internet Gateway
 |
 +-- Public Subnet
 |      |
 |      +-- 0.0.0.0/0 -> IGW
 |
 +-- Private Subnet
        |
        +-- 0.0.0.0/0 -> NAT Gateway
```

Both subnets belong to the same VPC and therefore have access to the same Internet Gateway at the VPC level.

However, only the public subnet has a route directly to the Internet Gateway.

Therefore:

```text
Public Subnet
    -> IGW
    -> Internet

Private Subnet
    -> NAT Gateway
    -> IGW
    -> Internet
```

This distinction is essential.

---

## What Makes a Resource Internet-Accessible?

For an IPv4 resource to communicate directly with the internet, multiple conditions must be satisfied.

A typical path requires:

```text
VPC
 +
Internet Gateway
 +
Route to IGW
 +
Public IPv4 / Elastic IP
 +
Security Group
 +
NACL
 +
Application
```

For example:

```text
EC2
10.0.10.20
Public IPv4: 203.0.113.x
       |
       v
Public Subnet
       |
       v
0.0.0.0/0 -> IGW
       |
       v
Internet
```

Removing any required part can prevent connectivity.

---

## Public IPv4 Addressing

An Internet Gateway does not automatically assign public IPv4 addresses to resources.

For an EC2 instance to have direct public IPv4 connectivity, it generally needs a public IPv4 address or Elastic IP associated with the relevant network interface.

For example:

```text
Private IP:
10.0.10.25

Public IPv4:
203.0.113.25
```

The Internet Gateway performs the necessary one-to-one translation between the public and private IPv4 addresses for internet communication.

The application itself normally continues using the instance's private IP internally.

---

## Elastic IP Addresses

An Elastic IP address is a static public IPv4 address that can be associated with supported AWS resources.

A common use case is a resource that requires a stable public IPv4 address.

However, avoid assigning Elastic IPs to application servers simply because public connectivity is convenient.

A stronger production architecture is usually:

```text
Internet
   |
   v
Public ALB
   |
   v
Private Application
```

rather than:

```text
Internet
   |
   v
Elastic IP
   |
   v
EC2
Django
```

The latter exposes the application host directly.

---

## Internet Gateway and Load Balancers

Internet-facing Application Load Balancers and Network Load Balancers are commonly deployed across public subnets.

The architecture is:

```text
Internet
    |
    v
Internet Gateway
    |
    v
Public Subnets
    |
    v
Internet-Facing ALB
    |
    v
Private Application Subnets
```

This provides a public ingress layer without requiring public IP addresses on the backend application instances.

For Django or FastAPI:

```text
Client
  |
  | HTTPS
  v
Public ALB
  |
  | HTTP/HTTPS
  v
Private Django / FastAPI
```

The application Security Group can allow traffic from the ALB Security Group rather than from the entire internet.

---

## Internet Gateway and Private Subnets

Private subnets do not normally route directly to the Internet Gateway for outbound internet access.

Instead:

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
Public Subnet
       |
       v
Internet Gateway
       |
       v
Internet
```

The Internet Gateway is therefore still involved in private-subnet internet access, but indirectly through the NAT Gateway.

This is a critical distinction:

> A private subnet can use the Internet Gateway indirectly through a NAT Gateway without becoming a public subnet.

---

## Internet Gateway and NAT Gateway

The two services have different responsibilities.

| Component | Primary purpose | Typical subnet |
|---|---|---|
| Internet Gateway | Connect VPC to internet | VPC-level component |
| NAT Gateway | Outbound internet access for private resources | Public subnet |
| Public Load Balancer | Internet-facing application ingress | Public subnet |
| Private Application | Internal application execution | Private subnet |
| Database | Private stateful storage | Private subnet |

Typical traffic:

```text
Private API
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

The NAT Gateway provides the translation and controlled egress behavior for private IPv4 workloads.

The Internet Gateway provides the VPC's internet edge.

---

## Internet Gateway and IPv6

IPv6 networking differs from traditional private IPv4 networking.

An IPv6 address assigned to a resource can be globally routable.

For example:

```text
Resource
2600:xxxx:xxxx::10
       |
       v
Route Table
       |
       v
::/0 -> Internet Gateway
       |
       v
Internet
```

There is no need for NAT merely because the resource uses an IPv6 address.

Security Groups and Network ACLs remain important because globally routable does not mean unrestricted.

A production IPv6 architecture should explicitly decide:

- Which resources receive IPv6 addresses
- Which subnets are internet-routable
- Which inbound ports are allowed
- Which outbound destinations are permitted
- Whether IPv6 egress requires additional controls

---

## IPv4 vs IPv6 Internet Connectivity

| Characteristic | IPv4 | IPv6 |
|---|---|---|
| Typical private VPC address | Yes | Not normally equivalent to RFC1918 private IPv4 |
| Public addressing | Public IPv4 / Elastic IP | Globally routable IPv6 |
| NAT required for internet access | Common for private IPv4 | Generally no |
| Internet Gateway | Yes | Yes |
| Default route | `0.0.0.0/0` | `::/0` |
| Security controls required | Yes | Yes |

IPv6 should not be treated as an automatic security improvement. Its globally routable addressing model requires deliberate firewall and Security Group design.

---

## Internet Gateway Routing

A public route table normally contains:

```text
Destination       Target

10.0.0.0/16       local
0.0.0.0/0         igw-xxxxxxxx
```

For IPv6:

```text
Destination       Target

2600:xxxx::/56    local
::/0              igw-xxxxxxxx
```

The route table determines whether traffic is sent toward the Internet Gateway.

Without the appropriate route, attaching an Internet Gateway to the VPC does not provide public subnet connectivity.

---

## Internet Gateway and Route Tables

The relationship is:

```text
Internet Gateway
       |
       | Attached to VPC
       |
       v
Route Table
       |
       | 0.0.0.0/0 -> IGW
       |
       v
Public Subnet
```

The Internet Gateway does not need to be associated with each subnet individually.

The route table is what determines which subnet traffic uses the IGW.

---

## Internet Gateway and Security Groups

Routing and security are separate.

For example:

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
EC2
```

Even when the route is correct, the Security Group can reject inbound traffic.

For HTTPS:

```text
Inbound:
TCP 443
Source: 0.0.0.0/0
```

may be appropriate for a deliberately public load balancer.

For an internal database:

```text
Inbound:
TCP 5432
Source: Application Security Group
```

is more appropriate.

The Internet Gateway should never be treated as a Security Group.

---

## Internet Gateway and Network ACLs

NACLs operate at the subnet boundary.

A public subnet may therefore have:

```text
Internet
   |
   v
Internet Gateway
   |
   v
Public Subnet NACL
   |
   v
Load Balancer
```

NACLs are stateless, so both inbound and outbound traffic must be considered.

For example, permitting TCP 443 inbound while unintentionally blocking required response traffic can still break the application.

In most application architectures, Security Groups are the primary network access-control mechanism, while NACLs are used for broader subnet-level controls where required.

---

## Internet Gateway and VPC Flow Logs

VPC Flow Logs can help investigate network connectivity involving public resources.

Useful information includes:

- Source address
- Destination address
- Source port
- Destination port
- Protocol
- Action
- Traffic volume
- Network interface

A simplified investigation might be:

```text
Client
   |
   v
Internet Gateway
   |
   v
Public ALB
   |
   v
Flow Logs
```

Flow Logs can help determine whether traffic reached the relevant network interface and whether it was accepted or rejected.

They do not replace route-table inspection.

---

## Internet Gateway and VPC Flow

A simplified inbound request looks like:

```mermaid
sequenceDiagram
    participant Client as Internet Client
    participant IGW as Internet Gateway
    participant RT as Route Table
    participant ALB as Public Load Balancer
    participant API as Private API

    Client->>IGW: HTTPS request
    IGW->>RT: VPC routing
    RT->>ALB: Deliver to public resource
    ALB->>API: Forward request
    API-->>ALB: Response
    ALB-->>IGW: HTTPS response
    IGW-->>Client: Response
```

The application does not need a public IP if the load balancer is the public ingress point.

---

## Internet Gateway and Backend Architecture

A production Django architecture might be:

```text
                       Internet
                           |
                           v
                  +----------------+
                  | Internet GW    |
                  +----------------+
                           |
                           v
                  +----------------+
                  | Public ALB     |
                  +----------------+
                           |
                           v
              +-------------------------+
              | Private App Subnets     |
              |                         |
              | Django / FastAPI        |
              +-------------------------+
                    |             |
                    v             v
              PostgreSQL        Redis
```

The Internet Gateway exists at the edge.

The application and data tiers remain private.

This reduces the number of directly exposed resources.

---

## Internet Gateway and Microservices

Consider a microservice architecture:

```text
Internet
    |
    v
Internet Gateway
    |
    v
Public Load Balancer
    |
    v
API Gateway / Ingress
    |
    +----> Order Service
    |
    +----> User Service
    |
    +----> Payment Service
```

The services can remain in private subnets.

Internal communication may use:

- HTTP
- REST
- gRPC
- Service discovery
- Internal load balancers

The Internet Gateway should generally provide the external network edge rather than becoming the direct ingress path for every microservice.

---

## Internet Gateway and Nginx

Nginx can be deployed behind an internet-facing load balancer:

```text
Internet
    |
    v
Internet Gateway
    |
    v
Public ALB
    |
    v
Private Nginx
    |
    v
Django / FastAPI
```

Alternatively, Nginx itself can be deployed on a public host.

However, using a managed public load balancer can provide a more scalable ingress architecture.

The important distinction is:

```text
Internet Gateway
    -> Network-level internet connectivity

Nginx
    -> HTTP-level reverse proxying
```

They solve different problems.

---

## Internet Gateway and ECS

A common ECS architecture is:

```text
Internet
    |
    v
Internet Gateway
    |
    v
Public ALB
    |
    v
Private ECS Tasks
```

The ECS tasks do not need public IP addresses for inbound application traffic.

If the tasks require outbound internet access:

```text
ECS Task
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

This provides a clean separation between public ingress and private application execution.

---

## Internet Gateway and EKS

A common EKS architecture is:

```text
Internet
    |
    v
Internet Gateway
    |
    v
Public Load Balancer
    |
    v
Private EKS Workloads
```

Worker nodes are often placed in private subnets.

Outbound dependencies may use:

```text
Private Node
    |
    +----> NAT Gateway
    |
    +----> VPC Endpoint
```

The Internet Gateway therefore remains part of the VPC's public edge even when the Kubernetes workloads themselves are private.

---

## Internet Gateway and Database Security

Databases should generally not be directly exposed to the internet.

Avoid:

```text
Internet
    |
    v
Internet Gateway
    |
    v
Public Database
```

Prefer:

```text
Internet
    |
    v
Internet Gateway
    |
    v
Public ALB
    |
    v
Private Application
    |
    v
Private Database
```

The database Security Group should permit only the required application sources.

For PostgreSQL:

```text
TCP 5432
Source: application-sg
```

rather than:

```text
TCP 5432
Source: 0.0.0.0/0
```

---

## Internet Gateway and Redis

Redis is generally an internal infrastructure component.

A typical architecture is:

```text
Private API
    |
    v
Redis
```

There is normally no reason for internet clients to connect directly to Redis.

The Internet Gateway should therefore not be part of the normal application-to-Redis traffic path.

A Redis Security Group should restrict access to the workloads that actually require Redis.

---

## Internet Gateway and Kafka

Kafka brokers are generally internal infrastructure.

A typical architecture is:

```text
Private API
    |
    v
Private Kafka
```

External internet access should not be required for normal broker-to-client communication unless the architecture explicitly calls for it.

Kafka clients need reliable routing to the broker addresses returned in metadata.

Therefore:

```text
DNS
+
Route Tables
+
Security Groups
+
Kafka advertised addresses
```

must all be consistent.

---

## Internet Gateway vs NAT Gateway

These components are frequently confused.

| Feature | Internet Gateway | NAT Gateway |
|---|---|---|
| VPC internet edge | Yes | Uses IGW |
| Public subnet target | Yes | No |
| Private subnet outbound internet | Indirectly | Yes |
| Provides NAT for private IPv4 | No | Yes |
| Publicly reachable resource | Can support | No |
| Typical placement | VPC-level attachment | Public subnet |
| Main purpose | Internet connectivity | Private IPv4 egress |

A common architecture is:

```text
Public Resource
    |
    v
Internet Gateway
    |
    v
Internet
```

and:

```text
Private Resource
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

---

## Internet Gateway vs VPC Endpoint

These solve different connectivity problems.

| Component | Purpose |
|---|---|
| Internet Gateway | Internet connectivity |
| VPC Endpoint | Private connectivity to supported AWS services |

For example:

```text
Private Application
       |
       v
S3 VPC Endpoint
       |
       v
Amazon S3
```

does not require sending the traffic through a public Internet Gateway path.

For AWS service dependencies, evaluate VPC endpoints where appropriate.

---

## Internet Gateway vs Transit Gateway

These are also fundamentally different.

```text
Internet Gateway
    |
    v
Internet
```

versus:

```text
VPC
 |
 v
Transit Gateway
 |
 +-- VPC
 +-- VPC
 +-- VPN
 +-- Direct Connect
```

An Internet Gateway provides internet connectivity.

A Transit Gateway provides centralized private network connectivity between attached networks.

Do not use Transit Gateway merely because a VPC needs internet access.

---

## Internet Gateway and Network Security Architecture

A layered production design can look like:

```mermaid
flowchart TB
    Internet["Internet"]
    IGW["Internet Gateway"]

    subgraph Public["Public Subnets"]
        ALB["Internet-Facing ALB"]
        NAT["NAT Gateway"]
    end

    subgraph Private["Private Subnets"]
        API["Django / FastAPI"]
        WORKER["Celery / Workers"]
        DB["PostgreSQL"]
        CACHE["Redis"]
    end

    Internet --> IGW
    IGW --> ALB
    ALB --> API

    API --> DB
    API --> CACHE
    WORKER --> DB

    API --> NAT
    NAT --> IGW
    IGW --> Internet
```

This architecture gives the Internet Gateway two important roles:

- Public ingress/egress for public resources
- Internet edge for NAT-based private egress

---

## Internet Gateway High Availability

Internet Gateways are designed as highly available, horizontally scaled AWS infrastructure.

You do not deploy one IGW per Availability Zone.

Instead:

```text
VPC
 |
 +-- Internet Gateway
 |
 +-- AZ A
 |    |
 |    +-- Public Subnet
 |
 +-- AZ B
      |
      +-- Public Subnet
```

The single VPC-level Internet Gateway supports the VPC's internet connectivity.

High availability is instead achieved through distributing workloads and public networking components across Availability Zones.

For example:

```text
AZ A
 |
 +-- Public ALB subnet
 +-- Private app subnet

AZ B
 |
 +-- Public ALB subnet
 +-- Private app subnet
```

---

## Internet Gateway Attachment

An Internet Gateway must be attached to the VPC before it can be used for routing.

The lifecycle is:

```text
Create VPC
    |
    v
Create Internet Gateway
    |
    v
Attach IGW to VPC
    |
    v
Create public route
    |
    v
Associate route table with subnet
    |
    v
Configure public resource
```

A route to an Internet Gateway cannot provide working connectivity if the gateway is not attached to the intended VPC.

---

## AWS CLI Inspection

List Internet Gateways:

```bash
aws ec2 describe-internet-gateways
```

List Internet Gateways attached to a specific VPC:

```bash
aws ec2 describe-internet-gateways \
    --filters Name=attachment.vpc-id,Values=vpc-xxxxxxxx
```

Inspect a specific Internet Gateway:

```bash
aws ec2 describe-internet-gateways \
    --internet-gateway-ids igw-xxxxxxxx
```

Find the VPC attachment:

```bash
aws ec2 describe-internet-gateways \
    --internet-gateway-ids igw-xxxxxxxx \
    --query 'InternetGateways[].Attachments[]'
```

Inspect public route tables:

```bash
aws ec2 describe-route-tables \
    --filters Name=vpc-id,Values=vpc-xxxxxxxx \
    --query 'RouteTables[].{RouteTable:RouteTableId,Routes:Routes}'
```

Look specifically for Internet Gateway routes:

```bash
aws ec2 describe-route-tables \
    --filters Name=vpc-id,Values=vpc-xxxxxxxx \
    --query 'RouteTables[].Routes[?GatewayId!=null].[DestinationCidrBlock,GatewayId]'
```

---

## Creating an Internet Gateway With AWS CLI

Create the gateway:

```bash
aws ec2 create-internet-gateway \
    --tag-specifications 'ResourceType=internet-gateway,Tags=[{Key=Name,Value=production-igw}]'
```

The command returns the Internet Gateway ID.

Attach it to a VPC:

```bash
aws ec2 attach-internet-gateway \
    --internet-gateway-id igw-xxxxxxxx \
    --vpc-id vpc-xxxxxxxx
```

Create a public route:

```bash
aws ec2 create-route \
    --route-table-id rtb-xxxxxxxx \
    --destination-cidr-block 0.0.0.0/0 \
    --gateway-id igw-xxxxxxxx
```

Associate the public route table with a subnet:

```bash
aws ec2 associate-route-table \
    --route-table-id rtb-xxxxxxxx \
    --subnet-id subnet-xxxxxxxx
```

In production, these resources should generally be defined through Infrastructure as Code.

---

## Terraform Example

A basic Terraform configuration can define an Internet Gateway and public route table:

```hcl
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "production-igw"
  }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name = "public"
  }
}

resource "aws_route_table_association" "public_a" {
  subnet_id      = aws_subnet.public_a.id
  route_table_id = aws_route_table.public.id
}
```

A complete production configuration should also consider:

- IPv6 routes where required
- Multiple Availability Zones
- Security Groups
- NACLs where required
- NAT architecture
- Load balancers
- VPC endpoints
- DNS
- Monitoring
- Infrastructure lifecycle

---

## Troubleshooting Internet Gateway Connectivity

When a public resource cannot reach the internet, validate the complete path.

```text
Resource
   |
   v
Public Subnet
   |
   v
Route Table
   |
   +-- 0.0.0.0/0 -> IGW
   |
   v
Internet Gateway
   |
   v
Internet
```

Check the following in order:

1. Is the resource in the expected subnet?
2. Is the subnet associated with the expected route table?
3. Does the route table contain `0.0.0.0/0 -> Internet Gateway`?
4. Is the Internet Gateway attached to the VPC?
5. Does the resource have an appropriate public IPv4 address or IPv6 address?
6. Does the Security Group allow the traffic?
7. Do NACLs allow the required traffic?
8. Is the operating system firewall blocking traffic?
9. Is the application listening on the expected interface and port?
10. Is DNS resolving correctly?

This avoids changing multiple networking controls simultaneously and losing the original failure signal.

---

## Troubleshooting: Route Exists but Internet Still Fails

Suppose the route table contains:

```text
0.0.0.0/0 -> igw-xxxxxxxx
```

but the EC2 instance cannot reach the internet.

The route alone is insufficient.

Check:

```text
Route
  +
Public address
  +
Security Group
  +
NACL
  +
OS firewall
  +
Application
```

For example, an EC2 instance with only:

```text
10.0.10.25
```

and no public IPv4 or IPv6 address cannot be treated as a directly internet-addressable host merely because its subnet has a route to the Internet Gateway.

---

## Troubleshooting: Public Load Balancer

If an internet-facing ALB is unreachable:

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
ALB
```

check:

- ALB scheme
- Public subnet placement
- Route table
- Internet Gateway attachment
- ALB Security Group
- NACLs
- Listener
- Target Group health
- Backend Security Group

A healthy route to the ALB does not guarantee healthy backend targets.

---

## Troubleshooting: Private Application Egress

If a private Django application cannot reach an external API, the Internet Gateway itself is usually not the first thing to investigate.

The expected path is:

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
Public Route Table
   |
   v
Internet Gateway
   |
   v
External API
```

Check:

- Private route to NAT Gateway
- NAT Gateway state
- NAT Gateway subnet
- Public subnet route to IGW
- Elastic IP associated with NAT Gateway
- NACLs
- DNS
- Destination availability

---

## Common Mistakes

### Attaching an IGW and Assuming the VPC Is Public

Attaching an Internet Gateway is not enough.

A subnet also needs an appropriate route to it.

### Assuming Every Resource in the VPC Can Reach the Internet

Private subnets may intentionally lack direct internet routes.

### Assuming a Public Subnet Makes an Instance Public

A resource generally also requires appropriate public addressing and security configuration.

### Giving Databases Public Addresses

A database usually does not need direct internet exposure.

Keep it in a private data tier.

### Using an Internet Gateway for Private Egress Directly

Private IPv4 workloads commonly use:

```text
Private Subnet
    -> NAT Gateway
    -> Internet Gateway
```

rather than routing their default route directly to the IGW.

### Confusing IGW With NAT Gateway

The Internet Gateway provides the VPC's internet edge.

The NAT Gateway provides outbound address translation for private IPv4 workloads.

### Allowing `0.0.0.0/0` on Sensitive Ports

A public route does not mean every port should be open.

Avoid publicly exposing:

```text
5432
6379
9092
3306
```

unless there is an explicit and carefully secured requirement.

### Ignoring IPv6

A resource with a globally routable IPv6 address can be directly reachable if routing and security controls permit it.

IPv6 rules must therefore be reviewed separately from IPv4.

### Using Manual Production Route Changes

Manual changes can create infrastructure drift when Terraform or another IaC system manages the VPC.

---

## Security Considerations

The Internet Gateway is an edge component, so public-facing architecture should minimize directly exposed resources.

Prefer:

```text
Internet
    |
    v
Public ALB
    |
    v
Private API
    |
    v
Private Database
```

over:

```text
Internet
    |
    +----> API Server
    +----> Database
    +----> Redis
    +----> Kafka
```

The second design unnecessarily increases the attack surface.

Security should be layered:

```text
Internet Gateway
      |
      v
Route Tables
      |
      v
Security Groups
      |
      v
NACLs where appropriate
      |
      v
TLS
      |
      v
Application Authentication
      |
      v
Authorization
```

---

## Scalability Considerations

The Internet Gateway itself is managed and horizontally scaled by AWS.

Application scalability should instead focus on the components behind it.

For example:

```text
Internet
    |
    v
Internet Gateway
    |
    v
ALB
   / \
  /   \
API A API B
  |     |
  +-----+
     |
 PostgreSQL
```

Scaling the API should generally involve adding application capacity rather than adding additional Internet Gateways.

Similarly, public load balancers should be deployed across multiple Availability Zones.

---

## Reliability Considerations

Internet Gateways are designed as highly available AWS infrastructure.

The application architecture still needs redundancy.

A resilient public API might use:

```text
                Internet
                   |
                   v
              Internet GW
                   |
          +--------+--------+
          |                 |
          v                 v
       Public AZ A       Public AZ B
          |                 |
          v                 v
        ALB nodes across Availability Zones
                 |
          +------+------+
          |             |
          v             v
       API A          API B
```

The Internet Gateway itself is not normally treated as an AZ-specific component.

---

## Cost Considerations

Internet Gateways do not generally incur a separate hourly charge simply for being attached to a VPC.

However, internet traffic can still incur AWS networking charges depending on:

- Data transfer direction
- AWS service
- Region
- Cross-AZ traffic
- NAT Gateway usage
- Load balancer usage
- Other networking components

A common cost optimization is to avoid unnecessary NAT traffic for AWS services where appropriate VPC endpoints can provide private connectivity.

For example:

```text
Private Application
       |
       v
S3 VPC Endpoint
       |
       v
S3
```

can avoid sending that traffic through:

```text
Private Application
       |
       v
NAT Gateway
       |
       v
Internet Gateway
```

The exact cost benefit depends on traffic volume and endpoint architecture.

---

## Disaster Recovery Considerations

The Internet Gateway itself is simple compared with the rest of the VPC architecture, but DR must reproduce the complete public connectivity design.

A DR environment should account for:

```text
VPC
 |
 +-- Internet Gateway
 |
 +-- Public Route Tables
 |
 +-- Public Subnets
 |
 +-- Load Balancer
 |
 +-- Private Application Routes
 |
 +-- NAT Gateways
 |
 +-- Security Groups
 |
 +-- DNS
```

A failover design that restores compute but lacks public routing is incomplete.

---

## Infrastructure-as-Code Best Practices

For production VPCs:

- Define the Internet Gateway in Terraform, CloudFormation, or another IaC system.
- Use explicit names and tags.
- Define route-table associations explicitly.
- Avoid manual production changes.
- Review route changes through CI/CD.
- Keep public and private routing definitions separate.
- Validate IPv4 and IPv6 routes independently.
- Test connectivity after network changes.
- Document intended traffic flows.
- Monitor configuration drift.

A network change should be treated as a production infrastructure change, not an incidental configuration edit.

---

## Senior-Level Design Perspective

At an intermediate level, the Internet Gateway can be remembered as:

```text
VPC -> Internet
```

At a senior level, the important question is:

> Which workloads should have a direct public path, and which workloads should reach the internet only through controlled egress?

A mature architecture might therefore look like:

```text
                         Internet
                            |
                            v
                     Internet Gateway
                            |
             +--------------+--------------+
             |                             |
             v                             v
       Public ALB                    NAT Gateways
             |                             |
             v                             v
      Private APIs                 Private Workloads
             |                             |
      +------+------+                       |
      |             |                       |
      v             v                       v
 PostgreSQL       Redis              External APIs
```

The Internet Gateway is the network edge, not the application's security model.

Senior engineers should evaluate:

- Public exposure
- Routing
- Addressing
- Security Groups
- NACLs
- NAT architecture
- IPv6
- Multi-AZ design
- Egress dependencies
- Cost
- Observability
- Failure behavior

---

## Interview Traps

### What is an Internet Gateway?

An AWS-managed VPC component that provides a path between a VPC and the internet.

### Does attaching an Internet Gateway make all subnets public?

No. Subnet route tables determine whether traffic has a direct route to the Internet Gateway.

### Does an Internet Gateway assign public IP addresses?

No. Public addressing is a separate concern.

### Where is a NAT Gateway normally deployed?

In a public subnet with a route to the Internet Gateway.

### Can a private subnet use an Internet Gateway?

Private IPv4 workloads normally use a NAT Gateway for internet egress rather than routing directly to the IGW.

### Does an Internet Gateway provide NAT?

For public IPv4 communication, the IGW supports the required one-to-one public/private address translation for resources with public IPv4 addresses. It is not a replacement for a NAT Gateway used by private IPv4 workloads.

### Do you need one Internet Gateway per Availability Zone?

No. An Internet Gateway is a VPC-level component designed for high availability.

### Can an Internet Gateway route traffic between two private VPCs?

No. Use mechanisms such as VPC peering or Transit Gateway for private VPC-to-VPC connectivity.

### Can a database be placed in a VPC with an Internet Gateway?

Yes. The presence of an IGW on the VPC does not make the database public. The database should normally remain in private subnets without a direct route to the IGW.

### What is the difference between an IGW and NAT Gateway?

The IGW provides the VPC's internet edge. A NAT Gateway provides outbound internet access and address translation for private IPv4 resources.

### Does an IGW replace Security Groups?

No. Routing and security controls are separate layers.

### Why can an instance with a public IP still fail to reach the internet?

Possible causes include:

- Missing route to the IGW
- Incorrect subnet association
- Security Group rules
- NACL rules
- OS firewall
- DNS failure
- Application configuration

## Key Takeaways

- An Internet Gateway provides the VPC-level path to the public internet, but attaching an IGW alone does not make a subnet or resource public.
- Direct public IPv4 connectivity requires appropriate routing, public addressing, and permissive network and application security controls.
- Production architectures typically expose a load balancer through public subnets while keeping Django, FastAPI, workers, databases, Redis, and Kafka in private subnets.
- Private IPv4 workloads commonly reach the internet through a NAT Gateway, which then uses the Internet Gateway for external connectivity.
- The Internet Gateway is a highly available network edge component; application high availability still requires multi-AZ load balancing, private workload redundancy, controlled routing, and layered security.