# Subnets

A subnet is a range of IP addresses within a VPC, scoped to a single Availability Zone. Subnets are the building blocks of VPC network architecture — they determine how resources are organized, isolated, and connected.

Every resource deployed in a VPC must be placed in a subnet. The design of your subnet layout directly impacts security, availability, and operational management.

---

# Public vs Private Subnets

The distinction between public and private subnets is determined by the **route table**, not by the subnet itself.

## Public Subnet

- Has a route to an **Internet Gateway** (0.0.0.0/0 → IGW)
- Resources can have public IP addresses
- Directly accessible from the internet (if allowed by security groups)
- Used for: ALBs, NAT Gateways, bastion hosts

## Private Subnet

- No route to an Internet Gateway
- Resources cannot be reached from the internet
- Outbound internet via NAT Gateway (if needed)
- Used for: Application servers, databases, internal services

```text
Internet
    │
    ▼
Internet Gateway
    │
    ├──► Public Subnet (route: 0.0.0.0/0 → IGW)
    │    ├── ALB
    │    └── NAT Gateway
    │              │
    │              ▼
    └──► Private Subnet (route: 0.0.0.0/0 → NAT GW)
         ├── EC2 Instances
         ├── ECS Tasks
         └── Lambda (VPC-attached)
              │
         Data Subnet (no internet route)
         ├── RDS
         ├── ElastiCache
         └── DynamoDB (via VPC Endpoint)
```

---

# Subnet Design Patterns

## Three-Tier Architecture (Recommended)

| Tier | Subnet | Resources | Internet Access |
|------|--------|-----------|----------------|
| **Public** | 10.0.1.0/24, 10.0.2.0/24 | ALB, NAT Gateway | Full (IGW) |
| **Private (App)** | 10.0.3.0/24, 10.0.4.0/24 | EC2, ECS, Lambda | Outbound only (NAT GW) |
| **Private (Data)** | 10.0.5.0/24, 10.0.6.0/24 | RDS, ElastiCache | None |

## Multi-AZ Deployment

Always deploy subnets across at least **2 Availability Zones** for high availability.

```text
VPC (10.0.0.0/16)
│
├── AZ-1 (ap-south-1a)
│   ├── Public:  10.0.1.0/24
│   ├── Private: 10.0.3.0/24
│   └── Data:    10.0.5.0/24
│
└── AZ-2 (ap-south-1b)
    ├── Public:  10.0.2.0/24
    ├── Private: 10.0.4.0/24
    └── Data:    10.0.6.0/24
```

---

# Subnet Sizing

| CIDR | Addresses | Usable | Use Case |
|------|-----------|--------|----------|
| /28 | 16 | 11 | Very small (firewall, NAT) |
| /26 | 64 | 59 | Small services |
| /24 | 256 | 251 | Standard workloads |
| /22 | 1,024 | 1,019 | Large EKS clusters |
| /20 | 4,096 | 4,091 | Very large deployments |

## Best Practices

- Use **/24 or larger** for application subnets (EKS and ECS consume IPs quickly)
- Plan for growth — it is easier to start large than to resize later
- Leave room for additional subnets (don't allocate the entire VPC CIDR)
- EKS clusters can consume hundreds of IPs (pod networking uses subnet IPs)

---

# Subnet Route Table Association

Every subnet is associated with exactly one route table. If not explicitly associated, it uses the VPC's **main route table**.

```text
Public Subnet Route Table:
┌──────────────────┬──────────────────┐
│ Destination      │ Target           │
├──────────────────┼──────────────────┤
│ 10.0.0.0/16      │ local            │
│ 0.0.0.0/0        │ igw-abc123       │
└──────────────────┴──────────────────┘

Private Subnet Route Table:
┌──────────────────┬──────────────────┐
│ Destination      │ Target           │
├──────────────────┼──────────────────┤
│ 10.0.0.0/16      │ local            │
│ 0.0.0.0/0        │ nat-xyz789       │
└──────────────────┴──────────────────┘

Data Subnet Route Table:
┌──────────────────┬──────────────────┐
│ Destination      │ Target           │
├──────────────────┼──────────────────┤
│ 10.0.0.0/16      │ local            │
│ (no 0.0.0.0/0)   │                  │
└──────────────────┴──────────────────┘
```

---

# Key Takeaways

- Subnets are scoped to a single Availability Zone — deploy across 2+ AZs for HA.
- A subnet is "public" because its route table has a route to an Internet Gateway, not because of any subnet property.
- Use a three-tier model: public (ALB), private app (compute), private data (databases).
- AWS reserves 5 IPs per subnet — factor this into sizing.
- Size subnets generously — EKS/ECS workloads consume IPs rapidly.
- Every subnet must be associated with a route table (explicit or main).

---
