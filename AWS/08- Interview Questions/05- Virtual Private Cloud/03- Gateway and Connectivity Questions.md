# 03- Gateway and Connectivity Questions

## Overview

VPC gateway and connectivity questions test whether an engineer understands how traffic moves between a VPC, the Internet, AWS services, other VPCs, on-premises networks, and external systems.

A strong interview answer should distinguish between:

- **Routing** — where traffic should go.
- **Gateway connectivity** — which network boundary or AWS service provides the path.
- **Security** — whether the traffic is permitted.
- **Name resolution** — how a destination is translated to an address.
- **Application behavior** — whether the destination service actually accepts the connection.

The most important connectivity components are:

| Component | Primary Purpose |
|---|---|
| Internet Gateway | Internet connectivity for VPC resources |
| NAT Gateway | Outbound Internet access for private resources |
| Egress-only Internet Gateway | Outbound IPv6 Internet connectivity |
| VPC Gateway Endpoint | Private connectivity to supported AWS services |
| VPC Interface Endpoint | Private connectivity to AWS services through ENIs |
| Transit Gateway | Centralized connectivity between VPCs and networks |
| VPC Peering | Private point-to-point VPC connectivity |
| Site-to-Site VPN | Encrypted connectivity between AWS and external networks |
| Direct Connect | Dedicated private connectivity to AWS |
| Route Table | Determines the next hop for network traffic |

A useful mental model is:

```text
Application
    |
    v
Destination IP
    |
    v
Route Table
    |
    v
Gateway / Endpoint / Peering / TGW / VPN
    |
    v
Destination Network Interface
    |
    v
Security Controls
    |
    v
Application Service
```

A connectivity mechanism does not automatically grant authorization.

## Internet Gateway

### Question: What is an Internet Gateway?

**Answer:**

An Internet Gateway, or IGW, is a VPC component that provides connectivity between a VPC and the Internet.

For IPv4, Internet connectivity generally requires:

- An Internet Gateway attached to the VPC.
- A route toward the Internet Gateway.
- Appropriate public addressing.
- Security Group and NACL permissions.

A simplified architecture is:

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
EC2 / ALB
```

The route table might contain:

```text
0.0.0.0/0 → Internet Gateway
```

The presence of an Internet Gateway alone does not make every resource publicly reachable.

---

### Question: What makes a subnet public?

**Answer:**

A subnet is generally considered public when its route table has a route to an Internet Gateway.

For example:

```text
0.0.0.0/0 → igw-xxxxxxxx
```

However, a resource inside that subnet still needs appropriate addressing and security configuration to communicate with the Internet.

A public subnet therefore does not mean:

```text
Every resource is publicly accessible.
```

It means:

```text
The subnet has a route toward the Internet Gateway.
```

---

### Question: What is required for an EC2 instance to communicate directly with the Internet?

**Answer:**

For a typical IPv4 architecture, verify:

1. The VPC has an Internet Gateway attached.
2. The instance's subnet route table has a default route to the IGW.
3. The instance has a public IPv4 address or appropriate public addressing.
4. Security Groups permit the traffic.
5. NACLs permit the traffic.
6. The operating system and application allow the traffic.

The path is approximately:

```text
EC2
 |
 | Public IPv4
 v
Internet Gateway
 |
 v
Internet
```

A missing route, public address, or security rule can break connectivity.

---

## NAT Gateway

### Question: Why is a NAT Gateway used?

**Answer:**

A NAT Gateway allows resources in private subnets to initiate outbound IPv4 connections to destinations outside the VPC without assigning public IPv4 addresses to those resources.

Typical architecture:

```text
Private Application
        |
        | 0.0.0.0/0
        v
   NAT Gateway
        |
        v
Internet Gateway
        |
        v
     Internet
```

The private subnet route table might contain:

```text
0.0.0.0/0 → nat-xxxxxxxx
```

The NAT Gateway itself resides in a public subnet whose route table contains:

```text
0.0.0.0/0 → igw-xxxxxxxx
```

---

### Question: Why must a NAT Gateway be placed in a public subnet?

**Answer:**

The NAT Gateway requires a path to the Internet through an Internet Gateway.

A common architecture is:

```text
Private Subnet
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

The NAT Gateway's subnet needs a route toward the IGW.

Putting the NAT Gateway in a private subnet would prevent it from providing the intended Internet egress path.

---

### Question: Does a NAT Gateway allow inbound Internet connections to private instances?

**Answer:**

No.

A NAT Gateway is designed primarily for connections initiated by private resources.

For example:

```text
Private API
    |
    | HTTPS request
    v
NAT Gateway
    |
    v
External API
```

The external system cannot normally initiate an arbitrary inbound connection through the NAT Gateway to the private instance.

This is one reason NAT Gateway is useful for private application workloads.

---

### Question: Why should NAT Gateways usually be deployed per Availability Zone?

**Answer:**

For high availability and reduced dependency on cross-AZ networking, production architectures commonly deploy a NAT Gateway in each Availability Zone.

For example:

```text
              Internet Gateway
                     |
          +----------+----------+
          |                     |
        AZ-A                  AZ-B
          |                     |
     NAT Gateway            NAT Gateway
          |                     |
     Private App           Private App
```

Each private subnet uses the NAT Gateway in its own Availability Zone.

This reduces the impact of an AZ-level failure and can avoid unnecessary cross-AZ data transfer.

---

## Egress-Only Internet Gateway

### Question: What is an egress-only Internet Gateway?

**Answer:**

An egress-only Internet Gateway provides outbound Internet connectivity for IPv6 traffic from a VPC.

It is conceptually similar to NAT for outbound-only behavior, but it is specifically designed for IPv6.

For example:

```text
Private IPv6 Workload
        |
        v
Egress-only Internet Gateway
        |
        v
Internet
```

It does not provide general unsolicited inbound Internet connectivity to the IPv6 resources behind it.

---

### Question: What is the difference between NAT Gateway and Egress-Only Internet Gateway?

**Answer:**

| Feature | NAT Gateway | Egress-Only IGW |
|---|---|---|
| Primary protocol | IPv4 | IPv6 |
| Purpose | Outbound Internet access | Outbound IPv6 Internet access |
| Translation | Performs NAT | No NAT |
| Public IPv4 required on private workload | No | Not applicable |
| Inbound initiation | Not supported as general inbound path | Prevented for unsolicited inbound traffic |

The key distinction is IPv4 NAT versus IPv6 egress-only connectivity.

---

## Route Tables

### Question: What is the role of a route table in VPC connectivity?

**Answer:**

A route table determines where packets destined for specific networks should be sent.

For example:

```text
10.20.0.0/16 → local
0.0.0.0/0    → igw-xxxxxxxx
```

The `local` route enables communication within the VPC CIDR.

The default route sends unmatched IPv4 destinations toward the Internet Gateway.

Routing answers:

```text
"Where should this packet go next?"
```

It does not answer:

```text
"Is this packet authorized?"
```

---

### Question: How does AWS select a route?

**Answer:**

AWS uses the most specific matching route.

For example:

```text
10.0.0.0/8     → Target A
10.20.0.0/16   → Target B
10.20.5.0/24   → Target C
0.0.0.0/0      → Target D
```

Traffic destined for:

```text
10.20.5.25
```

matches multiple routes, but the `/24` route is the most specific and therefore takes precedence.

This principle is critical when troubleshooting overlapping or unexpected routes.

---

### Question: What is the local route in a VPC route table?

**Answer:**

The local route represents connectivity within the VPC's CIDR range.

For example:

```text
10.0.0.0/16 → local
```

This allows resources within the VPC to communicate according to their addressing and security configuration.

The local route cannot simply be treated as unrestricted communication because Security Groups and NACLs still apply.

---

## VPC Peering

### Question: What is VPC Peering?

**Answer:**

VPC Peering creates private network connectivity between two VPCs.

For example:

```text
VPC A
10.0.0.0/16
     |
     | VPC Peering
     |
VPC B
10.1.0.0/16
```

The VPC route tables must contain appropriate routes.

For example:

```text
VPC A:
10.1.0.0/16 → pcx-xxxxxxxx

VPC B:
10.0.0.0/16 → pcx-xxxxxxxx
```

Security controls must also permit the desired traffic.

---

### Question: What is a major limitation of VPC Peering?

**Answer:**

VPC Peering is a point-to-point connectivity model.

If an organization has many VPCs, managing a large number of peering relationships can become difficult.

For example:

```text
A ----- B
| \     |
|  \    |
|   \   |
C ----- D
```

As the number of VPCs grows, route and connection management becomes more complex.

Transit Gateway is often more appropriate for larger network topologies.

---

### Question: Can VPC Peering be transitive?

**Answer:**

No.

If:

```text
VPC A ↔ VPC B
VPC B ↔ VPC C
```

that does not automatically create:

```text
VPC A ↔ VPC C
```

Traffic cannot simply use VPC B as a router for VPC A to reach VPC C through standard VPC Peering.

This is a common interview trap.

---

## Transit Gateway

### Question: What is AWS Transit Gateway?

**Answer:**

Transit Gateway is a centralized network transit service that can connect multiple VPCs and external networks.

A simplified architecture is:

```text
                 Transit Gateway
                /       |       \
               /        |        \
            VPC-A     VPC-B     VPC-C
```

It can simplify large-scale network connectivity compared with maintaining many individual VPC peerings.

---

### Question: Why use Transit Gateway instead of VPC Peering?

**Answer:**

Transit Gateway is useful when the network contains many VPCs or external networks.

For example:

```text
                Transit Gateway
                /      |       \
               /       |        \
          Production   Dev     Shared
             VPC       VPC      VPC
```

Benefits include:

- Centralized routing.
- Easier multi-VPC connectivity.
- Connectivity to supported external networks.
- Better scalability for hub-and-spoke architectures.
- Route-table-based network segmentation.

However, centralized networking also creates operational dependencies and requires careful route-table design.

---

### Question: Does Transit Gateway automatically allow communication between attached VPCs?

**Answer:**

No.

Transit Gateway attachment and routing are separate concepts.

A working path requires appropriate routes on the VPC side and Transit Gateway side.

Conceptually:

```text
VPC A
 |
 | VPC route
 v
Transit Gateway
 |
 | TGW route table
 v
VPC B
 |
 v
Destination
```

Security Groups and NACLs must also allow the traffic.

---

## VPC Endpoints

### Question: What problem do VPC endpoints solve?

**Answer:**

VPC endpoints provide private connectivity from VPC workloads to supported AWS services without requiring the workload to traverse a public Internet path.

This is particularly useful for private application environments.

Instead of:

```text
Private EC2
   |
   v
NAT Gateway
   |
   v
Internet
   |
   v
AWS Service
```

a workload can use:

```text
Private EC2
   |
   v
VPC Endpoint
   |
   v
AWS Service
```

This can improve security architecture and reduce dependence on NAT infrastructure.

---

### Question: What are the main types of VPC endpoints?

**Answer:**

The two major endpoint models commonly encountered are:

| Type | Implementation |
|---|---|
| Gateway Endpoint | Route-table based |
| Interface Endpoint | Elastic Network Interfaces |

Gateway endpoints are commonly used for services such as Amazon S3 and DynamoDB.

Interface endpoints use private IP addresses provided through ENIs and are powered by AWS PrivateLink.

---

### Question: What is a Gateway Endpoint?

**Answer:**

A Gateway Endpoint provides private connectivity from a VPC to supported AWS services using route tables.

For example:

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

The route table directs relevant traffic to the endpoint.

This can allow private workloads to access supported AWS services without requiring NAT Gateway-based Internet egress.

---

### Question: What is an Interface Endpoint?

**Answer:**

An Interface Endpoint creates Elastic Network Interfaces in selected subnets.

Applications connect to those private IP addresses.

Conceptually:

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
AWS Service
```

Security Groups can be associated with the endpoint network interfaces.

Interface endpoints are commonly used with AWS services and applications exposed through AWS PrivateLink.

---

### Question: Why can VPC endpoint DNS configuration cause connectivity failures?

**Answer:**

Applications may resolve an AWS service hostname to public addresses when the intended architecture requires private endpoint addresses.

For interface endpoints, private DNS integration can cause the standard AWS service hostname to resolve to the endpoint's private IP addresses from within the VPC.

If DNS behavior is incorrect, the application may use an unintended path.

Troubleshoot:

- VPC DNS support.
- VPC DNS hostnames.
- Endpoint configuration.
- Private DNS configuration.
- Route tables.
- Endpoint Security Groups.
- IAM permissions.

---

## AWS PrivateLink

### Question: What is AWS PrivateLink?

**Answer:**

AWS PrivateLink provides private connectivity to supported services through interface endpoints.

It allows consumers to access services without requiring direct network connectivity to the provider's VPC.

A simplified architecture is:

```text
Consumer VPC
     |
     v
Interface Endpoint
     |
     v
PrivateLink
     |
     v
Provider Service
```

This is particularly useful for exposing services to other VPCs or AWS accounts without establishing full network-level connectivity between the networks.

---

### Question: How is PrivateLink different from VPC Peering?

**Answer:**

VPC Peering provides network connectivity between VPCs.

PrivateLink provides private access to a specific service.

| Feature | VPC Peering | PrivateLink |
|---|---|---|
| Connectivity model | VPC-to-VPC | Service-to-consumer |
| Scope | Broad network connectivity | Specific service |
| Consumer access | Network-level | Service-level |
| CIDR overlap | Can create design constraints | More flexible |
| Typical use | Internal network connectivity | Service publishing |

PrivateLink is often preferable when you want to expose a service without exposing an entire network.

---

## VPN Connectivity

### Question: What is AWS Site-to-Site VPN?

**Answer:**

Site-to-Site VPN creates encrypted connectivity between an external network and an AWS VPC.

For example:

```text
Corporate Network
      |
      | Encrypted VPN
      v
Virtual Private Gateway / Transit Gateway
      |
      v
AWS VPC
```

The external network commonly uses a customer gateway configuration, while AWS provides the corresponding VPN endpoint.

---

### Question: When would you use Site-to-Site VPN?

**Answer:**

VPN is appropriate when an organization needs encrypted network connectivity between AWS and an external network.

Typical use cases include:

- Hybrid applications.
- Corporate data centers.
- Legacy systems.
- Private database access.
- Gradual cloud migrations.
- Backup connectivity.

VPN generally provides faster deployment than dedicated physical connectivity but has different performance characteristics than Direct Connect.

---

### Question: What is the difference between VPN and Direct Connect?

**Answer:**

| Feature | Site-to-Site VPN | Direct Connect |
|---|---|---|
| Transport | Internet-based encrypted tunnel | Dedicated connectivity |
| Encryption | Built into VPN | Requires additional encryption when needed |
| Deployment | Usually faster | More infrastructure/provider coordination |
| Latency | Internet-dependent | More predictable |
| Typical use | Hybrid connectivity, backup | High-volume or predictable private connectivity |

A production architecture may use both.

```text
Corporate Network
       |
       +------ Direct Connect ------> AWS
       |
       +------ VPN -----------------> AWS
```

The VPN connection can provide backup connectivity depending on the architecture.

---

## Direct Connect

### Question: What is AWS Direct Connect?

**Answer:**

AWS Direct Connect provides dedicated network connectivity between an external network and AWS.

It can provide more predictable network characteristics than Internet-based VPN connectivity.

Typical architecture:

```text
Corporate Data Center
        |
        v
Direct Connect
        |
        v
AWS Connectivity
        |
        v
Transit Gateway / VPC
```

Direct Connect is generally used when organizations have significant network, performance, compliance, or hybrid-cloud requirements.

---

## Connectivity Decision Matrix

### Question: How would you choose between VPC Peering, Transit Gateway, PrivateLink, VPN, and Direct Connect?

**Answer:**

| Requirement | Recommended Mechanism |
|---|---|
| Two VPCs need private network connectivity | VPC Peering |
| Many VPCs need centralized connectivity | Transit Gateway |
| Expose one service privately | PrivateLink |
| Connect AWS to a corporate network over Internet | Site-to-Site VPN |
| Dedicated hybrid connectivity | Direct Connect |
| Private access to supported AWS services | VPC Endpoint |

The architectural question should be:

```text
Do I need network connectivity
or
do I need service connectivity?
```

That distinction often determines the correct solution.

---

## Connectivity Request Lifecycle

Consider an API in a private subnet calling an external HTTPS service.

```mermaid
sequenceDiagram
    participant API as Private API
    participant RT as Route Table
    participant NAT as NAT Gateway
    participant IGW as Internet Gateway
    participant EXT as External API

    API->>RT: Send HTTPS request
    RT->>NAT: Match 0.0.0.0/0
    NAT->>IGW: Translate and forward
    IGW->>EXT: Internet request
    EXT-->>IGW: Response
    IGW-->>NAT: Response
    NAT-->>API: Return traffic
```

At each stage, different failure modes are possible.

| Stage | Typical Failure |
|---|---|
| DNS | Hostname does not resolve |
| Route table | No matching route |
| NAT | NAT unavailable or incorrectly routed |
| IGW | Incorrect public path |
| Security Group | Traffic blocked |
| NACL | Stateless filtering blocks flow |
| External service | Destination rejects or times out |
| Application | TLS, authentication, or protocol failure |

---

## Gateway and Connectivity Troubleshooting

### Question: A private EC2 instance cannot access the Internet. What do you check?

**Answer:**

Check the complete path:

```text
EC2
 ↓
Private Subnet Route Table
 ↓
NAT Gateway
 ↓
NAT Subnet Route Table
 ↓
Internet Gateway
 ↓
Internet
```

Verify:

1. The private subnet has a default route to the NAT Gateway.
2. The NAT Gateway is available.
3. The NAT Gateway is in a public subnet.
4. The NAT subnet has a default route to the Internet Gateway.
5. The NAT Gateway has appropriate public connectivity.
6. Security Groups permit outbound traffic.
7. NACLs allow the outbound and return traffic.
8. DNS resolution works.
9. The external destination is reachable.

---

### Question: A public EC2 instance cannot access the Internet. What should you check?

**Answer:**

Verify:

```text
EC2
 ↓
Public Subnet Route Table
 ↓
Internet Gateway
 ↓
Internet
```

Then check:

- Public IPv4 address.
- Internet Gateway attachment.
- Default route.
- Security Groups.
- NACLs.
- OS firewall.
- DNS configuration.

A common mistake is assuming that placing an instance in a public subnet automatically gives it Internet connectivity.

---

### Question: An application can reach one VPC but not another. What do you check?

**Answer:**

For cross-VPC connectivity:

```text
Source VPC
   |
   v
Source Route Table
   |
   v
Peering / Transit Gateway
   |
   v
Destination Route Table
   |
   v
Destination ENI
   |
   v
Security Group
```

Check:

1. CIDRs.
2. Connectivity attachment.
3. Source route.
4. Destination route.
5. Transit Gateway route table if applicable.
6. Security Groups.
7. NACLs.
8. DNS if hostnames are involved.

---

## Common Route Table Mistakes

### Mistake: Creating a NAT Gateway but forgetting the private route

Creating:

```text
NAT Gateway
```

does not automatically update every private subnet.

The private subnet still needs:

```text
0.0.0.0/0 → NAT Gateway
```

Without this route, outbound Internet traffic has no path through the NAT Gateway.

---

### Mistake: Routing private traffic through the Internet unnecessarily

If a service can be accessed privately through:

- VPC endpoint.
- Transit Gateway.
- VPC Peering.
- PrivateLink.

prefer the appropriate private path instead of unnecessarily sending traffic through public Internet infrastructure.

This can improve:

- Security.
- Architecture clarity.
- Reliability.
- Cost efficiency.

---

### Mistake: Forgetting the return route

Connectivity is bidirectional for most request/response protocols.

A source-side route alone is insufficient if the destination network does not know how to return traffic.

For example:

```text
VPC A
10.0.0.0/16
   |
   v
Transit Gateway
   |
   v
VPC B
10.1.0.0/16
```

Both networks need appropriate routes for the required traffic.

---

## High Availability

### Question: How would you design highly available VPC connectivity?

**Answer:**

Distribute critical connectivity components across Availability Zones where supported.

A common architecture is:

```text
                    Internet
                       |
                Internet Gateway
                       |
          +------------+------------+
          |                         |
         AZ-A                      AZ-B
          |                         |
       Public                   Public
       Subnet                   Subnet
          |                         |
       NAT-A                     NAT-B
          |                         |
       Private                  Private
       App-A                    App-B
```

For production systems:

- Avoid a single NAT Gateway for all AZs when AZ-level resilience is important.
- Use multiple Availability Zones.
- Distribute application workloads.
- Use redundant VPN connectivity where appropriate.
- Design Transit Gateway and Direct Connect architectures for failure scenarios.
- Test failover rather than relying solely on diagrams.

---

## Security Considerations

Connectivity mechanisms should always be combined with least-privilege security controls.

### Internet Gateway

Restrict publicly reachable workloads through:

- Security Groups.
- NACLs where appropriate.
- Load balancers.
- Application authentication.
- TLS.

### NAT Gateway

Treat NAT as an egress path, not a security boundary.

Consider:

- Egress filtering.
- Network Firewall where required.
- DNS controls.
- Application allowlists.
- VPC endpoints for supported AWS services.

### Transit Gateway

Use separate route tables and controlled attachments when isolation is required.

### VPC Peering

Do not assume peering implies unrestricted access.

Restrict:

- Routes.
- Security Groups.
- NACLs.

### PrivateLink

Restrict consumers using:

- Endpoint policies where applicable.
- Security Groups.
- IAM.
- Service-side authorization.

---

## Cost Considerations

Connectivity architecture has operational cost implications.

| Component | Typical Cost Consideration |
|---|---|
| NAT Gateway | Hourly + data processing |
| Transit Gateway | Attachment and data processing |
| VPC Peering | Data transfer considerations |
| Interface Endpoint | Hourly per endpoint/AZ + data processing |
| VPN | Connection/hour and data transfer |
| Direct Connect | Port/provider/network costs |
| Internet Gateway | No separate hourly gateway charge, but associated data transfer can apply |

A common optimization is evaluating whether high-volume private AWS service traffic should use an appropriate VPC endpoint instead of traversing NAT.

Do not optimize solely for hourly infrastructure cost. Consider:

- Availability.
- Operational complexity.
- Data transfer.
- Security.
- Failure domains.

---

## Interview Scenarios

### Scenario: Private applications need access to S3 but the organization wants to eliminate NAT dependency. What would you propose?

**Answer:**

Evaluate an S3 Gateway Endpoint.

Architecture:

```text
Private Application
       |
       v
Route Table
       |
       v
S3 Gateway Endpoint
       |
       v
S3
```

Then verify:

- Route table association.
- Endpoint policy.
- IAM permissions.
- S3 bucket policy.
- DNS behavior where relevant.

This avoids requiring the application to reach S3 through a NAT Gateway.

---

### Scenario: Ten VPCs need to communicate with each other. Would you create 45 peering connections?

**Answer:**

No.

A large mesh of VPC peering relationships becomes difficult to manage.

I would evaluate Transit Gateway:

```text
VPC-A \
VPC-B  \
VPC-C   → Transit Gateway
VPC-D  /
VPC-E /
```

The exact architecture depends on traffic isolation, routing requirements, account structure, and operational constraints.

---

### Scenario: A company wants to expose one internal API to another AWS account without exposing the entire VPC. What would you use?

**Answer:**

Evaluate AWS PrivateLink.

The architecture becomes:

```text
Consumer VPC
     |
     v
Interface Endpoint
     |
     v
PrivateLink
     |
     v
Provider API
```

This exposes the service rather than requiring broad network-level connectivity between the VPCs.

---

### Scenario: A VPC has an Internet Gateway but private EC2 instances cannot reach the Internet. Why?

**Answer:**

An Internet Gateway does not automatically provide outbound Internet access to private subnets.

A typical private subnet needs:

```text
Private Route Table
0.0.0.0/0 → NAT Gateway
```

and the NAT Gateway's public subnet needs:

```text
Public Route Table
0.0.0.0/0 → Internet Gateway
```

---

## Interview Traps

### Trap: "A NAT Gateway is a firewall."

**Correct answer:**

A NAT Gateway provides address translation and outbound connectivity. It should not be treated as the primary application firewall.

---

### Trap: "VPC Peering is transitive."

**Correct answer:**

VPC Peering is not transitive.

---

### Trap: "Transit Gateway automatically routes traffic between every VPC."

**Correct answer:**

Transit Gateway connectivity depends on attachment configuration, Transit Gateway route tables, VPC route tables, and security controls.

---

### Trap: "A VPC endpoint is always an interface endpoint."

**Correct answer:**

VPC endpoints include different models, notably Gateway Endpoints and Interface Endpoints.

---

### Trap: "PrivateLink connects entire VPCs."

**Correct answer:**

PrivateLink is primarily service-oriented. It allows consumers to privately access published services without requiring broad VPC-to-VPC connectivity.

---

### Trap: "A public subnet makes every resource public."

**Correct answer:**

A public subnet has a route to an Internet Gateway. Individual resources still require appropriate addressing and security configuration.

---

## Diagnostic CLI Commands

### Inspect Internet Gateways

```bash
aws ec2 describe-internet-gateways \
  --query 'InternetGateways[*].[InternetGatewayId,Attachments[*].VpcId]' \
  --output table
```

### Inspect NAT Gateways

```bash
aws ec2 describe-nat-gateways \
  --query 'NatGateways[*].[NatGatewayId,State,SubnetId,VpcId,NatGatewayAddresses[*].PublicIp]' \
  --output table
```

### Inspect Route Tables

```bash
aws ec2 describe-route-tables \
  --query 'RouteTables[*].[RouteTableId,VpcId,Routes[*].[DestinationCidrBlock,GatewayId,NatGatewayId,TransitGatewayId,VpcPeeringConnectionId]]' \
  --output table
```

### Inspect VPC Peering

```bash
aws ec2 describe-vpc-peering-connections \
  --query 'VpcPeeringConnections[*].[VpcPeeringConnectionId,Status.Code,RequesterVpcInfo.VpcId,AccepterVpcInfo.VpcId]' \
  --output table
```

### Inspect Transit Gateway Attachments

```bash
aws ec2 describe-transit-gateway-attachments \
  --query 'TransitGatewayAttachments[*].[TransitGatewayAttachmentId,ResourceType,ResourceId,State,TransitGatewayId]' \
  --output table
```

### Inspect VPC Endpoints

```bash
aws ec2 describe-vpc-endpoints \
  --query 'VpcEndpoints[*].[VpcEndpointId,VpcId,VpcEndpointType,ServiceName,State]' \
  --output table
```

### Inspect VPN Connections

```bash
aws ec2 describe-vpn-connections \
  --query 'VpnConnections[*].[VpnConnectionId,State,Type,TransitGatewayId,VpnGatewayId]' \
  --output table
```

---

## Connectivity Decision Framework

When designing or troubleshooting connectivity, use this sequence:

```text
What is the source?
        |
        v
What is the destination?
        |
        v
Is it the same VPC?
        |
   +----+----+
   |         |
  Yes        No
   |         |
   v         v
Local     What network relationship?
route       |
            +---- Peering
            |
            +---- Transit Gateway
            |
            +---- VPN
            |
            +---- Direct Connect
            |
            +---- PrivateLink
            |
            +---- VPC Endpoint
```

Then verify:

```text
DNS
 ↓
Route
 ↓
Connectivity Attachment
 ↓
Destination Route
 ↓
Security Group
 ↓
NACL
 ↓
Service Listener
 ↓
Application Protocol
```

This approach prevents troubleshooting from becoming a sequence of random configuration changes.

## Key Takeaways

- **Route tables determine the network path, while gateways and connectivity services provide the appropriate next hop; neither replaces Security Groups or other authorization controls.**
- **NAT Gateway provides outbound IPv4 connectivity for private workloads, while Internet Gateway provides VPC Internet connectivity and Egress-Only Internet Gateway supports outbound IPv6 connectivity.**
- **VPC Peering is point-to-point and non-transitive, while Transit Gateway provides a scalable hub-and-spoke model for larger multi-VPC and hybrid networks.**
- **VPC endpoints and PrivateLink provide private service-oriented connectivity and can reduce unnecessary dependence on public Internet paths and NAT infrastructure.**
- **Production connectivity troubleshooting should trace the complete path: DNS → route → gateway/connectivity mechanism → destination route → Security Group/NACL → service listener → application behavior.**