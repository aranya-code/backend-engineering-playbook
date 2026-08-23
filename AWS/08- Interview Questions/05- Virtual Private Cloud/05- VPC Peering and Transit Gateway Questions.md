# 05- VPC Peering and Transit Gateway Questions

## Overview

VPC Peering and AWS Transit Gateway solve a similar high-level problem: connecting networks privately within AWS. The architectural difference is significant.

**VPC Peering** creates a direct private network connection between two VPCs. **Transit Gateway (TGW)** provides a centralized network transit layer through which multiple VPCs and other network attachments can communicate.

The key interview question is usually not simply "What is VPC Peering?" but rather:

> "When would you choose VPC Peering versus Transit Gateway?"

A strong answer considers:

- Number of VPCs.
- Routing complexity.
- Network topology.
- Account boundaries.
- Region boundaries.
- Centralized routing requirements.
- Security inspection.
- Operational ownership.
- Cost.
- Scalability.

A useful mental model is:

```text
VPC Peering

VPC A <----------------> VPC B


Transit Gateway

VPC A ----\
VPC B -----+----> Transit Gateway ----> VPC D
VPC C ----/
```

VPC Peering is fundamentally **point-to-point**.

Transit Gateway is fundamentally **hub-and-spoke transit networking**.

## VPC Peering

### What Is VPC Peering?

VPC Peering is a private networking connection between two VPCs that allows resources in those VPCs to communicate using private IP addresses.

The traffic does not require:

- Internet Gateway.
- NAT Gateway.
- Public IP addresses.
- Public Internet routing.

Conceptually:

```text
VPC A                         VPC B
10.10.0.0/16                  10.20.0.0/16

+-----------+                 +-----------+
| Backend A |                 | Backend B |
+-----+-----+                 +-----+-----+
      |                             |
      +-------- VPC Peering --------+
```

### Why VPC Peering Exists

VPC Peering is useful when two VPCs need direct private connectivity and the topology is relatively simple.

Typical examples include:

- Application VPC → shared services VPC.
- Production VPC → database VPC.
- Development VPC → centralized tooling VPC.
- Two business-unit VPCs requiring limited private communication.

### How VPC Peering Works

A VPC peering connection is established between two VPCs.

Both sides must configure appropriate routes.

For example:

```text
VPC A:
10.10.0.0/16

VPC B:
10.20.0.0/16
```

VPC A route table:

```text
Destination      Target
10.10.0.0/16     local
10.20.0.0/16     pcx-xxxxxxxx
```

VPC B route table:

```text
Destination      Target
10.20.0.0/16     local
10.10.0.0/16     pcx-xxxxxxxx
```

The route must exist on both sides for bidirectional communication.

## VPC Peering Traffic Flow

```mermaid
sequenceDiagram
    participant A as VPC A Workload
    participant RA as VPC A Route Table
    participant P as Peering Connection
    participant RB as VPC B Route Table
    participant B as VPC B Workload

    A->>RA: Send packet to VPC B CIDR
    RA->>P: Match peering route
    P->>RB: Deliver to VPC B
    RB->>B: Route to destination
    B-->>A: Return traffic through peering
```

The important operational point is that **routing is required on both sides**.

Creating the peering connection alone does not make workloads reachable.

## VPC Peering Requirements

Before establishing peering, verify:

- CIDR blocks do not overlap.
- Both VPCs can support the desired connectivity.
- Appropriate route tables can be updated.
- Security Groups permit the traffic.
- Network ACLs do not block the traffic.
- DNS requirements are understood.
- The peering connection is accepted where required.

### CIDR Overlap

A common interview question is:

> "Can you peer two VPCs with overlapping CIDR blocks?"

For normal VPC Peering, overlapping CIDR ranges are not supported.

For example:

```text
VPC A: 10.0.0.0/16
VPC B: 10.0.0.0/16
```

This creates ambiguous routing.

A better design is:

```text
VPC A: 10.0.0.0/16
VPC B: 10.1.0.0/16
VPC C: 10.2.0.0/16
```

CIDR planning should therefore happen before large-scale VPC deployment.

## VPC Peering Across AWS Accounts

VPC Peering can connect VPCs owned by different AWS accounts.

Typical architecture:

```text
AWS Account A
    |
    | VPC Peering
    |
AWS Account B
```

The connection requires the appropriate authorization and acceptance process.

This is useful for organizations where different teams or business units own separate AWS accounts.

## VPC Peering Across Regions

VPC Peering can also be used across AWS Regions.

Conceptually:

```text
Region A                         Region B

VPC A                            VPC B
10.10.0.0/16                     10.20.0.0/16
   |                                 |
   +------ Inter-Region Peering -----+
```

The traffic remains on AWS infrastructure rather than traversing the public Internet.

However, cross-region connectivity introduces:

- Additional latency.
- Inter-region data transfer costs.
- More operational considerations.
- Region-specific failure considerations.

## VPC Peering Is Not Transitive

This is one of the most important VPC Peering interview questions.

Suppose:

```text
VPC A
  |
  | Peering
  |
VPC B
  |
  | Peering
  |
VPC C
```

You might expect:

```text
VPC A → VPC B → VPC C
```

to work.

It does not.

VPC Peering does not provide transitive routing.

The architecture is:

```text
A <----> B <----> C

A -X-> C
```

To connect A and C, you need another supported connectivity mechanism, such as:

```text
A <----> C
```

or a Transit Gateway architecture.

## Why Non-Transitive Routing Matters

Consider ten VPCs.

If every VPC needs to communicate directly with every other VPC, the number of peering relationships grows rapidly.

For a full mesh of `n` VPCs:

```text
Connections = n × (n - 1) / 2
```

For example:

| VPCs | Peering Connections |
|---:|---:|
| 2 | 1 |
| 3 | 3 |
| 5 | 10 |
| 10 | 45 |
| 20 | 190 |
| 50 | 1,225 |

This is why VPC Peering becomes operationally difficult at larger scale.

## VPC Peering Advantages

VPC Peering is attractive because it is:

- Direct.
- Simple for small topologies.
- Private.
- Low-latency.
- Easy to reason about at small scale.
- Suitable for isolated VPC-to-VPC relationships.

## VPC Peering Limitations

Important limitations include:

- No transitive routing.
- Full-mesh complexity at scale.
- CIDR overlap restrictions.
- Distributed route management.
- More difficult centralized network governance.
- More difficult inspection architectures.

## Transit Gateway

### What Is Transit Gateway?

AWS Transit Gateway is a regional network transit hub that allows multiple VPCs and supported network attachments to connect through a centralized routing layer.

Instead of establishing direct peering relationships between every VPC:

```text
VPC A <--> VPC B
VPC A <--> VPC C
VPC B <--> VPC C
```

you can use:

```text
          VPC A
             |
             |
VPC B ---- Transit Gateway ---- VPC C
             |
             |
          VPC D
```

This dramatically simplifies large network topologies.

## Why Transit Gateway Exists

Transit Gateway exists to solve the scalability and operational complexity associated with connecting many networks.

Typical enterprise requirements include:

- Multiple production VPCs.
- Multiple application VPCs.
- Shared services VPCs.
- Centralized security inspection.
- Hybrid connectivity.
- AWS Direct Connect.
- Site-to-Site VPN.
- Multi-account networking.

Transit Gateway provides a centralized routing architecture for these use cases.

## Transit Gateway Architecture

```mermaid
flowchart TB
    A[VPC A<br/>Production]
    B[VPC B<br/>Development]
    C[VPC C<br/>Shared Services]
    D[VPC D<br/>Data Platform]

    TGW[Transit Gateway]

    A --> TGW
    B --> TGW
    C --> TGW
    D --> TGW
```

The Transit Gateway becomes the network transit layer.

## Transit Gateway Attachments

A Transit Gateway does not directly "connect to everything."

Resources connect to the TGW through **attachments**.

Common attachment types include:

- VPC attachments.
- Site-to-Site VPN attachments.
- Direct Connect Gateway associations.
- Transit Gateway Connect attachments.

For a VPC:

```text
VPC
 |
 | TGW VPC Attachment
 v
Transit Gateway
```

The VPC route tables must also send appropriate traffic toward the TGW.

## Transit Gateway Routing

Transit Gateway has its own route tables.

This is an important distinction:

```text
VPC Route Table
       |
       v
Transit Gateway
       |
       v
TGW Route Table
       |
       v
Destination Attachment
```

A packet may therefore be affected by both:

1. The VPC route table.
2. The Transit Gateway route table.

Both need to produce the intended path.

## VPC Route Table vs Transit Gateway Route Table

| Component | Responsibility |
|---|---|
| VPC Route Table | Determines how traffic leaves the VPC subnet |
| TGW Route Table | Determines which TGW attachment receives the traffic |
| Security Group | Controls allowed stateful traffic |
| Network ACL | Controls subnet-level stateless traffic |

A common troubleshooting mistake is checking only the VPC route table and ignoring the Transit Gateway route table.

## Transit Gateway Route Tables

Transit Gateway supports multiple route tables.

This enables network segmentation.

For example:

```text
                    Transit Gateway
                          |
              +-----------+-----------+
              |                       |
        Production TGW RT       Shared TGW RT
              |                       |
          Prod VPCs              Shared VPCs
```

You can control which attachments can communicate by controlling route propagation and associations.

This is significantly more powerful than treating the TGW as a single unrestricted routing table.

## Transit Gateway Route Propagation

VPC routes can be propagated into a TGW route table depending on the configuration.

Conceptually:

```text
VPC Attachment
      |
      v
Route Propagation
      |
      v
TGW Route Table
```

This reduces manual route management in large environments.

However, automatic propagation should still be designed carefully. Blindly propagating every network into every routing domain can create unintended connectivity.

## Transit Gateway Route Table Association

An attachment can be associated with a TGW route table.

Conceptually:

```text
VPC Production
      |
      v
Prod TGW Route Table
```

Another VPC can use a different routing domain:

```text
VPC Development
      |
      v
Dev TGW Route Table
```

This is useful for isolation.

## Transit Gateway Segmentation

Consider an organization with:

```text
Production VPC
Development VPC
Security VPC
Shared Services VPC
```

A desired policy might be:

```text
Production → Shared Services     Allowed
Development → Shared Services    Allowed
Production → Development         Denied
Development → Production         Denied
Production → Security            Allowed
Development → Security           Allowed
```

Transit Gateway route tables can help implement this segmentation.

The key idea is:

> Connectivity should be intentionally granted through routing domains rather than assuming that attachment to the TGW means universal connectivity.

## VPC Peering vs Transit Gateway

| Characteristic | VPC Peering | Transit Gateway |
|---|---|---|
| Topology | Point-to-point | Hub-and-spoke |
| Transitive routing | No | Yes, through TGW |
| Best for | Small/simple relationships | Large/multi-VPC environments |
| Centralized routing | Limited | Strong |
| Route management | Distributed | Centralized |
| Multi-account | Supported | Strong enterprise use case |
| Hybrid connectivity | Limited | Strong |
| Segmentation | More distributed | TGW route tables |
| Operational complexity at scale | High | Lower |
| Cost model | Connection/data transfer dependent | TGW attachment/data processing dependent |

## Interview Question: When Would You Choose VPC Peering?

Use VPC Peering when:

- Only a small number of VPCs need connectivity.
- The relationship is direct.
- Transitive routing is unnecessary.
- Network topology is simple.
- Centralized routing is unnecessary.
- The operational overhead of Transit Gateway is not justified.

Example:

```text
Application VPC <----> Shared Services VPC
```

If this is the only required relationship, VPC Peering may be simpler.

## Interview Question: When Would You Choose Transit Gateway?

Choose Transit Gateway when:

- Many VPCs need connectivity.
- Centralized routing is desirable.
- Multiple AWS accounts are involved.
- Hybrid networking is required.
- VPN or Direct Connect integration is required.
- Network segmentation is required.
- The organization expects the network topology to grow.

Example:

```text
Account A
  VPC A ----\
             \
Account B     \
  VPC B ------ Transit Gateway
             /
Account C   /
  VPC C ---/
```

## Interview Scenario: 50 VPCs Need Connectivity

Suppose an organization has 50 VPCs and wants broad private connectivity.

A poor design would be a full peering mesh.

The theoretical number of connections is:

```text
50 × 49 / 2 = 1,225
```

A Transit Gateway architecture is much easier to operate:

```text
VPC 1 ----\
VPC 2 -----\
VPC 3 ------\
...          > Transit Gateway
VPC 49 -----/
VPC 50 ----/
```

The exact connectivity policy can then be implemented using TGW route tables and attachment associations.

## Interview Scenario: Three VPCs

Suppose:

```text
VPC A → Application
VPC B → Shared Services
VPC C → Database
```

If only A needs to communicate with B and C, and the topology is unlikely to grow, VPC Peering may be appropriate.

```text
A ---- Peering ---- B
|
|
+---- Peering ---- C
```

But if the organization expects many additional VPCs, introducing Transit Gateway early may reduce future migration complexity.

The correct answer depends on both **current topology and expected growth**.

## Interview Question: Is Transit Gateway a Router?

At a conceptual level, Transit Gateway acts as a managed regional network transit hub with routing capabilities.

It is better to explain it as:

> A managed network transit service that provides centralized routing between attached networks.

Avoid reducing the answer to simply:

> "It is a router."

The interview may continue into:

- Route tables.
- Attachments.
- Propagation.
- Associations.
- Segmentation.
- Hybrid connectivity.

## Interview Question: Is Transit Gateway Transitive?

Yes, Transit Gateway is designed to provide transit routing between supported attachments according to its routing configuration.

For example:

```text
VPC A
  |
  v
TGW
  |
  v
VPC B
```

VPC A does not need a direct VPC Peering relationship with VPC B.

However, the required routes and policies must exist.

## Important Transit Gateway Routing Caveat

"Attached to TGW" does not mean "automatically reachable."

A typical flow requires:

```text
Application Subnet
       |
       v
VPC Route Table
       |
       v
TGW Attachment
       |
       v
TGW Route Table
       |
       v
Destination Attachment
       |
       v
Destination VPC Route Table
       |
       v
Destination
```

A failure at any stage can break connectivity.

## Transit Gateway and Shared Services

A common enterprise architecture is:

```text
                 Transit Gateway
                       |
       +---------------+---------------+
       |               |               |
       v               v               v
 Production       Development      Shared Services
 VPCs             VPCs             VPC
```

The Shared Services VPC might contain:

- Internal DNS.
- Logging infrastructure.
- Monitoring services.
- Internal APIs.
- Security tooling.
- Directory services.
- Shared databases where appropriate.

TGW route tables can control which environments can reach these services.

## Transit Gateway and Hybrid Connectivity

Transit Gateway is especially useful when connecting AWS networks to on-premises infrastructure.

Example:

```text
On-Premises
     |
     v
VPN / Direct Connect
     |
     v
Transit Gateway
     |
     +-------- VPC A
     |
     +-------- VPC B
     |
     +-------- VPC C
```

This avoids building independent VPN or routing relationships for every VPC.

## Transit Gateway and Site-to-Site VPN

A common enterprise design is:

```text
Corporate Network
       |
       v
Site-to-Site VPN
       |
       v
Transit Gateway
       |
       +---- Production VPC
       +---- Shared Services VPC
       +---- Data VPC
```

This centralizes network connectivity.

Routing must still be designed in both directions.

## Transit Gateway and Direct Connect

For larger hybrid architectures:

```text
Corporate Data Center
        |
        v
Direct Connect
        |
        v
Direct Connect Gateway
        |
        v
Transit Gateway
        |
        +---- VPC A
        +---- VPC B
        +---- VPC C
```

This provides a scalable architecture for connecting on-premises networks to multiple VPCs.

## VPC Peering and Transit Gateway Security

Neither VPC Peering nor Transit Gateway is an authorization system.

They primarily provide network connectivity.

Security still requires:

- Security Groups.
- Network ACLs.
- IAM for AWS API authorization.
- Application-level authorization.
- Firewall/security appliances where appropriate.
- Route segmentation.

For example:

```text
TGW Connectivity
      |
      v
Network Reachability
      |
      v
Security Groups
      |
      v
Application Authorization
```

A route permitting traffic does not mean the application should trust the source.

## CIDR Planning

CIDR planning becomes increasingly important as the number of connected VPCs grows.

A poor allocation might look like:

```text
VPC A: 10.0.0.0/16
VPC B: 10.0.0.0/16
VPC C: 10.0.1.0/24
```

This creates overlap and routing ambiguity.

A planned enterprise allocation might look like:

```text
Production:
10.0.0.0/16

Development:
10.1.0.0/16

Shared Services:
10.2.0.0/16

Security:
10.3.0.0/16

Data Platform:
10.4.0.0/16
```

The exact address plan depends on organizational requirements, future growth, hybrid networks, and available private address space.

## Common Production Mistakes

### Mistake: Forgetting Return Routes

A connection can appear correctly configured in one direction while the response path is missing.

Always validate both directions:

```text
A → B
B → A
```

### Mistake: Assuming Peering Is Transitive

This is one of the most common interview and production misconceptions.

```text
A ↔ B ↔ C
```

does not imply:

```text
A ↔ C
```

### Mistake: Using a Full Peering Mesh at Large Scale

The number of relationships grows quadratically.

Use centralized networking when the topology requires it.

### Mistake: Ignoring CIDR Overlap

CIDR conflicts can prevent connectivity designs from working and can be extremely expensive to remediate later.

### Mistake: Checking Only VPC Route Tables

For Transit Gateway architectures, inspect both:

```text
VPC Route Table
+
TGW Route Table
```

### Mistake: Treating TGW as an Unrestricted Network

A Transit Gateway can centralize connectivity, but production architectures should use route-table segmentation deliberately.

### Mistake: Ignoring Cross-Account Ownership

In multi-account architectures, determine:

- Who owns the TGW?
- Who owns the VPC?
- Who can create attachments?
- Who approves connectivity?
- Who manages route policies?

Centralized networking usually requires clear ownership boundaries.

## Troubleshooting VPC Peering

Use a layered approach:

```text
1. Peering connection state
2. CIDR compatibility
3. Source subnet route table
4. Destination subnet route table
5. Security Groups
6. Network ACLs
7. DNS configuration if hostname-based access is used
8. Application-level behavior
```

List peering connections:

```bash
aws ec2 describe-vpc-peering-connections \
  --query 'VpcPeeringConnections[*].[VpcPeeringConnectionId,Status.Code,RequesterVpcInfo.VpcId,AccepterVpcInfo.VpcId]' \
  --output table
```

Inspect routes:

```bash
aws ec2 describe-route-tables \
  --query 'RouteTables[*].[RouteTableId,VpcId,Routes[*].[DestinationCidrBlock,VpcPeeringConnectionId,State]]' \
  --output table
```

Check Security Groups:

```bash
aws ec2 describe-security-groups \
  --group-ids sg-xxxxxxxx \
  --output json
```

## Troubleshooting Transit Gateway

A useful diagnostic flow is:

```mermaid
flowchart TD
    A[Application Cannot Reach Destination]
    B[Check Source VPC Route]
    C[Check TGW Attachment]
    D[Check TGW Route Table]
    E[Check Route Propagation / Static Route]
    F[Check Destination VPC Route]
    G[Check Security Groups and NACLs]
    H[Check Application]

    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
    F --> G
    G --> H
```

Inspect Transit Gateway:

```bash
aws ec2 describe-transit-gateways \
  --query 'TransitGateways[*].[TransitGatewayId,State,OwnerId]' \
  --output table
```

Inspect attachments:

```bash
aws ec2 describe-transit-gateway-attachments \
  --query 'TransitGatewayAttachments[*].[TransitGatewayAttachmentId,ResourceType,ResourceId,State,TransitGatewayId]' \
  --output table
```

Inspect TGW route tables:

```bash
aws ec2 describe-transit-gateway-route-tables \
  --query 'TransitGatewayRouteTables[*].[TransitGatewayRouteTableId,State,DefaultAssociationRouteTable,DefaultPropagationRouteTable]' \
  --output table
```

Inspect routes:

```bash
aws ec2 search-transit-gateway-routes \
  --transit-gateway-route-table-id tgw-rtb-xxxxxxxx \
  --filters Name=state,Values=active \
  --output table
```

The exact AWS CLI output depends on the configured route tables and AWS account.

## Reachability Analyzer

AWS Reachability Analyzer can help determine whether a network path between supported resources is reachable.

For VPC Peering and Transit Gateway troubleshooting, it can be useful for validating paths involving:

- Network interfaces.
- EC2 instances.
- Transit Gateway attachments.
- Route tables.
- Security Groups.
- Network ACLs.

It is particularly useful when manual inspection becomes difficult.

A strong troubleshooting workflow is:

```text
Application symptom
       |
       v
Reachability Analyzer
       |
       v
Routing / SG / NACL diagnosis
       |
       v
Configuration correction
       |
       v
Application validation
```

## Monitoring and Observability

Production network connectivity should not depend solely on manual CLI inspection.

Useful mechanisms include:

- VPC Flow Logs.
- CloudWatch metrics.
- CloudTrail.
- Transit Gateway monitoring.
- Reachability Analyzer.
- Application logs.
- Network monitoring systems.

For example:

```text
FastAPI
   |
   v
Network Request
   |
   v
Transit Gateway
   |
   v
VPC
   |
   v
PostgreSQL
```

If connectivity fails, application logs tell you **what the application experienced**, while network telemetry helps determine **where the network path failed**.

## Cost Considerations

VPC Peering and Transit Gateway have different cost and operational characteristics.

For architecture decisions, evaluate:

- Number of connections.
- Data transfer volume.
- Cross-AZ traffic.
- Cross-region traffic.
- Number of TGW attachments.
- TGW data processing.
- Operational complexity.
- Network inspection requirements.

Do not choose a networking architecture based only on the hourly service price.

A cheaper primitive can become more expensive operationally if it requires hundreds of individually managed relationships.

## High Availability

For production architectures:

### VPC Peering

VPC Peering itself is not tied to a single EC2 instance or subnet. However, the application route tables and workloads still need to be designed across multiple AZs.

### Transit Gateway

Transit Gateway is designed as a managed regional networking service. Workload VPCs should still use multi-AZ subnet and routing designs.

The important principle is:

> High availability applies to the entire network path, not just the connectivity service.

For example:

```text
ALB
 |
 +-- AZ-A → Application → TGW
 |
 +-- AZ-B → Application → TGW
```

Do not design a supposedly highly available application around a single-AZ dependency elsewhere in the network.

## VPC Peering vs Transit Gateway Decision Matrix

| Requirement | Preferred Option |
|---|---|
| Two VPCs need direct connectivity | VPC Peering |
| Small number of VPCs | VPC Peering |
| Many VPCs | Transit Gateway |
| Need transitive routing | Transit Gateway |
| Centralized route management | Transit Gateway |
| Centralized network segmentation | Transit Gateway |
| Hybrid AWS/on-premises connectivity | Transit Gateway |
| Simple point-to-point relationship | VPC Peering |
| Large multi-account network | Transit Gateway |
| Existing simple architecture with no growth | VPC Peering |
| Enterprise network hub | Transit Gateway |

This is a decision aid, not an absolute rule. Existing network architecture, cost, ownership, and future requirements must also be considered.

## Interview Questions and Answers

### What is VPC Peering?

VPC Peering is a private network connection between two VPCs that allows resources to communicate using private IP addresses.

### Is VPC Peering transitive?

No. VPC Peering is not transitive.

### Can VPC Peering connect VPCs in different AWS accounts?

Yes.

### Can VPC Peering connect VPCs in different Regions?

Yes, through inter-region VPC Peering.

### Can VPCs with overlapping CIDRs be peered?

No, overlapping CIDR ranges prevent normal VPC Peering connectivity.

### What is Transit Gateway?

Transit Gateway is a managed network transit hub that centralizes routing between multiple VPCs and supported network attachments.

### Why use Transit Gateway instead of VPC Peering?

Transit Gateway is generally more appropriate when many VPCs, accounts, or hybrid networks must communicate and centralized routing or segmentation is required.

### Is Transit Gateway transitive?

Yes. Transit Gateway is designed to provide transit routing between supported attachments according to its route configuration.

### Does attaching a VPC to Transit Gateway automatically make every other VPC reachable?

No. VPC route tables, TGW route-table associations/propagation or static routes, destination routes, and security controls must all permit the traffic.

### What is the difference between VPC route tables and TGW route tables?

The VPC route table determines where traffic leaving the VPC subnet should go. The TGW route table determines which Transit Gateway attachment should receive traffic after it reaches the TGW.

### What is a Transit Gateway attachment?

An attachment connects a supported network resource, such as a VPC or VPN, to the Transit Gateway.

### Can Transit Gateway connect to on-premises networks?

Yes. Common architectures use Site-to-Site VPN or Direct Connect with Transit Gateway.

### Can Transit Gateway provide network segmentation?

Yes. Multiple TGW route tables, attachment associations, propagation controls, and routes can be used to create separate connectivity domains.

### Is Transit Gateway a security boundary?

Not by itself. Security Groups, NACLs, firewalls, application authorization, and routing controls still need to be designed.

### How would you troubleshoot a VPC Peering timeout?

Check the peering state, source and destination routes, Security Groups, NACLs, DNS where relevant, and the application.

### How would you troubleshoot a Transit Gateway timeout?

Check the source VPC route, TGW attachment state, TGW route-table association, route propagation or static routes, destination VPC route, Security Groups, NACLs, and application behavior.

## Senior-Level Interview Scenario

### Scenario

An organization has:

```text
20 AWS accounts
80 VPCs
Multiple production environments
On-premises data centers
Shared security services
Shared monitoring services
```

The engineering team proposes creating VPC Peering between all VPCs.

### Evaluation

A full-mesh design would create:

```text
80 × 79 / 2 = 3,160
```

potential peering relationships.

That creates substantial operational complexity.

A more scalable architecture would generally use Transit Gateway:

```text
                         Transit Gateway
                    /      |      |      \
                   /       |      |       \
                VPCs     VPCs   Shared    VPN /
                              Services   Direct Connect
```

The architecture can then introduce separate routing domains for:

- Production.
- Development.
- Shared Services.
- Security.
- Data platforms.
- Hybrid connectivity.

The exact topology should be based on the organization's connectivity and security requirements, but the key architectural principle is centralized routing instead of an uncontrolled full mesh.

## Senior-Level Interview Trap

### "Transit Gateway is always better than VPC Peering."

Incorrect.

Transit Gateway solves a different scale and topology problem.

If two VPCs need a simple direct connection:

```text
VPC A <----> VPC B
```

VPC Peering may be simpler and more appropriate.

If dozens of VPCs need controlled connectivity:

```text
VPC A \
VPC B  \
VPC C   > TGW
VPC D  /
```

Transit Gateway becomes more attractive.

The correct engineering answer considers:

```text
Topology
+
Scale
+
Routing complexity
+
Security
+
Cost
+
Future growth
```

## Key Takeaways

- **VPC Peering is a direct point-to-point connection and is appropriate for relatively small, simple VPC-to-VPC connectivity requirements.**
- **VPC Peering is not transitive, while Transit Gateway provides centralized transit routing between supported attachments according to its route configuration.**
- **Transit Gateway becomes increasingly valuable as the number of VPCs, AWS accounts, hybrid connections, and routing domains grows.**
- **Transit Gateway connectivity requires both VPC routing and TGW routing to be correct; attachment alone does not guarantee reachability.**
- **Choose between Peering and Transit Gateway based on topology, scale, routing complexity, security, cost, ownership, and expected future growth rather than using one universally.**