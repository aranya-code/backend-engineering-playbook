# Route Tables, Internet Gateway & NAT Gateway

> Learn how Amazon VPC routes network traffic using Route Tables, Internet Gateways (IGW), NAT Gateways, and Elastic IPs. This chapter covers routing fundamentals, public and private internet access, gateway configuration, and production networking patterns using the AWS CLI.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Understand Route Tables
- Create and manage Route Tables
- Configure Internet Gateways
- Configure NAT Gateways
- Understand Elastic IPs
- Build public and private networking
- Design highly available internet connectivity

---

# How Routing Works

Every packet leaving an EC2 instance follows a route.

```text
EC2

↓

Route Table

↓

Gateway

↓

Destination
```

Without routing, resources cannot communicate outside their subnet.

---

# Route Table Architecture

```text
Subnet

↓

Route Table

↓

Destination

↓

Target
```

Each subnet is associated with one Route Table.

---

# Components of a Route

Every route contains:

| Component | Description |
|-----------|-------------|
| Destination | CIDR Block |
| Target | Gateway or Network Interface |

Example:

```text
Destination

0.0.0.0/0

↓

Internet Gateway
```

---

# Local Route

Every Route Table automatically contains:

```text
Destination

10.0.0.0/16

↓

Local
```

This allows communication between resources inside the VPC.

---

# Internet Route

Public internet access requires:

```text
0.0.0.0/0

↓

Internet Gateway
```

---

# List Route Tables

```bash
aws ec2 describe-route-tables
```

Returns:

- Route Table ID
- Routes
- Associations
- VPC ID

---

# Create a Route Table

```bash
aws ec2 create-route-table \
--vpc-id vpc-0123456789abcdef0
```

---

# Delete a Route Table

```bash
aws ec2 delete-route-table \
--route-table-id rtb-0123456789abcdef0
```

Cannot delete the Main Route Table.

---

# Associate a Route Table

```bash
aws ec2 associate-route-table \
--subnet-id subnet-0123456789abcdef0 \
--route-table-id rtb-0123456789abcdef0
```

Each subnet uses only one Route Table.

---

# Replace a Route Table Association

```bash
aws ec2 replace-route-table-association \
--association-id rtbassoc-xxxxxxxx \
--route-table-id rtb-yyyyyyyy
```

Useful during migrations.

---

# What is an Internet Gateway?

An Internet Gateway (IGW) enables communication between a VPC and the Internet.

```text
Internet

↓

Internet Gateway

↓

VPC
```

Without an IGW, public internet access is impossible.

---

# Internet Gateway Architecture

```text
Internet

↓

Internet Gateway

↓

Public Route Table

↓

Public Subnet

↓

EC2
```

---

# Create an Internet Gateway

```bash
aws ec2 create-internet-gateway
```

---

# List Internet Gateways

```bash
aws ec2 describe-internet-gateways
```

---

# Attach Internet Gateway

```bash
aws ec2 attach-internet-gateway \
--internet-gateway-id igw-0123456789abcdef0 \
--vpc-id vpc-0123456789abcdef0
```

The IGW must be attached before it can be used.

---

# Detach Internet Gateway

```bash
aws ec2 detach-internet-gateway \
--internet-gateway-id igw-0123456789abcdef0 \
--vpc-id vpc-0123456789abcdef0
```

---

# Delete Internet Gateway

```bash
aws ec2 delete-internet-gateway \
--internet-gateway-id igw-0123456789abcdef0
```

The gateway must be detached first.

---

# Add an Internet Route

```bash
aws ec2 create-route \
--route-table-id rtb-0123456789abcdef0 \
--destination-cidr-block 0.0.0.0/0 \
--gateway-id igw-0123456789abcdef0
```

Now the subnet has internet access.

---

# Public Subnet Workflow

```text
Internet

↓

Internet Gateway

↓

Route Table

↓

Public Subnet

↓

EC2
```

---

# What is a NAT Gateway?

A NAT Gateway provides outbound internet access for private subnets.

Resources can:

- Download updates
- Access AWS APIs
- Connect to external services

They cannot receive inbound internet traffic.

---

# NAT Gateway Architecture

```text
Internet

↓

Internet Gateway

↓

NAT Gateway

↓

Private Route Table

↓

Private Subnet

↓

Application
```

---

# Why Not Attach an IGW to a Private Subnet?

Because:

```text
Private Subnet

↓

No Public IP

↓

No Direct Internet Access
```

Instead:

```text
Private Subnet

↓

NAT Gateway

↓

Internet
```

---

# Elastic IP

A NAT Gateway requires an Elastic IP.

```text
Elastic IP

↓

NAT Gateway

↓

Internet
```

---

# Allocate an Elastic IP

```bash
aws ec2 allocate-address \
--domain vpc
```

---

# List Elastic IPs

```bash
aws ec2 describe-addresses
```

---

# Release an Elastic IP

```bash
aws ec2 release-address \
--allocation-id eipalloc-0123456789abcdef0
```

---

# Create a NAT Gateway

```bash
aws ec2 create-nat-gateway \
--subnet-id subnet-public \
--allocation-id eipalloc-0123456789abcdef0
```

A NAT Gateway must always be created inside a **public subnet**.

---

# List NAT Gateways

```bash
aws ec2 describe-nat-gateways
```

---

# Delete a NAT Gateway

```bash
aws ec2 delete-nat-gateway \
--nat-gateway-id nat-0123456789abcdef0
```

---

# Private Route

Private subnets typically contain:

```text
Destination

0.0.0.0/0

↓

NAT Gateway
```

---

# Public vs Private Routing

Public Route Table

```text
0.0.0.0/0

↓

Internet Gateway
```

Private Route Table

```text
0.0.0.0/0

↓

NAT Gateway
```

---

# Production Architecture

```text
Internet
      │
      ▼
Internet Gateway
      │
      ▼
Public Subnet
      │
      ├── Load Balancer
      └── NAT Gateway
             │
             ▼
Private Subnets
      │
      ├── Application Servers
      └── Databases
```

This is one of the most common enterprise AWS architectures.

---

# Highly Available NAT Design

Avoid using a single NAT Gateway.

Example:

```text
AZ-A

↓

NAT Gateway A

────────────

AZ-B

↓

NAT Gateway B
```

Each Availability Zone should have its own NAT Gateway.

---

# Common Errors

## InvalidRouteTableID.NotFound

Verify:

- Route Table ID
- Region
- AWS Account

---

## Gateway.NotAttached

The Internet Gateway has not been attached to the VPC.

Attach it before creating routes.

---

## ElasticIpAlreadyAssociated

The Elastic IP is already attached to another resource.

Allocate a new Elastic IP.

---

## DependencyViolation

Occurs when deleting:

- Internet Gateway
- Route Table
- NAT Gateway

Remove dependent resources first.

---

# Production Best Practices

- Use separate Route Tables for public and private subnets.
- Attach only one Internet Gateway per VPC.
- Place NAT Gateways in public subnets.
- Deploy one NAT Gateway per Availability Zone.
- Keep databases in private subnets.
- Tag networking resources consistently.
- Review route configurations regularly.
- Minimize unnecessary internet exposure.

---

# Real-World Workflow

```text
Create VPC

↓

Create Subnets

↓

Create Internet Gateway

↓

Create Route Table

↓

Attach Internet Gateway

↓

Create NAT Gateway

↓

Configure Routes

↓

Deploy EC2
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
Public Route Table
      │
      ▼
Public Subnet
      │
      ▼
NAT Gateway
      │
      ▼
Private Route Table
      │
      ▼
Private Subnet
```

The Internet Gateway provides inbound and outbound internet connectivity for public resources, while the NAT Gateway provides outbound-only connectivity for private resources.

---

# Interview Note

### Question

**What is the difference between an Internet Gateway and a NAT Gateway?**

### Answer

An **Internet Gateway (IGW)** enables resources in public subnets to communicate directly with the internet, supporting both inbound and outbound traffic when paired with public IP addresses. A **NAT Gateway**, on the other hand, enables resources in private subnets to initiate outbound connections to the internet without allowing inbound connections. In production, public-facing resources such as Load Balancers reside behind an Internet Gateway, while application servers and databases remain in private subnets using a NAT Gateway for secure outbound access.

---

# Key Takeaways

- Route Tables determine where network traffic is sent.
- Every subnet is associated with one Route Table.
- Internet Gateways provide direct internet access for public subnets.
- NAT Gateways provide outbound internet access for private subnets.
- NAT Gateways require an Elastic IP and must reside in a public subnet.
- Production environments separate public and private routing.
- Highly available architectures deploy one NAT Gateway per Availability Zone.