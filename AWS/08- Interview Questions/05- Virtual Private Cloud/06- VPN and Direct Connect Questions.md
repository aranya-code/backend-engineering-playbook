# 06- VPN and Direct Connect Questions

## Overview

AWS VPN and AWS Direct Connect provide private connectivity between AWS environments and external networks such as corporate data centers, branch offices, and remote infrastructure.

The central interview distinction is:

- **Site-to-Site VPN** uses encrypted tunnels over an underlying IP network, typically the public Internet.
- **AWS Direct Connect** provides a dedicated network connection between an on-premises environment and AWS through a Direct Connect location.
- **Transit Gateway** can act as a centralized routing hub for VPN and Direct Connect connectivity across multiple VPCs.

A common enterprise architecture is:

```text
                         AWS Cloud
                              |
                    +---------+---------+
                    |                   |
               Transit Gateway      Shared Services
                    |
          +---------+---------+
          |         |         |
        VPC A     VPC B      VPC C
          |
          |
     VPN / Direct Connect
          |
          v
   Corporate Network
```

The correct solution depends on:

- Connectivity requirements.
- Encryption requirements.
- Bandwidth.
- Latency.
- Availability.
- Cost.
- Operational complexity.
- Number of VPCs.
- Number of on-premises locations.
- Disaster recovery requirements.

## Site-to-Site VPN

### What Is Site-to-Site VPN?

AWS Site-to-Site VPN creates encrypted IPsec tunnels between an AWS VPC and an external network.

A typical connection is:

```text
Corporate Network
       |
       | IPsec VPN
       |
       v
Virtual Private Gateway / Transit Gateway
       |
       v
       VPC
```

The underlying network can be the public Internet, while the traffic between the customer gateway and AWS VPN endpoint is encrypted.

### Why Site-to-Site VPN Exists

VPN is useful when an organization needs private and encrypted connectivity without provisioning a dedicated physical network connection.

Typical use cases include:

- Connecting a corporate data center to AWS.
- Connecting branch offices to AWS.
- Quickly establishing hybrid connectivity.
- Backup connectivity for Direct Connect.
- Development and testing environments.
- Disaster recovery connectivity.

## How Site-to-Site VPN Works

At a high level:

```mermaid
sequenceDiagram
    participant OnPrem as On-Premises Network
    participant CGW as Customer Gateway
    participant VPN as AWS VPN Endpoint
    participant VPC as VPC

    OnPrem->>CGW: Private network traffic
    CGW->>VPN: Encrypted IPsec tunnel
    VPN->>VPC: Decrypted traffic
    VPC-->>VPN: Response traffic
    VPN-->>CGW: Encrypted response
    CGW-->>OnPrem: Deliver response
```

The customer side generally has a **Customer Gateway** representing the external network endpoint.

The AWS side can use a:

- Virtual Private Gateway.
- Transit Gateway.

The VPN tunnels use IPsec encryption.

## Customer Gateway

A Customer Gateway represents the customer-side VPN endpoint or routing configuration.

The actual device may be:

- Cisco router.
- Fortinet appliance.
- Palo Alto firewall.
- StrongSwan-based Linux system.
- Other compatible network appliance.

The customer gateway configuration must match the AWS VPN configuration.

## Virtual Private Gateway

A Virtual Private Gateway (VGW) is an AWS-side VPN gateway associated with a VPC.

Conceptually:

```text
On-Premises
     |
     | VPN
     v
Customer Gateway
     |
     v
Virtual Private Gateway
     |
     v
VPC
```

VGW is suitable for simpler architectures where a VPN connection is associated with a specific VPC.

## Transit Gateway and VPN

For larger environments, VPN can terminate on Transit Gateway.

```text
Corporate Network
       |
       | VPN
       v
Transit Gateway
       |
       +-------- VPC A
       |
       +-------- VPC B
       |
       +-------- VPC C
```

This is useful when the same on-premises network needs connectivity to multiple VPCs.

Instead of maintaining separate VPN relationships for every VPC, Transit Gateway can centralize routing.

## Site-to-Site VPN Tunnels

An AWS Site-to-Site VPN connection typically provides two tunnels for redundancy.

Conceptually:

```text
                    +---- Tunnel 1 ----+
                    |                  |
On-Premises --------+                  +---- AWS
                    |                  |
                    +---- Tunnel 2 ----+
```

Production designs should take advantage of redundant tunnels rather than treating the VPN as a single logical path.

A strong interview answer should mention:

> A production VPN architecture should account for tunnel redundancy and failure detection rather than relying on a single tunnel.

## Static vs Dynamic Routing

VPN connectivity can use:

- Static routing.
- Dynamic routing using BGP.

### Static Routing

Routes are explicitly configured.

Example:

```text
10.20.0.0/16 → VPN
10.30.0.0/16 → VPN
```

Advantages:

- Simple.
- Predictable.
- Suitable for small networks.

Limitations:

- Manual route management.
- Less suitable for large or frequently changing networks.
- Failover can become more operationally complex.

### Dynamic Routing with BGP

BGP allows routing information to be exchanged dynamically.

Conceptually:

```text
On-Premises Router
       |
       | BGP
       |
       v
AWS VPN / TGW
```

Advantages:

- Dynamic route exchange.
- Better support for changing network topology.
- Improved failover behavior.
- Better suited to larger hybrid environments.

For production hybrid networking, BGP is generally preferable when the network architecture and equipment support it.

## Direct Connect

### What Is AWS Direct Connect?

AWS Direct Connect provides a dedicated network connection between an on-premises environment and AWS through a Direct Connect location.

Conceptually:

```text
Corporate Data Center
        |
        |
        v
Direct Connect Location
        |
        |
        v
AWS
```

Unlike VPN, Direct Connect does not use the public Internet as the underlying connectivity path.

### Why Direct Connect Exists

Direct Connect is designed for workloads that require more predictable network characteristics or significant network traffic between on-premises infrastructure and AWS.

Typical use cases include:

- Large-scale hybrid applications.
- High-volume data transfer.
- Enterprise databases.
- Data analytics.
- Storage integration.
- Consistent network performance requirements.
- Long-lived hybrid architectures.

## Direct Connect Architecture

A typical architecture is:

```mermaid
flowchart LR
    DC[Corporate Data Center]
    DX[Direct Connect]
    DXGW[Direct Connect Gateway]
    TGW[Transit Gateway]
    A[VPC A]
    B[VPC B]
    C[VPC C]

    DC --> DX
    DX --> DXGW
    DXGW --> TGW
    TGW --> A
    TGW --> B
    TGW --> C
```

The exact architecture depends on whether connectivity is being provided directly to a VPC through a virtual private gateway or through a Transit Gateway.

## Direct Connect Location

Direct Connect connections are established through Direct Connect locations or approved connectivity providers.

The physical connection itself is not simply a cable directly from an organization's office to an AWS Region.

Instead, connectivity is established through an AWS Direct Connect location or partner architecture.

This distinction matters in interviews because Direct Connect is a **physical/private network connectivity service**, not merely another type of VPN.

## Virtual Interface

Direct Connect uses virtual interfaces to establish logical connectivity over the physical connection.

Important types include:

| Virtual Interface | Typical Purpose |
|---|---|
| Private VIF | Private connectivity to VPC resources |
| Transit VIF | Connectivity to a Transit Gateway through a Direct Connect Gateway |
| Public VIF | Access to AWS public services |

For modern multi-VPC architectures, Transit VIF combined with Direct Connect Gateway and Transit Gateway is an important design pattern.

## Direct Connect Gateway

A Direct Connect Gateway can provide connectivity from Direct Connect to supported AWS networking resources across Regions and accounts, subject to the supported architecture and configuration.

A common enterprise path is:

```text
On-Premises
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

This architecture separates:

- Physical connectivity.
- Direct Connect association.
- Transit routing.
- VPC networking.

That separation makes large hybrid networks easier to operate.

## VPN vs Direct Connect

| Characteristic | Site-to-Site VPN | Direct Connect |
|---|---|---|
| Underlying connectivity | Typically Internet | Dedicated/private connection |
| Encryption | IPsec | Not inherently encrypted |
| Setup time | Usually faster | Usually longer |
| Physical provisioning | No | Yes |
| Latency consistency | Less predictable | More predictable |
| Bandwidth | Lower/flexible depending on configuration | Designed for higher dedicated capacity |
| Cost | Generally lower entry cost | Higher infrastructure cost |
| Best use | Fast/private encrypted connectivity | Long-term high-volume hybrid connectivity |
| Failover | Multiple tunnels | Requires redundant connectivity design |
| Encryption requirement | Built in through IPsec | Additional encryption may be required |

The key interview point is:

> Direct Connect provides private network connectivity, but it does not automatically mean the traffic is encrypted.

If encryption is required, organizations may layer encryption mechanisms over the Direct Connect connection, depending on the architecture and security requirements.

## VPN vs Direct Connect: Decision Criteria

Use VPN when:

- Fast deployment is important.
- Traffic volume is moderate.
- Internet-based connectivity is acceptable.
- IPsec encryption is required.
- Cost needs to remain relatively low.
- The environment is temporary or development-focused.

Use Direct Connect when:

- Traffic volume is high.
- Predictable network performance matters.
- Hybrid connectivity is a long-term requirement.
- Dedicated connectivity is justified.
- The organization needs enterprise-grade connectivity to AWS.

Use both when:

- Hybrid connectivity is business-critical.
- Direct Connect is the primary path.
- VPN is required as backup connectivity.

A common architecture is:

```text
                 +----------------+
                 | Transit Gateway|
                 +-------+--------+
                         |
             +-----------+-----------+
             |                       |
       Direct Connect               VPN
       Primary Path              Backup Path
             |                       |
             +-----------+-----------+
                         |
                  Corporate Network
```

The exact failover design depends on routing configuration and the organization's operational requirements.

## VPN High Availability

A production VPN design should consider:

- Both VPN tunnels.
- Redundant customer-side devices where appropriate.
- Dynamic routing where appropriate.
- Independent network paths.
- Monitoring.
- Automated failover.
- Route convergence.

Avoid designs where:

```text
Corporate Network
       |
   Single Router
       |
     Single VPN
       |
      AWS
```

becomes a single point of failure.

A stronger architecture is:

```text
             AWS
              |
       +------+------+
       |             |
    Tunnel 1       Tunnel 2
       |             |
 Router A         Router B
       |             |
       +------+------+
              |
        Corporate Network
```

The physical topology should also avoid common-mode failures where possible.

## Direct Connect High Availability

Direct Connect should not be treated as inherently highly available merely because it is a dedicated connection.

Production architectures should consider:

- Multiple Direct Connect connections.
- Separate Direct Connect locations where appropriate.
- Independent customer routers.
- Independent power/network paths.
- Multiple AWS Regions where required.
- VPN backup.

Example:

```text
                 AWS
                  |
        +---------+---------+
        |                   |
   Direct Connect 1    Direct Connect 2
        |                   |
   DX Location A       DX Location B
        |                   |
   Router A            Router B
        |                   |
        +--------+----------+
                 |
          Corporate Network
```

The goal is to eliminate single points of failure across the entire path.

## Direct Connect and Encryption

A frequent interview trap is:

> "Is Direct Connect encrypted?"

The correct answer is:

> Direct Connect provides dedicated network connectivity, but the Direct Connect service itself does not automatically provide end-to-end application traffic encryption.

If encryption is required, use an appropriate encryption mechanism based on the architecture.

For sensitive applications, application-layer encryption such as TLS remains important regardless of the underlying network path.

## VPN and Direct Connect with Transit Gateway

A common enterprise architecture combines both services:

```text
                         Transit Gateway
                      /       |       \
                     /        |        \
                  VPC A      VPC B     VPC C
                     |
                     |
              +------+------+
              |             |
             VPN       Direct Connect
              |             |
              +------+------+
                     |
              Corporate Network
```

This provides:

- Centralized routing.
- Multiple VPC connectivity.
- Hybrid network integration.
- Redundancy.
- Segmentation.

Transit Gateway route tables can determine which VPCs are reachable from on-premises networks.

## Routing Flow

Consider:

```text
On-Premises
10.100.0.0/16

VPC
10.10.0.0/16
```

A request from:

```text
10.100.1.10
```

to:

```text
10.10.20.15
```

might follow:

```text
Application
    |
    v
On-Prem Route
    |
    v
VPN / Direct Connect
    |
    v
Transit Gateway
    |
    v
TGW Route Table
    |
    v
VPC Attachment
    |
    v
VPC Route Table
    |
    v
Destination ENI
```

Return traffic must have a valid reverse path.

## Reverse Path Routing

A very common production failure is asymmetric or missing return routing.

For example:

```text
On-Prem → AWS
```

works, but:

```text
AWS → On-Prem
```

fails.

Always validate:

```text
Source → Destination
Destination → Source
```

Network connectivity is bidirectional unless the application protocol or security policy intentionally makes it otherwise.

## VPN and Security Groups

Security Groups still apply to traffic entering or leaving supported AWS resources.

For example:

```text
On-Prem
10.100.0.0/16
     |
     | VPN
     v
EC2
10.10.10.10
```

The EC2 Security Group might require:

```text
Inbound:
TCP 443
Source: 10.100.0.0/16
```

A VPN route permitting the traffic does not override the Security Group.

## VPN and Network ACLs

Network ACLs are subnet-level stateless controls.

A connectivity path may therefore require:

```text
Route Table
+
Security Group
+
Network ACL
+
VPN/TGW routing
```

Because NACLs are stateless, return traffic must be explicitly allowed where required.

This makes overly restrictive NACLs a common source of confusing VPN connectivity failures.

## VPN and DNS

VPN connectivity does not automatically solve DNS.

For example, an on-premises client may reach:

```text
10.10.20.10
```

but fail to resolve:

```text
database.internal.example.com
```

If hybrid DNS is required, design DNS resolution explicitly using appropriate AWS and on-premises DNS integration.

Potential components include:

- Route 53 Resolver.
- Resolver inbound endpoints.
- Resolver outbound endpoints.
- On-premises DNS servers.
- Conditional forwarding.

The network path and DNS path should be treated as separate troubleshooting layers.

## BGP and Route Propagation

BGP becomes particularly valuable when multiple network paths exist.

Example:

```text
Corporate Network
       |
   +---+---+
   |       |
  VPN     DX
   |       |
   +---+---+
       |
      TGW
```

BGP can dynamically exchange routes and assist with path selection and failover.

However, BGP should not be treated as magic automatic failover.

Engineers must understand:

- Advertised prefixes.
- Local preference.
- AS paths.
- Route filtering.
- Propagation.
- Convergence.
- Primary/backup design.

## Interview Question: What Is the Difference Between VPN and Direct Connect?

A strong answer:

> Site-to-Site VPN establishes encrypted IPsec connectivity over an underlying IP network, typically the Internet. Direct Connect provides dedicated network connectivity between the customer's network and AWS through a Direct Connect location. VPN is generally faster and cheaper to establish, while Direct Connect is better suited to high-volume, predictable, long-term hybrid connectivity.

## Interview Question: Is Direct Connect More Secure Than VPN?

This requires nuance.

Direct Connect does not traverse the public Internet in the same way as an Internet-based VPN, but Direct Connect itself does not automatically encrypt application traffic.

VPN provides IPsec encryption.

Therefore:

```text
VPN:
Private connectivity + IPsec encryption

Direct Connect:
Dedicated/private connectivity + encryption must be separately designed when required
```

Security should be evaluated based on the complete architecture rather than simply labeling one service "more secure."

## Interview Question: Can VPN Be Used as a Backup for Direct Connect?

Yes.

A common production architecture uses:

```text
Primary:
Direct Connect

Backup:
Site-to-Site VPN
```

The routing architecture determines how traffic fails over.

BGP can be used to dynamically exchange routes and influence path selection.

## Interview Question: Why Would You Use Both VPN and Direct Connect?

Using both can provide:

- Primary/backup connectivity.
- Better availability.
- Faster recovery from Direct Connect failures.
- Encryption options.
- Operational flexibility.

Example:

```text
Corporate Network
       |
       +------ Direct Connect ------+
       |                            |
       +----------- VPN ------------+---- AWS
```

## Interview Question: What Is a Virtual Private Gateway?

A Virtual Private Gateway is an AWS-side VPN gateway that can be attached to a VPC.

It is appropriate for simpler VPN-to-VPC architectures.

For larger multi-VPC architectures, Transit Gateway is often more appropriate because it provides centralized routing.

## Interview Question: What Is a Customer Gateway?

A Customer Gateway represents the customer-side VPN endpoint or routing configuration used to establish the Site-to-Site VPN connection.

It is associated with the external network device or configuration.

## Interview Question: What Is Direct Connect Gateway?

Direct Connect Gateway is a global AWS networking resource that allows Direct Connect connectivity to be associated with supported AWS network resources, including Transit Gateway and virtual private gateways according to the supported architecture.

A common modern pattern is:

```text
On-Prem
   |
Direct Connect
   |
Direct Connect Gateway
   |
Transit Gateway
   |
Multiple VPCs
```

## Interview Question: What Is a Transit VIF?

A Transit Virtual Interface is used with Direct Connect to connect to a Transit Gateway through a Direct Connect Gateway.

Conceptually:

```text
On-Prem
   |
Direct Connect
   |
Transit VIF
   |
Direct Connect Gateway
   |
Transit Gateway
   |
Multiple VPCs
```

This is particularly useful for large multi-VPC hybrid architectures.

## Interview Question: What Is a Private VIF?

A Private Virtual Interface provides private connectivity over Direct Connect to AWS private resources through supported gateway architectures.

A typical conceptual path is:

```text
On-Prem
   |
Direct Connect
   |
Private VIF
   |
Virtual Private Gateway
   |
VPC
```

## Interview Question: What Is a Public VIF?

A Public VIF provides connectivity from a Direct Connect connection to AWS public services and public AWS endpoints.

It is different from a private VIF, which is used for private network connectivity.

## Interview Question: Does VPN Require a Public IP?

For traditional AWS Site-to-Site VPN architectures, the customer gateway generally uses a publicly reachable IP address for the VPN endpoint.

The exact supported configuration depends on the VPN architecture and AWS capabilities in use.

The important interview distinction is:

> VPN uses an IP network to establish encrypted tunnels; Direct Connect provides dedicated connectivity.

## Interview Question: Can Direct Connect Connect Multiple VPCs?

Yes.

A common scalable design uses:

```text
Direct Connect
      |
Direct Connect Gateway
      |
Transit Gateway
      |
+-----+-----+-----+
|     |     |     |
VPC A VPC B VPC C
```

This avoids building independent physical connectivity for every VPC.

## Interview Scenario: Large Enterprise Hybrid Architecture

### Requirements

An organization has:

- 50 VPCs.
- Two corporate data centers.
- Large data-transfer requirements.
- Production and development environments.
- A security inspection environment.
- High availability requirements.

### Recommended Architecture

A reasonable architecture would be:

```text
                 Corporate DC 1
                       |
                  Direct Connect
                       |
                       +--------+
                                |
                              DXGW
                                |
                                v
                         Transit Gateway
                       /      |       \
                      /       |        \
                 Prod VPCs Dev VPCs Security VPC
                      \
                       \
                 Corporate DC 2
                       |
                  Direct Connect
```

VPN connections can provide backup connectivity:

```text
Corporate Network
       |
       +---- Direct Connect ----> TGW
       |
       +---- VPN ---------------> TGW
```

The exact topology should account for:

- Routing domains.
- BGP configuration.
- Route filtering.
- Failure domains.
- Security inspection.
- Data-transfer costs.
- Regional architecture.
- Operational ownership.

## Interview Scenario: Small Development Environment

Suppose a development team has one VPC and needs occasional access from a corporate network.

A full Direct Connect architecture may be unnecessarily complex.

A Site-to-Site VPN may be more appropriate:

```text
Developer Network
       |
       | VPN
       v
      VPC
```

The solution should be evaluated against:

- Traffic volume.
- Availability requirements.
- Security requirements.
- Latency requirements.
- Expected lifetime of the environment.

## Troubleshooting VPN Connectivity

Use a layered troubleshooting approach.

```text
VPN State
   |
   v
Tunnel State
   |
   v
BGP / Static Routes
   |
   v
VPC Route Table
   |
   v
TGW Route Table
   |
   v
Security Group
   |
   v
Network ACL
   |
   v
DNS
   |
   v
Application
```

Useful AWS CLI commands include:

```bash
aws ec2 describe-vpn-connections \
  --query 'VpnConnections[*].[VpnConnectionId,State,CustomerGatewayId,TransitGatewayId,VirtualPrivateGatewayId]' \
  --output table
```

Inspect VPN tunnel information:

```bash
aws ec2 describe-vpn-connections \
  --vpn-connection-ids vpn-xxxxxxxx \
  --query 'VpnConnections[*].VgwTelemetry' \
  --output table
```

Inspect route tables:

```bash
aws ec2 describe-route-tables \
  --output table
```

For Transit Gateway-based VPNs:

```bash
aws ec2 describe-transit-gateway-attachments \
  --query 'TransitGatewayAttachments[*].[TransitGatewayAttachmentId,ResourceType,ResourceId,State]' \
  --output table
```

Inspect TGW routes:

```bash
aws ec2 search-transit-gateway-routes \
  --transit-gateway-route-table-id tgw-rtb-xxxxxxxx \
  --filters Name=state,Values=active \
  --output table
```

## Troubleshooting Direct Connect

Check the connectivity layers in order:

```text
Physical Connection
       |
       v
Virtual Interface
       |
       v
BGP Session
       |
       v
Direct Connect Gateway
       |
       v
Transit Gateway / VGW
       |
       v
VPC Route Table
       |
       v
Security Controls
       |
       v
Application
```

The exact command set depends on the Direct Connect architecture.

Useful AWS CLI commands include:

```bash
aws directconnect describe-connections \
  --output table
```

List virtual interfaces:

```bash
aws directconnect describe-virtual-interfaces \
  --output table
```

Inspect a specific virtual interface:

```bash
aws directconnect describe-virtual-interfaces \
  --virtual-interface-id dxvif-xxxxxxxx \
  --output json
```

The most important fields to inspect include:

- Connection state.
- Virtual interface state.
- BGP state.
- BGP ASN.
- Advertised routes.
- Learned routes.
- VLAN configuration.
- Gateway associations.

## Monitoring Hybrid Connectivity

Production monitoring should cover both network infrastructure and application behavior.

Useful signals include:

| Layer | Useful Signal |
|---|---|
| VPN | Tunnel state |
| VPN | Tunnel telemetry |
| BGP | Session state |
| Direct Connect | Connection state |
| Direct Connect | Virtual interface state |
| Direct Connect | BGP state |
| TGW | Attachment state |
| TGW | Route state |
| VPC | Flow Logs |
| Application | Request failures/timeouts |
| DNS | Resolution failures |

VPC Flow Logs can help determine whether traffic is reaching an ENI and whether it is being accepted or rejected at the VPC networking layer.

## Security Best Practices

### Encrypt Sensitive Application Traffic

Even when using Direct Connect, application protocols should generally use encryption such as TLS.

For example:

```text
Client
  |
 HTTPS / TLS
  |
Hybrid Network
  |
  v
Application
```

Do not assume that private network connectivity eliminates the need for application-level encryption.

### Restrict Security Groups

Avoid:

```text
0.0.0.0/0
```

for internal services when a narrower source range is sufficient.

Prefer:

```text
10.100.0.0/16
```

or an appropriate security-group reference where supported by the architecture.

### Control Route Propagation

Do not advertise every network to every routing domain without an explicit requirement.

A production network should follow least-privilege principles at the routing layer.

## Scalability Considerations

For small hybrid environments:

```text
VPC
 |
VPN
 |
On-Prem
```

may be sufficient.

As the architecture grows:

```text
                    Transit Gateway
                  /       |       \
                VPC      VPC      VPC
                  |
             DX / VPN
                  |
              On-Prem
```

becomes easier to operate.

At enterprise scale, design around:

- Centralized routing.
- Route domains.
- BGP.
- Redundant connections.
- Account boundaries.
- Region boundaries.
- Monitoring.
- Automation.

## Cost Considerations

When comparing VPN and Direct Connect, consider total cost rather than only connectivity pricing.

Factors include:

- VPN hourly charges.
- Direct Connect port charges.
- Colocation/provider costs.
- Transit Gateway attachment costs.
- Transit Gateway data processing.
- Data transfer.
- Cross-region traffic.
- Network security appliances.
- Operational costs.

A high-volume workload may justify Direct Connect even when its infrastructure cost is higher because predictable dedicated connectivity can be operationally valuable.

## Common Production Mistakes

### Using a Single VPN Tunnel

A single tunnel creates unnecessary availability risk.

Use the redundant tunnel design provided by AWS and consider redundancy on the customer side.

### Assuming Direct Connect Is Automatically Encrypted

Direct Connect provides dedicated connectivity, not automatic end-to-end application encryption.

Design encryption separately where required.

### Ignoring BGP

For large hybrid networks, manually maintaining every route becomes difficult.

Use dynamic routing where appropriate.

### Forgetting Return Routes

Always validate both directions:

```text
AWS → On-Prem
On-Prem → AWS
```

### Ignoring Route Propagation

A BGP session can be established while application traffic still fails because the relevant route is not available in the required routing table.

### Treating VPN as "Private Internet"

VPN provides encrypted tunnels over an underlying IP network. It does not create a physically dedicated network connection.

### Treating Direct Connect as a Complete Network Architecture

Direct Connect is a connectivity primitive.

A production design still requires:

- Routing.
- BGP.
- Gateway associations.
- Security controls.
- High availability.
- Monitoring.
- Failure handling.

## Interview Traps

### "VPN Is Always Less Secure Than Direct Connect"

Too simplistic.

VPN provides IPsec encryption.

Direct Connect provides dedicated connectivity but does not automatically encrypt application traffic.

Security depends on the complete architecture.

### "Direct Connect Replaces Transit Gateway"

Incorrect.

They solve different problems.

```text
Direct Connect
    =
Connectivity into AWS

Transit Gateway
    =
Centralized routing between networks
```

They are often used together.

### "Transit Gateway Makes Every VPC Reachable"

Incorrect.

Routing tables, associations, propagation, and security controls determine actual connectivity.

### "BGP Means Automatic Failover"

Incomplete.

BGP enables dynamic route exchange and can support failover, but route advertisements and path-selection policies must be designed correctly.

### "VPN Is Only for Small Environments"

Incorrect.

VPN can be used in large architectures, particularly as backup connectivity or when its performance and cost characteristics meet requirements.

## Senior-Level Design Principles

A senior engineer should evaluate hybrid connectivity using the entire network path:

```text
Physical Connectivity
        +
Routing
        +
Encryption
        +
Security
        +
Availability
        +
Observability
        +
Cost
```

Do not evaluate VPN or Direct Connect as isolated AWS services.

For example, a highly available Direct Connect connection is not enough if:

```text
Direct Connect
      |
      v
Single Router
      |
      v
Single Firewall
      |
      v
Single VPC Subnet
```

creates multiple other single points of failure.

Similarly, a redundant VPN is not useful if the customer network has only one physical uplink.

## Key Takeaways

- **Site-to-Site VPN provides encrypted IPsec connectivity over an underlying IP network, while Direct Connect provides dedicated/private connectivity without automatically encrypting application traffic.**
- **Transit Gateway commonly acts as the centralized routing layer for VPN and Direct Connect connectivity to multiple VPCs.**
- **Production hybrid architectures should use redundant network paths and validate routing, BGP, security controls, and return traffic rather than relying on connectivity status alone.**
- **Direct Connect is generally suited to high-volume, predictable, long-term hybrid connectivity, while VPN is faster to deploy and often more cost-effective for simpler or backup scenarios.**
- **VPN, Direct Connect, and Transit Gateway solve different problems and are frequently combined rather than treated as mutually exclusive alternatives.**