# Private APIs & VPC Endpoints

## Overview

Not every API should be accessible from the public internet.

Many enterprise applications expose APIs that are intended only for:

- Internal microservices
- Corporate applications
- Backend systems
- Banking applications
- Healthcare systems
- Government workloads

For these scenarios, Amazon API Gateway supports **Private APIs**, allowing APIs to be accessed only from within an Amazon VPC through **AWS PrivateLink (Interface VPC Endpoints)**.

Unlike Regional or Edge-Optimized APIs, Private APIs are **not publicly accessible**.

---

# Public API vs Private API

Public API:

```text
Internet

↓

API Gateway

↓

Backend
```

Anyone with network connectivity can reach the endpoint (subject to authentication and authorization).

Private API:

```text
VPC

↓

Interface VPC Endpoint

↓

Private API Gateway

↓

Backend
```

Traffic never traverses the public internet.

---

# What is AWS PrivateLink?

AWS PrivateLink enables private connectivity between VPCs and AWS services without requiring:

- Internet Gateway
- NAT Gateway
- VPN
- Direct public IP addresses

Architecture:

```text
EC2

↓

VPC Endpoint

↓

AWS PrivateLink

↓

API Gateway
```

Communication remains entirely within the AWS network.

---

# Architecture

```text
                EC2 Instance

                     │

                     ▼

          Interface VPC Endpoint

                     │

             AWS PrivateLink

                     │

                     ▼

         Private API Gateway

                     │

                     ▼

        Lambda / ECS / EC2 Backend
```

The API is inaccessible from the internet.

---

# Interface VPC Endpoint

Private APIs require an **Interface VPC Endpoint**.

Example:

```text
com.amazonaws.region.execute-api
```

This endpoint creates private network interfaces inside the VPC.

---

# Request Flow

```text
Application

↓

Private DNS

↓

VPC Endpoint

↓

API Gateway

↓

Backend
```

All communication remains within AWS.

---

# Endpoint Policies

Interface VPC Endpoints support IAM policies.

Example:

```text
Allow

↓

Specific API

↓

Specific Account
```

This provides another layer of security.

---

# Resource Policies

Private APIs commonly use Resource Policies.

Example:

```text
Allow

↓

Specific VPC

↓

Specific VPC Endpoint
```

Only approved networks may invoke the API.

---

# Restricting by VPC

Example policy:

```text
Allow

VPC-A

-------------------

Deny

VPC-B
```

Only workloads inside VPC-A can access the API.

---

# Restricting by VPC Endpoint

Instead of allowing an entire VPC:

```text
Allow

vpce-123456
```

Only requests through that endpoint succeed.

---

# Private DNS

Private DNS simplifies API access.

Without Private DNS:

```text
vpce-xxxx.execute-api.region.amazonaws.com
```

With Private DNS:

```text
api.internal.company.com
```

Applications use familiar hostnames.

---

# DNS Resolution

```text
Application

↓

Private DNS

↓

VPC Endpoint

↓

Private API
```

No public DNS lookup occurs.

---

# Security Model

Multiple security layers work together.

```text
IAM

↓

Resource Policy

↓

VPC Endpoint Policy

↓

Backend Authorization
```

Even if one layer is misconfigured, additional layers continue protecting the API.

---

# Private API with Lambda

```text
Private API

↓

Lambda

↓

DynamoDB
```

A common serverless architecture for internal systems.

---

# Private API with ECS

```text
Private API

↓

VPC Link

↓

Internal Load Balancer

↓

Amazon ECS
```

Frequently used for containerized microservices.

---

# Hybrid Architecture

Corporate applications often combine VPN or Direct Connect with Private APIs.

```text
Corporate Network

↓

VPN / Direct Connect

↓

Amazon VPC

↓

Private API Gateway
```

Internal users securely access APIs without exposing them publicly.

---

# Private API vs Regional API

| Private API | Regional API |
|--------------|--------------|
| Private network only | Public endpoint |
| Uses PrivateLink | Internet accessible |
| Requires Interface VPC Endpoint | No VPC Endpoint required |
| Ideal for internal systems | Ideal for public services |

---

# Private API vs Edge-Optimized API

| Private API | Edge-Optimized API |
|--------------|-------------------|
| Internal access only | Global public access |
| No CloudFront | Uses CloudFront |
| Enterprise workloads | Customer-facing APIs |

---

# Common Use Cases

Private APIs are commonly used for:

- Internal microservices
- Enterprise applications
- Banking systems
- Healthcare platforms
- ERP integrations
- Internal administrative APIs
- Corporate automation
- Secure service-to-service communication

---

# High Availability

Private APIs remain highly available.

```text
VPC Endpoint

↓

API Gateway

↓

Multiple AZs
```

Interface Endpoints are deployed across Availability Zones for resilience.

---

# Monitoring

Private APIs integrate with:

- CloudWatch Metrics
- CloudWatch Logs
- Access Logs
- AWS X-Ray

Monitoring capabilities are identical to public APIs.

---

# Cost Considerations

Additional costs include:

- Interface VPC Endpoints
- PrivateLink hourly charges
- Data processing charges

These costs are generally acceptable for enterprise security requirements.

---

# Real-World Example

A banking platform exposes internal APIs.

```text
ATM Systems

↓

Private API

↓

Account Service

↓

Payment Service

↓

Customer Database
```

No public internet access is allowed.

Only applications inside the organization's AWS network can invoke the APIs.

---

# Best Practices

- Use Private APIs for internal-only workloads.
- Restrict access using Resource Policies.
- Limit access to approved VPC Endpoints.
- Enable Private DNS for simplified service discovery.
- Combine IAM, Resource Policies, and Endpoint Policies for defense in depth.
- Monitor Private APIs using CloudWatch and X-Ray.
- Avoid exposing sensitive internal services through public APIs.

---

# Common Interview Questions

### What is a Private API in API Gateway?

A Private API is an API Gateway endpoint that is accessible only from within an Amazon VPC using AWS PrivateLink through an Interface VPC Endpoint.

---

### Which AWS service enables Private APIs?

**AWS PrivateLink**, using an **Interface VPC Endpoint**.

---

### Can Private APIs be accessed from the public internet?

No.

Private APIs are accessible only through authorized Interface VPC Endpoints within a VPC.

---

### What is the purpose of a Resource Policy in a Private API?

Resource Policies restrict which AWS accounts, VPCs, or VPC Endpoints are allowed to invoke the API.

---

### When should you use a Private API instead of a Regional API?

Use a Private API when the API is intended only for internal applications, microservices, or enterprise systems that should never be exposed to the public internet.

---

# Key Takeaways

- Private APIs allow Amazon API Gateway to expose endpoints only within Amazon VPCs using AWS PrivateLink.
- Interface VPC Endpoints provide secure, private connectivity without traversing the public internet.
- Resource Policies and VPC Endpoint Policies provide fine-grained access control.
- Private APIs are ideal for internal microservices, enterprise integrations, and highly regulated workloads.
- Combining Private APIs with CloudWatch, X-Ray, and layered security creates a secure, production-ready internal API platform.