# 03- VPC Networking

# Overview

One of the most common production issues in AWS Lambda occurs when functions are configured to run inside an Amazon VPC. While placing Lambda inside a VPC enables secure access to private resources such as Amazon RDS, ElastiCache, Amazon EFS, and internal services, it also introduces networking complexity.

Misconfigured subnets, route tables, security groups, NAT Gateways, or VPC Endpoints can prevent Lambda from accessing databases, AWS services, or even the public internet.

This chapter explains common VPC networking problems, how to troubleshoot them, and production best practices.

---

# Lambda Networking

By default, Lambda executes **outside your VPC**.

```
Lambda

↓

Internet Access

↓

AWS Managed Network
```

Advantages

- Fast startup
- Internet access
- No networking configuration

---

# Lambda Inside a VPC

When private resources are required:

```
Lambda

↓

Private Subnet

↓

Aurora
```

Lambda attaches an **Elastic Network Interface (ENI)** to access VPC resources.

---

# Typical VPC Architecture

```
                VPC

┌────────────────────────────────────┐

Public Subnet

├── Internet Gateway

├── NAT Gateway

└────────────────────────────────────┘

            │

Private Subnet

├── Lambda

├── Aurora

├── Redis

└── EFS

└────────────────────────────────────┘
```

---

# Common Networking Problems

Typical issues include:

- Cannot connect to RDS
- Cannot reach the internet
- DNS failures
- Security Group blocks
- Incorrect Route Tables
- Missing NAT Gateway
- Missing VPC Endpoint
- Timeout errors

---

# Problem: Cannot Connect to RDS

Architecture

```
Lambda

↓

Aurora

❌ Connection Failed
```

---

## Investigation

Verify:

- Database endpoint
- Security Groups
- Subnets
- Route Tables
- Database status

---

## Security Group Example

Correct

```
Lambda SG

↓

Port 5432

↓

Aurora SG
```

Incorrect

```
Lambda SG

↓

Blocked

↓

Aurora
```

---

# Problem: Lambda Cannot Access Internet

Symptoms

```
HTTPS Request

↓

Timeout
```

Examples

- Stripe
- Twilio
- OpenAI
- GitHub API

---

## Root Cause

Private subnets do not have direct internet access.

---

## Solution

```
Lambda

↓

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

Without a NAT Gateway, outbound internet access is unavailable.

---

# Problem: DNS Resolution Failure

Example

```
UnknownHostException

or

NameResolutionError
```

---

## Possible Causes

- DNS Hostnames disabled
- DNS Resolution disabled
- Incorrect endpoint
- Network configuration

---

## Investigation

Check

```
VPC

↓

DNS Hostnames

↓

Enabled
```

and

```
DNS Resolution

↓

Enabled
```

---

# Problem: Connection Timeout

Example

```
Connection timed out
```

Possible causes

- Missing route
- Security Group
- NACL
- NAT Gateway
- Incorrect endpoint

---

## Investigation Workflow

```
Lambda

↓

Subnet

↓

Route Table

↓

Security Group

↓

Destination
```

---

# Problem: Security Group Misconfiguration

Bad

```
Lambda SG

↓

No Outbound Rule
```

Good

```
Lambda SG

↓

Aurora SG

↓

5432
```

Always verify inbound and outbound rules.

---

# Problem: Network ACL Blocking Traffic

Security Groups are stateful.

Network ACLs are stateless.

Example

```
Lambda

↓

Subnet

↓

NACL

↓

Blocked
```

Review both inbound and outbound rules.

---

# Problem: Incorrect Route Table

Example

Private subnet

↓

No NAT Route

↓

Internet Access Fails

Correct route

```
0.0.0.0/0

↓

NAT Gateway
```

---

# Problem: Missing VPC Endpoint

Without a VPC Endpoint:

```
Lambda

↓

Private Subnet

↓

S3

↓

Internet

↓

NAT Required
```

With Gateway Endpoint

```
Lambda

↓

Private Subnet

↓

S3 Endpoint

↓

S3
```

Benefits

- Lower cost
- Lower latency
- Improved security

---

# Common AWS VPC Endpoints

Useful endpoints

- S3
- DynamoDB
- Secrets Manager
- Systems Manager
- CloudWatch Logs
- ECR
- STS

These services can often be accessed without a NAT Gateway.

---

# Problem: Slow Database Connection

Symptoms

```
Lambda

↓

Aurora

↓

High Latency
```

Possible causes

- DNS lookup
- Connection creation
- Network congestion

---

## Solution

Use

```
Lambda

↓

RDS Proxy

↓

Aurora
```

Benefits

- Connection pooling
- Better scalability
- Lower latency

---

# Problem: Lambda Cannot Mount EFS

Possible causes

- Wrong Security Group
- Wrong Mount Target
- Wrong Subnet
- EFS not available

Required architecture

```
Lambda

↓

Security Group

↓

EFS Mount Target
```

---

# Problem: ENI Limit Reached

Example

```
Elastic Network Interface limit exceeded
```

Cause

Large-scale Lambda execution inside a VPC.

Solutions

- Reduce unnecessary VPC usage
- Request service quota increase
- Optimize concurrency

---

# Using AWS Reachability Analyzer

AWS Reachability Analyzer helps verify connectivity.

Example

```
Lambda ENI

↓

Security Group

↓

Route Table

↓

Aurora
```

This identifies blocked paths automatically.

---

# CloudWatch Metrics

Useful metrics

- Errors
- Duration
- Throttles
- Concurrent Executions

These indicate whether networking issues are affecting execution.

---

# Using AWS X-Ray

X-Ray helps identify slow network operations.

Example

```
Lambda

↓

Database

4200 ms
```

The trace shows whether latency originates from networking or the database.

---

# Networking Checklist

Before deploying:

- [ ] Lambda in correct subnet
- [ ] Security Groups configured
- [ ] Route Tables verified
- [ ] NAT Gateway available
- [ ] DNS enabled
- [ ] VPC Endpoints configured
- [ ] Database reachable
- [ ] CloudWatch monitoring enabled

---

# Common Mistakes

❌ Putting every Lambda inside a VPC

❌ Forgetting NAT Gateway

❌ Blocking Security Groups

❌ Wrong Route Tables

❌ Ignoring DNS settings

❌ Direct database connections instead of RDS Proxy

---

# Best Practices

✅ Place Lambda inside a VPC only when necessary.

✅ Use private subnets for databases.

✅ Use NAT Gateways only when internet access is required.

✅ Use Gateway and Interface VPC Endpoints where possible.

✅ Use RDS Proxy for relational databases.

✅ Keep Security Groups minimal.

✅ Monitor networking with CloudWatch and AWS X-Ray.

---

# Real-World Production Example

```
Users

↓

API Gateway

↓

Lambda

↓

Private Subnet

↓

RDS Proxy

↓

Aurora

↓

Secrets Manager (VPC Endpoint)

↓

CloudWatch
```

This architecture provides secure private networking while maintaining observability and scalability.

---

# Senior Backend Engineering Perspective

Networking issues are among the most frequent causes of Lambda production incidents because they often manifest as generic timeouts rather than explicit errors. Senior engineers understand the entire network path—from Lambda ENIs and subnets to route tables, security groups, NAT Gateways, and VPC Endpoints—and use a systematic approach to isolate failures. Proper VPC design balances security, cost, latency, and operational simplicity.

---

# Key Takeaways

- Lambda runs outside a VPC by default and should only be placed inside a VPC when private resources must be accessed.
- Most VPC-related failures involve Security Groups, Route Tables, NAT Gateways, DNS, or VPC Endpoints.
- RDS Proxy is the preferred way to connect Lambda to relational databases.
- AWS Reachability Analyzer, CloudWatch, and AWS X-Ray are valuable tools for diagnosing networking issues.
- A well-designed VPC architecture improves security without sacrificing performance or maintainability.