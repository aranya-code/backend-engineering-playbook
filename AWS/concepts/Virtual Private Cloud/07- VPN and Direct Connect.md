# VPN and Direct Connect

AWS provides two primary methods for connecting on-premises data centers to AWS: **Site-to-Site VPN** (encrypted tunnel over the public internet) and **AWS Direct Connect** (dedicated private network connection). Both enable hybrid cloud architectures, but they differ significantly in performance, cost, reliability, and setup time.

Understanding these options is critical for designing hybrid connectivity, disaster recovery, and enterprise migration architectures.

---

# Site-to-Site VPN

## What is Site-to-Site VPN?

A Site-to-Site VPN creates an **encrypted IPsec tunnel** between your on-premises network and your AWS VPC over the public internet.

## Components

| Component | Description |
|-----------|-------------|
| **Virtual Private Gateway (VGW)** | AWS-side VPN endpoint, attached to a VPC |
| **Customer Gateway (CGW)** | On-premises VPN device (router/firewall) |
| **VPN Connection** | Two IPsec tunnels (for HA) between VGW and CGW |

## Architecture

```text
On-Premises Data Center              AWS Cloud
┌──────────────────┐                 ┌──────────────────┐
│                  │                 │       VPC        │
│  Customer        │   IPsec VPN    │                  │
│  Gateway     ════╪═══════════════╪═══ Virtual       │
│  (Router)    ════╪═══════════════╪═══ Private       │
│                  │  2 Tunnels     │    Gateway       │
│  Servers         │  (for HA)      │                  │
│                  │                 │  EC2 / RDS       │
└──────────────────┘                 └──────────────────┘
        │                                    │
     Public Internet                  AWS Backbone
```

## Key Characteristics

- **Quick setup** — can be configured in minutes
- **Encrypted** — IPsec encryption for all traffic
- **Two tunnels** — for redundancy (active-passive or active-active)
- **Uses public internet** — performance depends on internet quality
- **Bandwidth** — up to 1.25 Gbps per VPN tunnel
- **Cost** — ~$0.05/hour per VPN connection + data transfer

## Limitations

- Performance depends on public internet quality
- Latency is variable and unpredictable
- 1.25 Gbps maximum per tunnel
- Not suitable for latency-sensitive or high-bandwidth workloads

---

# AWS Direct Connect

## What is Direct Connect?

AWS Direct Connect establishes a **dedicated private network connection** between your data center and AWS, bypassing the public internet entirely.

## Key Characteristics

- **Dedicated connection** — physical fiber connection to AWS
- **Private** — traffic never traverses the public internet
- **Consistent performance** — predictable latency and throughput
- **High bandwidth** — 1 Gbps, 10 Gbps, or 100 Gbps dedicated connections
- **Setup time** — weeks to months (physical infrastructure required)
- **Cost** — port-hour charges + data transfer out

## Connection Types

| Type | Bandwidth | Use Case |
|------|-----------|----------|
| **Dedicated** | 1 Gbps, 10 Gbps, 100 Gbps | Large enterprise, high volume |
| **Hosted** | 50 Mbps – 10 Gbps | Smaller workloads, through partners |

## Architecture

```text
On-Premises            DX Location           AWS
┌──────────┐         ┌──────────┐         ┌──────────┐
│          │         │          │         │          │
│  Data    │  Fiber  │  AWS     │  Fiber  │  AWS     │
│  Center  ├────────►│  Direct  ├────────►│  Region  │
│          │         │  Connect │         │          │
│  Router  │         │  Router  │         │  VPC     │
│          │         │          │         │          │
└──────────┘         └──────────┘         └──────────┘
                    (Colocation Facility)
```

## Virtual Interfaces (VIFs)

Direct Connect uses virtual interfaces to access AWS resources:

| VIF Type | Purpose | Access To |
|----------|---------|-----------|
| **Private VIF** | Connect to VPCs | Resources in private subnets via VGW or Direct Connect Gateway |
| **Public VIF** | Connect to public AWS services | S3, DynamoDB, public endpoints |
| **Transit VIF** | Connect to Transit Gateway | Multiple VPCs via Transit Gateway |

---

# VPN vs Direct Connect Comparison

| Feature | Site-to-Site VPN | Direct Connect |
|---------|-----------------|----------------|
| **Connection** | Over public internet | Dedicated private fiber |
| **Encryption** | IPsec (built-in) | Not encrypted by default |
| **Bandwidth** | Up to 1.25 Gbps/tunnel | 1/10/100 Gbps |
| **Latency** | Variable | Consistent, low |
| **Setup time** | Minutes | Weeks to months |
| **Redundancy** | 2 tunnels per connection | Must order 2 connections |
| **Cost** | Low (~$0.05/hr) | Higher (port + data transfer) |
| **Best for** | Quick setup, backup, low bandwidth | High bandwidth, consistent performance |

---

# Hybrid Architecture Patterns

## Pattern 1: VPN Only (Simple/Low Cost)

```text
On-Premises ═══ VPN ═══ VPC
```

Best for: Development, testing, low-bandwidth production.

## Pattern 2: Direct Connect Only (Performance)

```text
On-Premises ─── DX ─── VPC
```

Best for: Large data transfers, latency-sensitive applications.

## Pattern 3: Direct Connect + VPN Backup (Recommended)

```text
On-Premises ─── DX (Primary) ──── VPC
On-Premises ═══ VPN (Backup) ════ VPC
```

Best for: Production workloads requiring high availability and consistent performance. If Direct Connect fails, VPN provides automatic failover.

## Pattern 4: Direct Connect + VPN Encryption

```text
On-Premises ═══ VPN over DX ═══ VPC
```

Run a VPN connection **over** Direct Connect for encryption. Direct Connect itself does not encrypt traffic. This provides both dedicated bandwidth and encryption.

---

# Direct Connect Gateway

A Direct Connect Gateway connects a Direct Connect connection to **multiple VPCs across different regions**.

```text
On-Premises
     │
     ▼
Direct Connect
     │
     ▼
┌─────────────────────┐
│ DX Gateway (Global) │
└──────┬──────┬───────┘
       │      │
       ▼      ▼
    VPC A    VPC B
 (Mumbai)  (Virginia)
```

Without a DX Gateway, you would need a separate Direct Connect for each region.

---

# Key Takeaways

- **VPN** = quick, cheap, encrypted, but variable performance over public internet.
- **Direct Connect** = dedicated, consistent, high bandwidth, but expensive and slow to set up.
- Production best practice: **Direct Connect primary + VPN backup**.
- Direct Connect is **not encrypted** by default — run VPN over DX for encryption.
- Use **Virtual Interfaces** (VIFs) to access private VPCs, public services, or Transit Gateway.
- **Direct Connect Gateway** enables a single DX to reach VPCs in multiple regions.
- VPN can be set up in minutes; Direct Connect takes weeks to months.

---
