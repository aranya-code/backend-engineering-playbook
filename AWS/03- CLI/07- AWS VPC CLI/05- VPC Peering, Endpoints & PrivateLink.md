# VPC Peering, Endpoints & PrivateLink

> Learn how to securely connect Amazon VPCs and AWS services using VPC Peering, VPC Endpoints, AWS PrivateLink, and Gateway Endpoints. This chapter covers private networking, cross-VPC communication, endpoint types, DNS resolution, AWS CLI commands, and production networking best practices.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Understand VPC Peering
- Configure VPC Peering Connections
- Understand VPC Endpoints
- Configure Gateway Endpoints
- Configure Interface Endpoints
- Understand AWS PrivateLink
- Build secure private AWS networking

---

# Why Connect VPCs?

Large AWS environments rarely consist of a single VPC.

Examples:

- Production
- Development
- Shared Services
- Security
- Networking

These VPCs often need to communicate securely.

---

# Connectivity Options

AWS provides multiple methods.

```text
VPC

│

├── VPC Peering

├── Transit Gateway

├── VPN

├── Direct Connect

├── Gateway Endpoint

└── PrivateLink
```

This chapter focuses on VPC Peering and Endpoints.

---

# What is VPC Peering?

VPC Peering creates a private connection between two VPCs.

```text
VPC A

⇄

VPC B
```

Traffic remains entirely within the AWS network.

---

# VPC Peering Architecture

```text
VPC A

↓

Peering Connection

↓

VPC B
```

Resources communicate using private IP addresses.

---

# VPC Peering Characteristics

- Private communication
- No Internet Gateway required
- No VPN required
- No NAT Gateway required
- Supports cross-account peering
- Supports cross-region peering

---

# VPC Peering Limitations

VPC Peering is **non-transitive**.

Example:

```text
VPC A

↓

VPC B

↓

VPC C
```

A cannot communicate with C automatically.

Each connection must be created explicitly.

---

# Create a Peering Connection

```bash
aws ec2 create-vpc-peering-connection \
--vpc-id vpc-11111111 \
--peer-vpc-id vpc-22222222
```

---

# Accept a Peering Connection

```bash
aws ec2 accept-vpc-peering-connection \
--vpc-peering-connection-id pcx-0123456789abcdef0
```

---

# List Peering Connections

```bash
aws ec2 describe-vpc-peering-connections
```

---

# Delete a Peering Connection

```bash
aws ec2 delete-vpc-peering-connection \
--vpc-peering-connection-id pcx-0123456789abcdef0
```

---

# Update Route Tables

Peering alone is not enough.

Each VPC Route Table must contain a route.

Example:

```text
Destination

10.1.0.0/16

↓

Peering Connection
```

Without route updates, traffic cannot flow.

---

# Security Groups

Security Groups must also allow traffic from the peer VPC.

Example:

```text
Application SG

↓

Allow

10.1.0.0/16
```

---

# What are VPC Endpoints?

A VPC Endpoint allows private access to AWS services.

Instead of:

```text
EC2

↓

Internet

↓

Amazon S3
```

Use:

```text
EC2

↓

VPC Endpoint

↓

Amazon S3
```

Traffic never leaves AWS.

---

# Types of VPC Endpoints

AWS supports:

```text
Gateway Endpoint

↓

S3

DynamoDB
```

```text
Interface Endpoint

↓

Most AWS Services
```

---

# Gateway Endpoint

Gateway Endpoints support:

- Amazon S3
- Amazon DynamoDB

No Elastic IP or NAT Gateway is required.

---

# Gateway Endpoint Architecture

```text
Private Subnet

↓

Gateway Endpoint

↓

Amazon S3
```

Traffic remains private.

---

# Create a Gateway Endpoint

```bash
aws ec2 create-vpc-endpoint \
--vpc-id vpc-0123456789abcdef0 \
--service-name com.amazonaws.ap-south-1.s3 \
--vpc-endpoint-type Gateway \
--route-table-ids rtb-0123456789abcdef0
```

---

# Interface Endpoint

Interface Endpoints create Elastic Network Interfaces (ENIs).

Supported services include:

- Secrets Manager
- SSM
- CloudWatch
- SNS
- SQS
- KMS
- ECR

---

# Interface Endpoint Architecture

```text
Private Subnet

↓

ENI

↓

AWS Service
```

---

# Create an Interface Endpoint

```bash
aws ec2 create-vpc-endpoint \
--vpc-id vpc-0123456789abcdef0 \
--service-name com.amazonaws.ap-south-1.ssm \
--vpc-endpoint-type Interface \
--subnet-ids subnet-0123456789abcdef0 \
--security-group-ids sg-0123456789abcdef0
```

---

# List VPC Endpoints

```bash
aws ec2 describe-vpc-endpoints
```

---

# Delete a VPC Endpoint

```bash
aws ec2 delete-vpc-endpoints \
--vpc-endpoint-ids vpce-0123456789abcdef0
```

---

# What is AWS PrivateLink?

AWS PrivateLink is built on Interface Endpoints.

It enables private connectivity to:

- AWS Services
- Partner Services
- Customer Services

Without exposing traffic to the public internet.

---

# PrivateLink Architecture

```text
Consumer VPC

↓

Interface Endpoint

↓

PrivateLink

↓

Provider VPC
```

Applications communicate securely over private IP addresses.

---

# Private DNS

Many Interface Endpoints support Private DNS.

Example:

Instead of:

```text
public-service.amazonaws.com
```

Applications continue using the same DNS name while traffic is routed privately.

---

# Gateway Endpoint vs Interface Endpoint

| Feature | Gateway Endpoint | Interface Endpoint |
|----------|-----------------|-------------------|
| Services | S3, DynamoDB | Most AWS Services |
| Uses ENI | No | Yes |
| Uses Route Tables | Yes | No |
| Security Groups | No | Yes |
| Cost | No hourly charge | Hourly + Data Processing |

---

# VPC Peering vs PrivateLink

| Feature | VPC Peering | PrivateLink |
|----------|------------|-------------|
| Connects Entire VPC | Yes | No |
| Connects Specific Service | No | Yes |
| Uses Private IP | Yes | Yes |
| Transitive | No | No |
| Cross Account | Yes | Yes |

---

# Common Errors

## InvalidVpcPeeringConnectionID.NotFound

Verify:

- Peering Connection ID
- Region
- AWS Account

---

## Route Not Found

The Route Table has not been updated.

Add the appropriate route.

---

## Endpoint Service Not Available

Verify:

- AWS Region
- Service Name
- Endpoint Type

---

## Security Group Blocking Traffic

For Interface Endpoints, verify:

- Inbound Rules
- Outbound Rules
- Security Group Associations

---

# Production Best Practices

- Prefer VPC Endpoints over NAT Gateway for AWS service access.
- Use Gateway Endpoints for Amazon S3 and DynamoDB.
- Use Interface Endpoints for management services such as SSM and Secrets Manager.
- Update Route Tables after creating Peering Connections.
- Use Security Groups to restrict endpoint access.
- Use Private DNS whenever possible.
- Avoid exposing internal services to the internet.
- Monitor endpoint usage and costs.

---

# Real-World Workflow

```text
Private EC2

↓

VPC Endpoint

↓

Secrets Manager

↓

Retrieve Database Credentials

↓

Connect to RDS
```

No internet connectivity is required.

---

# Architecture Note

```text
VPC
      │
      ├── VPC Peering
      ├── Gateway Endpoint
      ├── Interface Endpoint
      └── AWS PrivateLink
              │
              ▼
      Secure Private Connectivity
```

These services enable private communication between VPCs and AWS services while minimizing internet exposure.

---

# Interview Note

### Question

**What is the difference between VPC Peering and AWS PrivateLink?**

### Answer

**VPC Peering** connects two entire VPCs, allowing resources in both VPCs to communicate over private IP addresses. It provides full network connectivity between the VPCs but is non-transitive. **AWS PrivateLink**, on the other hand, exposes a specific service through Interface Endpoints without granting access to the entire VPC. PrivateLink is ideal for securely exposing applications or AWS services while minimizing the network access granted to consumers.

---

# Key Takeaways

- VPC Peering provides private connectivity between VPCs.
- VPC Peering is non-transitive.
- VPC Endpoints enable private access to AWS services.
- Gateway Endpoints support Amazon S3 and DynamoDB.
- Interface Endpoints support most AWS services.
- AWS PrivateLink securely exposes individual services without exposing an entire VPC.
- Using VPC Endpoints reduces internet dependency and improves security.