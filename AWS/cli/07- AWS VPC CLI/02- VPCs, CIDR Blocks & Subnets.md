# VPCs, CIDR Blocks & Subnets

> Learn how to create, configure, and manage Amazon VPCs, CIDR blocks, IPv4 addressing, IPv6, and subnets using the AWS CLI. This chapter covers network planning, subnet design, IP allocation, Availability Zones, and production networking practices.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Create Amazon VPCs
- Understand CIDR notation
- Configure IPv4 and IPv6
- Create public and private subnets
- Understand subnet sizing
- Associate CIDR blocks
- Design production VPC layouts

---

# Creating a VPC

A VPC requires an IPv4 CIDR block.

Example:

```text
10.0.0.0/16
```

Create a VPC:

```bash
aws ec2 create-vpc \
--cidr-block 10.0.0.0/16
```

Example output:

```text
VpcId

vpc-0123456789abcdef0
```

---

# Tag a VPC

Production resources should always be tagged.

```bash
aws ec2 create-tags \
--resources vpc-0123456789abcdef0 \
--tags Key=Name,Value=Production-VPC
```

---

# List VPCs

```bash
aws ec2 describe-vpcs
```

Useful information includes:

- VPC ID
- CIDR Block
- Default VPC
- State
- Owner ID

---

# Delete a VPC

```bash
aws ec2 delete-vpc \
--vpc-id vpc-0123456789abcdef0
```

A VPC cannot be deleted until all dependent resources have been removed.

---

# Understanding CIDR

CIDR stands for:

> **Classless Inter-Domain Routing**

CIDR defines how many IP addresses are available inside a network.

Example:

```text
10.0.0.0/16
```

The `/16` represents the network prefix.

---

# CIDR Cheat Sheet

| CIDR | Total IPs | Usable IPs |
|------|----------:|-----------:|
| /24 | 256 | 251 |
| /23 | 512 | 507 |
| /22 | 1024 | 1019 |
| /21 | 2048 | 2043 |
| /20 | 4096 | 4091 |
| /19 | 8192 | 8187 |
| /18 | 16384 | 16379 |
| /17 | 32768 | 32763 |
| /16 | 65536 | 65531 |

AWS reserves **5 IP addresses** in every subnet.

---

# Reserved AWS IP Addresses

Example:

```text
Subnet

10.0.1.0/24
```

AWS reserves:

```text
10.0.1.0

Network Address
```

```text
10.0.1.1

VPC Router
```

```text
10.0.1.2

DNS Server
```

```text
10.0.1.3

Reserved
```

```text
10.0.1.255

Broadcast Reserved
```

Only the remaining addresses are available for EC2 instances.

---

# Secondary CIDR Blocks

A VPC can contain multiple CIDR blocks.

Example:

```text
Primary

10.0.0.0/16
```

```text
Secondary

172.16.0.0/16
```

Useful for:

- Network expansion
- Migrations
- Multi-team environments

---

# Associate a CIDR Block

```bash
aws ec2 associate-vpc-cidr-block \
--vpc-id vpc-0123456789abcdef0 \
--cidr-block 172.16.0.0/16
```

---

# IPv4 vs IPv6

IPv4 example:

```text
10.0.1.25
```

IPv6 example:

```text
2406:da00:abcd::15
```

AWS supports dual-stack networking.

---

# Associate an IPv6 CIDR Block

```bash
aws ec2 associate-vpc-cidr-block \
--vpc-id vpc-0123456789abcdef0 \
--amazon-provided-ipv6-cidr-block
```

AWS automatically allocates an IPv6 range.

---

# What is a Subnet?

A subnet is a smaller network inside a VPC.

Example:

```text
VPC

10.0.0.0/16

│

├── 10.0.1.0/24

├── 10.0.2.0/24

├── 10.0.3.0/24

└── 10.0.4.0/24
```

Subnets improve organization and isolation.

---

# Create a Subnet

```bash
aws ec2 create-subnet \
--vpc-id vpc-0123456789abcdef0 \
--cidr-block 10.0.1.0/24 \
--availability-zone ap-south-1a
```

---

# List Subnets

```bash
aws ec2 describe-subnets
```

Returns:

- Subnet ID
- CIDR
- AZ
- Available IPs
- VPC ID

---

# Describe a Subnet

```bash
aws ec2 describe-subnets \
--subnet-ids subnet-0123456789abcdef0
```

---

# Delete a Subnet

```bash
aws ec2 delete-subnet \
--subnet-id subnet-0123456789abcdef0
```

---

# Public Subnet

A subnet becomes public when:

- It has a route to an Internet Gateway.
- Instances receive public IP addresses.

```text
Internet

↓

Internet Gateway

↓

Public Subnet

↓

EC2
```

---

# Private Subnet

A private subnet has **no direct route** to the Internet.

```text
Internet

↓

NAT Gateway

↓

Private Subnet

↓

Application

↓

Database
```

Production databases are typically placed in private subnets.

---

# Enable Public IP Assignment

Automatically assign public IPs.

```bash
aws ec2 modify-subnet-attribute \
--subnet-id subnet-0123456789abcdef0 \
--map-public-ip-on-launch
```

Useful for public web servers.

---

# Availability Zones

Each subnet belongs to one Availability Zone.

Example:

```text
Region

│

├── ap-south-1a

│      Public

│      Private

│

├── ap-south-1b

│      Public

│      Private

│

└── ap-south-1c

       Public

       Private
```

---

# Highly Available Design

A common production architecture.

```text
AZ-A

Public

Private

────────────

AZ-B

Public

Private
```

Applications continue running even if one AZ fails.

---

# Production Subnet Layout

```text
10.0.0.0/16

│

├── Public-A

10.0.1.0/24

├── Public-B

10.0.2.0/24

├── Private-App-A

10.0.11.0/24

├── Private-App-B

10.0.12.0/24

├── Private-DB-A

10.0.21.0/24

└── Private-DB-B

10.0.22.0/24
```

This layout separates web, application, and database tiers.

---

# Network Planning

Before creating a VPC, decide:

- Number of Availability Zones
- Number of public subnets
- Number of private subnets
- Expected growth
- Hybrid networking requirements
- IPv6 support

Good planning prevents costly redesigns.

---

# Common Errors

## InvalidVpcID.NotFound

Verify:

- VPC ID
- Region
- AWS Account

---

## InvalidSubnet.Range

Occurs when:

- CIDR overlaps another subnet.
- CIDR is outside the VPC range.

---

## DependencyViolation

A subnet cannot be deleted while resources still exist.

Check for:

- EC2 instances
- NAT Gateway
- ENIs
- Load Balancers

---

# Production Best Practices

- Plan IP addressing before deployment.
- Leave room for future subnet expansion.
- Use multiple Availability Zones.
- Separate web, application, and database tiers.
- Avoid overlapping CIDR blocks.
- Tag all networking resources.
- Prefer private subnets for backend services.
- Enable IPv6 where appropriate.

---

# Real-World Workflow

```text
Design Network

↓

Create VPC

↓

Create Subnets

↓

Assign CIDR Blocks

↓

Deploy Resources

↓

Configure Routing

↓

Secure Network
```

---

# Architecture Note

```text
AWS Region
      │
      ▼
VPC (10.0.0.0/16)
      │
 ┌────┼───────────────┐
 ▼    ▼               ▼
Public Subnets   Private Subnets
      │                 │
      ▼                 ▼
Web Tier          App & Database Tier
```

A well-designed subnet layout is the foundation of scalable, secure, and highly available AWS infrastructure.

---

# Interview Note

### Question

**What is the difference between a VPC CIDR block and a Subnet CIDR block?**

### Answer

A **VPC CIDR block** defines the total IP address range available for the entire VPC. A **Subnet CIDR block** is a smaller range carved out from the VPC CIDR block and assigned to a specific Availability Zone. All subnet CIDR blocks must be contained within the VPC CIDR range and must not overlap with one another.

---

# Key Takeaways

- A VPC must have at least one IPv4 CIDR block.
- Subnets divide a VPC into smaller network segments.
- AWS reserves five IP addresses in every subnet.
- Public and private subnets differ based on routing, not just IP addresses.
- Multi-AZ subnet design improves availability.
- Careful IP planning is essential for scalable AWS networking.
- Tagging and structured subnet layouts simplify long-term operations.