# VPC Peering and Transit Gateway

VPC Peering and Transit Gateway are the two primary methods for connecting multiple VPCs. VPC Peering creates a direct, one-to-one connection between two VPCs, while Transit Gateway acts as a central hub that connects multiple VPCs, VPNs, and Direct Connect in a hub-and-spoke model.

Choosing between them depends on the number of VPCs, network complexity, and operational requirements.

---

# VPC Peering

## What is VPC Peering?

A VPC Peering connection is a networking connection between two VPCs that enables routing traffic between them using private IP addresses. Both VPCs behave as if they are on the same network.

## Key Characteristics

- **One-to-one** — each peering connects exactly two VPCs
- **Non-transitive** — if VPC A peers with B, and B peers with C, A cannot reach C through B
- **Cross-account** — peering works across different AWS accounts
- **Cross-region** — peering works across different AWS regions (inter-region peering)
- **No bandwidth bottleneck** — uses AWS backbone infrastructure
- **Free** — no hourly charges (data transfer charges apply for cross-region)

## Requirements

- **Non-overlapping CIDR blocks** — the VPCs must have different IP ranges
- **Route table entries** — both VPCs must add routes pointing to the peering connection
- **Security group rules** — must explicitly allow traffic from the peered VPC

```text
VPC A (10.0.0.0/16)              VPC B (172.16.0.0/16)
┌──────────────────┐             ┌──────────────────┐
│                  │             │                  │
│  Route Table:    │  Peering    │  Route Table:    │
│  172.16.0.0/16   │◄───────────►│  10.0.0.0/16     │
│  → pcx-abc123    │  Connection │  → pcx-abc123    │
│                  │             │                  │
│  EC2 (10.0.1.5)  │             │  EC2 (172.16.1.5)│
└──────────────────┘             └──────────────────┘
```

## Non-Transitive Limitation

```text
VPC A ◄───Peering───► VPC B ◄───Peering───► VPC C

VPC A CANNOT reach VPC C through VPC B.
A separate A↔C peering is required.
```

For N VPCs, you need **N × (N-1) / 2** peering connections. This does not scale:

| VPCs | Peering Connections Needed |
|------|--------------------------|
| 3 | 3 |
| 5 | 10 |
| 10 | 45 |
| 20 | 190 |

---

# Transit Gateway

## What is Transit Gateway?

AWS Transit Gateway is a **regional network hub** that connects multiple VPCs, VPN connections, and Direct Connect gateways through a central point, using a hub-and-spoke model.

## Key Characteristics

- **Hub-and-spoke** — single attachment point for all VPCs and connections
- **Transitive routing** — all attached networks can communicate (if allowed)
- **Scales** — supports up to 5,000 attachments per TGW
- **Cross-account** — share via AWS RAM (Resource Access Manager)
- **Cross-region** — peer Transit Gateways across regions
- **Route tables** — TGW has its own route tables for traffic control
- **Charged** — hourly per attachment + data processing

## Architecture

```text
                    ┌─────────────────┐
                    │ Transit Gateway │
                    │    (Hub)        │
                    └────────┬────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
          ▼                  ▼                  ▼
   ┌──────────┐      ┌──────────┐      ┌──────────┐
   │  VPC A   │      │  VPC B   │      │  VPC C   │
   │ (Prod)   │      │ (Dev)    │      │ (Shared) │
   └──────────┘      └──────────┘      └──────────┘
          │                                     │
          ▼                                     ▼
   ┌──────────┐                          ┌──────────┐
   │ VPN      │                          │ Direct   │
   │ (On-Prem)│                          │ Connect  │
   └──────────┘                          └──────────┘
```

## TGW Route Tables

Transit Gateway uses its own route tables to control which VPCs can communicate:

```text
TGW Route Table (Production):
┌──────────────────┬──────────────────┐
│ Destination      │ Attachment       │
├──────────────────┼──────────────────┤
│ 10.0.0.0/16      │ VPC-A (Prod)     │
│ 172.16.0.0/16    │ VPC-C (Shared)   │
│ 192.168.0.0/16   │ VPN (On-Prem)    │
└──────────────────┴──────────────────┘

TGW Route Table (Development):
┌──────────────────┬──────────────────┐
│ Destination      │ Attachment       │
├──────────────────┼──────────────────┤
│ 10.1.0.0/16      │ VPC-B (Dev)      │
│ 172.16.0.0/16    │ VPC-C (Shared)   │
└──────────────────┴──────────────────┘
```

This allows production VPCs to access shared services and on-premises, while development VPCs can only access shared services — **network segmentation through routing**.

---

# VPC Peering vs Transit Gateway

| Feature | VPC Peering | Transit Gateway |
|---------|------------|----------------|
| **Model** | Point-to-point | Hub-and-spoke |
| **Transitive** | No | Yes |
| **Scalability** | Poor (N² connections) | Excellent (5,000 attachments) |
| **Cross-account** | Yes | Yes (via RAM) |
| **Cross-region** | Yes | Yes (TGW peering) |
| **Route tables** | VPC route tables | TGW route tables (centralized) |
| **VPN/DX integration** | No | Yes (direct attachment) |
| **Bandwidth** | No limit | Up to 50 Gbps per AZ |
| **Cost** | Free (data transfer charges) | ~$0.05/hr per attachment + data |
| **Best for** | 2-3 VPCs | 4+ VPCs, hybrid connectivity |

---

# When to Use Each

## Use VPC Peering When:

- You have **2-3 VPCs** that need to communicate
- You want **free** connectivity (no hourly charges)
- Simple, direct connections are sufficient
- No need for centralized routing or VPN integration

## Use Transit Gateway When:

- You have **4+ VPCs** or expect to grow
- You need **transitive routing** between VPCs
- You need **hybrid connectivity** (VPN, Direct Connect)
- You want **centralized network management** with TGW route tables
- You need **network segmentation** (prod vs dev isolation)
- Multi-account architecture with shared services

---

# Key Takeaways

- **VPC Peering** is free, simple, point-to-point, but non-transitive and doesn't scale.
- **Transit Gateway** is a paid, centralized hub supporting transitive routing and hybrid connectivity.
- VPC Peering requires N×(N-1)/2 connections; Transit Gateway needs N attachments.
- TGW route tables enable network segmentation (isolate prod from dev).
- Use VPC Peering for simple 2-3 VPC setups; use Transit Gateway for enterprise architectures.
- Both require non-overlapping CIDRs and explicit route table entries.

---
