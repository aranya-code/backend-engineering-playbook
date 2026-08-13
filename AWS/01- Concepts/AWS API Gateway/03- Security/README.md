# API Gateway Security

API security is one of the most critical responsibilities of Amazon API Gateway. Before a request reaches your backend service, API Gateway can authenticate users, authorize access, validate requests, enforce rate limits, apply resource policies, inspect traffic with AWS WAF, and encrypt communication using HTTPS or Mutual TLS (mTLS).

This section provides a comprehensive guide to securing APIs using the native security features of Amazon API Gateway. It covers authentication mechanisms, authorization models, traffic protection, certificate management, and production security best practices.

By the end of this section, you'll understand how to build secure, scalable, and production-ready APIs on AWS.

---

# Quick Navigation

| Chapter | Topic |
|----------|-------|
| [01 - API Security Overview](./01-%20API%20Security%20Overview.md) | Learn the security architecture of API Gateway, authentication vs authorization, and the layered security model used in production. |
| [02 - IAM Authorization](./02-%20IAM%20Authorization.md) | Understand how API Gateway uses IAM policies and AWS Signature Version 4 (SigV4) for secure service-to-service communication. |
| [03 - Resource Policies](./03-%20Resource%20Policies.md) | Learn how to control who can invoke your APIs using resource-based IAM policies, IP restrictions, VPC endpoints, and cross-account access. |
| [04 - Lambda Authorizers](./04-%20Lambda%20Authorizers.md) | Implement custom authentication and authorization logic using AWS Lambda for legacy systems and advanced security requirements. |
| [05 - Amazon Cognito Authorizers](./05-%20Amazon%20Cognito%20Authorizers.md) | Learn how API Gateway integrates with Amazon Cognito User Pools for managed JWT-based authentication. |
| [06 - JWT Authorizers (HTTP API)](./06-%20JWT%20Authorizers%20(HTTP%20API).md) | Explore native JWT validation for HTTP APIs using OpenID Connect (OIDC) identity providers such as Cognito, Auth0, and Okta. |
| [07 - API Keys & Usage Plans](./07-%20API%20Keys%20%26%20Usage%20Plans.md) | Understand API consumer identification, request quotas, rate limiting, subscription plans, and why API Keys are not authentication. |
| [08 - Mutual TLS (mTLS)](./08-%20Mutual%20TLS%20(mTLS).md) | Learn how Mutual TLS provides strong client authentication using X.509 certificates for enterprise and B2B APIs. |
| [09 - AWS WAF Integration](./09-%20AWS%20WAF%20Integration.md) | Protect APIs from SQL Injection, XSS, bots, malicious IPs, and HTTP floods using AWS Web Application Firewall. |
| [10 - Custom Domain Names & ACM](./10-%20Custom%20Domain%20Names%20%26%20ACM.md) | Configure branded API endpoints, HTTPS certificates with AWS Certificate Manager, Base Path Mapping, and production-ready custom domains. |
| [11 - Security Best Practices](./11-%20Security%20Best%20Practices.md) | Learn production-grade security recommendations, defense-in-depth, monitoring, secret management, and common mistakes to avoid. |

---

# Learning Path

```text
API Security Fundamentals

          │

          ▼

IAM Authorization

          │

          ▼

Resource Policies

          │

          ▼

Lambda Authorizers

          │

          ▼

Amazon Cognito

          │

          ▼

JWT Authorizers

          │

          ▼

API Keys & Usage Plans

          │

          ▼

Mutual TLS (mTLS)

          │

          ▼

AWS WAF

          │

          ▼

Custom Domain Names & ACM

          │

          ▼

Security Best Practices
```

The chapters move from core authentication and authorization concepts to advanced production security features.

---

# Prerequisites

Before studying API Gateway Security, you should understand:

- API Gateway fundamentals
- REST APIs and HTTP
- HTTPS and TLS basics
- IAM fundamentals
- JSON Web Tokens (JWT)
- AWS Lambda basics
- Basic networking concepts

---

# What You'll Learn

After completing this section, you'll be able to:

- Design secure APIs using multiple layers of protection.
- Choose the right authentication mechanism for different workloads.
- Implement IAM Authorization for AWS workloads.
- Restrict API access using Resource Policies.
- Build custom authentication with Lambda Authorizers.
- Secure APIs using Amazon Cognito and JWT Authorizers.
- Configure API Keys and Usage Plans correctly.
- Implement Mutual TLS (mTLS) for B2B integrations.
- Protect APIs with AWS WAF.
- Configure production-ready Custom Domain Names and ACM certificates.
- Apply industry-standard API security best practices.

---

# Security Architecture

```text
                 Internet
                     │
                     ▼
               AWS Shield
                     │
                     ▼
                AWS WAF
                     │
                     ▼
          Custom Domain (HTTPS)
                     │
                     ▼
          Amazon API Gateway
                     │
      Authentication & Authorization
                     │
         Resource Policies
                     │
        Throttling & Usage Plans
                     │
                     ▼
      Lambda / ECS / EC2 Backend
                     │
                     ▼
                 Database
```

A secure API uses multiple independent security controls rather than relying on a single authentication mechanism.

---

# Authentication Decision Guide

```text
Who is calling the API?

        │

        ├──────────── AWS Service
        │
        ▼
IAM Authorization

        │

        ├──────────── End User
        │
        ▼
Cognito or JWT Authorizer

        │

        ├──────────── Legacy Authentication
        │
        ▼
Lambda Authorizer

        │

        ├──────────── Partner Organization
        │
        ▼
Mutual TLS (mTLS)

        │

        └──────────── Public API Consumers
                 │
                 ▼
API Keys + Usage Plans
```

Choosing the correct authentication mechanism simplifies security while reducing operational complexity.

---

# Security Layer Comparison

| Feature | Primary Purpose |
|----------|-----------------|
| IAM Authorization | Secure AWS identities and service-to-service communication |
| Resource Policies | Restrict who can invoke an API |
| Lambda Authorizers | Custom authentication and authorization |
| Cognito Authorizers | Managed user authentication |
| JWT Authorizers | Native JWT validation for HTTP APIs |
| API Keys | Consumer identification and usage tracking |
| Usage Plans | Rate limits and request quotas |
| Mutual TLS | Strong client certificate authentication |
| AWS WAF | Protection against web attacks |
| ACM | HTTPS certificate management |

Each feature addresses a different aspect of API security and should be combined where appropriate.

---

# Production Recommendations

For most production APIs:

- Always use HTTPS with ACM-managed certificates.
- Use Cognito or JWT Authorizers for customer-facing applications.
- Use IAM Authorization for AWS service-to-service communication.
- Protect internet-facing APIs with AWS WAF.
- Enable throttling and Usage Plans where appropriate.
- Apply Resource Policies to restrict trusted callers.
- Use Mutual TLS for enterprise or B2B integrations.
- Enable CloudWatch logging and CloudTrail auditing.
- Follow the Principle of Least Privilege for IAM permissions.
- Store secrets in AWS Secrets Manager or Systems Manager Parameter Store.

---

# Real-World Architectures

### Public REST API

```text
Internet

↓

AWS WAF

↓

API Gateway

↓

JWT Authorizer

↓

Lambda

↓

Amazon DynamoDB
```

---

### Internal Microservice API

```text
Amazon ECS

↓

IAM Authorization

↓

API Gateway

↓

Lambda

↓

Amazon RDS
```

---

### Banking API

```text
Partner Bank

↓

Mutual TLS

↓

API Gateway

↓

JWT Validation

↓

Payment Service
```

---

### SaaS Platform

```text
Customer

↓

Amazon Cognito

↓

API Gateway

↓

Usage Plans

↓

Microservices
```

---

# Interview Focus

This section prepares you for common Backend Developer, Cloud Engineer, and AWS Solution Architect interview questions, including:

- IAM Authorization vs JWT Authorizers
- Resource Policies vs IAM Policies
- Cognito vs Lambda Authorizers
- API Keys vs Authentication
- Mutual TLS (mTLS)
- AWS WAF integration
- Custom Domain Names and ACM
- API Gateway security architecture
- Production security best practices
- Defense in Depth

---

# Repository Structure

```text
security/
│
├── 01- API Security Overview.md
├── 02- IAM Authorization.md
├── 03- Resource Policies.md
├── 04- Lambda Authorizers.md
├── 05- Amazon Cognito Authorizers.md
├── 06- JWT Authorizers (HTTP API).md
├── 07- API Keys & Usage Plans.md
├── 08- Mutual TLS (mTLS).md
├── 09- AWS WAF Integration.md
├── 10- Custom Domain Names & ACM.md
├── 11- Security Best Practices.md
└── README.md
```

---

# Best Practices

Throughout this section, you'll learn to:

- Apply Defense in Depth instead of relying on a single security mechanism.
- Use the appropriate authentication method for each workload.
- Protect APIs before requests reach backend services.
- Minimize permissions using the Principle of Least Privilege.
- Monitor APIs continuously using CloudWatch and CloudTrail.
- Combine authentication, authorization, throttling, WAF, and monitoring for production-grade security.
- Design secure APIs that are scalable, maintainable, and compliant with industry best practices.