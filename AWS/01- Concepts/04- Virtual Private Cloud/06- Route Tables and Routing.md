# 06- Route Tables and Routing

## Overview

Route tables are the control plane for packet forwarding inside an Amazon VPC. They determine where traffic from resources in a subnet should be sent based on the destination IP address.

A VPC can contain multiple route tables, and each subnet is associated with a route table. The route table then determines whether traffic stays inside the VPC, reaches the internet, passes through a NAT Gateway, travels through a VPC peering connection, reaches a Transit Gateway, uses a VPN, or follows another supported network path.

A simplified request path looks like this:

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
    +---- local VPC
    +---- Internet Gateway
    +---- NAT Gateway
    +---- VPC Peering
    +---- Transit Gateway
    +---- VPN / Virtual Private Gateway
    +---- VPC Endpoint
    +---- Network Firewall / Appliance
```

For backend engineers, routing is one of the most important concepts in VPC troubleshooting. A Security Group can allow traffic, but if the route table does not provide a path to the destination, the connection still fails.

---

## What Is a Route Table?

A route table is a collection of routing rules called **routes**.

Each route contains at least:

```text
Destination CIDR
Target
```

For example:

```text
Destination       Target

10.0.0.0/16       local
0.0.0.0/0         igw-xxxxxxxx
```

This means:

- Traffic destined for `10.0.0.0/16` stays within the VPC.
- Other IPv4 destinations match `0.0.0.0/0` and are sent to the Internet Gateway.

A route table does not itself provide connectivity. It specifies the next network target to which matching traffic should be forwarded.

---

## Why Route Tables Exist

Route tables provide traffic-direction control.

Without routing decisions, a VPC would not know whether a packet should:

- Stay inside the VPC
- Reach another VPC
- Reach the internet
- Reach an on-premises network
- Pass through a NAT Gateway
- Reach an AWS service through an endpoint
- Pass through a centralized network appliance

For example:

```text
Django Application
        |
        | Destination: PostgreSQL
        v
Route Table
        |
        | 10.0.20.0/24 -> local
        v
PostgreSQL
```

The route table provides the network path.

Security controls then determine whether the traffic is allowed.

---

## Route Table and Subnet Relationship

A subnet is associated with a route table.

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

Traffic originating from a resource in a subnet uses the route table associated with that subnet.

This is why changing a route table can affect every resource using the associated subnet.

---

## Main Route Table

Every VPC has a main route table.

A subnet that is not explicitly associated with another route table uses the VPC's main route table.

For production infrastructure, explicitly associating subnets with intended route tables is often easier to reason about than relying heavily on the main route table.

A common pattern is:

```text
Public Subnets
    |
    v
Public Route Table

Private Application Subnets
    |
    v
Private Route Table

Private Data Subnets
    |
    v
Data Route Table
```

This makes the intended routing architecture explicit.

---

## Local Route

A VPC route table automatically contains a route representing the VPC's local CIDR.

For:

```text
VPC:
10.0.0.0/16
```

the route table contains:

```text
Destination       Target

10.0.0.0/16       local
```

This allows resources within the VPC to communicate using the VPC's local routing, subject to Security Groups and Network ACLs.

For example:

```text
Application
10.0.10.25
     |
     v
10.0.0.0/16 -> local
     |
     v
Database
10.0.20.30
```

No NAT Gateway or Internet Gateway is required for normal same-VPC private communication.

---

## Default Route

A default route matches destinations that do not match a more specific route.

For IPv4:

```text
0.0.0.0/0
```

For IPv6:

```text
::/0
```

Example:

```text
Destination       Target

10.0.0.0/16       local
0.0.0.0/0         igw-xxxxxxxx
```

A packet destined for:

```text
8.8.8.8
```

does not match:

```text
10.0.0.0/16
```

so it falls back to:

```text
0.0.0.0/0
```

and follows that route.

---

## Route Matching

AWS routing uses the most specific matching route.

Consider:

```text
Destination       Target

10.0.0.0/16       local
10.0.20.0/24      network-appliance
0.0.0.0/0         nat-xxxxxxxx
```

For destination:

```text
10.0.20.50
```

all three routes can technically match.

However:

```text
10.0.20.0/24
```

is more specific than:

```text
10.0.0.0/16
```

and:

```text
0.0.0.0/0
```

Therefore the more specific route is selected.

This is called **longest prefix match**.

---

## Longest Prefix Match

The general rule is:

> The route with the longest matching network prefix is preferred.

For example:

```text
10.0.0.0/8
10.0.0.0/16
10.0.20.0/24
10.0.20.128/25
```

For:

```text
10.0.20.150
```

the most specific matching route is:

```text
10.0.20.128/25
```

Understanding this is essential when debugging complex routing configurations.

---

## Public Subnet Route Table

A typical public subnet route table looks like:

```text
Destination       Target

10.0.0.0/16       local
0.0.0.0/0         igw-xxxxxxxx
```

The traffic flow is:

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

A resource still needs appropriate public addressing and security configuration to communicate directly with the public internet.

---

## Private Application Route Table

A private application subnet may use:

```text
Destination       Target

10.0.0.0/16       local
0.0.0.0/0         nat-xxxxxxxx
```

Traffic to another resource inside the VPC follows:

```text
10.0.20.0/24
```

if that destination is reachable through the local VPC route.

Traffic to an external destination follows:

```text
0.0.0.0/0
```

and goes through the NAT Gateway.

Example:

```text
FastAPI
   |
   v
Private Route Table
   |
   +-- 10.0.0.0/16 -> local
   |
   +-- 0.0.0.0/0 -> NAT Gateway
```

---

## Private Data Route Table

A database subnet may intentionally have no internet default route:

```text
Destination       Target

10.0.0.0/16       local
```

This allows internal VPC communication without creating an internet path.

For example:

```text
Django
   |
   v
10.0.0.0/16 -> local
   |
   v
PostgreSQL
```

This is often preferable for stateful workloads that do not require outbound internet access.

---

## Route Tables and Internet Gateway

An Internet Gateway provides a VPC path to the internet.

A typical public subnet architecture is:

```text
Public Subnet
     |
     v
Route Table
     |
     | 0.0.0.0/0
     v
Internet Gateway
     |
     v
Internet
```

The Internet Gateway must be attached to the VPC.

A route to a nonexistent or unattached target cannot provide working connectivity.

---

## Route Tables and NAT Gateway

A NAT Gateway allows private resources to initiate outbound internet connections without requiring direct public internet routing.

Typical configuration:

```text
Private App Route Table

Destination       Target

10.0.0.0/16       local
0.0.0.0/0         nat-xxxxxxxx
```

Traffic flows:

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

The NAT Gateway itself is normally placed in a public subnet whose route table provides a path to the Internet Gateway.

---

## NAT Gateway Routing Requirements

For a private application to use a NAT Gateway successfully:

```text
Private Subnet
    |
    +-- 0.0.0.0/0 -> NAT Gateway
                         |
                         v
                    Public Subnet
                         |
                         +-- 0.0.0.0/0 -> Internet Gateway
```

If the NAT Gateway is correctly configured but the public subnet does not have a route to the Internet Gateway, outbound connectivity will fail.

Routing must therefore be considered across both subnets.

---

## Availability Zone-Aware NAT Routing

A highly available architecture can place NAT Gateways in multiple Availability Zones.

```text
AZ A
|
+-- Private App A
|      |
|      +--> NAT A
|
+-- Public Subnet A

AZ B
|
+-- Private App B
       |
       +--> NAT B
|
+-- Public Subnet B
```

The corresponding route tables can be:

```text
Private Route Table A
0.0.0.0/0 -> NAT A

Private Route Table B
0.0.0.0/0 -> NAT B
```

This avoids making an application subnet in one AZ dependent on a NAT Gateway in another AZ.

The trade-off is additional NAT Gateway cost.

---

## Route Tables and VPC Peering

VPC peering connects two VPCs privately.

Example:

```text
VPC A
10.0.0.0/16
       |
       | Peering Connection
       |
VPC B
10.1.0.0/16
```

The route table in VPC A needs a route such as:

```text
Destination       Target

10.1.0.0/16       pcx-xxxxxxxx
```

VPC B needs the reverse route:

```text
Destination       Target

10.0.0.0/16       pcx-xxxxxxxx
```

Both sides need appropriate routing.

The Security Groups and NACLs must also permit the traffic.

---

## Route Tables and Transit Gateway

Transit Gateway provides centralized connectivity between VPCs and other networks.

Example:

```text
VPC A
10.0.0.0/16
    |
    v
Transit Gateway
    |
    +---- VPC B
    |
    +---- VPC C
    |
    +---- VPN
    |
    +---- Direct Connect
```

A VPC route table may contain:

```text
Destination       Target

10.0.0.0/16       local
10.1.0.0/16       tgw-xxxxxxxx
10.2.0.0/16       tgw-xxxxxxxx
```

The Transit Gateway also has its own route tables and routing behavior.

This creates multiple routing layers that must be analyzed during troubleshooting.

---

## Route Tables and VPN

A VPN-connected architecture may look like:

```text
AWS VPC
10.0.0.0/16
     |
     v
Virtual Private Gateway / Transit Gateway
     |
     v
VPN
     |
     v
On-Premises
10.100.0.0/16
```

The AWS-side route table may contain:

```text
Destination       Target

10.0.0.0/16       local
10.100.0.0/16     VPN target
```

The on-premises side must also know how to route traffic back to the AWS CIDR.

Routing is bidirectional from an application perspective.

A forward route without a return route results in failed connections.

---

## Route Tables and Direct Connect

Direct Connect can provide private connectivity between AWS and on-premises infrastructure.

The architecture may be:

```text
AWS VPC
   |
   v
Transit Gateway / Virtual Private Gateway
   |
   v
Direct Connect
   |
   v
Corporate Network
```

CIDR allocation becomes particularly important because AWS and on-premises networks should generally use non-overlapping address ranges.

---

## Route Tables and VPC Endpoints

VPC endpoints provide private connectivity to supported AWS services.

The routing behavior depends on the endpoint type.

### Gateway Endpoint

Gateway endpoints are commonly used for services such as Amazon S3 and Amazon DynamoDB.

A route can be associated with a route table for the endpoint.

Conceptually:

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

### Interface Endpoint

Interface endpoints use elastic network interfaces and private IP addresses within selected subnets.

Traffic is generally resolved through private DNS and sent to the endpoint network interfaces.

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
AWS Service
```

---

## Route Tables and Network Appliances

Centralized inspection architectures may send traffic through a firewall or network appliance.

For example:

```text
Application
    |
    v
Route Table
    |
    v
Network Firewall
    |
    v
Destination
```

A route might look conceptually like:

```text
Destination       Target

0.0.0.0/0         Firewall / Appliance
```

This allows organizations to implement centralized traffic inspection.

However, introducing appliances increases routing complexity and creates additional failure and capacity considerations.

---

## Route Tables and Network Segmentation

Route tables can help implement network segmentation.

For example:

```text
Application Subnet
    |
    +-- local VPC
    +-- Database CIDR
    +-- NAT Gateway

Data Subnet
    |
    +-- local VPC
```

The application can reach the database.

The database does not necessarily receive an internet route.

This is more precise than giving every subnet the same route table.

---

## Route Table Design Patterns

### Shared Public Route Table

```text
Public Route Table
|
+-- Public A
+-- Public B
+-- Public C
```

Useful when all public subnets require the same routes.

### Per-AZ Private Route Tables

```text
Private Route A
|
+-- App A
    |
    +-- NAT A

Private Route B
|
+-- App B
    |
    +-- NAT B
```

Useful when each Availability Zone should use local NAT infrastructure.

### Dedicated Data Route Table

```text
Data Route Table
|
+-- Data A
+-- Data B
```

Useful when database subnets require more restrictive routing.

---

## Route Table Design Example

Consider:

```text
VPC
10.0.0.0/16
```

with:

```text
Public A
10.0.1.0/24

Public B
10.0.2.0/24

App A
10.0.11.0/20

App B
10.0.12.0/20

Data A
10.0.21.0/24

Data B
10.0.22.0/24
```

A possible route architecture is:

### Public Route Table

```text
Destination       Target

10.0.0.0/16       local
0.0.0.0/0         Internet Gateway
```

Associated with:

```text
Public A
Public B
```

### Private App Route Table A

```text
Destination       Target

10.0.0.0/16       local
0.0.0.0/0         NAT Gateway A
```

Associated with:

```text
App A
```

### Private App Route Table B

```text
Destination       Target

10.0.0.0/16       local
0.0.0.0/0         NAT Gateway B
```

Associated with:

```text
App B
```

### Data Route Table

```text
Destination       Target

10.0.0.0/16       local
```

Associated with:

```text
Data A
Data B
```

This creates a simple and predictable routing topology.

---

## Route Table Request Lifecycle

Consider:

```text
Django -> PostgreSQL
```

The networking flow is conceptually:

```mermaid
sequenceDiagram
    participant API as Django API
    participant ENI as API ENI
    participant RT as Route Table
    participant DBRT as Data Network
    participant DB as PostgreSQL

    API->>ENI: Send TCP packet
    ENI->>RT: Determine destination route
    RT->>DBRT: Follow local VPC path
    DBRT->>DB: Deliver packet
    DB-->>API: TCP response
```

The important point is that routing occurs before security controls can produce a successful end-to-end connection.

A complete connectivity path also involves:

```text
DNS
+
Routing
+
Security Groups
+
NACLs
+
Application listener
```

---

## Route Tables and Security Groups

Routing and security controls perform different jobs.

### Route Table

Answers:

> Where should this packet go?

### Security Group

Answers:

> Is this traffic allowed for this network interface?

### Network ACL

Answers:

> Is this traffic allowed at the subnet boundary?

A useful troubleshooting model is:

```text
Source
  |
  v
Route?
  |
  +-- No -> Connectivity fails
  |
  +-- Yes
       |
       v
Security Group?
       |
       +-- No -> Connectivity fails
       |
       +-- Yes
            |
            v
NACL?
            |
            +-- No -> Connectivity fails
            |
            +-- Yes
                 |
                 v
Destination application?
```

This prevents the common mistake of treating every networking failure as a Security Group problem.

---

## Stateless vs Stateful Networking Controls

Route tables are not security filters.

They simply determine traffic destinations.

Security Groups are stateful.

NACLs are stateless.

For example:

```text
Client
  |
  | SYN
  v
Server
  |
  | SYN-ACK
  v
Client
```

A route table must provide the path.

The Security Groups must allow the connection.

NACLs must allow both directions where applicable.

---

## Route Table and Return Traffic

One of the most common routing mistakes is considering only the forward direction.

For:

```text
Application -> Database
```

the response must also return:

```text
Database -> Application
```

The destination and routing path for the response must be valid.

This becomes especially important with:

- VPN
- Transit Gateway
- VPC peering
- Network appliances
- Firewalls
- Multi-VPC architectures

A valid forward path does not guarantee a valid return path.

---

## Asymmetric Routing

Asymmetric routing occurs when traffic takes different paths in opposite directions.

Example:

```text
Request:
Application
   |
   v
Firewall A
   |
   v
Database

Response:
Database
   |
   v
Firewall B
   |
   v
Application
```

Some stateful network devices may reject or mishandle such traffic because the return path does not traverse the expected device.

When introducing centralized inspection, routing symmetry should be explicitly evaluated.

---

## Blackhole Routes

A route can become unusable when its target is unavailable or removed.

AWS may identify such routes as blackhole routes.

For example:

```text
10.1.0.0/16 -> Deleted Peering Connection
```

The route remains conceptually present but cannot forward traffic successfully.

Blackhole routes are important during:

- VPC peering removal
- Transit Gateway changes
- VPN changes
- Network appliance replacement
- Infrastructure migrations

They should be removed or corrected when no longer valid.

---

## Route Propagation

Some AWS networking architectures can dynamically propagate routes.

For example, VPN connectivity can involve route propagation through a virtual private gateway.

The benefit is that routes learned through supported connectivity mechanisms can appear without manually creating every route.

However, explicit routing is often easier to reason about in infrastructure-as-code environments.

Always understand whether a route is:

- Static
- Propagated
- Automatically created
- Managed by another AWS networking service

---

## Static vs Dynamic Routing

### Static Routing

Routes are explicitly configured.

Example:

```text
10.100.0.0/16 -> VPN
```

Advantages:

- Predictable
- Easy to audit
- Simple for small networks

Limitations:

- Manual maintenance
- More operational work as networks grow

### Dynamic Routing

Routes can be learned through routing protocols or AWS networking mechanisms.

Advantages:

- Better for complex networks
- Can adapt to topology changes

Limitations:

- More complex
- Requires stronger operational knowledge
- Harder to debug without proper observability

Large enterprise networks often combine static and dynamic routing.

---

## Route Table Security Considerations

Route tables are not normally used as a replacement for application security.

Avoid assuming:

```text
No route = authorization
```

Routing controls reachability, but if a route exists, Security Groups and application authorization still matter.

For sensitive environments:

```text
Routing
+
Security Groups
+
NACLs where appropriate
+
IAM
+
Application authorization
+
Encryption
```

should work together.

---

## Least-Privilege Routing

A useful principle is:

> Provide only the network paths a workload actually requires.

For example, a database subnet may need:

```text
VPC local
```

but not:

```text
0.0.0.0/0 -> Internet Gateway
```

An application subnet may need:

```text
VPC local
0.0.0.0/0 -> NAT Gateway
```

A centralized security architecture may intentionally route selected traffic through an inspection layer.

Avoid adding broad default routes without understanding their purpose.

---

## Route Tables and DNS

Routing and DNS are separate systems.

A service may resolve correctly:

```text
postgres.internal.example.com
        |
        v
10.0.21.25
```

but the application can still fail to connect if there is no route to:

```text
10.0.21.0/24
```

Conversely, a valid route is useless if DNS resolves to the wrong address.

Troubleshooting should therefore separate:

```text
DNS resolution
        |
        v
Destination IP
        |
        v
Route selection
        |
        v
Security controls
        |
        v
Application listener
```

---

## Route Tables and Microservices

Consider:

```text
API Gateway
    |
    v
Order Service
    |
    v
Payment Service
    |
    v
Database
```

In a private microservice architecture, route tables provide the network paths between service networks.

However, not every service needs unrestricted access to every other service.

Combine routing with Security Groups and service-level authorization.

For example:

```text
orders-sg
    |
    +-- payment-sg: allowed

payment-sg
    |
    +-- database-sg: allowed
```

The route table provides reachability while Security Groups narrow the allowed communication.

---

## Route Tables and Kubernetes

EKS networking can make route-table reasoning more complex because there may be:

- Nodes
- Pod IPs
- Load balancers
- VPC CNI networking
- NAT Gateways
- VPC endpoints
- Transit Gateway connectivity

A simplified path is:

```text
Pod
 |
 v
Node / VPC Networking
 |
 v
Subnet Route Table
 |
 +-- local
 +-- NAT
 +-- TGW
 +-- VPC Endpoint
```

IP allocation and routing must be considered together.

A Kubernetes workload may have sufficient CPU and memory but still fail because its subnet cannot provide enough addresses or the required route does not exist.

---

## Route Tables and Docker

Docker networking inside an EC2 instance is different from VPC routing.

The architecture can contain multiple networking layers:

```text
Container
   |
   v
Docker Network
   |
   v
EC2 ENI
   |
   v
VPC Subnet
   |
   v
VPC Route Table
```

A container connectivity issue therefore does not necessarily indicate a VPC route-table problem.

Troubleshooting should identify the layer at which traffic stops.

---

## Route Tables and Nginx

An Nginx reverse proxy may be deployed privately behind a public load balancer:

```text
Internet
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

The route tables determine the network paths.

Nginx then operates at the application protocol layer.

This distinction matters:

```text
VPC Route Table
    -> IP routing

Nginx
    -> HTTP / HTTPS routing
```

They solve different routing problems.

---

## Route Tables and Kafka

Kafka clusters are particularly sensitive to network topology because clients must be able to reach the broker addresses returned in metadata.

A simplified architecture is:

```text
Application
    |
    v
VPC Route Table
    |
    v
Kafka Broker
```

If the application can reach one Kafka endpoint but cannot reach the broker addresses advertised by Kafka, the issue may appear to be a Kafka problem while the underlying cause is network routing or address reachability.

Private DNS, subnet routing, Security Groups, and broker advertised addresses must therefore align.

---

## Route Table Troubleshooting Methodology

When troubleshooting connectivity, follow the actual packet path.

### Identify Source

Determine:

```text
Source resource
Source IP
Source subnet
Source ENI
```

### Identify Destination

Determine:

```text
Destination hostname
Destination IP
Destination subnet
Destination ENI
Destination port
```

### Validate DNS

Check:

```text
Hostname -> IP
```

### Inspect Source Route Table

Find the route matching the destination.

### Inspect Intermediate Targets

If traffic uses:

```text
NAT
TGW
VPN
Peering
Firewall
Endpoint
```

inspect that component.

### Inspect Destination Route

Verify the return path.

### Inspect Security Controls

Check:

```text
Security Groups
NACLs
```

### Verify Application Listener

Finally verify:

```text
IP
Port
Protocol
Process
```

This sequence avoids random configuration changes.

---

## Route Troubleshooting Example

Suppose:

```text
Django:
10.0.11.20

PostgreSQL:
10.0.21.30
```

Django cannot connect to PostgreSQL.

Start with:

```text
Destination:
10.0.21.30
```

Source subnet route table:

```text
10.0.0.0/16 -> local
```

The route exists.

Next inspect:

```text
Django Security Group
PostgreSQL Security Group
Django NACL
PostgreSQL NACL
```

If the database Security Group allows:

```text
TCP 5432
Source: Django Security Group
```

the network path is likely valid and the investigation should move toward:

- Database listener
- PostgreSQL configuration
- DNS
- Credentials
- Connection limits

This demonstrates why routing should be checked separately from security and application configuration.

---

## AWS CLI Inspection

List route tables:

```bash
aws ec2 describe-route-tables
```

Filter route tables for a VPC:

```bash
aws ec2 describe-route-tables \
    --filters Name=vpc-id,Values=vpc-xxxxxxxx
```

Display routes in a readable form:

```bash
aws ec2 describe-route-tables \
    --filters Name=vpc-id,Values=vpc-xxxxxxxx \
    --query 'RouteTables[].Routes[].{Destination:DestinationCidrBlock,IPv6:DestinationIpv6CidrBlock,Target:GatewayId,NAT:NatGatewayId,TGW:TransitGatewayId,Peering:VpcPeeringConnectionId}'
```

Inspect a specific route table:

```bash
aws ec2 describe-route-tables \
    --route-table-ids rtb-xxxxxxxx
```

Find subnet associations:

```bash
aws ec2 describe-route-tables \
    --route-table-ids rtb-xxxxxxxx \
    --query 'RouteTables[].Associations[]'
```

Inspect routes to a specific destination:

```bash
aws ec2 describe-route-tables \
    --route-table-ids rtb-xxxxxxxx \
    --query 'RouteTables[].Routes[]'
```

These commands are useful during deployment validation and incident investigation.

---

## Creating a Route With AWS CLI

Create a route to an Internet Gateway:

```bash
aws ec2 create-route \
    --route-table-id rtb-xxxxxxxx \
    --destination-cidr-block 0.0.0.0/0 \
    --gateway-id igw-xxxxxxxx
```

Create a route through a NAT Gateway:

```bash
aws ec2 create-route \
    --route-table-id rtb-xxxxxxxx \
    --destination-cidr-block 0.0.0.0/0 \
    --nat-gateway-id nat-xxxxxxxx
```

Create a route through VPC peering:

```bash
aws ec2 create-route \
    --route-table-id rtb-xxxxxxxx \
    --destination-cidr-block 10.1.0.0/16 \
    --vpc-peering-connection-id pcx-xxxxxxxx
```

Create a Transit Gateway route:

```bash
aws ec2 create-route \
    --route-table-id rtb-xxxxxxxx \
    --destination-cidr-block 10.2.0.0/16 \
    --transit-gateway-id tgw-xxxxxxxx
```

In production, these changes are generally better managed through Infrastructure as Code and reviewed through CI/CD.

---

## Infrastructure as Code

Terraform can define route tables explicitly.

Example:

```hcl
resource "aws_route_table" "private_app_a" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.az_a.id
  }

  tags = {
    Name = "private-app-a"
  }
}

resource "aws_route_table_association" "private_app_a" {
  subnet_id      = aws_subnet.private_app_a.id
  route_table_id = aws_route_table.private_app_a.id
}
```

This approach provides:

- Version control
- Reviewable changes
- Repeatability
- Environment consistency
- Easier disaster recovery
- Auditable network changes

Avoid manually changing production routes when the infrastructure is managed through IaC unless the change is part of a controlled incident procedure.

---

## Route Table Change Management

Routing changes can affect many workloads simultaneously.

Before changing a route table, identify:

```text
Route table
    |
    +-- Associated subnets
          |
          +-- Resources
          +-- Applications
          +-- Dependencies
```

A single route change can therefore affect:

- APIs
- Workers
- Databases
- Kubernetes
- External integrations
- Monitoring
- Deployment systems

Production route changes should be reviewed with the same discipline as application code changes.

---

## Monitoring and Observability

Routing failures should be observable.

Useful tools and signals include:

- VPC Flow Logs
- Reachability Analyzer
- CloudWatch metrics for related network services
- Transit Gateway route inspection
- NAT Gateway metrics
- VPN state and route information
- Load balancer health
- Application connection errors

VPC Flow Logs can help answer:

```text
Was traffic accepted or rejected?
Which source IP generated it?
Which destination IP was targeted?
Which port was used?
```

Flow Logs do not replace route inspection, but they provide valuable evidence.

---

## AWS Reachability Analyzer

AWS Reachability Analyzer can help analyze whether a network path exists between supported AWS resources.

Conceptually:

```text
Source
  |
  v
Route
  |
  v
Network Interface
  |
  v
Security Group
  |
  v
NACL
  |
  v
Destination
```

It is useful when manually tracing a complex path becomes difficult.

A production troubleshooting workflow can combine:

```text
Reachability Analyzer
+
Route Table Inspection
+
VPC Flow Logs
+
Security Group Inspection
```

---

## Cost Considerations

Route tables themselves generally do not represent a major direct cost.

The targets selected by routes can create costs.

Examples:

```text
Route
  |
  +-- NAT Gateway
  +-- Transit Gateway
  +-- Network Firewall
  +-- Cross-AZ path
```

Important considerations include:

- NAT Gateway processing
- Transit Gateway processing
- Cross-AZ data transfer
- Network Firewall processing
- Network appliance costs

Routing should therefore be designed for both correctness and traffic efficiency.

---

## Reliability Considerations

A route table should not create unnecessary single points of failure.

Examples:

```text
AZ A Application
    |
    v
NAT A

AZ B Application
    |
    v
NAT B
```

is generally more AZ-isolated than:

```text
AZ A Application
    |
    v
NAT A

AZ B Application
    |
    v
NAT A
```

Similarly, centralized network appliances should be deployed with sufficient redundancy when they sit on critical traffic paths.

A route is only as reliable as the target behind it.

---

## Disaster Recovery Considerations

DR environments need complete routing architecture, not just replicated compute.

For example:

```text
Primary Region
|
+-- VPC
|   +-- Public Routes
|   +-- Private Routes
|   +-- Data Routes
|
+-- External Connectivity

DR Region
|
+-- VPC
    +-- Public Routes
    +-- Private Routes
    +-- Data Routes
    +-- External Connectivity
```

Validate:

- CIDRs
- Route tables
- NAT architecture
- Transit Gateway routes
- VPN connectivity
- VPC endpoints
- Security Groups
- DNS
- Return paths

A DR workload that cannot reach its dependencies is not a complete recovery solution.

---

## Common Mistakes

### Assuming a Security Group Can Create a Route

It cannot.

A Security Group can allow traffic, but the route table must provide a path.

### Adding `0.0.0.0/0` Everywhere

A default route to an Internet Gateway or NAT Gateway should exist only where required.

### Forgetting the Return Route

A request path can exist while the response path does not.

### Using the Wrong Route Table

A subnet may be associated with a different route table than expected.

### Ignoring the Main Route Table

A subnet without an explicit association uses the main route table.

### Routing Through a Deleted Resource

This can create blackhole routes.

### Ignoring Longest Prefix Match

A more specific route can override a broader route.

### Assuming Same VPC Means Every Connection Works

Same-VPC traffic still depends on:

- Security Groups
- NACLs
- Correct destination
- Application listeners

### Sending All Traffic Through a Centralized Appliance

This can introduce:

- Bottlenecks
- Cross-AZ traffic
- Additional latency
- Single points of failure

### Manually Modifying IaC-Managed Routes

Manual changes create configuration drift and can be overwritten by later deployments.

---

## Senior-Level Routing Design

At an intermediate level, routing means understanding:

```text
Destination -> Target
```

At a senior level, routing means understanding the complete network graph.

For example:

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
Load Balancer
   |
   v
Private Application
   |
   +----> Local VPC Route ----> PostgreSQL
   |
   +----> NAT Gateway -------> Internet
   |
   +----> VPC Endpoint ------> AWS Service
   |
   +----> Transit Gateway ---> Other VPC
   |
   +----> VPN ---------------> On-Premises
```

A senior engineer should be able to determine:

- Which route table is used
- Which route matches
- Why that route wins
- Which target receives the packet
- Whether the target is reachable
- Whether the response can return
- Whether Security Groups allow the traffic
- Whether NACLs allow the traffic
- Whether the architecture introduces cross-AZ traffic
- Whether the design remains available during failures

---

## Interview Traps

### What is a route table?

A collection of routes that determines where traffic from associated subnets is directed.

### What is the local route?

The automatically available route representing the VPC's own CIDR, enabling internal VPC routing.

### What does `0.0.0.0/0` represent?

The default IPv4 route, matching destinations that do not match a more specific route.

### What is longest prefix match?

The routing rule where the most specific matching CIDR is preferred.

### Does every subnet have its own route table?

No. Multiple subnets can share a route table.

### What makes a subnet public?

Typically, its route table has a route to an Internet Gateway.

### Can a private subnet communicate with the internet?

Yes, commonly through a NAT Gateway for outbound traffic.

### Does a NAT Gateway belong in a private subnet?

No. A NAT Gateway used for internet egress is normally deployed in a public subnet.

### Can resources in the same VPC communicate without a route?

The VPC's local route provides the normal same-VPC path, but Security Groups and NACLs can still prevent the communication.

### Why can a route exist but traffic still fail?

The route target may be unavailable, the return route may be missing, Security Groups or NACLs may block traffic, DNS may resolve incorrectly, or the destination application may not be listening.

### Why are route tables important in VPC peering?

Each side needs appropriate routes for the remote CIDR, and the CIDRs should generally not overlap.

### What happens if a route target is deleted?

The route can become a blackhole route and traffic using it cannot reach the intended destination.

## Key Takeaways

- Route tables determine where VPC traffic goes by matching destination CIDRs to network targets such as local routing, Internet Gateways, NAT Gateways, Transit Gateways, VPNs, peering connections, and endpoints.
- AWS uses longest-prefix matching, so the most specific matching route takes precedence over broader routes.
- Successful connectivity requires more than a route: the complete path must also satisfy Security Groups, NACLs, DNS, return routing, and destination application requirements.
- Production routing should be explicit, AZ-aware, observable, version-controlled, and designed around failure behavior, traffic cost, and future connectivity requirements.
- Troubleshooting should trace the actual packet path from source to destination and back rather than treating every network failure as a Security Group problem.