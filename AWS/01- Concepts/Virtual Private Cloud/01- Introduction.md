# VPC — Introduction

Amazon Virtual Private Cloud (VPC) is a logically isolated virtual network within the AWS cloud where you deploy and run AWS resources. A VPC gives you complete control over your virtual networking environment — including IP address ranges, subnets, route tables, gateways, and security controls.

Every AWS account comes with a default VPC in each region, but production workloads should always use custom VPCs designed with proper network segmentation, security controls, and connectivity patterns.

---

# Why VPC Matters

Without a VPC, AWS resources would run on a flat, shared network with no isolation. VPC solves this by providing:

- **Network isolation** — Your resources are logically separated from other AWS customers
- **IP address control** — You define the CIDR ranges and subnet layout
- **Security boundaries** — Security groups and NACLs control traffic flow
- **Connectivity options** — Internet, VPN, Direct Connect, peering, Transit Gateway
- **Compliance** — Meet regulatory requirements for network segregation

---

# VPC Core Components

```text
┌─────────────────────────────────────────────────────────┐
│                        VPC                               │
│                   (10.0.0.0/16)                          │
│                                                          │
│   ┌─────────────────────┐  ┌─────────────────────┐     │
│   │   Public Subnet     │  │   Public Subnet     │     │
│   │   (10.0.1.0/24)     │  │   (10.0.2.0/24)     │     │
│   │   AZ: ap-south-1a   │  │   AZ: ap-south-1b   │     │
│   │                     │  │                     │     │
│   │   ┌─────┐  ┌─────┐ │  │   ┌─────┐           │     │
│   │   │ ALB │  │ NAT │ │  │   │ ALB │           │     │
│   │   └─────┘  └─────┘ │  │   └─────┘           │     │
│   └─────────────────────┘  └─────────────────────┘     │
│                                                          │
│   ┌─────────────────────┐  ┌─────────────────────┐     │
│   │   Private Subnet    │  │   Private Subnet    │     │
│   │   (10.0.3.0/24)     │  │   (10.0.4.0/24)     │     │
│   │   AZ: ap-south-1a   │  │   AZ: ap-south-1b   │     │
│   │                     │  │                     │     │
│   │   ┌─────┐  ┌─────┐ │  │   ┌─────┐  ┌─────┐ │     │
│   │   │ EC2 │  │ EC2 │ │  │   │ EC2 │  │ EC2 │ │     │
│   │   └─────┘  └─────┘ │  │   └─────┘  └─────┘ │     │
│   └─────────────────────┘  └─────────────────────┘     │
│                                                          │
│   ┌─────────────────────┐  ┌─────────────────────┐     │
│   │   Data Subnet       │  │   Data Subnet       │     │
│   │   (10.0.5.0/24)     │  │   (10.0.6.0/24)     │     │
│   │   AZ: ap-south-1a   │  │   AZ: ap-south-1b   │     │
│   │                     │  │                     │     │
│   │   ┌─────┐           │  │   ┌─────┐           │     │
│   │   │ RDS │           │  │   │ RDS │           │     │
│   │   │(Pri)│           │  │   │(Stb)│           │     │
│   │   └─────┘           │  │   └─────┘           │     │
│   └─────────────────────┘  └─────────────────────┘     │
│                                                          │
│   Internet Gateway ◄──► Public Subnets                  │
│   NAT Gateway      ◄──► Private → Internet (outbound)  │
│   VPC Endpoints    ◄──► AWS Services (private)          │
└─────────────────────────────────────────────────────────┘
```

---

# Key Components Overview

| Component | Purpose |
|-----------|---------|
| **VPC** | The virtual network itself — defined by a CIDR block |
| **Subnets** | Subdivisions of a VPC within a single AZ |
| **Route Tables** | Rules that determine where traffic is directed |
| **Internet Gateway** | Enables internet access for public subnets |
| **NAT Gateway** | Enables outbound internet for private subnets |
| **Security Groups** | Stateful, instance-level firewalls |
| **NACLs** | Stateless, subnet-level firewalls |
| **VPC Endpoints** | Private access to AWS services |
| **VPC Peering** | Private connection between two VPCs |
| **Transit Gateway** | Hub-and-spoke connectivity for multiple VPCs |
| **VPN / Direct Connect** | Hybrid cloud connectivity to on-premises |
| **Flow Logs** | Network traffic monitoring and auditing |

---

# VPC CIDR Blocks

A VPC is defined by a primary CIDR block.

## Allowed Range

- Minimum: `/28` (16 IP addresses)
- Maximum: `/16` (65,536 IP addresses)
- Must be from RFC 1918 private ranges:

| Range | CIDR | Addresses |
|-------|------|-----------|
| 10.0.0.0 – 10.255.255.255 | 10.0.0.0/8 | 16 million |
| 172.16.0.0 – 172.31.255.255 | 172.16.0.0/12 | 1 million |
| 192.168.0.0 – 192.168.255.255 | 192.168.0.0/16 | 65,536 |

## Secondary CIDRs

- A VPC can have up to 5 CIDR blocks (extendable to 50)
- Secondary CIDRs must not overlap with the primary or other secondary blocks
- Useful when you outgrow the original address space

## Reserved IP Addresses

AWS reserves **5 IP addresses** in every subnet:

| Address | Purpose |
|---------|---------|
| x.x.x.0 | Network address |
| x.x.x.1 | VPC router |
| x.x.x.2 | DNS server |
| x.x.x.3 | Reserved for future use |
| x.x.x.255 | Broadcast (not supported in VPC) |

A `/24` subnet provides 256 addresses − 5 reserved = **251 usable addresses**.

---

# Default VPC vs Custom VPC

| Feature | Default VPC | Custom VPC |
|---------|------------|------------|
| Created automatically | Yes (one per region) | No (you create it) |
| CIDR block | 172.31.0.0/16 | You choose |
| Subnets | One public per AZ | You design |
| Internet Gateway | Attached | You attach |
| Route table | Routes to IGW | You configure |
| Security | Permissive defaults | You define |
| Production use | **Not recommended** | **Recommended** |

---

# Key Takeaways

- A VPC is your private, isolated network in AWS — the foundation of all cloud architecture.
- You control the IP range (CIDR), subnet layout, routing, and security.
- AWS reserves 5 IPs per subnet — plan your CIDR blocks accordingly.
- Default VPCs exist for convenience; custom VPCs should be used for production.
- Multi-AZ subnet deployment is essential for high availability.
- VPC design decisions are foundational — they are difficult to change after deployment.

---
