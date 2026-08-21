# 02- VPC Components

## Overview

Amazon VPC is composed of several networking primitives that work together to control addressing, segmentation, routing, connectivity, security, and observability.

Understanding these components individually is useful, but production VPC design requires understanding how they interact. A route table can determine where traffic should go, while a Security Group can still reject it. A private subnet can reach the internet through a NAT Gateway without accepting direct inbound internet traffic. A VPC endpoint can provide private access to an AWS service without traversing a NAT Gateway.

The core VPC components can be grouped into several responsibilities:

| Responsibility | Components |
|---|---|
| Network boundary | VPC |
| Addressing | CIDR blocks, private IP addresses, Elastic IP addresses |
| Segmentation | Subnets |
| Routing | Route tables, routes |
| Internet connectivity | Internet Gateway |
| Outbound connectivity | NAT Gateway |
| Private AWS service access | VPC endpoints |
| Network security | Security Groups, Network ACLs |
| Network interfaces | Elastic Network Interfaces |
| Inter-VPC connectivity | VPC peering, Transit Gateway |
| Hybrid connectivity | Site-to-Site VPN, Direct Connect |
| Observability | VPC Flow Logs |
| Network diagnostics | Reachability Analyzer |

A useful mental model is:

```text
                         Amazon VPC
                              |
          +-------------------+-------------------+
          |                   |                   |
      Addressing          Segmentation         Routing
          |                   |                   |
      CIDR blocks          Subnets          Route tables
          |                   |
          +---------+---------+
                    |
             Network Interfaces
                    |
          +---------+---------+
          |                   |
       Security           Connectivity
       controls               |
          |           +-------+--------+
          |           |       |        |
       SG / NACL     IGW     NAT    Endpoints
                              |
                         External access
```

The most important production skill is understanding the traffic path through these components rather than memorizing each service independently.

---

## VPC

### What It Is

A VPC is a logically isolated virtual network within an AWS Region.

It defines the primary networking boundary for workloads such as:

- EC2 instances
- ECS tasks
- EKS nodes and pods
- RDS databases
- ElastiCache clusters
- Internal load balancers
- Lambda functions configured for VPC access
- Self-managed services

A VPC requires an IP address range, typically defined using an IPv4 CIDR block.

Example:

```text
10.0.0.0/16
```

### Why It Exists

A VPC provides control over:

- IP addressing
- Network segmentation
- Routing
- Internet access
- Private connectivity
- Network security
- Network observability

It gives backend workloads a predictable network boundary instead of placing every resource into an uncontrolled shared network.

### Example

```text
VPC: 10.0.0.0/16

    Public Subnets
        10.0.1.0/24
        10.0.2.0/24

    Application Subnets
        10.0.11.0/24
        10.0.12.0/24

    Database Subnets
        10.0.21.0/24
        10.0.22.0/24
```

### Production Considerations

VPC CIDR planning should account for:

- Future subnet growth
- Multiple Availability Zones
- EKS or container IP requirements
- VPC peering
- Transit Gateway
- VPN connectivity
- On-premises address ranges
- Multi-account networking
- Future acquisitions or network integration

CIDR planning is difficult to change after a VPC becomes deeply integrated into production infrastructure.

---

## CIDR Blocks and IP Addressing

### What It Is

CIDR notation defines an IP address range.

For example:

```text
10.0.0.0/16
```

represents the VPC's address space.

Subnets allocate smaller ranges from the VPC CIDR.

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

### Why It Exists

CIDR provides a structured way to divide a network into smaller addressable segments.

This is important for:

- Network segmentation
- Routing
- Scaling
- Multi-AZ architecture
- Network connectivity between environments

### Production Considerations

Avoid overlapping CIDRs between networks that may need to communicate.

For example:

```text
VPC A: 10.0.0.0/16
VPC B: 10.0.0.0/16
```

This creates problems when attempting to establish straightforward private routing between the networks.

Prefer deliberate network allocation such as:

```text
Production: 10.0.0.0/16
Staging:    10.1.0.0/16
Development:10.2.0.0/16
Shared:     10.3.0.0/16
```

The exact ranges depend on the organization's overall network plan.

---

## Subnets

### What It Is

A subnet is a logical subdivision of a VPC's IP address range.

A subnet belongs to a single Availability Zone.

For example:

```text
VPC
10.0.0.0/16
    |
    +-- 10.0.1.0/24 -> AZ A
    +-- 10.0.2.0/24 -> AZ B
    +-- 10.0.3.0/24 -> AZ C
```

### Why It Exists

Subnets provide:

- Network segmentation
- IP allocation boundaries
- Routing boundaries
- Availability Zone placement
- Security boundaries

### Public vs Private Subnets

The distinction is primarily based on routing.

A public subnet typically has:

```text
0.0.0.0/0 -> Internet Gateway
```

A private subnet might have:

```text
0.0.0.0/0 -> NAT Gateway
```

A private subnet may also have no default internet route at all.

### Production Pattern

```mermaid
flowchart TB
    VPC["VPC"]

    AZ1["Availability Zone A"]
    AZ2["Availability Zone B"]

    PUB1["Public Subnet"]
    APP1["Private App Subnet"]
    DB1["Private DB Subnet"]

    PUB2["Public Subnet"]
    APP2["Private App Subnet"]
    DB2["Private DB Subnet"]

    VPC --> AZ1
    VPC --> AZ2

    AZ1 --> PUB1
    AZ1 --> APP1
    AZ1 --> DB1

    AZ2 --> PUB2
    AZ2 --> APP2
    AZ2 --> DB2
```

### Common Mistake

Calling a subnet public simply because an EC2 instance inside it has a public IP is an incomplete mental model.

Public reachability depends on the combination of:

- Route table
- Internet Gateway
- Addressing
- Security Group
- Network ACL
- Destination configuration

---

## Route Tables

### What It Is

A route table contains routing rules that determine where network traffic should be sent.

Example:

```text
Destination       Target
10.0.0.0/16       local
0.0.0.0/0         igw-xxxxxxxx
```

The `local` route allows communication within the VPC's address space.

### Why It Exists

Route tables determine network paths.

They answer:

> "Where should traffic destined for this IP range go?"

They do not answer:

> "Is the traffic allowed?"

That is handled by security controls.

### Public Route Table

```text
Destination       Target
10.0.0.0/16       local
0.0.0.0/0         igw-xxxxxxxx
```

### Private Route Table

```text
Destination       Target
10.0.0.0/16       local
0.0.0.0/0         nat-xxxxxxxx
```

### VPC Endpoint Route

Some endpoint types introduce specific routing behavior for supported AWS services.

The resulting architecture can be:

```text
Private Application
        |
        v
Route Table
        |
        v
VPC Endpoint
        |
        v
AWS Service
```

### Production Considerations

Keep route tables understandable.

Large environments can become difficult to operate when routes are created without a clear ownership model.

Document:

- Route purpose
- Destination
- Target
- Associated subnets
- Network ownership
- Failure behavior

---

## Internet Gateway

### What It Is

An Internet Gateway provides internet connectivity for a VPC.

It is attached to the VPC and provides the VPC-side connectivity required for internet communication.

### Typical Flow

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
Network Interface
    |
    v
Application
```

### Important Characteristics

An Internet Gateway:

- Is horizontally scaled by AWS
- Does not require provisioning EC2 instances
- Supports internet connectivity for eligible resources
- Works with VPC routing
- Does not automatically expose every VPC resource

### Common Mistake

A common misconception is:

```text
Internet Gateway attached
        =
Everything is public
```

This is incorrect.

The route table must direct traffic through the gateway, and the resource must have appropriate addressing and security configuration.

---

## NAT Gateway

### What It Is

A NAT Gateway provides outbound connectivity from private resources to external destinations.

Typical flow:

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

### Why It Exists

Private workloads often need outbound internet access for:

- Package downloads
- External APIs
- Software repositories
- Dependency installation
- Third-party integrations

The application does not need to be directly reachable from the internet.

### Production Architecture

For high availability, NAT Gateway placement should be considered alongside Availability Zone architecture.

For example:

```text
AZ A
    Private App Subnet
          |
          v
      NAT Gateway A
          |
          v
      Internet Gateway

AZ B
    Private App Subnet
          |
          v
      NAT Gateway B
          |
          v
      Internet Gateway
```

This avoids making application connectivity dependent on a single AZ's NAT path.

### Cost Considerations

NAT Gateways can become significant cost drivers in high-volume environments because charges can apply for:

- NAT Gateway runtime
- Data processing
- Data transfer

For supported AWS services, VPC endpoints can sometimes reduce unnecessary NAT traffic.

---

## Elastic Network Interface

### What It Is

An Elastic Network Interface (ENI) is a virtual network interface attached to a resource or used by AWS networking services.

It can have:

- Private IP addresses
- Security Groups
- MAC address
- Public or Elastic IP association where applicable

### Why It Matters

The ENI is an important abstraction because network traffic ultimately reaches network interfaces.

For example:

```text
Client
   |
   v
Route
   |
   v
Network Interface
   |
   v
EC2 Instance
```

For containers and other managed services, AWS may create and manage network interfaces on behalf of the service.

### Security Groups and ENIs

Security Groups are associated with network interfaces.

This makes the ENI an important point when troubleshooting connectivity.

If an application cannot reach a database, inspect:

```text
Source ENI
    |
    +-- Security Groups
    |
    +-- Subnet
    |
    +-- Route Table

Destination ENI
    |
    +-- Security Groups
    |
    +-- Subnet
    |
    +-- Route Table
```

---

## Security Groups

### What It Is

A Security Group is a stateful virtual firewall associated with network interfaces.

It controls allowed inbound and outbound traffic.

Example:

```text
Application Security Group

Inbound:
TCP 443
Source: Load Balancer Security Group
```

Database:

```text
Database Security Group

Inbound:
TCP 5432
Source: Application Security Group
```

### Why It Exists

Security Groups provide fine-grained network authorization at the resource level.

They are particularly useful for modeling application dependencies.

```text
ALB
 |
 | TCP 443
 v
API
 |
 | TCP 5432
 v
PostgreSQL
```

### Stateful Behavior

Security Groups are stateful.

If an allowed connection is established, return traffic is automatically allowed as part of that established flow.

This differs from Network ACLs.

### Production Best Practice

Prefer Security Group references over broad CIDR rules when workloads have explicit service relationships.

Prefer:

```text
db-sg
Inbound TCP 5432
Source: api-sg
```

over:

```text
db-sg
Inbound TCP 5432
Source: 10.0.0.0/16
```

when the architecture allows the more precise relationship.

---

## Network ACLs

### What It Is

A Network Access Control List is a stateless subnet-level traffic filter.

NACLs operate at the subnet boundary rather than directly at an individual application resource.

### Security Group vs NACL

| Characteristic | Security Group | Network ACL |
|---|---|---|
| Scope | Network interface/resource | Subnet |
| State | Stateful | Stateless |
| Rules | Allow rules | Allow and deny rules |
| Typical use | Resource-level access control | Subnet-level boundary |
| Return traffic | Automatically handled | Must be explicitly permitted |
| Rule ordering | Not based on numeric evaluation order in the same way | Rule number matters |

### Why Statelessness Matters

Suppose an outbound request uses an ephemeral source port.

The response must also be permitted by the relevant NACL rules.

This is a common source of connectivity problems.

### Production Guidance

Use NACLs when subnet-level filtering provides meaningful security or compliance value.

Do not introduce complex NACL policies without operational expertise and testing.

Security Groups should normally remain the primary resource-level control.

---

## VPC Endpoints

### What It Is

VPC endpoints provide private connectivity between a VPC and supported AWS services.

They are especially valuable for private application environments.

Instead of:

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
AWS Service
```

the architecture can sometimes be:

```text
Private Application
       |
       v
VPC Endpoint
       |
       v
AWS Service
```

### Why It Exists

VPC endpoints can provide:

- Private service access
- Reduced dependence on NAT
- Improved network isolation
- More explicit access control
- Potential cost optimization

### Gateway Endpoints

Gateway endpoints are primarily associated with services such as:

- Amazon S3
- Amazon DynamoDB

They use route tables to direct supported service traffic.

### Interface Endpoints

Interface endpoints use endpoint network interfaces and are based on AWS PrivateLink.

They can provide private access to supported AWS services and endpoint services.

### Production Considerations

Consider:

- Which services need private access
- Endpoint policies
- DNS behavior
- Security Groups
- Availability Zone placement
- Endpoint cost
- Centralized endpoint architecture

Do not create endpoints indiscriminately. Evaluate actual traffic patterns and security requirements.

---

## VPC Peering

### What It Is

VPC Peering creates private network connectivity between two VPCs.

Example:

```text
VPC A
10.0.0.0/16
     |
     | Peering
     |
VPC B
10.1.0.0/16
```

### Requirements

The CIDR ranges should not overlap for normal private routing between the networks.

Routes must be configured appropriately on both sides.

Security controls must also allow the traffic.

### When to Use It

VPC peering is appropriate for relatively straightforward connectivity between VPCs.

### Limitation

A large number of VPCs can produce complex point-to-point topology.

For example:

```text
A <----> B
A <----> C
A <----> D
B <----> C
B <----> D
C <----> D
```

This becomes difficult to operate as the number of networks grows.

Transit Gateway is often more appropriate for centralized multi-VPC networking.

---

## Transit Gateway

### What It Is

AWS Transit Gateway provides a central network transit layer.

```text
                 VPC A
                   |
                   |
VPC B -------- Transit Gateway -------- VPC C
                   |
                   |
                 VPC D
```

### Why It Exists

It simplifies large-scale connectivity between:

- VPCs
- VPN connections
- Direct Connect
- Multiple AWS accounts
- Shared network infrastructure

### Production Considerations

Transit Gateway architectures require deliberate route management.

Consider:

- Route tables
- Attachment isolation
- Account boundaries
- Shared services
- Inspection architectures
- Failure domains
- Cross-Region connectivity
- Cost

Transit Gateway is an architectural tool, not simply a replacement for every VPC peering connection.

---

## VPC Flow Logs

### What It Is

VPC Flow Logs capture metadata about network traffic.

They can be useful for:

- Connectivity troubleshooting
- Security analysis
- Traffic visibility
- Incident investigation
- Network auditing

A flow record can help answer questions such as:

```text
Who attempted the connection?
What was the destination?
Which port was used?
Was the traffic accepted or rejected?
Which network interface was involved?
```

### What It Does Not Capture

Flow Logs are not packet captures.

They provide traffic metadata rather than complete application payloads.

### Production Usage

A typical architecture might be:

```text
VPC
 |
 +-- Flow Logs
       |
       v
 CloudWatch Logs / S3
       |
       v
 Analysis / Athena / Security tooling
```

Flow Logs should be integrated into the organization's observability and incident-response strategy.

---

## VPC Reachability Analyzer

### What It Is

VPC Reachability Analyzer is a configuration analysis tool for determining whether a network path can exist between specified resources.

It can help identify problems involving:

- Route tables
- Security Groups
- Network ACLs
- Network interfaces
- Gateways
- Network paths

### Why It Matters

Traditional troubleshooting often involves manually checking multiple components.

Reachability Analyzer can reduce this effort by analyzing the configured network path.

A useful troubleshooting workflow is:

```text
Application timeout
       |
       v
Check DNS
       |
       v
Check Reachability
       |
       v
Check Routes
       |
       v
Check Security Groups
       |
       v
Check NACLs
       |
       v
Inspect Flow Logs
```

---

## Elastic IP Addresses

### What It Is

An Elastic IP is a static public IPv4 address that can be associated with supported AWS resources.

They are useful when a stable public IP is required.

Common examples include:

- NAT Gateway
- Certain public-facing infrastructure requirements
- Legacy integrations requiring IP allowlisting

### Production Considerations

Avoid using static public IPs as the default architecture for application instances when a load balancer or managed service can provide a better abstraction.

For example:

```text
Preferred:

Internet
   |
   v
Load Balancer
   |
   v
Application Fleet
```

rather than:

```text
Internet
   |
   v
Static public IP
   |
   v
Single EC2 instance
```

The latter introduces a stronger dependency on an individual resource.

---

## DHCP Options

A VPC can use a DHCP options set to provide network configuration information to resources that use DHCP.

This can include configuration related to:

- Domain name
- Domain name servers
- NTP servers
- NetBIOS configuration

Most applications do not require custom DHCP options.

They become more relevant in enterprise environments with custom DNS or network integration requirements.

---

## DNS in a VPC

VPC networking includes DNS capabilities that are important for modern backend systems.

DNS affects:

- Internal service discovery
- AWS service endpoints
- Database endpoints
- Load balancer endpoints
- Private hosted zones
- Service-to-service communication

For example:

```text
api.internal.example.com
        |
        v
Private DNS
        |
        v
Internal Load Balancer
        |
        v
Microservice
```

DNS failures can appear to be network failures, so DNS resolution should be considered early during troubleshooting.

---

## Component Interaction

The most important VPC knowledge is how components work together.

Consider an application in a private subnet connecting to PostgreSQL.

```mermaid
sequenceDiagram
    participant API as Application
    participant RT as Route Table
    participant DB as PostgreSQL
    participant SG as Security Groups

    API->>RT: Destination 10.0.21.10:5432
    RT->>RT: Select local VPC route
    RT->>SG: Deliver traffic to DB ENI
    SG->>SG: Evaluate inbound TCP 5432
    SG->>DB: Allow connection
    DB-->>API: PostgreSQL response
```

The connection requires multiple components to cooperate:

```text
Application
    |
    v
Network Interface
    |
    v
Subnet
    |
    v
Route Table
    |
    v
Network Path
    |
    v
Destination Network Interface
    |
    v
Security Group
    |
    v
Destination Service
```

If any required layer is incorrectly configured, the connection may fail.

---

## Component Comparison

| Component | Primary role | Scope | Stateful | Typical production use |
|---|---|---|---|---|
| VPC | Network isolation | Region | N/A | Application network boundary |
| Subnet | Network segmentation | AZ | N/A | Public/private workload separation |
| Route Table | Traffic routing | Subnet association | N/A | Determine packet path |
| Internet Gateway | Internet connectivity | VPC | N/A | Public ingress/egress |
| NAT Gateway | Outbound connectivity | AZ/subnet routing | Managed | Private workloads reaching external networks |
| Security Group | Resource firewall | ENI/resource | Yes | Service-level access control |
| Network ACL | Subnet firewall | Subnet | No | Subnet-level filtering |
| VPC Endpoint | Private AWS service access | VPC/AZ | Depends on endpoint type | Private AWS API/service connectivity |
| VPC Peering | VPC-to-VPC connectivity | VPC pair | N/A | Small-scale private connectivity |
| Transit Gateway | Centralized network transit | Regional network | N/A | Large-scale multi-VPC networking |
| ENI | Network interface | Resource/networking | N/A | Resource network connectivity |
| Flow Logs | Network visibility | VPC/subnet/ENI | N/A | Monitoring and troubleshooting |
| Reachability Analyzer | Network path analysis | Network configuration | N/A | Diagnostics |

---

## Production Architecture

A common production architecture combines many of these components:

```mermaid
flowchart TB
    Internet["Internet"]

    IGW["Internet Gateway"]
    NAT1["NAT Gateway A"]
    NAT2["NAT Gateway B"]

    subgraph VPC["Amazon VPC 10.0.0.0/16"]
        subgraph AZ1["Availability Zone A"]
            PUB1["Public Subnet"]
            APP1["Private App Subnet"]
            DB1["Private Data Subnet"]
        end

        subgraph AZ2["Availability Zone B"]
            PUB2["Public Subnet"]
            APP2["Private App Subnet"]
            DB2["Private Data Subnet"]
        end

        EP["VPC Endpoints"]
    end

    Internet --> IGW
    IGW --> PUB1
    IGW --> PUB2

    PUB1 --> NAT1
    PUB2 --> NAT2

    NAT1 --> APP1
    NAT2 --> APP2

    APP1 --> DB1
    APP2 --> DB2

    APP1 --> EP
    APP2 --> EP
```

This architecture separates:

- Public ingress
- Private application workloads
- Private data services
- Outbound internet access
- Private AWS service access
- Availability Zones

The actual implementation should be adapted to workload requirements rather than copied mechanically.

---

## Backend Service Mapping

A typical backend stack might map to VPC components as follows:

| Backend component | Typical VPC placement | Primary network requirement |
|---|---|---|
| Nginx | Public or private depending on architecture | HTTP/HTTPS |
| ALB | Public/private subnet depending on exposure | HTTP/HTTPS |
| Django | Private subnet | Application traffic |
| FastAPI | Private subnet | HTTP/HTTPS or internal protocol |
| gRPC service | Private subnet | HTTP/2 |
| Celery worker | Private subnet | Broker/database access |
| PostgreSQL | Private data subnet | TCP 5432 |
| Redis | Private subnet | TCP 6379 |
| Kafka | Private subnet | Broker/client ports |
| EKS nodes | Private subnet | Kubernetes networking |
| External API | External network | NAT or other controlled egress |

The VPC should implement the network dependencies required by the application architecture rather than exposing every service to every network.

---

## Common Mistakes

### Treating All VPC Components as Independent

VPC components are interconnected.

A connectivity problem usually requires reasoning across multiple components.

### Allowing Broad Network Access

Rules such as:

```text
0.0.0.0/0
```

should be used only when the architecture genuinely requires unrestricted access.

### Using Security Groups as Routing

Security Groups do not determine network paths.

They control whether traffic is allowed after the network path exists.

### Using Route Tables as Security Controls

Routes determine destinations.

They are not a replacement for Security Groups or NACLs.

### Sending All AWS Traffic Through NAT

Private workloads may not need NAT for every AWS service.

Evaluate VPC endpoints where appropriate.

### Building Single-AZ Network Dependencies

A single NAT Gateway, networking appliance, or other critical dependency can become an Availability Zone failure domain.

### Creating Excessive VPC Peering

Large numbers of point-to-point connections become operationally expensive.

Consider Transit Gateway for larger environments.

### Ignoring IP Capacity

Subnet IP exhaustion can prevent new workloads from being created even when CPU and memory capacity are available.

This is particularly important for containerized workloads.

---

## Troubleshooting a VPC Connectivity Failure

When a backend service cannot reach another service, use a deterministic process.

### Identify the Exact Flow

Start with:

```text
Source
Destination
Protocol
Port
Direction
```

For example:

```text
Source:      API instance
Destination: PostgreSQL
Protocol:    TCP
Port:        5432
Direction:   API -> PostgreSQL
```

### Check DNS

```bash
nslookup database.internal.example.com
```

or:

```bash
dig database.internal.example.com
```

Verify that the hostname resolves to the expected address.

### Check Routing

Inspect the relevant route table.

```bash
aws ec2 describe-route-tables \
    --filters Name=vpc-id,Values=vpc-xxxxxxxx
```

Verify that the destination has a valid route.

### Check Security Groups

```bash
aws ec2 describe-security-groups \
    --group-ids sg-xxxxxxxx
```

Verify that the source is allowed to reach the destination on the required port.

### Check Network ACLs

```bash
aws ec2 describe-network-acls \
    --filters Name=vpc-id,Values=vpc-xxxxxxxx
```

Check both directions because NACLs are stateless.

### Check Flow Logs

Determine whether the traffic is being accepted or rejected.

### Check the Destination Service

A network path can be correct while the application itself is unavailable.

For PostgreSQL, for example, verify:

- PostgreSQL is listening
- Port 5432 is correct
- Database is healthy
- Connection limits are not exhausted
- The service is bound to the expected interface

---

## AWS CLI Component Inspection

List VPCs:

```bash
aws ec2 describe-vpcs
```

List subnets:

```bash
aws ec2 describe-subnets
```

List route tables:

```bash
aws ec2 describe-route-tables
```

List Internet Gateways:

```bash
aws ec2 describe-internet-gateways
```

List NAT Gateways:

```bash
aws ec2 describe-nat-gateways
```

List Security Groups:

```bash
aws ec2 describe-security-groups
```

List Network ACLs:

```bash
aws ec2 describe-network-acls
```

List network interfaces:

```bash
aws ec2 describe-network-interfaces
```

List VPC endpoints:

```bash
aws ec2 describe-vpc-endpoints
```

These commands are particularly useful during incident response and infrastructure validation.

---

## Security Considerations

A production VPC should follow least-privilege networking principles.

Prefer:

```text
Load Balancer
      |
      v
Application
      |
      v
Database
```

over:

```text
Internet
      |
      v
Everything
```

Important controls include:

- Private subnets for internal workloads
- Restrictive Security Groups
- Carefully designed NACLs where required
- VPC endpoint policies
- Flow Logs
- Encryption in transit
- Encryption at rest
- IAM controls
- Centralized logging
- Network monitoring
- Controlled outbound access

Network security should complement, not replace, application-level authentication and authorization.

---

## Scalability Considerations

VPC design can become a scaling constraint when network capacity is ignored.

Consider:

- Number of subnets
- Available IP addresses
- Number of network interfaces
- EKS pod IP consumption
- Number of endpoints
- Number of routes
- NAT throughput and cost
- Cross-AZ traffic
- Transit Gateway topology
- Hybrid network bandwidth

For container-heavy environments, IP capacity deserves particular attention.

A cluster may have sufficient compute capacity while failing to schedule workloads because no suitable network addresses remain.

---

## Reliability and Disaster Recovery

Network architecture should support the application's availability requirements.

For critical workloads:

- Use multiple Availability Zones.
- Avoid unnecessary single-AZ dependencies.
- Plan redundant network paths.
- Design NAT architecture appropriately.
- Avoid overlapping CIDRs across connected environments.
- Document route dependencies.
- Monitor network failures.
- Test failure scenarios.

For disaster recovery, consider whether the recovery environment requires:

- A separate VPC
- Separate CIDR ranges
- Cross-Region connectivity
- DNS failover
- Replicated data services
- Independent network infrastructure

A backup application deployed into a network that cannot reach its dependencies is not a viable disaster recovery architecture.

---

## Cost Considerations

Important VPC-related cost drivers include:

- NAT Gateway hourly charges
- NAT Gateway data processing
- Transit Gateway processing
- VPC endpoint charges
- Cross-AZ data transfer
- Cross-Region data transfer
- VPN
- Direct Connect
- Network security appliances

Optimize based on traffic patterns rather than blindly minimizing networking components.

For example, reducing NAT Gateways from two AZs to one may reduce cost but introduce a single-AZ dependency.

The correct design balances:

```text
Cost
+
Availability
+
Security
+
Performance
```

rather than optimizing only one dimension.

---

## Interview Traps

### Is a subnet public because it has a public IP range?

No. Public/private classification primarily depends on routing and internet gateway connectivity.

### Are Security Groups attached to subnets?

No. Security Groups are associated with network interfaces/resources. NACLs operate at the subnet level.

### Are Security Groups stateful?

Yes.

### Are NACLs stateful?

No. NACLs are stateless.

### Does a route table allow traffic?

A route table determines where traffic should go. It does not authorize the traffic.

### Does a NAT Gateway allow inbound internet connections to private instances?

No. It provides outbound connectivity for private resources.

### Can two VPCs with overlapping CIDRs communicate normally through private routing?

Overlapping CIDRs create routing ambiguity and prevent straightforward private connectivity.

### Is VPC peering transitive?

No. VPC peering does not provide automatic transitive routing.

### Why use Transit Gateway?

To simplify centralized connectivity across many VPCs and other networks.

### Why use VPC endpoints?

To provide private connectivity to supported AWS services and potentially reduce dependence on NAT and public paths.

## Key Takeaways

- A VPC is a system of interacting networking components; understanding traffic paths is more important than memorizing individual definitions.
- Route tables determine where packets go, while Security Groups and NACLs determine whether traffic is permitted at different network boundaries.
- Public and private subnet design should be based on routing and workload requirements, with application and data workloads generally kept private.
- Production VPCs must account for Availability Zones, IP capacity, outbound connectivity, inter-VPC networking, observability, security, and cost.
- Senior-level VPC troubleshooting starts with an exact source-to-destination flow and systematically validates DNS, routing, network interfaces, security controls, and the destination service.