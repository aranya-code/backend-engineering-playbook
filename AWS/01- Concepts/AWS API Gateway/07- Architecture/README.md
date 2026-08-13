# Architecture

The **Architecture** section demonstrates how Amazon API Gateway integrates with other AWS services to build secure, scalable, and production-ready applications.

Rather than focusing on individual API Gateway features, this section explores **real-world deployment architectures** used by backend engineers and cloud architects. You'll learn how API Gateway acts as the front door for serverless applications, containerized workloads, microservices, secure authentication systems, content delivery networks, and web application firewalls.

By the end of this section, you'll understand how to combine API Gateway with complementary AWS services to build modern enterprise APIs.

---

# Quick Navigation

| Chapter | Topic |
|----------|-------|
| [01 - API Gateway + Lambda](./01-%20API%20Gateway%20%2B%20Lambda.md) | Build fully serverless APIs by integrating API Gateway with AWS Lambda. |
| [02 - API Gateway + ECS](./02-%20API%20Gateway%20%2B%20ECS.md) | Expose containerized applications running on Amazon ECS through API Gateway. |
| [03 - API Gateway + Application Load Balancer (ALB)](./03-%20API%20Gateway%20%2B%20ALB.md) | Learn how API Gateway integrates with ALBs for scalable Layer 7 traffic distribution. |
| [04 - API Gateway + VPC Link](./04-%20API%20Gateway%20%2B%20VPC%20Link.md) | Securely connect API Gateway to private resources inside a VPC using VPC Link. |
| [05 - API Gateway + Microservices](./05-%20API%20Gateway%20%2B%20Microservices.md) | Design microservices architectures with API Gateway as the unified entry point. |
| [06 - API Gateway + Amazon Cognito](./06-%20API%20Gateway%20%2B%20Amazon%20Cognito.md) | Secure APIs using Amazon Cognito, JWT authentication, and OAuth 2.0. |
| [07 - API Gateway + CloudFront](./07-%20API%20Gateway%20%2B%20CloudFront.md) | Improve API performance using CloudFront edge locations, caching, and global delivery. |
| [08 - API Gateway + AWS WAF](./08-%20API%20Gateway%20%2B%20AWS%20WAF.md) | Protect APIs against common web attacks using AWS WAF and managed security rules. |

---

# Learning Path

```text
Serverless APIs

        │

        ▼

Containerized APIs

        │

        ▼

Private Networking

        │

        ▼

Microservices

        │

        ▼

Authentication

        │

        ▼

Global Performance

        │

        ▼

Security
```

Each chapter builds on the previous one, progressing from simple integrations to complete production architectures.

---

# Architecture Overview

```text
                        Users

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

      ┌───────────────────┼────────────────────┐

      ▼                   ▼                    ▼

   Lambda            VPC Link              Cognito

                          │

                          ▼

                 Application Load Balancer

                          │

          ┌───────────────┼───────────────┐

          ▼               ▼               ▼

      ECS Service     EC2 Service     EKS Cluster

                          │

                          ▼

             DynamoDB • Aurora • Redis • S3
```

This represents a common enterprise architecture for public APIs on AWS.

---

# Integration Patterns

This section covers four major integration patterns.

## Serverless

```text
API Gateway

↓

Lambda

↓

DynamoDB
```

Ideal for event-driven applications and REST APIs.

---

## Containerized

```text
API Gateway

↓

VPC Link

↓

ALB

↓

Amazon ECS
```

Suitable for Docker-based workloads and long-running services.

---

## Microservices

```text
API Gateway

↓

User Service

↓

Order Service

↓

Payment Service
```

Provides a unified API while allowing services to evolve independently.

---

## Secure Public APIs

```text
Client

↓

CloudFront

↓

AWS WAF

↓

API Gateway

↓

Amazon Cognito

↓

Backend
```

Combines security, authentication, and global performance.

---

# What You'll Learn

After completing this section, you'll be able to:

- Build serverless APIs using API Gateway and Lambda.
- Expose containerized workloads running on ECS through API Gateway.
- Securely connect API Gateway to private VPC resources using VPC Link.
- Design scalable microservices architectures.
- Authenticate users using Amazon Cognito and JWT tokens.
- Improve global API performance using CloudFront.
- Protect APIs from common web attacks using AWS WAF.
- Choose the appropriate integration architecture for different workloads.

---

# Choosing the Right Integration

| Scenario | Recommended Architecture |
|----------|--------------------------|
| Event-driven APIs | API Gateway + Lambda |
| Docker Containers | API Gateway + ECS |
| Private Applications | API Gateway + VPC Link |
| Enterprise Web Applications | API Gateway + ALB |
| Microservices | API Gateway + Microservices |
| User Authentication | API Gateway + Amazon Cognito |
| Global Public APIs | API Gateway + CloudFront |
| Internet-Facing APIs | API Gateway + AWS WAF |

---

# Production Reference Architecture

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

              JWT Authentication

                          │

                Request Validation

                          │

                     VPC Link

                          │

                          ▼

            Internal Application Load Balancer

                          │

          ┌───────────────┼───────────────┐

          ▼               ▼               ▼

      ECS Service    Lambda API     EC2 Service

                          │

                          ▼

            DynamoDB • Aurora • Redis
```

This layered architecture is representative of many enterprise production environments.

---

# Architecture Decision Guide

| Requirement | Recommended Service |
|-------------|---------------------|
| Fully Serverless | Lambda |
| Docker Containers | ECS |
| Traditional Web Applications | ALB + EC2 |
| Private Backend Connectivity | VPC Link |
| Authentication | Amazon Cognito |
| Global Performance | CloudFront |
| Web Application Firewall | AWS WAF |
| Public API Management | API Gateway |

---

# Best Practices

- Keep API Gateway as the single public entry point.
- Place backend services in private subnets whenever possible.
- Use VPC Link to access private workloads.
- Centralize authentication using Amazon Cognito.
- Deploy AWS WAF in front of internet-facing APIs.
- Use CloudFront for globally distributed applications.
- Keep backend services stateless to simplify scaling.
- Monitor every layer using CloudWatch and AWS X-Ray.
- Apply the principle of least privilege to IAM roles and policies.
- Automate deployments using Infrastructure as Code and CI/CD pipelines.

---

# Enterprise Architecture Principles

This section emphasizes several key architectural principles:

- **Separation of Concerns** – API Gateway manages API concerns while backend services focus on business logic.
- **Defense in Depth** – Combine CloudFront, WAF, API Gateway, Cognito, and backend security for layered protection.
- **Scalability** – Design every layer to scale independently.
- **Loose Coupling** – Backend implementations can change without affecting clients.
- **High Availability** – Use Multi-AZ deployments and managed AWS services wherever possible.

Following these principles results in secure, resilient, and maintainable API platforms suitable for enterprise production workloads.