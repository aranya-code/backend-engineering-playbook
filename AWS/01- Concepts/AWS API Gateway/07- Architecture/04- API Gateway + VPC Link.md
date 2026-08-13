# API Gateway + VPC Link

## Overview

Amazon API Gateway is a fully managed service that can expose APIs to the public internet. However, many enterprise applications run entirely inside private Amazon VPCs and should never be directly accessible from the internet.

Examples include:

- Internal microservices
- Banking applications
- Healthcare systems
- ERP systems
- Legacy applications
- Containerized services running on ECS or EKS

**VPC Link** enables API Gateway to securely connect to private resources inside a VPC without exposing those resources publicly.

It acts as a secure bridge between API Gateway and backend services hosted behind an **Application Load Balancer (ALB)** or **Network Load Balancer (NLB)**.

---

# Why VPC Link?

Without VPC Link:

```text
Internet

↓

API Gateway

↓

Private ECS Service
```

Problem:

```text
❌ Not Possible
```

Private services cannot be accessed directly.

With VPC Link:

```text
Internet

↓

API Gateway

↓

VPC Link

↓

Internal ALB

↓

Private ECS Service
```

Communication remains secure.

---

# High-Level Architecture

```text
                 Internet

                    │

                    ▼

           Amazon API Gateway

                    │

                VPC Link

                    │

                    ▼

      Internal Application Load Balancer

                    │

        ┌───────────┼───────────┐

        ▼           ▼           ▼

    ECS Task     ECS Task     ECS Task
```

The ECS tasks remain private inside the VPC.

---

# What is VPC Link?

A **VPC Link** is a managed network connection between:

```text
API Gateway

↓

Private Load Balancer

↓

Private Backend
```

It enables API Gateway to invoke private services securely.

---

# Supported Load Balancers

VPC Link supports:

- Application Load Balancer (ALB)
- Network Load Balancer (NLB)

Example:

```text
API Gateway

↓

VPC Link

↓

ALB
```

or

```text
API Gateway

↓

VPC Link

↓

NLB
```

---

# Request Flow

```text
Client

↓

HTTPS

↓

API Gateway

↓

Authentication

↓

Request Validation

↓

VPC Link

↓

ALB

↓

Backend Service

↓

Response

↓

Client
```

---

# Why Not Make ALB Public?

Public ALB:

```text
Internet

↓

ALB
```

Problems:

- Direct backend exposure
- Authentication handled by application
- Larger attack surface
- Harder API management

Private ALB:

```text
Internet

↓

API Gateway

↓

Private ALB
```

Provides much stronger security.

---

# Internal Networking

Everything after API Gateway stays inside AWS.

```text
API Gateway

↓

VPC Link

↓

Private VPC

↓

Backend
```

Traffic never leaves the AWS network.

---

# Security Layers

```text
Client

↓

JWT Authentication

↓

API Gateway

↓

Resource Policy

↓

VPC Link

↓

Private ALB

↓

Backend
```

Multiple layers protect the application.

---

# Integration with ECS

```text
API Gateway

↓

VPC Link

↓

ALB

↓

Amazon ECS

↓

Containers
```

One of the most common production architectures.

---

# Integration with EC2

```text
API Gateway

↓

VPC Link

↓

ALB

↓

EC2 Auto Scaling Group
```

Useful for traditional web applications.

---

# Integration with EKS

```text
API Gateway

↓

VPC Link

↓

ALB

↓

Amazon EKS

↓

Pods
```

Suitable for Kubernetes workloads.

---

# Microservices Example

```text
API Gateway

↓

VPC Link

↓

Internal ALB

│

├── User Service

├── Order Service

├── Payment Service

└── Inventory Service
```

All services remain private.

---

# Authentication Flow

```text
Client

↓

JWT Token

↓

API Gateway

↓

Validation

↓

VPC Link

↓

Backend
```

Unauthorized requests never reach backend services.

---

# High Availability

```text
API Gateway

↓

VPC Link

↓

ALB

↓

AZ-1

↓

Backend

------------------

AZ-2

↓

Backend
```

The architecture supports Multi-AZ deployments.

---

# Scalability

```text
Traffic

↓

API Gateway

↓

VPC Link

↓

ALB

↓

Auto Scaling

↓

Backend
```

Backend services scale independently.

---

# Monitoring

Monitor:

API Gateway:

- Request Count
- Latency
- 4XX Errors
- 5XX Errors

ALB:

- Healthy Hosts
- Request Count
- Response Time

Backend:

- CPU
- Memory
- Application Metrics

---

# Logging

Logs are available from:

```text
API Gateway

↓

CloudWatch Logs

-------------------

ALB Access Logs

↓

Amazon S3

-------------------

Application Logs

↓

CloudWatch Logs
```

These logs provide complete request visibility.

---

# Common Use Cases

VPC Link is commonly used for:

- Private ECS services
- Private EC2 applications
- Amazon EKS clusters
- Internal REST APIs
- Enterprise applications
- Legacy systems migrated to AWS
- Banking applications
- Healthcare platforms

---

# Advantages

- Secure private connectivity
- No public backend exposure
- Integrates with existing VPC architectures
- Supports ECS, EC2, and EKS
- Keeps API Gateway as the single public endpoint
- Simplifies backend security

---

# Limitations

- Additional networking configuration
- Requires an ALB or NLB
- Additional AWS cost
- Slightly higher latency than direct integrations
- Backend infrastructure must still be managed

---

# Production Architecture

```text
                     Internet

                         │

                         ▼

                  Amazon Route 53

                         │

                         ▼

                   CloudFront

                         │

                         ▼

                     AWS WAF

                         │

                         ▼

                 Amazon API Gateway

                         │

                      VPC Link

                         │

                         ▼

         Internal Application Load Balancer

                         │

        ┌────────────────┼────────────────┐

        ▼                ▼                ▼

   ECS Service      EC2 Service      EKS Cluster

                         │

                         ▼

          PostgreSQL • Redis • S3
```

This is one of the most common enterprise architectures on AWS.

---

# VPC Link vs Lambda Integration

| Feature | Lambda Integration | VPC Link |
|----------|-------------------|-----------|
| Backend | Lambda | ALB/NLB |
| Infrastructure | Serverless | VPC Resources |
| Long-running Applications | No | Yes |
| Docker Containers | Limited | Yes |
| Traditional Applications | No | Yes |
| VPC Connectivity | Optional | Primary Purpose |

---

# VPC Link vs Private API

| VPC Link | Private API |
|-----------|-------------|
| Connects API Gateway to private backends | Restricts who can access API Gateway |
| Backend Networking Feature | API Exposure Feature |
| Used with ALB/NLB | Used with Interface VPC Endpoints |
| Backend remains private | API itself remains private |

These features are complementary rather than competing.

---

# Best Practices

- Keep backend load balancers private.
- Use API Gateway as the only public entry point.
- Enable authentication before requests reach VPC Link.
- Deploy backend services across multiple Availability Zones.
- Monitor API Gateway, ALB, and backend services independently.
- Use Auto Scaling for ECS or EC2 workloads.
- Enable CloudWatch Logs and AWS X-Ray.
- Combine VPC Link with AWS WAF for additional protection.

---

# Common Interview Questions

### What is VPC Link?

VPC Link is a managed network connection that allows Amazon API Gateway to securely invoke private services running behind an Application Load Balancer or Network Load Balancer inside a VPC.

---

### Why is VPC Link required?

API Gateway cannot directly access private resources inside a VPC. VPC Link provides secure connectivity without exposing backend services to the public internet.

---

### Can VPC Link connect directly to an ECS task?

No.

VPC Link connects to an **Application Load Balancer (ALB)** or **Network Load Balancer (NLB)**, which then routes requests to ECS tasks or other backend resources.

---

### Is VPC Link only for ECS?

No.

VPC Link works with any backend behind an ALB or NLB, including ECS, EC2, Amazon EKS, and other private services.

---

### What is the difference between VPC Link and Private API?

VPC Link provides secure connectivity **from API Gateway to private backend services**, whereas Private APIs restrict **who can invoke API Gateway itself** using Interface VPC Endpoints and AWS PrivateLink.

---

# Key Takeaways

- VPC Link securely connects Amazon API Gateway to private backend services running inside an Amazon VPC.
- It enables API Gateway to integrate with private ALBs and NLBs without exposing backend services to the public internet.
- VPC Link is commonly used with Amazon ECS, EC2, Amazon EKS, and enterprise applications requiring private networking.
- Authentication, authorization, and request validation are handled by API Gateway before requests reach the backend.
- Combining API Gateway, VPC Link, private load balancers, and Auto Scaling creates a secure, scalable, and production-ready architecture for enterprise workloads.