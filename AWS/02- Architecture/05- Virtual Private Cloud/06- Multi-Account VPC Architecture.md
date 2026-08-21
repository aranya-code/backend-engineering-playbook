# 06- Multi-Account VPC Architecture

## Overview

A multi-account VPC architecture distributes workloads across multiple AWS accounts while providing controlled network connectivity between them.

This design is common in production AWS environments because an AWS account provides a strong administrative and security boundary. Instead of placing development, staging, production, shared services, security tooling, and networking infrastructure into one account, organizations can isolate them and explicitly control how they communicate.

A typical enterprise environment may contain:

```text
AWS Organization
│
├── Security Account
├── Network Account
├── Shared Services Account
├── Development Account
├── Staging Account
├── Production Account
└── Data / Analytics Accounts
```

Each workload account can contain one or more VPCs.

The network architecture must therefore solve two separate problems:

1. **Account isolation**
2. **Controlled cross-account connectivity**

The goal is not to connect every VPC to every other VPC. The goal is to establish the minimum connectivity required by the business and application architecture.

---

## Why Use Multiple AWS Accounts?

A single AWS account can host many VPCs, but account-level separation provides stronger operational boundaries.

Common reasons include:

- Production isolation
- Security boundary separation
- Independent IAM administration
- Reduced blast radius
- Separate billing and cost allocation
- Regulatory isolation
- Environment separation
- Delegated team ownership
- Centralized security controls
- Independent service quotas and limits

For example:

```text
Development Account
    |
    +---- Development VPC
    |
    +---- Development workloads


Production Account
    |
    +---- Production VPC
    |
    +---- Production workloads
```

A mistake in development should not automatically provide administrative access to production infrastructure.

---

## Account Isolation vs Network Isolation

These concepts are related but different.

### Account Isolation

Provides a boundary around:

- IAM policies
- Resources
- Billing
- Service quotas
- Administrative permissions
- Security controls

### Network Isolation

Controls:

- IP connectivity
- Routing
- Security Groups
- Network ACLs
- DNS
- Network inspection
- Traffic paths

A production account can still communicate with a development account if explicit network connectivity is configured.

Therefore:

> An AWS account boundary is not automatically a network boundary, and network connectivity should never be assumed simply because accounts belong to the same organization.

---

## Reference Architecture

A common enterprise topology uses a dedicated network account.

```mermaid
flowchart TB
    ORG["AWS Organization"]

    subgraph NET["Network Account"]
        TGW["Transit Gateway"]
        DNS["Centralized Private DNS"]
        INSPECT["Network Inspection"]
    end

    subgraph DEV["Development Account"]
        DEVVPC["Development VPC"]
        DEVAPP["Development Services"]
    end

    subgraph STG["Staging Account"]
        STGVPC["Staging VPC"]
        STGAPP["Staging Services"]
    end

    subgraph PROD["Production Account"]
        PRODVPC["Production VPC"]
        PRODAPP["Production Services"]
    end

    subgraph SHARED["Shared Services Account"]
        SHAREDVPC["Shared Services VPC"]
        TOOLS["Internal Tools"]
    end

    DEVVPC --> TGW
    STGVPC --> TGW
    PRODVPC --> TGW
    SHAREDVPC --> TGW

    TGW --> DNS
    TGW --> INSPECT
```

The network account owns centralized networking infrastructure while application teams retain ownership of their workload VPCs.

---

## AWS Organizations Structure

A multi-account VPC design usually starts with AWS Organizations.

A simplified organizational structure may look like:

```text
Root
│
├── Security OU
│   ├── Security Account
│   └── Log Archive Account
│
├── Infrastructure OU
│   ├── Network Account
│   └── Shared Services Account
│
├── Workloads OU
│   ├── Development Account
│   ├── Staging Account
│   └── Production Account
│
└── Sandbox OU
    └── Developer Sandbox Accounts
```

Organizational Units can be used to apply policies consistently.

For example, production accounts may receive stricter controls than sandbox accounts.

---

## Dedicated Network Account

A dedicated network account centralizes infrastructure that should be managed independently of application teams.

Typical resources include:

- Transit Gateway
- Network Firewall
- DNS infrastructure
- Centralized egress
- Inspection VPCs
- VPN connections
- Direct Connect integration
- Shared networking services

Example:

```text
                    Network Account
                          |
                 +--------+--------+
                 |                 |
            Transit Gateway   Inspection VPC
                 |
       +---------+---------+
       |         |         |
      Dev      Staging    Prod
```

This separates network administration from application administration.

---

## Transit Gateway

AWS Transit Gateway is commonly used as the central routing hub for multi-account VPC connectivity.

Instead of creating individual connections between every VPC:

```text
VPC A <----> VPC B
VPC A <----> VPC C
VPC A <----> VPC D
VPC B <----> VPC C
VPC B <----> VPC D
...
```

use:

```text
             VPC A
               |
               |
VPC B ---- Transit Gateway ---- VPC C
               |
               |
             VPC D
```

This provides a hub-and-spoke topology.

---

## Why Transit Gateway Matters

Without a centralized routing layer, network complexity grows rapidly as the number of VPCs increases.

For `N` VPCs, a full mesh can require approximately:

```text
N × (N - 1) / 2
```

pairwise relationships.

For example:

| VPCs | Full-Mesh Relationships |
|---:|---:|
| 3 | 3 |
| 5 | 10 |
| 10 | 45 |
| 20 | 190 |
| 50 | 1,225 |

Transit Gateway reduces this relationship complexity by providing a central routing layer.

However, Transit Gateway does not automatically mean every attached VPC should communicate with every other VPC.

---

## Transit Gateway Attachments

A VPC connects to Transit Gateway through a VPC attachment.

Conceptually:

```text
Production VPC
     |
     | TGW Attachment
     v
Transit Gateway
```

The VPC must have appropriate subnet routing toward the Transit Gateway.

Example route:

```text
Destination       Target
--------------------------------
10.0.0.0/8        tgw-xxxxxxxx
```

The Transit Gateway then determines whether the destination network is reachable.

---

## Transit Gateway Route Tables

Transit Gateway route tables provide traffic segmentation.

For example:

```text
Production TGW Route Table
```

may contain only routes required by production.

A separate route table could handle shared services:

```text
Shared Services TGW Route Table
```

This enables network segmentation without requiring every VPC to communicate with every other VPC.

---

## Environment Segmentation

A strong multi-account architecture usually separates environments.

For example:

```text
Development
     |
     X
Production

Development
     |
     v
Shared Services

Production
     |
     v
Shared Services
```

The exact policy depends on organizational requirements.

Production should not generally depend directly on development resources.

---

## Example Routing Model

Consider:

```text
10.10.0.0/16  Development
10.20.0.0/16  Staging
10.30.0.0/16  Production
10.40.0.0/16  Shared Services
```

A reasonable policy might be:

| Source | Destination | Allowed |
|---|---|---|
| Development | Shared Services | Yes |
| Staging | Shared Services | Yes |
| Production | Shared Services | Yes |
| Development | Production | No |
| Staging | Production | No |
| Production | Development | No |
| Development | Staging | Usually no |

The network should implement intentional connectivity rather than simply providing universal reachability.

---

## VPC CIDR Planning Across Accounts

CIDR planning becomes more important as the number of VPCs grows.

Overlapping CIDRs can make routing between VPCs difficult or impossible.

Avoid:

```text
Development VPC
10.0.0.0/16

Production VPC
10.0.0.0/16
```

when direct connectivity is required.

Prefer a centrally managed allocation strategy.

Example:

```text
10.0.0.0/16    Shared Services
10.10.0.0/16   Development
10.20.0.0/16   Staging
10.30.0.0/16   Production
10.40.0.0/16   Data
10.50.0.0/16   Security
```

The actual addressing scheme should be designed around organizational scale and future expansion.

---

## CIDR Allocation Strategy

A useful allocation strategy is to reserve address ranges by environment, business unit, region, or account.

For example:

```text
10.0.0.0/8
│
├── 10.0.0.0/12    Production
├── 10.16.0.0/12   Staging
├── 10.32.0.0/12   Development
├── 10.48.0.0/12   Shared Services
└── 10.64.0.0/12   Future
```

Within each allocation:

```text
Production
│
├── Region A
│   ├── VPC 1
│   └── VPC 2
│
└── Region B
    ├── VPC 1
    └── VPC 2
```

The goal is predictable summarization and future growth.

---

## VPC Peering vs Transit Gateway

VPC Peering provides direct private connectivity between two VPCs.

```text
VPC A <---- VPC Peering ----> VPC B
```

It is useful for limited connectivity.

Transit Gateway is more appropriate when many VPCs or networks need centralized connectivity.

| Feature | VPC Peering | Transit Gateway |
|---|---|---|
| Topology | Point-to-point | Hub-and-spoke |
| Large-scale networking | Less suitable | Suitable |
| Centralized routing | Limited | Strong |
| Network segmentation | Limited | Strong |
| Multi-account | Supported | Supported |
| Operational complexity | Grows with peers | More centralized |
| Cost model | Per connection/data | TGW processing + attachments/data |

A common mistake is using VPC Peering as the default architecture for a rapidly growing organization.

---

## Shared Services VPC

A shared services account can host services used by multiple application accounts.

Example:

```text
                 Transit Gateway
                       |
        +--------------+--------------+
        |              |              |
      Dev            Staging         Prod
        \              |              /
         \             |             /
          +------ Shared Services ---+
```

Potential shared services include:

- Internal DNS
- CI/CD infrastructure
- Artifact repositories
- Monitoring
- Logging
- Security tooling
- Internal APIs
- Bastion replacement tooling
- Developer platforms

Not every shared service should necessarily be centralized. Centralization should be based on operational ownership, security, latency, and failure-domain requirements.

---

## Shared Services With PrivateLink

AWS PrivateLink can expose selected services privately without providing broad network connectivity.

Example:

```text
Application Account
       |
       v
Interface Endpoint
       |
       v
PrivateLink
       |
       v
Shared Service
```

This is useful when consumers need access to one service but should not receive network-level access to the entire provider VPC.

PrivateLink is therefore an important complement to Transit Gateway.

---

## Transit Gateway vs PrivateLink

These mechanisms solve different problems.

| Requirement | Preferred Mechanism |
|---|---|
| Route between VPC networks | Transit Gateway |
| Expose one service privately | PrivateLink |
| Connect two small VPCs | VPC Peering |
| Connect on-premises networks | VPN / Direct Connect + TGW |
| Centralize network routing | Transit Gateway |
| Service-provider style architecture | PrivateLink |

Think of Transit Gateway as **network connectivity** and PrivateLink as **service connectivity**.

---

## Centralized Network Inspection

Security-sensitive organizations may route traffic through a dedicated inspection VPC.

Example:

```text
Application VPC
      |
      v
Transit Gateway
      |
      v
Inspection VPC
      |
      v
Firewall
      |
      v
Destination
```

The inspection layer can provide:

- Network Firewall
- Third-party firewalls
- Traffic inspection
- IDS/IPS
- Egress filtering

Centralized inspection increases control but also increases architecture complexity.

---

## Centralized Egress

A common enterprise pattern centralizes Internet egress.

```text
Application VPC
      |
      v
Transit Gateway
      |
      v
Egress VPC
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

This can simplify:

- Egress policy
- IP allowlisting
- Monitoring
- Security inspection
- Internet access governance

However, the design must account for:

- Cross-AZ traffic
- NAT capacity
- Failure handling
- Routing complexity
- Data-transfer costs

---

## Private-Only Workload Accounts

Workload VPCs can remain private while still consuming shared services.

Example:

```text
Production Account
       |
   Private VPC
       |
       +---- TGW ---- Shared Services
       |
       +---- Endpoint ---- AWS Services
       |
       +---- TGW ---- Corporate Network
```

The workload account does not need to own:

- Internet Gateway
- Public IP addresses
- Public load balancers

unless its specific workload requires them.

---

## AWS Resource Access Across Accounts

Networking and IAM are separate concerns.

A service may require both:

```text
Network Connectivity
+
IAM Authorization
```

For example, an application in Account A accessing an S3 bucket in Account B may require:

- Network connectivity if using a private path
- IAM permissions
- Resource-based bucket policy

Successful routing does not imply authorization.

Likewise, correct IAM permissions do not create network connectivity.

---

## Cross-Account Security Groups

AWS supports cross-account Security Group references in certain networking configurations.

This can allow a rule such as:

```text
Database SG
Source: Application SG
Port: 5432
```

instead of:

```text
Database SG
Source: 10.10.0.0/16
Port: 5432
```

Security Group references are generally more expressive than broad CIDR-based rules because they describe workload identity at the network-control layer.

Always verify the supported topology and service-specific constraints before depending on cross-account Security Group references.

---

## Cross-Account DNS

DNS becomes increasingly important in multi-account architectures.

A centralized DNS design may provide:

```text
internal.example.com
│
├── orders.internal.example.com
├── payments.internal.example.com
├── users.internal.example.com
└── platform.internal.example.com
```

Route 53 Resolver can be used to forward DNS queries between VPCs and connected networks.

A centralized DNS architecture can avoid duplicating DNS logic across dozens of accounts.

---

## Route 53 Resolver

A centralized architecture can use:

```text
Workload VPC
      |
      v
Route 53 Resolver
      |
      v
Shared DNS
```

Resolver endpoints and forwarding rules can support communication with:

- On-premises DNS
- Other AWS VPCs
- Corporate domains
- Private hosted zones

DNS should be treated as a core dependency rather than an afterthought.

---

## Multi-Region Considerations

Multi-account architecture frequently expands into multiple AWS Regions.

For example:

```text
Region A
├── Production Account
├── Shared Services
└── Network Account

Region B
├── Production Account
├── Shared Services
└── Network Account
```

Cross-region connectivity introduces additional considerations:

- CIDR planning
- Transit Gateway peering
- Latency
- Data transfer costs
- Regional failure scenarios
- DNS behavior
- Application data replication

Do not assume a single-region routing model can simply be copied across regions.

---

## Multi-Region Network Architecture

A simplified design:

```mermaid
flowchart LR
    TGWA["Transit Gateway - Region A"]
    TGWB["Transit Gateway - Region B"]

    PRODA["Production VPC - Region A"]
    PRODB["Production VPC - Region B"]

    SHAREA["Shared Services - Region A"]
    SHARED_B["Shared Services - Region B"]

    PRODA --> TGWA
    SHAREA --> TGWA

    PRODB --> TGWB
    SHARED_B --> TGWB

    TGWA <-->|Inter-Region Connectivity| TGWB
```

Traffic should remain regional when possible.

Cross-region communication should be intentional.

---

## Account-Level Network Responsibilities

A useful ownership model is:

| Component | Typical Owner |
|---|---|
| AWS Organizations | Platform / Cloud Team |
| Transit Gateway | Network Team |
| Network Firewall | Security / Network Team |
| Workload VPC | Application / Platform Team |
| Application Security Groups | Application Team |
| Shared DNS | Network / Platform Team |
| Application DNS records | Application Team |
| VPC Endpoints | Platform / Network Team |
| NAT / Egress | Network Team |
| Application resources | Application Team |

The exact ownership model depends on organizational structure.

The important principle is explicit responsibility.

---

## Landing Zone Integration

A multi-account VPC architecture often forms part of a larger AWS landing zone.

A landing zone may standardize:

- Account creation
- Organizational Units
- IAM
- Logging
- Security controls
- Networking
- Guardrails
- Billing
- Monitoring

The network architecture should be designed as part of this broader operating model rather than as an isolated VPC project.

---

## Infrastructure as Code

Multi-account networking should be managed through Infrastructure as Code.

Suitable technologies include:

- Terraform
- AWS CloudFormation
- AWS CDK
- AWS Control Tower integrations
- CI/CD pipelines

A simplified Terraform structure might be:

```text
infrastructure/
├── accounts/
│   ├── development/
│   ├── staging/
│   └── production/
│
├── networking/
│   ├── transit-gateway/
│   ├── dns/
│   ├── inspection/
│   └── egress/
│
└── modules/
    ├── vpc/
    ├── subnet/
    └── endpoint/
```

The exact repository structure should reflect the organization's deployment model.

---

## Deployment Pipeline

Network changes should be reviewed like application code.

A typical workflow:

```text
Developer
   |
   v
Git Commit
   |
   v
Pull Request
   |
   v
Terraform Plan
   |
   v
Security / Network Review
   |
   v
Approval
   |
   v
Terraform Apply
```

Network changes can affect multiple production accounts, so automated validation and controlled deployment are important.

---

## Security Best Practices

### Minimize Cross-Account Connectivity

Do not connect every VPC to every other VPC simply because Transit Gateway makes it easy.

### Segment Transit Gateway Route Tables

Use route tables to establish explicit connectivity domains.

### Avoid Overlapping CIDRs

CIDR conflicts can become a long-term architectural constraint.

### Separate Network Administration

Network infrastructure should not depend on permissions granted to application developers.

### Use Least-Privilege IAM

Network administrators should receive only the permissions required for network management.

### Centralize Logging

Collect:

- VPC Flow Logs
- CloudTrail
- DNS query logs where appropriate
- Firewall logs
- Transit Gateway-related telemetry

### Encrypt Sensitive Traffic

Private networking does not eliminate the need for encryption.

Use:

- TLS
- mTLS where appropriate
- IPsec VPN
- Service-level encryption

---

## Scalability Considerations

As the number of accounts grows, network architecture must scale operationally.

Consider:

- CIDR allocation automation
- Automated VPC provisioning
- Transit Gateway attachment workflows
- Centralized DNS
- Standard subnet patterns
- Standard Security Group patterns
- Automated endpoint provisioning
- Network policy validation

A design that works for five accounts may become difficult to operate at fifty or five hundred accounts.

---

## Reliability Considerations

Network infrastructure is production infrastructure.

Design for:

- Multi-AZ routing
- Redundant VPN connectivity
- Redundant Direct Connect paths where required
- Resilient Transit Gateway architecture
- Multiple NAT Gateways when centralized egress is used
- Multiple inspection paths where required
- DNS redundancy
- Tested failure scenarios

The application should not depend on a single network appliance or Availability Zone.

---

## Cost Considerations

Multi-account networking introduces additional costs.

Potential cost sources include:

- Transit Gateway attachments
- Transit Gateway data processing
- VPC interface endpoints
- NAT Gateways
- Cross-AZ traffic
- Cross-region traffic
- VPN connections
- Direct Connect
- Network Firewall
- Third-party firewall appliances

Cost analysis should follow traffic patterns rather than simply counting resources.

For example:

```text
Application VPC
      |
      v
TGW
      |
      v
Central Egress VPC
      |
      v
NAT
```

may create additional data-processing and cross-AZ charges compared with local egress.

---

## Monitoring and Observability

Monitor the network at multiple layers.

### VPC

- VPC Flow Logs
- Route tables
- Subnet utilization
- Endpoint usage
- NAT metrics

### Transit Gateway

Monitor:

- Attachment health
- Bytes processed
- Packet counts
- Route propagation
- Route-table configuration

### DNS

Monitor:

- Resolver errors
- Query latency
- Forwarding failures
- Private hosted zone resolution

### Security

Monitor:

- Rejected flows
- Firewall events
- Unexpected cross-account traffic
- Unauthorized configuration changes

### Operations

Use AWS CloudTrail to identify:

- Route changes
- Attachment changes
- Security Group modifications
- Network policy changes

---

## Troubleshooting Cross-Account Connectivity

Use a deterministic troubleshooting process.

### Verify CIDR Ranges

Check whether source and destination CIDRs overlap.

### Verify VPC Attachment

Confirm that the VPC has an active Transit Gateway attachment.

### Verify Subnet Routes

The workload subnet must have a route toward the Transit Gateway.

### Verify Transit Gateway Route Table

Confirm the destination route exists.

### Verify Return Path

The destination must have a route back to the source.

### Verify Security Groups

Confirm the destination allows the source.

### Verify Network ACLs

Check both inbound and outbound subnet-level rules.

### Verify DNS

Confirm the hostname resolves to the expected private address.

### Verify Flow Logs

Determine whether traffic is being accepted or rejected.

---

## Common Mistakes

### Treating Transit Gateway as Full-Mesh Connectivity

A Transit Gateway is a routing hub, not a requirement that all networks communicate.

Use route tables to enforce segmentation.

### Overlapping CIDRs

Two VPCs with overlapping address space can make future connectivity difficult.

CIDR planning should happen before VPC creation.

### Centralizing Everything

Not every workload needs to traverse centralized infrastructure.

Centralization can introduce:

- Latency
- Cost
- Operational dependencies
- Additional failure modes

### Allowing Broad Cross-Account Access

Avoid:

```text
Production
    |
    +---- All VPCs
```

when only one service dependency is required.

### Mixing Environment Traffic

Development should not automatically have access to production.

### Ignoring DNS

A correct route does not help if the application cannot resolve the destination.

### Treating IAM and Networking as the Same Control

Network connectivity and authorization are separate controls.

### Manual Configuration

Manual changes across many accounts are difficult to audit and reproduce.

Use Infrastructure as Code.

---

## Interview Traps

### "Does a Transit Gateway Make All VPCs Reachable?"

No.

VPC attachments and Transit Gateway route tables determine which networks can communicate.

### "Does Being in the Same AWS Organization Allow Network Communication?"

No.

Organization membership does not create network connectivity.

### "Can Two VPCs Have the Same CIDR?"

They can exist independently, but overlapping CIDRs create significant limitations for direct routing between them.

### "Is PrivateLink a Replacement for Transit Gateway?"

No.

PrivateLink provides private service access, while Transit Gateway provides network-level connectivity.

### "Does IAM Permission Create Network Access?"

No.

IAM controls authorization to AWS resources and APIs. Network routing and network controls determine whether packets can reach a destination.

### "Is a Private VPC Completely Isolated?"

Not necessarily.

It can communicate with other private networks, AWS services, corporate networks, and even the Internet through controlled egress paths.

---

## Production Architecture Example

Consider an organization running Django, FastAPI, PostgreSQL, Redis, Kafka, and Kubernetes workloads.

```text
                         AWS Organization
                                |
                +---------------+---------------+
                |               |               |
          Dev Account     Staging Account   Prod Account
                |               |               |
             VPC Dev         VPC Staging      VPC Prod
                |               |               |
                +---------------+---------------+
                                |
                         Transit Gateway
                                |
                +---------------+---------------+
                |               |               |
          Shared Services   Inspection       Egress
              VPC              VPC             VPC
                |               |               |
             DNS/Tools       Firewall          NAT
                |
          PrivateLink Services
```

Workload VPCs remain independently owned while the network layer provides controlled connectivity.

A production application might then look like:

```text
Internal Client
      |
      v
Private DNS
      |
      v
Internal ALB
      |
      v
Kubernetes / ECS / EC2
      |
      +---- PostgreSQL
      |
      +---- Redis
      |
      +---- Kafka
      |
      +---- AWS VPC Endpoints
      |
      +---- Shared Services
```

The production workload does not need unrestricted connectivity to development resources.

---

## Recommended Design Principles

A mature multi-account VPC architecture should follow these principles:

1. **Separate environments and trust boundaries.**
2. **Centralize networking where centralization provides operational value.**
3. **Keep workload ownership inside workload accounts.**
4. **Use Transit Gateway for scalable network connectivity.**
5. **Use PrivateLink when only service-level access is required.**
6. **Plan CIDRs centrally before creating VPCs.**
7. **Use private DNS consistently.**
8. **Minimize cross-account connectivity.**
9. **Automate networking through Infrastructure as Code.**
10. **Monitor and audit network changes continuously.**

---

## Key Takeaways

- Multi-account VPC architecture uses AWS accounts as administrative and security boundaries while providing controlled network connectivity through services such as Transit Gateway, VPC Peering, and PrivateLink.
- Transit Gateway simplifies large-scale routing, but route tables must still enforce explicit segmentation between development, staging, production, shared services, and other network domains.
- Centralized CIDR planning, DNS, egress, inspection, and networking ownership become increasingly important as the number of AWS accounts and VPCs grows.
- IAM authorization and network connectivity are separate controls; successful routing does not grant resource access, and IAM permission does not create network reachability.
- Production multi-account networking should be Multi-AZ, observable, least-privilege, Infrastructure-as-Code managed, and designed around explicit connectivity requirements rather than unrestricted network reachability.