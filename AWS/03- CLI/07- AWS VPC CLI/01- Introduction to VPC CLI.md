# Introduction to Amazon VPC CLI

> Learn how to build, manage, and troubleshoot Amazon Virtual Private Cloud (VPC) using the AWS Command Line Interface (AWS CLI). This chapter introduces Amazon VPC architecture, networking fundamentals, IP addressing, routing concepts, and the core AWS CLI commands used to manage networking infrastructure.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Understand Amazon VPC
- Understand AWS networking fundamentals
- Navigate VPC CLI commands
- Understand CIDR blocks
- Understand public and private networking
- Understand VPC components
- Build a strong networking foundation for AWS

---

# Why Learn Amazon VPC?

Amazon VPC is the networking foundation of AWS.

Almost every AWS service operates inside or connects to a VPC.

Examples include:

- EC2
- RDS
- ECS
- EKS
- Lambda
- ElastiCache
- Redshift
- OpenSearch

Understanding VPC is essential for designing secure, scalable, and highly available cloud infrastructure.

---

# What is Amazon VPC?

Amazon Virtual Private Cloud (VPC) is a logically isolated virtual network within AWS.

It allows you to:

- Launch AWS resources
- Control IP addressing
- Configure routing
- Define network security
- Connect private infrastructure
- Isolate environments

Think of a VPC as your own private data center inside AWS.

---

# Traditional Network vs Amazon VPC

Traditional Data Center

```text
Servers

↓

Switches

↓

Routers

↓

Firewalls
```

Amazon VPC

```text
VPC

↓

Subnets

↓

Route Tables

↓

Security Groups

↓

Internet Gateway
```

AWS provides the networking infrastructure while you control the network configuration.

---

# High-Level Architecture

```text
AWS Region
     │
     ▼
VPC
     │
 ┌───┴───────────────┐
 ▼                   ▼
Public Subnet    Private Subnet
     │                 │
     ▼                 ▼
EC2 Instance      Database
```

A VPC can span multiple Availability Zones within a Region.

---

# VPC Components

A typical VPC consists of:

```text
VPC

│

├── CIDR Block

├── Subnets

├── Route Tables

├── Internet Gateway

├── NAT Gateway

├── Security Groups

├── Network ACLs

├── Elastic IP

└── VPC Endpoints
```

Each component plays a specific role in networking.

---

# What is a CIDR Block?

A CIDR (Classless Inter-Domain Routing) block defines the IP address range available inside a VPC.

Example:

```text
10.0.0.0/16
```

This represents:

- Network Address: `10.0.0.0`
- Prefix Length: `/16`

The prefix determines how many IP addresses are available.

---

# Example CIDR Ranges

```text
10.0.0.0/16

172.16.0.0/16

192.168.0.0/16
```

These are private IP address ranges commonly used in AWS.

---

# Public vs Private Subnets

Public Subnet

```text
Internet

↓

Internet Gateway

↓

Public Subnet

↓

Web Server
```

Private Subnet

```text
Internet

↓

NAT Gateway

↓

Private Subnet

↓

Database
```

Public subnets allow direct internet access, while private subnets do not.

---

# Why Use Multiple Subnets?

Separating workloads improves:

- Security
- Availability
- Scalability
- Fault isolation

Example:

```text
Public Subnet

↓

Load Balancer

↓

Private Subnet

↓

Application Server

↓

Private Subnet

↓

Database
```

This is one of the most common production architectures.

---

# Availability Zones

A VPC spans an AWS Region.

Subnets exist within Availability Zones.

Example:

```text
Region

│

├── AZ A

│     └── Public Subnet

│

└── AZ B

      └── Private Subnet
```

Using multiple AZs improves availability.

---

# VPC Limits

Each VPC has limits for:

- CIDR blocks
- Subnets
- Route Tables
- Security Groups
- Network ACLs
- Elastic IPs

Many limits can be increased through AWS Service Quotas.

---

# How AWS CLI Communicates with VPC

VPC commands follow this pattern:

```bash
aws ec2 <operation>
```

Unlike S3 or Lambda, there is no dedicated `aws vpc` namespace.

VPC operations are managed through the **EC2 API**.

---

# Common VPC Commands

Examples:

```bash
aws ec2 describe-vpcs
```

```bash
aws ec2 create-vpc
```

```bash
aws ec2 delete-vpc
```

```bash
aws ec2 describe-subnets
```

---

# List All VPCs

```bash
aws ec2 describe-vpcs
```

Displays:

- VPC ID
- CIDR Block
- State
- Default VPC
- Tags

---

# Describe a Specific VPC

```bash
aws ec2 describe-vpcs \
--vpc-ids vpc-0123456789abcdef0
```

Useful for inspecting a single VPC.

---

# List Subnets

```bash
aws ec2 describe-subnets
```

Returns:

- Subnet ID
- CIDR
- Availability Zone
- Available IP addresses

---

# List Route Tables

```bash
aws ec2 describe-route-tables
```

Displays routing configuration for each VPC.

---

# Verify Current AWS Identity

Before making networking changes:

```bash
aws sts get-caller-identity
```

Always verify the active AWS account.

---

# Global CLI Options

Examples:

```bash
aws ec2 describe-vpcs \
--profile production
```

```bash
aws ec2 describe-vpcs \
--region ap-south-1
```

```bash
aws ec2 describe-vpcs \
--output table
```

---

# Default VPC

Every AWS Region initially contains a **Default VPC**.

Characteristics:

- Public subnets
- Internet Gateway attached
- Default route table
- Default Security Group
- Default Network ACL

Production environments often use **custom VPCs** instead of the default.

---

# Custom VPC

A custom VPC allows complete control over:

- IP addressing
- Routing
- Security
- Internet connectivity
- Hybrid networking

Nearly all enterprise AWS deployments use custom VPCs.

---

# Production Tip

Avoid deploying production workloads into the **Default VPC**.

Instead:

```text
Production

↓

Custom VPC

↓

Public Subnets

↓

Private Subnets

↓

Dedicated Security Groups
```

This provides better security, isolation, and scalability.

---

# Architecture Note

```text
AWS Region
      │
      ▼
Amazon VPC
      │
 ┌────┼─────────────┐
 ▼    ▼             ▼
Subnets
Route Tables
Security Groups
      │
      ▼
AWS Resources
```

Amazon VPC provides the networking foundation for nearly every AWS service.

---

# Interview Note

### Question

**What is Amazon VPC, and why is it important?**

### Answer

Amazon Virtual Private Cloud (VPC) is a logically isolated virtual network within AWS where you can launch and manage cloud resources. It provides complete control over IP addressing, subnets, routing, internet connectivity, and network security. VPC is the foundation of AWS networking and is essential for building secure, scalable, and highly available cloud architectures.

---

# Key Takeaways

- Amazon VPC is the networking foundation of AWS.
- A VPC is a logically isolated virtual network.
- VPCs contain CIDR blocks, subnets, route tables, security groups, and gateways.
- VPC management is performed through the `aws ec2` CLI namespace.
- Public and private subnets provide controlled internet access.
- Production environments should use custom VPCs instead of the default VPC.
- Understanding VPC is essential before working with services like ECS, RDS, EKS, and Lambda VPC integration.