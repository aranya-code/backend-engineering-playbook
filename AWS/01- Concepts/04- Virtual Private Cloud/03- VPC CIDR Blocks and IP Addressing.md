# 03- VPC CIDR Blocks and IP Addressing

## Overview

CIDR blocks and IP addressing define the address space in which VPC resources communicate. Every VPC design ultimately depends on having a deliberate IP allocation strategy because subnets, routing, VPC peering, Transit Gateway connectivity, VPNs, Direct Connect, containers, and hybrid networks all depend on predictable address ranges.

For a backend engineer, CIDR planning is not just an IP-addressing exercise. It directly affects:

- How many workloads can run in a subnet
- How many Availability Zones can be supported
- Whether VPCs can communicate
- Whether hybrid connectivity is possible
- Whether Kubernetes can obtain enough addresses
- How traffic is routed
- How environments are isolated
- How easily infrastructure can scale
- How difficult future network migrations will be

A poorly planned CIDR scheme can remain invisible during early development and become a major architectural constraint once the organization introduces multiple VPCs, AWS accounts, Kubernetes clusters, on-premises connectivity, or multi-Region networking.

---

## What Is CIDR?

CIDR stands for **Classless Inter-Domain Routing**.

CIDR represents an IP network using an address and a prefix length:

```text
10.0.0.0/16
```

The prefix length determines how many bits represent the network portion of the address.

For IPv4:

```text
IPv4 address = 32 bits
```

Therefore:

```text
10.0.0.0/16
```

means:

```text
16 bits  -> network
16 bits  -> host/address space
```

The larger the prefix number, the smaller the address range.

For example:

| CIDR | Total IPv4 addresses |
|---|---:|
| `/8` | 16,777,216 |
| `/16` | 65,536 |
| `/20` | 4,096 |
| `/24` | 256 |
| `/28` | 16 |

These are mathematical address counts. AWS reserves five IPv4 addresses in each subnet, so the number of usable IPv4 addresses available to resources is smaller.

---

## Why CIDR Matters in AWS

AWS networking uses CIDR blocks extensively.

A typical hierarchy is:

```text
VPC
10.0.0.0/16
    |
    +-- Subnet
    |   10.0.1.0/24
    |
    +-- Subnet
    |   10.0.2.0/24
    |
    +-- Subnet
        10.0.3.0/24
```

The VPC defines the larger address space.

Subnets carve that space into smaller network segments.

Route tables then use IP ranges to determine where traffic should go.

For example:

```text
Destination       Target
10.0.0.0/16       local
0.0.0.0/0         igw-xxxxxxxx
```

The CIDR is therefore directly involved in both **address allocation** and **routing decisions**.

---

## IPv4 Address Structure

An IPv4 address contains 32 bits and is commonly written as four decimal octets.

Example:

```text
10.20.30.40
```

Each octet represents 8 bits:

```text
10        20        30        40
00001010  00010100  00011110  00101000
```

With CIDR:

```text
10.20.30.40/24
```

the first 24 bits represent the network portion.

Conceptually:

```text
Network portion                Host portion
<------------------------>     <-------->
10.20.30                    .40
        /24
```

The prefix length determines where the network portion ends.

---

## CIDR Prefix Length

The `/number` after an IP address represents the prefix length.

Examples:

```text
10.0.0.0/8
10.0.0.0/16
10.0.0.0/24
10.0.0.0/28
```

As the prefix length increases, the network becomes smaller.

```text
/8
 |
 +---- Large address space

/16
 |
 +---- Medium address space

/24
 |
 +---- Smaller address space

/28
 |
 +---- Very small address space
```

A useful rule is:

> Larger CIDR prefix = fewer addresses.

For example:

```text
10.0.0.0/16
```

contains many more addresses than:

```text
10.0.0.0/24
```

---

## VPC CIDR Blocks

A VPC requires an IPv4 CIDR block when it is created.

A common production example is:

```text
10.0.0.0/16
```

This provides a large address space that can be divided into multiple subnets.

For example:

```text
VPC: 10.0.0.0/16

Public:
10.0.1.0/24
10.0.2.0/24

Application:
10.0.11.0/24
10.0.12.0/24

Database:
10.0.21.0/24
10.0.22.0/24
```

The exact allocation should depend on workload requirements rather than following a fixed template.

---

## Choosing a VPC CIDR

CIDR selection should be treated as an architectural decision.

Consider:

- Number of Availability Zones
- Number of subnets
- Expected workload growth
- EC2 instances
- ECS tasks
- EKS pods
- Lambda ENIs
- Load balancers
- VPC endpoints
- Future VPC peering
- Transit Gateway
- On-premises networks
- VPN
- Direct Connect
- Multi-account networking
- Disaster recovery environments

A VPC that initially hosts five EC2 instances may eventually host hundreds of services and thousands of network interfaces.

The initial address space should account for that possibility.

---

## Private IPv4 Address Ranges

RFC 1918 defines commonly used private IPv4 ranges:

| Private range | CIDR |
|---|---|
| `10.0.0.0 - 10.255.255.255` | `10.0.0.0/8` |
| `172.16.0.0 - 172.31.255.255` | `172.16.0.0/12` |
| `192.168.0.0 - 192.168.255.255` | `192.168.0.0/16` |

These ranges are commonly used for VPC networks.

For example:

```text
Production VPC
10.0.0.0/16

Staging VPC
10.1.0.0/16

Development VPC
10.2.0.0/16
```

There is no requirement to use exactly these ranges, but they are common choices.

---

## Public IPv4 Addresses

Public IPv4 addresses are globally routable addresses.

A resource may have:

- Private IPv4 address
- Public IPv4 address
- Elastic IP address

These serve different purposes.

### Private IP

Used for communication inside private networks.

Example:

```text
10.0.10.25
```

### Public IP

Provides public IPv4 connectivity where the surrounding network architecture permits it.

### Elastic IP

Provides a static public IPv4 address that can be associated with supported AWS resources.

For modern backend architectures, application servers typically do not need individually assigned public IPs.

A common design is:

```text
Internet
   |
   v
Application Load Balancer
   |
   v
Private Application Servers
```

---

## Subnet CIDR Blocks

Subnets receive smaller CIDR ranges from the VPC address space.

For example:

```text
VPC
10.0.0.0/16

Subnet A
10.0.1.0/24

Subnet B
10.0.2.0/24

Subnet C
10.0.3.0/24
```

The subnet ranges must fit within the VPC CIDR.

They must also not overlap with one another.

Valid:

```text
VPC: 10.0.0.0/16

Subnet A: 10.0.1.0/24
Subnet B: 10.0.2.0/24
Subnet C: 10.0.3.0/24
```

Invalid:

```text
Subnet A: 10.0.1.0/24
Subnet B: 10.0.1.128/25
```

because the second range overlaps with part of the first.

---

## AWS Reserved IPv4 Addresses

AWS reserves five IPv4 addresses within every subnet.

For example, for:

```text
10.0.1.0/24
```

the following addresses are reserved:

```text
10.0.1.0
10.0.1.1
10.0.1.2
10.0.1.3
10.0.1.255
```

Therefore:

```text
/24
256 total addresses

256 - 5
= 251 usable IPv4 addresses
```

This matters when estimating subnet capacity.

A subnet that mathematically contains 256 addresses does not provide 256 addresses for workload allocation.

---

## Subnet Sizing

Subnet size should be based on expected resource consumption.

A simplistic design might use:

```text
Public Subnet:     /24
Application:       /24
Database:          /24
```

This may be sufficient for a small application.

A high-scale environment may require much larger ranges.

The correct question is:

> How many network interfaces and IP addresses could this subnet need over its lifetime?

This becomes especially important for containerized environments.

---

## CIDR and Kubernetes

Kubernetes can consume significantly more IP addresses than a traditional VM-based application.

For example:

```text
EKS Node
   |
   +-- Primary ENI IP
   |
   +-- Secondary IPs
          |
          +-- Pod
          +-- Pod
          +-- Pod
          +-- Pod
```

Depending on the networking configuration, pod networking can consume addresses from the VPC or related networking ranges.

Therefore, an EKS cluster can exhaust subnet IP capacity even when EC2 CPU and memory are available.

This is one reason subnet sizing should be considered alongside:

- Maximum pod count
- Node count
- Instance types
- ENI limits
- Secondary IP capacity
- Cluster growth
- Availability Zone distribution

---

## CIDR Planning Across Availability Zones

A common production pattern is to allocate equivalent subnet ranges across multiple Availability Zones.

For example:

```text
VPC: 10.0.0.0/16

AZ A:
    Public: 10.0.1.0/24
    App:    10.0.11.0/20
    Data:   10.0.21.0/24

AZ B:
    Public: 10.0.2.0/24
    App:    10.0.12.0/20
    Data:   10.0.22.0/24
```

The exact ranges depend on the organization's IP plan.

The important principle is that address allocation should be predictable.

For example:

```text
10.0.x.0/24

x = Availability Zone or logical segment
```

A consistent scheme makes network operations easier.

---

## Hierarchical CIDR Allocation

Large organizations should consider hierarchical address allocation.

For example:

```text
10.0.0.0/8
    |
    +-- Production
    |   10.0.0.0/16
    |
    +-- Staging
    |   10.1.0.0/16
    |
    +-- Development
    |   10.2.0.0/16
    |
    +-- Shared Services
        10.3.0.0/16
```

Each environment can then be divided further:

```text
Production
10.0.0.0/16
    |
    +-- AZ A
    |   +-- Public
    |   +-- Application
    |   +-- Database
    |
    +-- AZ B
        +-- Public
        +-- Application
        +-- Database
```

This approach makes routing and network ownership easier to reason about.

---

## Avoiding Overlapping CIDRs

Overlapping CIDRs are one of the most important VPC design problems.

Consider:

```text
VPC A
10.0.0.0/16

VPC B
10.0.0.0/16
```

If these VPCs later need private communication, the overlapping address space creates ambiguity.

A better design is:

```text
VPC A
10.0.0.0/16

VPC B
10.1.0.0/16
```

and:

```text
VPC C
10.2.0.0/16
```

The same consideration applies to:

- On-premises networks
- VPN-connected networks
- Direct Connect
- Transit Gateway
- VPC peering
- Multi-Region environments

CIDR planning must therefore consider networks outside the current VPC.

---

## VPC Peering and CIDR

VPC peering commonly requires non-overlapping CIDR ranges for straightforward private routing.

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

Routes can then be configured to direct traffic appropriately.

Example:

```text
VPC A route table

Destination       Target
10.1.0.0/16       pcx-xxxxxxxx
```

and:

```text
VPC B route table

Destination       Target
10.0.0.0/16       pcx-xxxxxxxx
```

The Security Groups and NACLs must also allow the required traffic.

---

## Transit Gateway and CIDR Design

Transit Gateway architectures can connect many VPCs and external networks.

For example:

```mermaid
flowchart TB
    VPC1["Production VPC<br/>10.0.0.0/16"]
    VPC2["Staging VPC<br/>10.1.0.0/16"]
    VPC3["Shared Services<br/>10.2.0.0/16"]
    TGW["Transit Gateway"]
    ONPREM["On-Premises<br/>10.100.0.0/16"]

    VPC1 --> TGW
    VPC2 --> TGW
    VPC3 --> TGW
    ONPREM --> TGW
```

A centralized network becomes significantly easier to operate when address ranges are predictable and non-overlapping.

CIDR planning therefore becomes an organizational networking concern, not just a single-VPC concern.

---

## Hybrid Networking

Hybrid architectures commonly connect AWS to on-premises networks using:

- Site-to-Site VPN
- AWS Direct Connect
- Transit Gateway

Example:

```text
AWS VPC
10.0.0.0/16
      |
      v
Transit Gateway
      |
      +---- VPN
      |
      +---- Direct Connect
      |
      v
On-Premises
10.100.0.0/16
```

If the VPC and on-premises network use overlapping CIDRs, private routing becomes significantly more difficult.

For this reason, enterprise network teams should maintain a centralized IP address management strategy.

---

## Secondary VPC CIDR Blocks

AWS supports adding secondary IPv4 CIDR blocks to a VPC.

For example:

```text
Primary:
10.0.0.0/16

Secondary:
10.10.0.0/16
```

This can be useful when additional address capacity is required.

However, secondary CIDRs should not be treated as a substitute for thoughtful initial planning.

Before adding one, evaluate:

- Why the existing address space is insufficient
- Which subnets need expansion
- Whether new subnets can use the secondary range
- Whether connected networks can route to it
- Whether existing network architecture remains consistent

---

## IPv6 in VPCs

IPv6 uses 128-bit addresses and provides a vastly larger address space than IPv4.

An IPv6 address may look like:

```text
2001:db8:1234:5678::1
```

AWS VPCs can support IPv6 addressing alongside IPv4.

This is commonly referred to as dual-stack networking:

```text
Application
    |
    +-- IPv4
    |
    +-- IPv6
```

### Why IPv6 Matters

IPv6 can help address:

- IPv4 exhaustion
- Large-scale address requirements
- Modern internet-facing architectures
- Global connectivity requirements

However, introducing IPv6 requires understanding the entire application and security stack.

Do not assume that an application designed for IPv4 automatically behaves correctly in an IPv6 environment.

---

## Dual-Stack Architecture

A dual-stack backend might look like:

```mermaid
flowchart LR
    Client["Client"]
    LB["Load Balancer"]
    API["Application"]
    DB["Database"]

    Client -->|"IPv4 / IPv6"| LB
    LB -->|"Private networking"| API
    API -->|"Private networking"| DB
```

Applications, security policies, DNS, monitoring, and external integrations should all be evaluated before enabling IPv6.

---

## IPv6 and NAT

IPv6 does not require NAT in the same way IPv4 private networks commonly use NAT.

This changes the network design.

With IPv4:

```text
Private Application
       |
       v
NAT Gateway
       |
       v
Internet
```

IPv6 architectures can use routed IPv6 connectivity without requiring traditional IPv4-style NAT.

However, direct routability does not mean unrestricted access should be allowed.

Security controls remain necessary.

---

## DNS and IP Addressing

Backend applications generally should not hard-code private IP addresses.

Prefer DNS names:

```text
postgres.internal.example.com
redis.internal.example.com
api.internal.example.com
```

rather than:

```text
10.0.21.15
10.0.22.20
10.0.11.30
```

DNS provides an abstraction layer between application configuration and infrastructure.

For example:

```text
Django
   |
   | DATABASE_HOST=postgres.internal.example.com
   v
DNS
   |
   v
Database endpoint
```

This is particularly important when infrastructure is replaced, scaled, or moved.

---

## IP Addressing and Service Discovery

Microservices should generally use service discovery mechanisms rather than manually maintaining IP addresses.

For example:

```text
Order Service
     |
     | orders.internal.example.com
     v
Service Discovery
     |
     v
Order Service Instances
```

This allows the infrastructure to change without requiring application deployments every time an instance IP changes.

---

## IP Addressing and Containers

Containers introduce dynamic network allocation.

For example:

```text
ECS / EKS
    |
    +-- Service
         |
         +-- Task / Pod
         |     |
         |     +-- IP
         |
         +-- Task / Pod
               |
               +-- IP
```

When workloads scale horizontally:

```text
10 instances
    |
    v
100 instances
    |
    v
1000 instances
```

the network must have enough available addresses.

This is why IP planning is a capacity-planning concern.

---

## IP Addressing and Load Balancers

Load balancers also consume networking resources and IP capacity.

For example:

```text
Internet
   |
   v
Application Load Balancer
   |
   +-- AZ A subnet
   |
   +-- AZ B subnet
   |
   v
Application Targets
```

The subnets used by highly available load balancers must have sufficient capacity.

A subnet with insufficient available addresses can cause infrastructure provisioning or scaling operations to fail.

---

## IP Addressing and Lambda

Lambda functions configured for VPC access use network interfaces in the selected subnets.

This means large-scale Lambda deployments can affect subnet IP capacity.

The architecture should account for:

- Number of functions
- Concurrency
- Subnet availability
- Network interfaces
- VPC endpoints
- NAT requirements

The goal is to avoid discovering IP exhaustion only during a production scaling event.

---

## IP Capacity Planning

A practical capacity model should consider more than the number of EC2 instances.

Potential IP consumers include:

- EC2 instances
- ECS tasks
- EKS nodes
- EKS pods
- Load balancers
- Lambda networking
- VPC endpoints
- Network appliances
- NAT infrastructure
- Other AWS-managed networking resources

A simplified planning process is:

```text
Current IP usage
       +
Expected growth
       +
Scaling headroom
       +
Failure / AZ redistribution
       +
Future services
       =
Required subnet capacity
```

Do not size a subnet only for today's workload.

---

## Subnet Capacity Monitoring

Monitor subnet IP availability as an infrastructure capacity metric.

For example:

```text
Subnet
10.0.11.0/24

Total:
256

AWS-reserved:
5

Potentially usable:
251

Current allocation:
210

Remaining:
41
```

The exact available count should be obtained from AWS rather than calculated solely from theoretical CIDR size.

When remaining capacity becomes low, remediation may require:

- Larger subnets
- Additional subnets
- Secondary VPC CIDRs
- Workload redistribution
- Network redesign

---

## CIDR and Route Matching

Routing uses destination IP ranges.

Consider:

```text
10.0.0.0/16
10.0.10.0/24
```

A destination such as:

```text
10.0.10.25
```

matches both ranges.

Routing systems generally prefer the **most specific matching route**.

Therefore:

```text
10.0.10.0/24
```

is more specific than:

```text
10.0.0.0/16
```

This principle is critical when reasoning about complex route tables.

---

## Longest Prefix Match

Consider this route table:

```text
Destination       Target

10.0.0.0/16       local
10.0.10.0/24      appliance
0.0.0.0/0         NAT Gateway
```

For:

```text
10.0.10.25
```

the matching routes are:

```text
10.0.0.0/16
10.0.10.0/24
0.0.0.0/0
```

The most specific match is:

```text
10.0.10.0/24
```

Therefore traffic follows that route.

This concept becomes especially important when debugging:

- Transit Gateway
- VPN
- VPC peering
- Network appliances
- PrivateLink
- Hybrid networks

---

## CIDR Aggregation

CIDR also enables route summarization.

Instead of maintaining many routes:

```text
10.0.0.0/24
10.0.1.0/24
10.0.2.0/24
10.0.3.0/24
```

a larger aggregate may sometimes represent the same logical network:

```text
10.0.0.0/22
```

Route aggregation can reduce routing complexity.

However, aggregation must only be used when the address ranges and traffic requirements actually justify it.

Overly broad routes can unintentionally send traffic to the wrong destination.

---

## Common CIDR Mistakes

### Choosing a CIDR Too Small

Example:

```text
VPC: 10.0.0.0/24
```

This leaves very little room for subnet segmentation and workload growth.

### Overlapping Networks

Example:

```text
Production:
10.0.0.0/16

On-Premises:
10.0.0.0/16
```

This can severely complicate hybrid routing.

### Treating Theoretical Capacity as Usable Capacity

AWS reserves addresses in each subnet.

Always account for AWS-specific reservations.

### Ignoring Container IP Consumption

A cluster can exhaust addresses even when compute capacity remains available.

### Hard-Coding IP Addresses

Dynamic infrastructure makes static private IP assumptions fragile.

### Using Random Address Allocation

Inconsistent ranges make network operations and troubleshooting harder.

Prefer predictable allocation.

### Ignoring Future Connectivity

A VPC that works independently may become difficult to connect to later.

Consider future:

- VPC peering
- Transit Gateway
- VPN
- Direct Connect
- Multi-account networking
- Disaster recovery

---

## Production CIDR Design Example

Consider a backend platform with:

- Production
- Staging
- Development
- Shared services
- Three Availability Zones
- Application workloads
- Databases
- Kubernetes

A simplified allocation could be:

```text
Corporate Private Range
10.0.0.0/8
|
+-- Production
|   10.0.0.0/16
|
+-- Staging
|   10.1.0.0/16
|
+-- Development
|   10.2.0.0/16
|
+-- Shared Services
    10.3.0.0/16
```

Production:

```text
10.0.0.0/16
|
+-- AZ A
|   +-- Public
|   +-- Application
|   +-- Database
|
+-- AZ B
|   +-- Public
|   +-- Application
|   +-- Database
|
+-- AZ C
    +-- Public
    +-- Application
    +-- Database
```

This is only an example allocation strategy.

A real organization should use an enterprise-wide IP management plan.

---

## AWS CLI Inspection

List VPC CIDRs:

```bash
aws ec2 describe-vpcs \
    --query 'Vpcs[].{VpcId:VpcId,Cidr:CidrBlock}'
```

List subnet CIDRs:

```bash
aws ec2 describe-subnets \
    --query 'Subnets[].{SubnetId:SubnetId,VpcId:VpcId,Cidr:CidrBlock,AZ:AvailabilityZone}'
```

Filter subnets belonging to a VPC:

```bash
aws ec2 describe-subnets \
    --filters Name=vpc-id,Values=vpc-xxxxxxxx
```

Inspect available IPv4 addresses:

```bash
aws ec2 describe-subnets \
    --subnet-ids subnet-xxxxxxxx \
    --query 'Subnets[].{SubnetId:SubnetId,Cidr:CidrBlock,AvailableIPv4:AvailableIpAddressCount}'
```

Inspect VPC CIDR associations:

```bash
aws ec2 describe-vpcs \
    --vpc-ids vpc-xxxxxxxx \
    --query 'Vpcs[].CidrBlockAssociationSet'
```

These commands are useful when validating address capacity during deployments and incidents.

---

## IP Addressing Troubleshooting

When a workload cannot start because of network capacity, investigate in this order:

```text
Workload deployment failure
        |
        v
Check subnet
        |
        v
Check AvailableIpAddressCount
        |
        v
Identify IP consumers
        |
        v
Check workload scaling
        |
        v
Check ENI consumption
        |
        v
Evaluate subnet capacity
        |
        v
Determine expansion strategy
```

For connectivity problems, also inspect:

```text
Source IP
Destination IP
Source subnet
Destination subnet
Route tables
Security Groups
NACLs
Network interfaces
DNS resolution
```

IP addressing problems and routing problems can look similar from the application layer, so the actual network path must be identified.

---

## Security Considerations

CIDR ranges often become part of security policies.

For example:

```text
Allow:
10.0.0.0/16
```

may permit traffic from every workload in the VPC.

A more precise rule may be:

```text
Source:
Application Security Group
```

rather than a broad CIDR.

Avoid using CIDR ranges as a substitute for identity-based security when Security Group references or higher-level authorization mechanisms are available.

Also consider whether an internal CIDR represents:

- Trusted production workloads
- Developer environments
- Shared services
- Partner networks
- On-premises systems

Network location alone should not automatically imply application trust.

---

## Scalability Considerations

CIDR planning becomes increasingly important as infrastructure scales.

At small scale:

```text
VPC
  |
  +-- EC2
  +-- RDS
```

At larger scale:

```text
Organization
|
+-- Multiple Accounts
|      |
|      +-- Multiple VPCs
|
+-- EKS
|
+-- ECS
|
+-- RDS
|
+-- Redis
|
+-- Kafka
|
+-- Shared Services
|
+-- On-Premises
|
+-- Multiple Regions
```

Every additional network increases the importance of consistent address allocation.

At organizational scale, IP address management should be treated as shared infrastructure rather than an individual application team's local decision.

---

## High Availability Considerations

CIDR allocation should support multiple Availability Zones.

Do not allocate almost all address capacity to one AZ while leaving another with insufficient capacity.

A balanced model might be:

```text
AZ A
10.0.0.0/20

AZ B
10.0.16.0/20

AZ C
10.0.32.0/20
```

This gives each Availability Zone comparable address capacity.

The exact prefix should be based on workload requirements.

The objective is to prevent an AZ failure or workload rebalance from creating an IP exhaustion problem.

---

## Disaster Recovery Considerations

Disaster recovery environments should have deliberate CIDR ranges.

For example:

```text
Primary Region
10.0.0.0/16

DR Region
10.10.0.0/16
```

Non-overlapping ranges simplify:

- Cross-Region connectivity
- Transit Gateway routing
- VPN
- Replication
- Administrative access
- Network troubleshooting

A DR VPC should not be treated as an afterthought in IP planning.

---

## Cost Considerations

CIDR itself does not generally represent a major direct AWS cost.

However, poor CIDR design can create indirect costs.

Examples include:

- Additional networking infrastructure
- NAT Gateway dependency
- Network appliances
- Complex Transit Gateway architectures
- Migration projects
- Readdressing projects
- Operational overhead

A well-planned address space can therefore reduce future infrastructure and migration costs.

---

## Senior-Level CIDR Design Reasoning

At an intermediate level, CIDR knowledge means understanding:

```text
10.0.0.0/16
```

and being able to determine its approximate capacity.

At a senior level, CIDR planning involves answering questions such as:

- How much address space will the platform need in five years?
- How many VPCs will the organization operate?
- Will VPCs need to communicate?
- What address ranges exist on-premises?
- Will Kubernetes consume VPC addresses?
- How will multiple AWS accounts be connected?
- How will the DR Region be addressed?
- Can Transit Gateway route all networks without overlap?
- How will subnet capacity be monitored?
- What happens if an Availability Zone fails?
- Can the address architecture support future acquisitions or organizational expansion?

The senior-level concern is not simply:

> "How many IP addresses do I have?"

It is:

> "Can this address architecture continue supporting the organization's network topology as the platform grows?"

---

## Interview Traps

### What does `/16` mean?

It means the first 16 bits represent the network prefix.

For IPv4, the remaining 16 bits form the address space.

### Is `/24` larger than `/16`?

No.

`/16` contains more addresses than `/24`.

### Can two subnets overlap?

No. Subnet CIDRs within the same VPC must not overlap.

### Why are overlapping VPC CIDRs problematic?

They create ambiguity for private routing and make many connectivity architectures difficult or impossible to implement cleanly.

### Why does subnet size matter?

Subnet size determines available IP capacity for workloads and AWS-managed networking resources.

### Why can an EKS cluster experience IP exhaustion?

Depending on the networking model, pods and nodes can consume significant numbers of VPC IP addresses.

### Does a `/24` subnet provide 256 usable AWS addresses?

No. AWS reserves five IPv4 addresses in each subnet.

### Why plan CIDRs before creating VPC peering?

Because connected networks should have non-overlapping address spaces for straightforward private routing.

### Can adding a secondary VPC CIDR solve every IP exhaustion problem?

No. Existing subnet architecture, routing, workload placement, and connected networks must still be evaluated.

### Should applications use hard-coded private IP addresses?

Generally no. Prefer DNS-based service discovery and managed service endpoints.

## Key Takeaways

- CIDR planning defines the address capacity and routing foundation of a VPC and should be treated as a long-term architectural decision.
- Non-overlapping, predictable address ranges are essential for VPC peering, Transit Gateway, VPN, Direct Connect, multi-account, and disaster recovery architectures.
- Subnet capacity must account for AWS-reserved addresses and dynamic IP consumers such as EC2, ECS, EKS, Lambda, load balancers, and VPC endpoints.
- Production CIDR design should support Availability Zone distribution, future workload growth, hybrid networking, and organizational-scale network expansion.
- Senior-level CIDR design is about preserving future connectivity and scalability rather than simply calculating the number of available IP addresses.