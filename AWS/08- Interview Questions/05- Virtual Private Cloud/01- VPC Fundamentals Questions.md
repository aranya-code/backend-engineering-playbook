# 01- VPC Fundamentals Questions

## Overview

This document contains interview questions covering the foundational concepts of **Amazon VPC** that backend engineers are expected to understand when designing, deploying, and troubleshooting production workloads on AWS.

The questions progress from core networking concepts to architecture, routing, security, connectivity, scalability, and production troubleshooting.

The emphasis is on explaining **why** a VPC component exists, how components interact, and how those concepts apply to backend systems such as Django, FastAPI, microservices, PostgreSQL, Redis, ECS, and Kubernetes.

## Core VPC Concepts

### Question: What is an Amazon VPC?

**Answer:**

An Amazon Virtual Private Cloud (VPC) is a logically isolated network in AWS where you deploy and control networking resources such as subnets, route tables, gateways, network interfaces, and security controls.

A VPC provides the network boundary for AWS workloads.

A typical backend architecture may look like:

```text
                    Internet
                       |
                Internet Gateway
                       |
                Public Subnet
                       |
                  Load Balancer
                       |
              Private Application Subnet
                       |
             Django / FastAPI / ECS
                       |
                Private DB Subnet
                       |
                  PostgreSQL
```

A VPC allows engineers to control:

- IP addressing.
- Subnet segmentation.
- Routing.
- Internet connectivity.
- Private connectivity.
- Network security.
- DNS behavior.
- Connectivity between workloads and other networks.

---

### Question: Why do we use VPCs?

**Answer:**

VPCs provide network isolation and control.

A production backend generally should not place every resource directly on an unrestricted public network. Instead, workloads can be separated into public and private network segments.

For example:

```text
Internet
   |
   v
ALB
   |
   v
Private Application Servers
   |
   +----> PostgreSQL
   |
   +----> Redis
   |
   +----> Internal Services
```

This architecture reduces the public attack surface and allows network access to be controlled at multiple layers.

---

### Question: Is a VPC regional?

**Answer:**

Yes.

A VPC is associated with a single AWS Region.

For high availability, workloads inside the VPC are typically distributed across multiple Availability Zones.

```text
                    VPC
                     |
          +----------+----------+
          |                     |
        AZ-a                   AZ-b
          |                     |
     Public Subnet          Public Subnet
     Private Subnet         Private Subnet
```

A VPC itself spans Availability Zones within its Region, while individual subnets are associated with a single Availability Zone.

---

### Question: What is a subnet?

**Answer:**

A subnet is an IP address range inside a VPC.

Subnets are associated with a single Availability Zone and are commonly used to separate workloads by network role.

For example:

| Subnet | Purpose |
|---|---|
| Public subnet | Internet-facing resources |
| Private application subnet | APIs, application servers, workers |
| Private database subnet | PostgreSQL, database services |
| Isolated subnet | Resources with no direct Internet path |

A subnet is not inherently public or private.

Its behavior depends primarily on its routing configuration.

---

### Question: What makes a subnet public?

**Answer:**

A subnet is considered public when its associated route table contains a route to an Internet Gateway.

For example:

```text
0.0.0.0/0 → Internet Gateway
```

A common public subnet route table is:

| Destination | Target |
|---|---|
| `10.0.0.0/16` | local |
| `0.0.0.0/0` | Internet Gateway |

However, having a route to an Internet Gateway does not automatically make every resource inside the subnet Internet-accessible. The resource also needs appropriate addressing and security configuration.

---

### Question: What makes a subnet private?

**Answer:**

A private subnet does not have a direct route to an Internet Gateway.

A common private application subnet has:

```text
10.0.0.0/16 → local
0.0.0.0/0   → NAT Gateway
```

This allows workloads to initiate outbound Internet connections through a NAT Gateway without allowing unsolicited inbound Internet connections through that NAT path.

For example, a private FastAPI service might need to:

- Download external data.
- Call a third-party API.
- Access package repositories.
- Send requests to external services.

The NAT Gateway can provide the outbound path.

---

## CIDR and IP Addressing

### Question: What is CIDR?

**Answer:**

CIDR, or Classless Inter-Domain Routing, represents an IP address range.

For example:

```text
10.0.0.0/16
```

represents a range containing 65,536 IPv4 addresses.

The `/16` indicates that the first 16 bits represent the network portion.

Common VPC CIDR examples include:

```text
10.0.0.0/16
172.16.0.0/16
192.168.0.0/16
```

CIDR planning is important because overlapping address spaces can prevent or complicate connectivity between VPCs, on-premises networks, and other environments.

---

### Question: Why is CIDR planning important?

**Answer:**

Changing network addressing later can be operationally expensive.

Suppose:

```text
Production VPC:
10.0.0.0/16

Corporate network:
10.0.0.0/8
```

These address spaces overlap.

That creates problems for:

- VPC peering.
- Transit Gateway connectivity.
- Site-to-Site VPN.
- Routing.
- Hybrid networking.

A production organization should plan non-overlapping CIDRs before building a multi-VPC architecture.

---

### Question: Can two subnets in the same VPC overlap?

**Answer:**

No.

Subnet CIDR blocks within the same VPC must not overlap.

For example, this is valid:

```text
VPC: 10.0.0.0/16

Subnet A: 10.0.1.0/24
Subnet B: 10.0.2.0/24
Subnet C: 10.0.3.0/24
```

This is invalid:

```text
Subnet A: 10.0.1.0/24
Subnet B: 10.0.1.128/25
```

because the ranges overlap.

---

## Internet Connectivity

### Question: What is an Internet Gateway?

**Answer:**

An Internet Gateway (IGW) provides a VPC with a path to and from the Internet.

A typical public workload path is:

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
Application / Load Balancer
```

The route table needs an appropriate route such as:

```text
0.0.0.0/0 → igw-xxxxxxxx
```

The resource must also have appropriate public addressing and security configuration.

---

### Question: Does attaching an Internet Gateway automatically expose all resources?

**Answer:**

No.

Attaching an Internet Gateway to a VPC only makes the gateway available as a networking component.

A workload becomes Internet-reachable only when the complete network configuration permits it.

You must consider:

- Subnet route table.
- Public IPv4 address or appropriate public addressing.
- Security Group.
- Network ACL.
- Application listener.
- Operating-system firewall where applicable.

---

### Question: What is a NAT Gateway?

**Answer:**

A NAT Gateway allows resources in private subnets to initiate connections to external destinations without requiring those resources to have public IP addresses.

Typical architecture:

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

A common route is:

```text
0.0.0.0/0 → NAT Gateway
```

The NAT Gateway itself must be deployed in a subnet with an appropriate path to an Internet Gateway.

---

### Question: Why should application servers usually be placed in private subnets?

**Answer:**

Private subnets reduce direct Internet exposure.

For example:

```text
Internet
   |
   v
Application Load Balancer
   |
   v
Private ECS / EC2
   |
   +----> PostgreSQL
   |
   +----> Redis
```

The application does not need a public IP merely because users need to access the API.

The load balancer can provide the public entry point while the application remains privately addressed.

---

## Route Tables

### Question: What is a route table?

**Answer:**

A route table determines where network traffic is sent.

A simplified route table might contain:

| Destination | Target |
|---|---|
| `10.0.0.0/16` | local |
| `0.0.0.0/0` | NAT Gateway |

Another route table might contain:

| Destination | Target |
|---|---|
| `10.0.0.0/16` | local |
| `0.0.0.0/0` | Internet Gateway |

The selected route table depends on the subnet association.

---

### Question: How does AWS choose a route?

**Answer:**

AWS uses the most specific matching route.

For example:

```text
10.0.0.0/16 → local
10.0.10.0/24 → Transit Gateway
0.0.0.0/0 → NAT Gateway
```

Traffic destined for:

```text
10.0.10.25
```

matches both `/16` and `/24`, but `/24` is more specific and therefore takes precedence.

This principle is extremely important when troubleshooting routing issues.

---

### Question: What is the `local` route?

**Answer:**

The local route provides connectivity between resources using addresses within the VPC CIDR.

For example:

```text
VPC CIDR:
10.0.0.0/16

Route:
10.0.0.0/16 → local
```

This allows resources in different subnets of the VPC to communicate, subject to Security Group and NACL controls.

---

## Security Groups

### Question: What is a Security Group?

**Answer:**

A Security Group is a stateful virtual firewall associated with supported network interfaces.

Security Groups control inbound and outbound traffic.

For example, a PostgreSQL Security Group might allow:

```text
Inbound:
TCP 5432
Source:
Application Security Group
```

This is preferable to allowing:

```text
0.0.0.0/0
```

for a database.

---

### Question: Are Security Groups stateful?

**Answer:**

Yes.

If an inbound connection is permitted, the response traffic is automatically allowed as part of the established flow.

This differs from Network ACLs, which are stateless.

---

### Question: Can Security Groups deny traffic?

**Answer:**

Security Groups do not have explicit deny rules.

They work using allow rules.

If traffic does not match an applicable allow rule, it is denied.

This makes Security Groups conceptually different from NACLs, which support explicit allow and deny rules.

---

### Question: Can a Security Group reference another Security Group?

**Answer:**

Yes.

For example:

```text
ALB-SG
   |
   | allows TCP 8000
   v
API-SG
```

The API Security Group can allow traffic from the ALB Security Group rather than a fixed IP range.

This is useful for dynamic workloads such as:

- ECS.
- EC2 Auto Scaling.
- Kubernetes nodes.
- Internal microservices.

---

## Network ACLs

### Question: What is a Network ACL?

**Answer:**

A Network ACL, or NACL, is a stateless network-level access control mechanism associated with a subnet.

Unlike Security Groups, NACLs support explicit:

- Allow rules.
- Deny rules.

They are evaluated using rule numbers, with the first matching rule taking effect.

---

### Question: What is the main difference between Security Groups and NACLs?

**Answer:**

| Feature | Security Group | NACL |
|---|---|---|
| Scope | Network interface | Subnet |
| Stateful | Yes | No |
| Allow rules | Yes | Yes |
| Deny rules | No | Yes |
| Rule evaluation | All applicable rules | Lowest matching rule number |
| Common use | Workload-level security | Subnet-level filtering |

A common production pattern is:

```text
NACL
  ↓
Subnet-level boundary

Security Group
  ↓
Workload-level boundary
```

---

## Elastic Network Interfaces

### Question: What is an ENI?

**Answer:**

An Elastic Network Interface (ENI) is a virtual network interface attached to a resource.

It can have properties such as:

- Private IPv4 addresses.
- Public IPv4 association.
- Security Groups.
- MAC address.
- Subnet association.

Many AWS resources ultimately communicate through ENIs.

When troubleshooting a connectivity problem, identifying the actual ENI is often more useful than starting from the higher-level service name.

---

### Question: Why is the ENI important for troubleshooting?

**Answer:**

The ENI determines important networking characteristics of the workload.

For example:

```text
Workload
   |
   v
ENI
   |
   +-- Private IP
   +-- Subnet
   +-- Security Groups
   +-- Network interface state
```

A useful troubleshooting sequence is:

```text
Resource
→ ENI
→ Private IP
→ Subnet
→ Route Table
→ Security Groups
```

---

## Availability Zones

### Question: Why should production workloads use multiple Availability Zones?

**Answer:**

Using multiple Availability Zones improves availability by reducing dependency on a single isolated infrastructure location.

For example:

```text
                 Load Balancer
                  /         \
                 /           \
              AZ-a           AZ-b
               |               |
           API Server      API Server
               |               |
               +-------+-------+
                       |
                  Database
```

A typical highly available architecture distributes application resources across at least two Availability Zones.

---

### Question: Can a subnet span multiple Availability Zones?

**Answer:**

No.

A subnet belongs to exactly one Availability Zone.

If you need application capacity in two Availability Zones, you create separate subnets:

```text
AZ-a:
10.0.1.0/24

AZ-b:
10.0.2.0/24
```

---

## VPC DNS

### Question: What DNS capabilities does a VPC provide?

**Answer:**

A VPC can provide DNS resolution for workloads using Amazon-provided DNS infrastructure.

DNS configuration is controlled through VPC attributes such as:

- `enableDnsSupport`
- `enableDnsHostnames`

These settings are important for workloads that rely on AWS DNS names and service discovery.

---

### Question: Why is DNS important in backend systems?

**Answer:**

Backend services rarely communicate exclusively through hard-coded IP addresses.

For example:

```text
api.internal.example.com
postgres.internal.example.com
redis.internal.example.com
```

A microservice architecture may depend heavily on DNS for:

- Service discovery.
- Database endpoints.
- Load balancers.
- AWS services.
- Private hosted zones.

A DNS failure can therefore appear as an application connectivity failure even when routing and security controls are correct.

---

## VPC Endpoints

### Question: Why use a VPC Endpoint?

**Answer:**

VPC endpoints provide private connectivity between VPC resources and supported AWS services without requiring traffic to traverse the public Internet.

They are useful when workloads in private subnets need AWS services such as S3 or other supported services.

Conceptually:

```text
Private Workload
      |
      v
VPC Endpoint
      |
      v
AWS Service
```

This can reduce dependence on NAT for supported AWS service access and can improve network isolation.

---

### Question: What is the difference between Gateway and Interface VPC Endpoints?

**Answer:**

| Feature | Gateway Endpoint | Interface Endpoint |
|---|---|---|
| Common services | S3, DynamoDB | Many AWS services |
| Implementation | Route-table based | ENI-based |
| Private IPs | Not ENI-based | Yes |
| Security Group | No endpoint ENI SG | Yes |
| DNS | Service-specific behavior | Private DNS commonly used |

The exact service support should be verified against current AWS documentation.

---

## VPC Peering

### Question: What is VPC Peering?

**Answer:**

VPC Peering provides private network connectivity between two VPCs.

For example:

```text
VPC A
10.0.0.0/16
    |
    | Peering
    |
VPC B
10.1.0.0/16
```

Both VPCs require appropriate routes.

For example:

```text
VPC A:
10.1.0.0/16 → Peering Connection

VPC B:
10.0.0.0/16 → Peering Connection
```

Security controls must also permit the traffic.

---

### Question: What is a major limitation of VPC peering?

**Answer:**

VPC peering is not transitive.

For example:

```text
VPC A
  |
  v
VPC B
  |
  v
VPC C
```

A peering connection between A and B and another between B and C does not automatically provide A-to-C routing.

For large multi-VPC environments, AWS Transit Gateway is often a better architectural choice.

---

## Transit Gateway

### Question: What is AWS Transit Gateway?

**Answer:**

Transit Gateway provides a centralized network hub for connecting multiple VPCs and other supported networks.

For example:

```text
                 Transit Gateway
                /       |       \
               /        |        \
             VPC A     VPC B     VPC C
```

It is useful for organizations with many VPCs because it reduces the need for large numbers of point-to-point peering connections.

---

### Question: Why is Transit Gateway useful in large environments?

**Answer:**

Without a centralized connectivity model, many VPCs can create complex peering relationships.

A Transit Gateway provides a hub-and-spoke architecture:

```text
             Shared Network
                   |
            Transit Gateway
          /       |       |       \
       VPC-A    VPC-B   VPC-C    VPN
```

This makes centralized routing and network segmentation easier to manage.

---

## NAT and Private Workloads

### Question: Can a private subnet access the Internet?

**Answer:**

Yes, if an appropriate outbound path exists.

A common design is:

```text
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
```

The private workload does not need a public IP address.

---

### Question: Why can a NAT Gateway still fail even when it exists?

**Answer:**

The presence of a NAT Gateway alone does not guarantee connectivity.

You must verify:

```text
Private Subnet
    ↓
Correct Route Table
    ↓
0.0.0.0/0 → NAT Gateway
    ↓
NAT Gateway Subnet
    ↓
0.0.0.0/0 → Internet Gateway
    ↓
Internet
```

You should also consider:

- NACL rules.
- Security Groups.
- DNS.
- NAT Gateway health.
- Destination availability.

---

## VPC Routing and Troubleshooting

### Question: How would you troubleshoot an application that cannot connect to PostgreSQL?

**Answer:**

Use a layered approach.

```text
Application
   ↓
DNS
   ↓
Route
   ↓
Security Group
   ↓
NACL
   ↓
Network Path
   ↓
PostgreSQL
```

Check:

1. Is the PostgreSQL hostname resolving?
2. What IP does it resolve to?
3. Is the destination inside the expected VPC or network?
4. Does the source subnet have a route to the destination?
5. Does the database Security Group allow TCP `5432`?
6. Do NACLs allow the traffic and return traffic?
7. Is PostgreSQL actually listening?
8. Is the database healthy?

---

### Question: How would you troubleshoot an EC2 instance that cannot reach the Internet?

**Answer:**

Check:

```text
EC2
 ↓
ENI
 ↓
Subnet
 ↓
Route Table
 ↓
Internet Gateway / NAT Gateway
 ↓
Security Group
 ↓
NACL
 ↓
DNS
```

For a public instance, verify:

- Public IP.
- Internet Gateway.
- Route to IGW.
- Security Group.
- NACL.

For a private instance, verify:

- NAT Gateway.
- Private subnet route.
- NAT subnet route.
- Internet Gateway.
- NAT Gateway availability.

---

## Architecture Questions

### Question: How would you design a production VPC for a backend application?

**Answer:**

A common architecture is:

```text
                         Internet
                            |
                            v
                    Internet Gateway
                            |
                     Public Subnets
                    /              \
                   /                \
                 ALB                NAT
                   \                /
                    \              /
                 Private Subnets
                 /              \
                /                \
          Application          Worker
          ECS / EC2            Celery
                |
        +-------+-------+
        |               |
    PostgreSQL        Redis
```

A multi-AZ implementation might use:

```text
VPC
├── AZ-a
│   ├── Public Subnet
│   ├── Private Application Subnet
│   └── Private Database Subnet
│
└── AZ-b
    ├── Public Subnet
    ├── Private Application Subnet
    └── Private Database Subnet
```

Key design principles include:

- Public entry points should be minimized.
- Application workloads should generally be private.
- Databases should not be Internet-facing.
- Application capacity should span multiple Availability Zones.
- Security Groups should use least privilege.
- Network CIDRs should be planned for future connectivity.
- NAT and VPC endpoints should be used intentionally.
- Network observability should be enabled.

---

### Question: Should a database be deployed in a public subnet?

**Answer:**

Generally, no.

A production PostgreSQL database should normally be reachable only through private networking.

A common architecture is:

```text
Internet
   |
   v
ALB
   |
   v
Private Application
   |
   v
Private PostgreSQL
```

The database Security Group should permit database traffic only from trusted application Security Groups or network sources.

---

### Question: How would you connect an application to a database securely?

**Answer:**

Use network segmentation and least-privilege access.

Example:

```text
Application SG
      |
      | TCP 5432
      v
Database SG
```

The database Security Group should allow:

```text
TCP 5432
Source: Application Security Group
```

rather than:

```text
TCP 5432
Source: 0.0.0.0/0
```

Network access should be combined with database authentication, encryption, secrets management, and application-level authorization.

---

## Production and Senior-Level Questions

### Question: What are common VPC production failures?

**Answer:**

Common failures include:

| Failure | Typical Cause |
|---|---|
| Private workload cannot reach Internet | Missing NAT route |
| Public workload cannot reach Internet | Missing IGW route or public IP |
| Application cannot reach database | SG, NACL, route, DNS, or DB issue |
| VPC peering does not work | Missing routes or overlapping CIDRs |
| Transit Gateway path fails | Missing attachment or TGW route |
| AWS service access fails | Endpoint, route, endpoint policy, or DNS issue |
| Hostname does not resolve | DNS configuration or Route 53 issue |
| Requests intermittently fail | AZ-specific path, NACL, capacity, or dependency issue |
| Cross-VPC communication fails | Routing or CIDR overlap |
| Connectivity appears correct but requests fail | Application, TLS, port, or protocol issue |

The important interview point is that VPC failures are rarely diagnosed correctly by checking only one component.

---

### Question: What is the difference between routing and security?

**Answer:**

Routing determines **where traffic should go**.

Security controls determine **whether the traffic is allowed**.

For example:

```text
Route Table:
10.1.0.0/16 → Transit Gateway
```

means traffic has a route toward that destination.

It does not mean the traffic is permitted.

Security Groups and NACLs can still block the traffic.

A useful mental model is:

```text
Route:
"Where should the packet go?"

Security:
"Is this packet allowed?"
```

---

### Question: How do you systematically troubleshoot VPC connectivity?

**Answer:**

Start with the actual network path.

```text
Source
  ↓
ENI
  ↓
Subnet
  ↓
Route Table
  ↓
Security Group
  ↓
NACL
  ↓
Gateway / Endpoint / Peering / TGW / VPN
  ↓
Destination
```

Then validate:

1. DNS resolution.
2. TCP connectivity.
3. TLS connectivity where applicable.
4. Application protocol.
5. Application health.

AWS tools such as VPC Flow Logs and Reachability Analyzer can provide additional evidence.

---

## Interview Traps

### Trap: "A subnet is public because it has a public IP."

**Correct reasoning:**

A subnet's public/private classification is primarily determined by routing. A resource may have a public IP, but Internet connectivity still depends on the subnet's route table and other controls.

---

### Trap: "Security Groups are stateless."

**Correct answer:**

Security Groups are stateful.

Network ACLs are stateless.

---

### Trap: "NAT Gateway allows inbound Internet connections."

**Correct answer:**

NAT Gateway primarily enables outbound connections initiated by private resources. It is not a general-purpose inbound Internet gateway for private workloads.

---

### Trap: "VPC peering is transitive."

**Correct answer:**

VPC peering is not transitive.

A → B and B → C does not automatically provide A → C connectivity.

---

### Trap: "A route means traffic is allowed."

**Correct answer:**

A route only determines the network path. Security Groups, NACLs, endpoint policies, and other controls may still prevent communication.

---

### Trap: "Adding `0.0.0.0/0` to a route table makes a subnet public."

**Correct answer:**

The target matters.

For example:

```text
0.0.0.0/0 → Internet Gateway
```

provides an Internet path.

Whereas:

```text
0.0.0.0/0 → NAT Gateway
```

is typical for a private subnet's outbound Internet path.

---

## Practical AWS CLI Questions

### Question: How would you inspect a VPC?

**Answer:**

```bash
aws ec2 describe-vpcs \
  --query 'Vpcs[*].[VpcId,CidrBlock,State]' \
  --output table
```

---

### Question: How would you inspect subnets?

**Answer:**

```bash
aws ec2 describe-subnets \
  --query 'Subnets[*].[SubnetId,VpcId,AvailabilityZone,CidrBlock]' \
  --output table
```

---

### Question: How would you inspect route tables?

**Answer:**

```bash
aws ec2 describe-route-tables \
  --query 'RouteTables[*].[RouteTableId,VpcId,Routes]' \
  --output json
```

---

### Question: How would you inspect Security Groups?

**Answer:**

```bash
aws ec2 describe-security-groups \
  --query 'SecurityGroups[*].[GroupId,GroupName,VpcId]' \
  --output table
```

---

## Key Takeaways

- **A VPC is the foundational network boundary for AWS workloads**, providing control over addressing, subnets, routing, connectivity, DNS, and network security.
- **Subnets are Availability Zone scoped**, while public or private behavior primarily depends on route-table configuration and the available network path.
- **Routing and security are separate concerns**: route tables determine where traffic goes, while Security Groups and NACLs determine whether traffic is permitted.
- **Production VPC architecture should minimize public exposure**, use private application and database networking, distribute workloads across Availability Zones, and apply least-privilege connectivity.
- **Strong VPC interview answers are path-oriented**: identify the source and destination, then reason through ENI, subnet, route, security controls, gateways or network services, DNS, transport, and application behavior.