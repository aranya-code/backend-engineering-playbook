# 04 - VPC Endpoints for DynamoDB

## Overview

By default, applications access Amazon DynamoDB through **public AWS endpoints** over the internet using HTTPS.

Although the traffic is encrypted, some organizations require that traffic **never leave the AWS private network**.

To solve this problem, AWS provides **VPC Endpoints**.

A VPC Endpoint allows resources inside a Virtual Private Cloud (VPC) to communicate with DynamoDB **without traversing the public internet, NAT Gateway, Internet Gateway, or VPN**.

This improves:

- Security
- Network isolation
- Compliance
- Availability
- Cost optimization

---

# Learning Objectives

After completing this chapter, you will understand:

- What a VPC Endpoint is
- Why DynamoDB uses Gateway Endpoints
- How Gateway Endpoints work
- Endpoint Policies
- Security benefits
- Cost implications
- Production architectures
- Common mistakes

---

# The Default Connection

Without a VPC Endpoint:

```text
EC2

↓

Internet Gateway

↓

Public Internet

↓

DynamoDB Public Endpoint
```

Although traffic is encrypted with TLS, it still traverses public networking infrastructure.

---

# Using a VPC Endpoint

With a VPC Endpoint:

```text
EC2

↓

VPC

↓

Gateway Endpoint

↓

AWS Private Network

↓

DynamoDB
```

Traffic never leaves the AWS backbone network.

---

# Internal Architecture

```text
                VPC

 ┌──────────────────────────────────┐

 EC2        ECS        Lambda*

        │

        ▼

 Gateway Endpoint

        │

        ▼

 AWS Private Network

        │

        ▼

 DynamoDB
```

> *Lambda functions must be configured to run inside the VPC if they are expected to use the VPC Endpoint.

---

# Gateway Endpoint vs Interface Endpoint

AWS supports two primary endpoint types.

| Feature | Gateway Endpoint | Interface Endpoint |
|----------|-----------------|--------------------|
| Backed by ENIs | No | Yes |
| Uses Private IP | No | Yes |
| Hourly Charge | No | Yes |
| Used for DynamoDB | ✅ Yes | ❌ No |
| Used for Amazon S3 | ✅ Yes | ❌ No |
| Used for Most AWS Services | ❌ | ✅ |

**DynamoDB only supports Gateway VPC Endpoints.**

---

# How a Gateway Endpoint Works

When a request is made:

```text
Application

↓

DNS Resolution

↓

Route Table

↓

Gateway Endpoint

↓

AWS Network

↓

DynamoDB
```

AWS automatically routes the request through the endpoint.

No application code changes are required.

---

# Route Table Integration

A Gateway Endpoint is associated with one or more route tables.

```text
Private Subnet

↓

Route Table

↓

Gateway Endpoint

↓

DynamoDB
```

Instances using that route table automatically use the endpoint.

---

# Endpoint Policy

Besides IAM policies, a Gateway Endpoint can also have an **Endpoint Policy**.

Example:

```text
EC2

↓

Gateway Endpoint Policy

↓

Orders Table

↓

Allowed
```

But:

```text
Payments Table

↓

Denied
```

This provides another layer of security.

---

# Security Layers

A production request is evaluated through multiple layers.

```text
Application

↓

IAM Policy

↓

Endpoint Policy

↓

DynamoDB
```

Both policies must allow the request.

---

# Example Architecture

```text
                    VPC

        ┌───────────────────────────┐

     Private Subnet

            │

            ▼

         ECS Service

            │

            ▼

     Gateway Endpoint

            │

            ▼

        DynamoDB
```

The ECS tasks never require internet access.

---

# Lambda Architecture

Serverless applications often use:

```text
Lambda

↓

Private Subnet

↓

Gateway Endpoint

↓

DynamoDB
```

Benefits:

- Private networking
- No NAT dependency
- Lower operational complexity

---

# ECS Architecture

```text
Application

↓

Amazon ECS

↓

Private Subnet

↓

Gateway Endpoint

↓

DynamoDB
```

Containers communicate securely without exposing outbound internet traffic.

---

# EC2 Architecture

```text
EC2

↓

Private Subnet

↓

Gateway Endpoint

↓

DynamoDB
```

No Internet Gateway is required for DynamoDB access.

---

# Cost Benefits

Without VPC Endpoint:

```text
Private Subnet

↓

NAT Gateway

↓

Internet

↓

DynamoDB
```

NAT Gateway introduces:

- Hourly charges
- Data processing charges

With Gateway Endpoint:

```text
Private Subnet

↓

Gateway Endpoint

↓

DynamoDB
```

No NAT Gateway is required for DynamoDB traffic.

For workloads that make frequent DynamoDB calls from private subnets, this can significantly reduce networking costs.

---

# Security Benefits

Using Gateway Endpoints provides:

- No internet exposure
- Private AWS networking
- Reduced attack surface
- Easier compliance
- Centralized endpoint policies

---

# High Availability

Gateway Endpoints are managed AWS resources.

```text
Application

↓

Gateway Endpoint

↓

Highly Available AWS Network

↓

DynamoDB
```

There are no endpoint servers for you to manage.

---

# Endpoint Policies vs IAM Policies

| Feature | IAM Policy | Endpoint Policy |
|----------|------------|-----------------|
| Attached To | User / Role | Gateway Endpoint |
| Controls Identity | Yes | No |
| Controls Network Path | No | Yes |
| Resource Restriction | Yes | Yes |
| Used Together | ✅ | ✅ |

A request must satisfy **both** policy evaluations.

---

# Production Architecture

```text
                  Users

                     │

             Application Load Balancer

                     │

                     ▼

              ECS / EC2 / Lambda

                     │

             Private Subnets

                     │

             Gateway Endpoint

                     │

          AWS Private Backbone

                     │

                 DynamoDB
```

No internet access is required for database communication.

---

# Best Practices

- Use Gateway Endpoints for all production VPC workloads accessing DynamoDB.
- Keep compute resources in private subnets whenever possible.
- Restrict Endpoint Policies to approved tables.
- Continue enforcing least-privilege IAM policies.
- Monitor endpoint usage with CloudTrail and VPC Flow Logs.
- Remove unnecessary NAT Gateway dependencies for DynamoDB traffic.

---

# Common Mistakes

## Assuming HTTPS Alone Is Enough

HTTPS encrypts traffic, but it does not keep traffic entirely within the AWS private network.

Gateway Endpoints provide both encryption and private routing.

---

## Allowing Every Table

Poor endpoint policy:

```text
Allow

↓

All Tables
```

Better:

```text
Allow

↓

Orders

Customers
```

Restrict access to only required resources.

---

## Forgetting Route Tables

Creating a Gateway Endpoint is not sufficient.

The endpoint must be associated with the correct route tables; otherwise, workloads continue using the default network path.

---

## Relying Only on Endpoint Policies

Endpoint policies do not replace IAM.

Production systems should enforce both:

- IAM policies
- Endpoint policies

---

# Production Considerations

Large organizations commonly deploy:

```text
AWS Organizations

↓

Multiple AWS Accounts

↓

Private VPCs

↓

Gateway Endpoints

↓

DynamoDB
```

This architecture provides:

- Network isolation
- Lower networking costs
- Regulatory compliance
- Centralized security
- Simplified auditing

Gateway Endpoints are particularly valuable in financial services, healthcare, government, and enterprise environments where private connectivity is a security requirement.

---

# Interview Notes

A common interview question is:

> **Can DynamoDB be accessed without using the public internet?**

Yes. By creating a **Gateway VPC Endpoint** for DynamoDB, resources inside a VPC can communicate with DynamoDB entirely over the AWS private network.

---

Another common question is:

> **Does DynamoDB use an Interface Endpoint or a Gateway Endpoint?**

DynamoDB supports **Gateway VPC Endpoints**, not Interface Endpoints.

---

Another common question is:

> **Why use a Gateway Endpoint if traffic is already encrypted with HTTPS?**

HTTPS encrypts data in transit, but traffic may still traverse public networking infrastructure. A Gateway Endpoint keeps traffic on the AWS private backbone, improving security, compliance, and reducing dependence on internet connectivity.

---

Another common question is:

> **Can Gateway Endpoints reduce costs?**

Yes. Workloads in private subnets can access DynamoDB without routing through a NAT Gateway, reducing NAT Gateway hourly and data processing charges.

---

# Key Takeaways

- DynamoDB supports **Gateway VPC Endpoints** for private connectivity from Amazon VPC.
- Gateway Endpoints keep traffic on the AWS private backbone without using the public internet.
- They improve security, simplify compliance, and can reduce networking costs by eliminating NAT Gateway usage for DynamoDB traffic.
- Endpoint Policies provide an additional authorization layer alongside IAM policies.
- Gateway Endpoints are a standard best practice for production workloads running in private subnets.
- Combining private networking, IAM, endpoint policies, and KMS creates a strong security foundation for enterprise DynamoDB deployments.