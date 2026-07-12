# Cheat Sheet & Interview Guide

> A practical reference for the most commonly used Amazon VPC CLI commands, networking workflows, troubleshooting techniques, and interview preparation. This chapter serves as a day-to-day operational guide for Backend Engineers, DevOps Engineers, Cloud Engineers, Platform Engineers, and AWS Solutions Architects.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Quickly recall frequently used VPC CLI commands
- Build and manage Amazon VPCs
- Configure networking components
- Troubleshoot connectivity issues
- Design secure VPC architectures
- Prepare for AWS certification and backend engineering interviews

---

# Why a Cheat Sheet?

Amazon VPC is the networking backbone of AWS.

Instead of memorizing every command, experienced engineers remember:

- Network architecture
- Routing workflow
- Security workflow
- Connectivity options
- Troubleshooting process
- Production best practices

This chapter serves as a quick operational reference.

---

# Command Syntax

General syntax:

```bash
aws ec2 <operation>
```

Examples:

```bash
aws ec2 describe-vpcs
```

```bash
aws ec2 create-vpc
```

```bash
aws ec2 create-subnet
```

```bash
aws ec2 describe-route-tables
```

---

# VPC Commands

## List VPCs

```bash
aws ec2 describe-vpcs
```

---

## Create VPC

```bash
aws ec2 create-vpc
```

---

## Delete VPC

```bash
aws ec2 delete-vpc
```

---

## Associate CIDR Block

```bash
aws ec2 associate-vpc-cidr-block
```

---

# Subnet Commands

## List Subnets

```bash
aws ec2 describe-subnets
```

---

## Create Subnet

```bash
aws ec2 create-subnet
```

---

## Delete Subnet

```bash
aws ec2 delete-subnet
```

---

## Enable Auto Public IP

```bash
aws ec2 modify-subnet-attribute \
--map-public-ip-on-launch
```

---

# Route Table Commands

## List Route Tables

```bash
aws ec2 describe-route-tables
```

---

## Create Route Table

```bash
aws ec2 create-route-table
```

---

## Associate Route Table

```bash
aws ec2 associate-route-table
```

---

## Create Route

```bash
aws ec2 create-route
```

---

## Delete Route Table

```bash
aws ec2 delete-route-table
```

---

# Internet Gateway Commands

## Create Internet Gateway

```bash
aws ec2 create-internet-gateway
```

---

## Attach Internet Gateway

```bash
aws ec2 attach-internet-gateway
```

---

## Detach Internet Gateway

```bash
aws ec2 detach-internet-gateway
```

---

## Delete Internet Gateway

```bash
aws ec2 delete-internet-gateway
```

---

# NAT Gateway Commands

## Create NAT Gateway

```bash
aws ec2 create-nat-gateway
```

---

## List NAT Gateways

```bash
aws ec2 describe-nat-gateways
```

---

## Delete NAT Gateway

```bash
aws ec2 delete-nat-gateway
```

---

# Elastic IP Commands

## Allocate Elastic IP

```bash
aws ec2 allocate-address
```

---

## List Elastic IPs

```bash
aws ec2 describe-addresses
```

---

## Release Elastic IP

```bash
aws ec2 release-address
```

---

# Security Group Commands

## List Security Groups

```bash
aws ec2 describe-security-groups
```

---

## Create Security Group

```bash
aws ec2 create-security-group
```

---

## Delete Security Group

```bash
aws ec2 delete-security-group
```

---

## Add Inbound Rule

```bash
aws ec2 authorize-security-group-ingress
```

---

## Remove Inbound Rule

```bash
aws ec2 revoke-security-group-ingress
```

---

# Network ACL Commands

## List Network ACLs

```bash
aws ec2 describe-network-acls
```

---

## Create Network ACL

```bash
aws ec2 create-network-acl
```

---

## Delete Network ACL

```bash
aws ec2 delete-network-acl
```

---

## Create ACL Rule

```bash
aws ec2 create-network-acl-entry
```

---

# VPC Peering Commands

## Create Peering Connection

```bash
aws ec2 create-vpc-peering-connection
```

---

## Accept Peering Connection

```bash
aws ec2 accept-vpc-peering-connection
```

---

## List Peering Connections

```bash
aws ec2 describe-vpc-peering-connections
```

---

## Delete Peering Connection

```bash
aws ec2 delete-vpc-peering-connection
```

---

# VPC Endpoint Commands

## Create VPC Endpoint

```bash
aws ec2 create-vpc-endpoint
```

---

## List VPC Endpoints

```bash
aws ec2 describe-vpc-endpoints
```

---

## Delete VPC Endpoint

```bash
aws ec2 delete-vpc-endpoints
```

---

# Useful Global Options

| Option | Purpose |
|----------|----------|
| `--profile` | Use a named AWS profile |
| `--region` | Override default Region |
| `--output json` | JSON output |
| `--output table` | Table output |
| `--query` | Filter CLI output |
| `--debug` | Enable verbose debugging |
| `--no-cli-pager` | Disable CLI pager |

---

# Common Networking Components

| Component | Purpose |
|-----------|---------|
| VPC | Private virtual network |
| Subnet | Network segment inside a VPC |
| Route Table | Determines packet routing |
| Internet Gateway | Public internet access |
| NAT Gateway | Outbound internet for private subnets |
| Security Group | Instance-level firewall |
| Network ACL | Subnet-level firewall |
| Elastic IP | Static public IPv4 address |
| VPC Endpoint | Private AWS service access |
| VPC Peering | Private VPC-to-VPC connectivity |

---

# Common Errors

| Error | Cause | Resolution |
|--------|-------|------------|
| InvalidVpcID.NotFound | Invalid VPC ID | Verify VPC ID and Region |
| InvalidSubnetID.NotFound | Invalid Subnet | Verify subnet exists |
| InvalidRouteTableID.NotFound | Route Table missing | Verify Route Table |
| InvalidGroup.NotFound | Security Group missing | Verify Security Group |
| DependencyViolation | Resource still attached | Remove dependencies first |
| Gateway.NotAttached | Internet Gateway detached | Attach the Internet Gateway |
| InvalidSubnet.Range | CIDR overlap | Review subnet planning |

---

# Public Subnet Checklist

A public subnet requires:

- Internet Gateway attached
- Route Table with `0.0.0.0/0`
- Public IP assignment enabled
- Security Group allowing required traffic

---

# Private Subnet Checklist

A private subnet requires:

- NAT Gateway
- Route to NAT Gateway
- No public IP
- Private Security Groups

---

# Security Checklist

- Use least-privilege Security Groups.
- Never expose databases to the Internet.
- Restrict SSH to trusted IP addresses.
- Use Security Group references.
- Apply custom Network ACLs.
- Enable VPC Flow Logs.
- Regularly audit firewall rules.

---

# Production Architecture

```text
Internet
      │
      ▼
Internet Gateway
      │
      ▼
Application Load Balancer
      │
      ▼
Public Subnets
      │
      ▼
Private Application Subnets
      │
      ▼
Private Database Subnets
```

---

# Troubleshooting Workflow

```text
Connectivity Issue

↓

Check Route Table

↓

Check Security Group

↓

Check Network ACL

↓

Check Internet Gateway

↓

Check NAT Gateway

↓

Check DNS

↓

Verify Application
```

---

# Interview Questions

## 1. What is Amazon VPC?

**Answer**

Amazon VPC is a logically isolated virtual network that enables you to launch AWS resources securely with complete control over IP addressing, routing, internet connectivity, and network security.

---

## 2. What is the difference between a public and a private subnet?

**Answer**

A public subnet has a route to an Internet Gateway and typically contains resources with public IP addresses. A private subnet has no direct internet route and usually accesses the internet through a NAT Gateway for outbound-only connectivity.

---

## 3. What is the difference between an Internet Gateway and a NAT Gateway?

**Answer**

An Internet Gateway enables inbound and outbound internet access for resources with public IP addresses. A NAT Gateway allows resources in private subnets to initiate outbound internet connections without accepting inbound connections.

---

## 4. What is the difference between a Security Group and a Network ACL?

**Answer**

A Security Group is a stateful firewall attached to AWS resources and supports only allow rules. A Network ACL is a stateless firewall attached to subnets and supports both allow and deny rules.

---

## 5. Why are Route Tables important?

**Answer**

Route Tables determine where network traffic is forwarded. Without appropriate routes, resources cannot communicate with other networks, the internet, or peer VPCs.

---

## 6. What is VPC Peering?

**Answer**

VPC Peering establishes a private network connection between two VPCs, enabling communication over private IP addresses without using the public internet.

---

## 7. What are VPC Endpoints?

**Answer**

VPC Endpoints provide private connectivity from a VPC to supported AWS services without requiring an Internet Gateway, NAT Gateway, VPN, or Direct Connect.

---

## 8. Why use multiple Availability Zones?

**Answer**

Using multiple Availability Zones improves fault tolerance and high availability by ensuring workloads continue operating if one Availability Zone experiences an outage.

---

## 9. Why should databases be placed in private subnets?

**Answer**

Databases typically do not require direct internet access. Placing them in private subnets reduces the attack surface and improves overall security.

---

## 10. How would you troubleshoot an EC2 instance that cannot access the internet?

**Answer**

I would verify that the instance is in the correct subnet, check the associated Route Table, confirm that an Internet Gateway or NAT Gateway is correctly configured, review the Security Group and Network ACL rules, ensure a public IP is assigned if required, verify DNS settings, and inspect VPC Flow Logs if deeper analysis is needed.

---

# Senior Engineer Tips

Experienced cloud engineers typically:

- Design CIDR ranges before deployment.
- Use custom VPCs instead of the default VPC.
- Separate workloads into public and private subnets.
- Use Security Group references instead of IP-based rules.
- Keep databases isolated in private subnets.
- Deploy resources across multiple Availability Zones.
- Use VPC Endpoints instead of unnecessary NAT traffic.
- Enable VPC Flow Logs for production environments.
- Tag every networking resource consistently.
- Review networking architecture regularly.

---

# Quick Reference

| Task | Command |
|------|---------|
| List VPCs | `aws ec2 describe-vpcs` |
| Create VPC | `aws ec2 create-vpc` |
| List Subnets | `aws ec2 describe-subnets` |
| Create Subnet | `aws ec2 create-subnet` |
| Create Route Table | `aws ec2 create-route-table` |
| Create Internet Gateway | `aws ec2 create-internet-gateway` |
| Create NAT Gateway | `aws ec2 create-nat-gateway` |
| Create Security Group | `aws ec2 create-security-group` |
| Create VPC Endpoint | `aws ec2 create-vpc-endpoint` |
| Create Peering Connection | `aws ec2 create-vpc-peering-connection` |

---

# Final Thoughts

Amazon VPC is the networking foundation of AWS. Mastering the VPC CLI enables you to build secure, scalable, and highly available cloud architectures. Combined with Route Tables, Security Groups, Network ACLs, Internet Gateways, NAT Gateways, VPC Endpoints, and PrivateLink, Amazon VPC provides the networking capabilities required for modern cloud-native applications and enterprise workloads.

---
