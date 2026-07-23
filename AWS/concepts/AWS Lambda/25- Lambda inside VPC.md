# 25- Lambda inside VPC

# Introduction

By default, AWS Lambda functions execute in an AWS-managed network with internet connectivity (when required by AWS services). However, many enterprise applications need to access private resources such as databases, caches, or internal services that reside inside a Virtual Private Cloud (VPC).

Running Lambda inside a VPC enables secure communication with private infrastructure but also introduces networking considerations, performance implications, and additional costs.

This chapter explores how Lambda integrates with Amazon VPC, how networking works behind the scenes, common pitfalls, production architectures, and best practices.

---

# Why Run Lambda Inside a VPC?

Typical use cases include:

- Accessing Amazon RDS databases
- Connecting to Amazon ElastiCache (Redis/Memcached)
- Calling private EC2 services
- Accessing internal APIs
- Connecting to self-managed databases
- Accessing Amazon EFS
- Meeting security and compliance requirements

Example:

```
Internet

↓

API Gateway

↓

Lambda

↓

Private VPC

↓

Aurora PostgreSQL
```

---

# Default Lambda Networking

When a Lambda function is **not** attached to a VPC:

```
Client

↓

Lambda

↓

AWS Managed Network

↓

AWS Services
```

Characteristics:

- Managed networking
- Internet access available
- No subnet configuration
- No Security Groups
- Simpler deployment

---

# Lambda Attached to a VPC

When attached to a VPC:

```
Lambda

↓

Private Subnet

↓

Security Group

↓

Private Resources
```

Now Lambda behaves like a resource inside your VPC.

---

# Components Required

A Lambda running inside a VPC requires:

- VPC
- Subnets
- Security Groups
- Route Tables

Optional:

- NAT Gateway
- VPC Endpoints

---

# Architecture

```
                 Internet

                     │

             API Gateway

                     │

                 Lambda

                     │

          ┌──────────┴──────────┐

          │                     │

 Private Subnet A       Private Subnet B

          │                     │

      Aurora DB          ElastiCache
```

---

# Subnets

Lambda must be associated with one or more subnets.

AWS recommends selecting **at least two private subnets** across different Availability Zones.

Example:

```
VPC

├── Private Subnet A

├── Private Subnet B

└── Public Subnet
```

---

# Why Private Subnets?

Private subnets protect backend infrastructure.

```
Internet

↓

API Gateway

↓

Lambda

↓

Private Database
```

The database is never exposed directly to the internet.

---

# Security Groups

Security Groups act as virtual firewalls.

Example:

```
Lambda SG

↓

Allows

↓

Port 5432

↓

Aurora SG
```

Only approved traffic is permitted.

---

# Security Group Example

```
Lambda SG

Outbound

↓

Aurora SG

Port 5432
```

Aurora Security Group:

```
Inbound

↓

Lambda SG

Port 5432
```

This follows the principle of least privilege.

---

# Route Tables

Route tables determine where network traffic is sent.

Example:

```
Private Subnet

↓

Route Table

↓

NAT Gateway

↓

Internet
```

Without the correct routes, Lambda may not reach external services.

---

# Internet Access

A common misconception:

> Putting Lambda inside a VPC does **not** automatically provide internet access.

To reach the internet:

```
Private Subnet

↓

Route Table

↓

NAT Gateway

↓

Internet Gateway

↓

Internet
```

---

# NAT Gateway

A NAT Gateway enables outbound internet connectivity for resources in private subnets.

Example:

```
Lambda

↓

Private Subnet

↓

NAT Gateway

↓

Stripe API
```

Use cases:

- Calling third-party APIs
- Downloading updates
- Accessing public AWS endpoints (unless using VPC Endpoints)

---

# Without NAT Gateway

```
Lambda

↓

Private Subnet

↓

Internet

❌ Blocked
```

Common symptoms:

- Connection timeout
- DNS resolution failure
- Unable to reach external APIs

---

# VPC Endpoints

Instead of routing through the internet, Lambda can connect directly to AWS services.

Example:

```
Lambda

↓

VPC Endpoint

↓

Amazon S3
```

Benefits:

- Lower latency
- No NAT Gateway charges
- Private connectivity
- Improved security

---

# Common AWS Services Supporting VPC Endpoints

- Amazon S3
- DynamoDB
- Secrets Manager
- Systems Manager
- CloudWatch Logs
- ECR
- KMS
- SNS
- SQS

---

# Example Architecture Using VPC Endpoints

```
Lambda

↓

Private Subnet

↓

VPC Endpoint

↓

Secrets Manager

↓

Retrieve Credentials
```

Traffic never leaves the AWS network.

---

# Lambda ENIs

When Lambda connects to a VPC, AWS creates **Elastic Network Interfaces (ENIs)**.

```
Lambda

↓

Elastic Network Interface

↓

Private IP

↓

VPC
```

The ENI enables network communication inside the VPC.

---

# ENI Lifecycle

```
Invoke Lambda

↓

Create / Reuse ENI

↓

Attach to Subnet

↓

Execute Function
```

Modern Lambda networking reuses ENIs efficiently, reducing cold start overhead compared to earlier implementations.

---

# Multi-AZ Configuration

For high availability:

```
Availability Zone A

↓

Private Subnet

---------------------

Availability Zone B

↓

Private Subnet
```

Configure Lambda with subnets in multiple Availability Zones.

---

# Connecting to Amazon RDS

Example:

```
Lambda

↓

Private Subnet

↓

Security Group

↓

Aurora PostgreSQL
```

Best practice:

```
Lambda

↓

RDS Proxy

↓

Aurora
```

Benefits:

- Connection pooling
- Better scalability
- Reduced database load

---

# Connecting to Amazon ElastiCache

```
Lambda

↓

Redis

↓

Cache Lookup

↓

Database (If Needed)
```

Benefits:

- Faster response times
- Reduced database queries

---

# Connecting to Amazon EFS

```
Lambda

↓

Mount Target

↓

Amazon EFS
```

Ideal for:

- Shared files
- ML models
- Large datasets

---

# Accessing External APIs

Architecture:

```
Lambda

↓

Private Subnet

↓

NAT Gateway

↓

GitHub API

Stripe API

OpenAI API
```

---

# Monitoring

Useful CloudWatch metrics:

- Duration
- Errors
- Throttles
- Concurrent Executions

For networking issues:

- VPC Flow Logs
- CloudWatch Logs
- AWS X-Ray

---

# Common Problems

## Database Connection Timeout

Possible causes:

- Incorrect Security Group
- Wrong port
- Database unavailable
- Incorrect subnet
- Missing route

---

## Cannot Reach Internet

Usually caused by:

- No NAT Gateway
- Incorrect Route Table
- Network ACL restrictions

---

## Secrets Manager Timeout

Often indicates:

- Missing VPC Endpoint
- No NAT Gateway
- DNS configuration issue

---

## High Latency

Possible causes:

- Cold starts
- Large initialization
- Slow database queries
- External API delays

---

# Best Practices

✅ Use private subnets for Lambda.

✅ Configure multiple Availability Zones.

✅ Use Security Groups instead of broad CIDR rules.

✅ Use VPC Endpoints whenever possible.

✅ Use RDS Proxy for relational databases.

✅ Monitor networking with VPC Flow Logs.

✅ Apply least-privilege IAM permissions.

✅ Avoid placing databases in public subnets.

---

# Real-World Architecture

```
                 Users

                   │

             CloudFront

                   │

             API Gateway

                   │

                Lambda

                   │

        ┌──────────┴──────────┐

        │                     │

   Secrets Manager      Amazon S3
 (VPC Endpoint)      (Gateway Endpoint)

                   │

              RDS Proxy

                   │

          Aurora PostgreSQL

                   │

             ElastiCache
```

---

# Senior Backend Engineering Perspective

Connecting Lambda to a VPC is common in enterprise applications but requires thoughtful network design. The primary goals are security, availability, and efficient connectivity.

Senior engineers typically:

- Keep Lambda functions in private subnets.
- Use multiple Availability Zones for resilience.
- Minimize NAT Gateway usage by adopting VPC Endpoints where supported.
- Use RDS Proxy to prevent database connection exhaustion.
- Carefully configure Security Groups to allow only required traffic.
- Monitor network behavior using CloudWatch, VPC Flow Logs, and AWS X-Ray.

Understanding these networking patterns is essential for building secure, scalable, and production-ready serverless applications.

---

# Interview Questions

### Beginner

- Why would you run Lambda inside a VPC?
- What resources are required to connect Lambda to a VPC?
- Does Lambda automatically get internet access when placed in a VPC?

### Intermediate

- Explain the role of Security Groups in Lambda networking.
- Why is a NAT Gateway required for outbound internet access?
- What are VPC Endpoints, and when should they be used?

### Senior

- Design a highly available Lambda architecture that accesses Aurora PostgreSQL securely.
- Compare using a NAT Gateway versus VPC Endpoints for AWS service access.
- How would you troubleshoot a Lambda function timing out while accessing a private database?
- Explain how ENIs, subnets, Security Groups, and Route Tables work together when Lambda is attached to a VPC.

---

# Key Takeaways

- Lambda can securely access private resources by attaching to a VPC.
- Running inside a VPC requires proper subnet, Security Group, and route table configuration.
- Private subnets, RDS Proxy, and VPC Endpoints are common production best practices.
- NAT Gateways provide outbound internet access for private Lambda functions but introduce additional cost.
- A well-designed VPC architecture balances security, availability, performance, and operational efficiency.