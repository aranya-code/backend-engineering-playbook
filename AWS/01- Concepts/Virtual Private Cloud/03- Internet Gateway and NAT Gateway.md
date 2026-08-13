# Internet Gateway and NAT Gateway

Internet Gateways (IGW) and NAT Gateways are the two primary mechanisms for connecting VPC resources to the internet. The Internet Gateway provides full bidirectional internet access for public subnets, while the NAT Gateway provides outbound-only internet access for private subnets — keeping them unreachable from the internet.

Understanding the difference between these two gateways is fundamental to VPC networking and is one of the most tested VPC topics.

---

# Internet Gateway (IGW)

## What is an Internet Gateway?

An Internet Gateway is a horizontally scaled, redundant, and highly available VPC component that enables communication between instances in your VPC and the internet.

## Key Characteristics

- **One IGW per VPC** — you cannot attach multiple IGWs to a VPC
- **Highly available** — AWS manages redundancy across AZs
- **No bandwidth bottleneck** — scales automatically
- **No cost** — free to create and use
- **Supports IPv4 and IPv6**

## How IGW Works

For an instance to communicate with the internet, three conditions must be met:

```text
1. VPC has an Internet Gateway attached
2. Subnet route table has 0.0.0.0/0 → IGW
3. Instance has a public IP or Elastic IP

All three are required:

Internet ◄──► IGW ◄──► Route Table ◄──► Instance (Public IP)
```

## IGW and NAT (Network Address Translation)

The IGW performs **one-to-one NAT** between public and private IPs:

```text
Outbound:
Instance (10.0.1.5) ──► IGW translates to ──► 3.110.24.5 (Public IP)

Inbound:
Internet (3.110.24.5) ──► IGW translates to ──► 10.0.1.5 (Private IP)
```

---

# NAT Gateway

## What is a NAT Gateway?

A NAT Gateway enables instances in private subnets to initiate outbound connections to the internet (for software updates, API calls, etc.) while preventing inbound connections from the internet.

## Key Characteristics

- Managed by AWS — no patching or maintenance
- Deployed in a **public subnet**
- Requires an **Elastic IP**
- Supports up to **45 Gbps** bandwidth (scales automatically)
- **AZ-scoped** — deploy one per AZ for high availability
- **Charged** — hourly rate + data processing fee

## How NAT Gateway Works

```text
Private Instance (10.0.3.5)
         │
         │ (Private route table: 0.0.0.0/0 → NAT GW)
         ▼
NAT Gateway (10.0.1.100, EIP: 3.110.24.5)
         │
         │ (Public route table: 0.0.0.0/0 → IGW)
         ▼
Internet Gateway
         │
         ▼
      Internet
```

The private instance sends traffic to the NAT Gateway, which replaces the source IP with its own Elastic IP, forwards the request to the internet via the IGW, and routes the response back to the private instance.

---

## NAT Gateway HA Architecture

NAT Gateways are AZ-scoped. If an AZ goes down, instances in other AZs lose internet access if they share the same NAT Gateway.

**Solution:** Deploy a NAT Gateway in each AZ.

```text
AZ-1                          AZ-2
┌─────────────────┐           ┌─────────────────┐
│  Public Subnet  │           │  Public Subnet  │
│  NAT-GW-1 (EIP) │           │  NAT-GW-2 (EIP) │
└────────┬────────┘           └────────┬────────┘
         │                             │
┌────────┴────────┐           ┌────────┴────────┐
│ Private Subnet  │           │ Private Subnet  │
│ Route: 0.0.0.0  │           │ Route: 0.0.0.0  │
│  → NAT-GW-1    │           │  → NAT-GW-2    │
│                 │           │                 │
│  ┌────┐ ┌────┐ │           │  ┌────┐ ┌────┐ │
│  │EC2 │ │EC2 │ │           │  │EC2 │ │EC2 │ │
│  └────┘ └────┘ │           │  └────┘ └────┘ │
└─────────────────┘           └─────────────────┘
```

---

## NAT Gateway vs NAT Instance

| Feature | NAT Gateway | NAT Instance |
|---------|-------------|--------------|
| Managed by | AWS | Customer |
| Availability | HA within AZ | Manual (ASG required) |
| Bandwidth | Up to 45 Gbps | Depends on instance type |
| Maintenance | None | OS patching, monitoring |
| Cost | Higher (hourly + data) | Lower (EC2 pricing) |
| Security groups | Not supported | Supported |
| Bastion host | Cannot double as | Can double as |
| **Recommendation** | **Use for production** | Avoid (legacy approach) |

---

# IGW vs NAT Gateway Comparison

| Feature | Internet Gateway | NAT Gateway |
|---------|-----------------|-------------|
| Direction | Bidirectional (in + out) | Outbound only |
| Subnet type | Public subnets | Private subnets (deployed in public) |
| Instance requirement | Public IP or EIP | No public IP needed on instances |
| Cost | Free | Hourly + data processing |
| HA | Fully redundant across AZs | AZ-scoped (deploy per AZ) |
| Use case | ALB, public-facing services | Private instances needing internet |

---

# Pricing

## Internet Gateway

- **Free** — no charges for creating or using an IGW

## NAT Gateway

| Component | Cost (us-east-1) |
|-----------|-----------------|
| Hourly rate | ~$0.045/hour (~$32/month) |
| Data processing | ~$0.045/GB |

**Cost optimization tip:** Consider VPC Endpoints for AWS service access (S3, DynamoDB) to avoid routing that traffic through the NAT Gateway.

---

# Key Takeaways

- **IGW** = bidirectional internet access for public subnets (free, HA, one per VPC).
- **NAT Gateway** = outbound-only internet for private subnets (paid, AZ-scoped).
- A subnet is "public" only when its route table has a route to an IGW.
- Deploy one NAT Gateway per AZ for high availability.
- NAT Gateways are a significant cost factor — use VPC Endpoints to reduce traffic through them.
- NAT Instances are a legacy approach — use NAT Gateways for all new deployments.

---
