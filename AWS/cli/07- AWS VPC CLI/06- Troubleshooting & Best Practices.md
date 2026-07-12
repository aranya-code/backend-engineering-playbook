# Troubleshooting & Best Practices

> Learn how to troubleshoot Amazon VPC networking issues and apply production-ready networking best practices. This chapter covers connectivity failures, routing problems, DNS issues, Security Groups, Network ACLs, Internet Gateways, NAT Gateways, VPC Endpoints, and common production troubleshooting workflows.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Troubleshoot VPC connectivity issues
- Diagnose routing problems
- Verify Security Groups and Network ACLs
- Troubleshoot Internet and private connectivity
- Debug VPC Peering and Endpoints
- Apply networking best practices
- Build reliable production VPC architectures

---

# VPC Troubleshooting Workflow

When a resource cannot communicate:

```text
Application Failure
        │
        ▼
Check Route Table
        │
        ▼
Check Security Group
        │
        ▼
Check Network ACL
        │
        ▼
Check Gateway
        │
        ▼
Check DNS
        │
        ▼
Verify Connectivity
```

Always troubleshoot from the network outward.

---

# Verify the VPC

List all VPCs:

```bash
aws ec2 describe-vpcs
```

Verify:

- VPC ID
- CIDR Block
- State
- Region

---

# Verify Subnets

```bash
aws ec2 describe-subnets
```

Check:

- Subnet CIDR
- Availability Zone
- Available IP addresses
- VPC association

---

# Verify Route Tables

```bash
aws ec2 describe-route-tables
```

Confirm:

- Local route exists
- Internet route exists (if public)
- NAT Gateway route exists (if private)
- Peering routes exist (if applicable)

---

# No Internet Access

Possible causes:

- Missing Internet Gateway
- Missing route
- No public IP
- Security Group blocking traffic
- Network ACL blocking traffic

Workflow:

```text
EC2

↓

Public IP?

↓

Internet Gateway?

↓

Route Table?

↓

Security Group?

↓

Network ACL?
```

---

# Private Subnet Cannot Reach Internet

Verify:

```text
Private Route Table

↓

0.0.0.0/0

↓

NAT Gateway
```

Also verify:

- NAT Gateway is available
- Elastic IP attached
- NAT Gateway resides in a public subnet

---

# Cannot SSH to EC2

Check:

- EC2 running
- Public IP assigned
- Internet Gateway attached
- Route Table configured
- Security Group allows TCP 22
- Network ACL allows traffic

---

# Cannot Access Web Server

Verify:

Security Group:

```text
TCP 80

TCP 443
```

Route Table:

```text
0.0.0.0/0

↓

Internet Gateway
```

Also verify:

- Public IP
- Load Balancer configuration
- DNS records

---

# Security Group Issues

List Security Groups:

```bash
aws ec2 describe-security-groups
```

Verify:

- Correct ports
- Correct protocol
- Correct CIDR
- Security Group references

---

# Network ACL Issues

List Network ACLs:

```bash
aws ec2 describe-network-acls
```

Check:

- Rule numbers
- Allow/Deny actions
- Inbound rules
- Outbound rules

Remember:

NACLs are stateless.

---

# VPC Peering Problems

Verify:

```bash
aws ec2 describe-vpc-peering-connections
```

Check:

- Status is Active
- Route Tables updated
- CIDR ranges do not overlap
- Security Groups allow traffic

---

# CIDR Overlap

VPC Peering cannot be established if:

```text
VPC A

10.0.0.0/16

↓

VPC B

10.0.0.0/16
```

CIDR blocks must be unique.

---

# VPC Endpoint Issues

Verify:

```bash
aws ec2 describe-vpc-endpoints
```

Check:

- Endpoint status
- Service name
- Route Table association (Gateway Endpoint)
- Security Group (Interface Endpoint)

---

# DNS Resolution Problems

Amazon VPC provides a built-in DNS resolver.

Verify:

```text
DNS Resolution

Enabled
```

```text
DNS Hostnames

Enabled
```

Without these, internal name resolution may fail.

---

# Elastic IP Problems

List Elastic IPs:

```bash
aws ec2 describe-addresses
```

Verify:

- Allocation ID
- Association
- Correct Region

---

# NAT Gateway Problems

List NAT Gateways:

```bash
aws ec2 describe-nat-gateways
```

Verify:

- Available state
- Elastic IP attached
- Public subnet placement

---

# Common Errors

## InvalidVpcID.NotFound

Possible causes:

- Incorrect VPC ID
- Wrong Region
- Wrong AWS Account

---

## InvalidSubnetID.NotFound

Verify:

- Subnet ID
- Region
- Account

---

## InvalidRouteTableID.NotFound

Route Table does not exist.

Check resource IDs.

---

## InvalidGroup.NotFound

Security Group cannot be found.

Verify Region and VPC.

---

## DependencyViolation

Occurs when attempting to delete:

- VPC
- Internet Gateway
- Route Table
- NAT Gateway
- Subnet

Dependent resources must be removed first.

---

## CIDR Conflict

Occurs when:

- Subnet overlaps another subnet
- Secondary CIDR overlaps existing ranges

Always plan IP ranges carefully.

---

# Troubleshooting Checklist

Before investigating application issues, verify:

- □ VPC exists
- □ Subnet exists
- □ Correct Route Table
- □ Internet Gateway attached
- □ NAT Gateway healthy
- □ Security Groups correct
- □ Network ACL correct
- □ Public IP assigned (if needed)
- □ DNS resolution enabled
- □ VPC Endpoint healthy

---

# Production Best Practices

## Use Multiple Availability Zones

Avoid:

```text
One AZ

↓

Single Point of Failure
```

Prefer:

```text
AZ-A

↓

AZ-B

↓

High Availability
```

---

## Separate Public and Private Resources

Recommended:

```text
Public

↓

Load Balancer

↓

Private

↓

Application

↓

Database
```

---

## Follow Least Privilege

Security Groups should expose only required ports.

Example:

```text
22

↓

Admin IP Only
```

Not:

```text
22

↓

0.0.0.0/0
```

---

## Use VPC Endpoints

Instead of:

```text
Private EC2

↓

Internet

↓

S3
```

Use:

```text
Private EC2

↓

Gateway Endpoint

↓

S3
```

---

## Tag Everything

Recommended tags:

- Name
- Environment
- Team
- Owner
- Project

---

## Review Route Tables

Regularly audit:

- Internet routes
- NAT routes
- Peering routes
- Endpoint routes

---

## Minimize Internet Exposure

Only expose:

- Load Balancers
- Bastion Hosts (if used)
- Public APIs

Everything else should remain private.

---

# Real-World Workflow

```text
Design Network

↓

Create VPC

↓

Create Subnets

↓

Configure Routing

↓

Configure Security

↓

Deploy Resources

↓

Test Connectivity

↓

Production
```

---

# Architecture Note

```text
Internet
      │
      ▼
Internet Gateway
      │
      ▼
Public Subnet
      │
      ▼
Load Balancer
      │
      ▼
Private Subnet
      │
      ▼
Application
      │
      ▼
Database
```

A well-designed VPC isolates workloads, minimizes attack surface, and provides secure communication between AWS resources.

---

# Interview Note

### Question

**How would you troubleshoot an EC2 instance in a public subnet that cannot be accessed from the internet?**

### Answer

I would first verify that the EC2 instance has a public IP address and that the subnet's Route Table contains a default route (`0.0.0.0/0`) pointing to an Internet Gateway. Next, I would confirm that the Internet Gateway is attached to the VPC. I would then review the Security Group to ensure the required inbound ports (such as SSH on port 22 or HTTP on port 80) are allowed, followed by checking the Network ACL for any blocking rules. Finally, I would verify DNS resolution, confirm the correct Region and VPC, and use VPC Flow Logs if deeper network analysis is required.

---

# Key Takeaways

- Always troubleshoot networking layer by layer.
- Route Tables determine where traffic is sent.
- Security Groups protect resources; Network ACLs protect subnets.
- Internet Gateways enable public connectivity.
- NAT Gateways provide outbound internet access for private resources.
- VPC Endpoints improve security by eliminating unnecessary internet traffic.
- Multi-AZ networking and proper segmentation are essential for production-grade AWS environments.