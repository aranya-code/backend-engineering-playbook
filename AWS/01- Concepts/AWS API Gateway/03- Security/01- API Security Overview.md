# API Security Overview

## Overview

APIs are the primary entry point into modern applications. They expose business functionality, customer data, and internal services to external consumers. Because APIs are publicly accessible, they are a common target for attackers.

Amazon API Gateway provides multiple layers of security that help protect APIs from unauthorized access, abuse, and common web attacks.

Rather than relying solely on backend applications for security, API Gateway allows authentication, authorization, rate limiting, logging, monitoring, and traffic filtering to occur **before requests reach your backend**.

A secure API architecture combines API Gateway security features with backend application security.

---

# Why API Security Matters

Imagine an API that processes payments.

```text
Internet

↓

Payment API

↓

Database
```

Without security:

- Anyone can invoke the API.
- Attackers can flood the API.
- Sensitive data may be exposed.
- Unauthorized users may access customer information.

A secure architecture places API Gateway in front of backend services.

```text
                Internet
                    │
                    ▼
          Amazon API Gateway
                    │
    Authentication & Authorization
                    │
     Rate Limiting & Validation
                    │
                    ▼
            Backend Services
```

API Gateway acts as the first line of defense.

---

# Security Layers

API Gateway security is built using multiple independent layers.

```text
Client
   │
   ▼
Custom Domain (HTTPS)
   │
   ▼
AWS WAF
   │
   ▼
Authentication
   │
   ▼
Authorization
   │
   ▼
Resource Policy
   │
   ▼
Throttling
   │
   ▼
Backend
```

Each layer protects against a different type of threat.

---

# Security Features

API Gateway provides several built-in security capabilities.

| Feature | Purpose |
|----------|---------|
| IAM Authorization | Authenticate AWS users and services |
| Lambda Authorizer | Custom authentication logic |
| Amazon Cognito | User authentication using JWT tokens |
| JWT Authorizer | Validate OAuth/JWT tokens |
| Resource Policies | Restrict who can access the API |
| API Keys | Identify API consumers |
| Usage Plans | Control API consumption |
| AWS WAF | Protect against web attacks |
| HTTPS | Encrypt communication |
| CloudWatch Logs | Monitor API activity |

Each feature addresses a different security requirement.

---

# Authentication vs Authorization

These two concepts are often confused.

Authentication answers:

> **Who are you?**

Authorization answers:

> **What are you allowed to do?**

Example:

```text
User

↓

Login Successful

↓

Authenticated

↓

Allowed to Read Orders

↓

Authorized
```

Another example:

```text
User

↓

Authenticated

↓

Delete Customer Data

↓

Not Authorized
```

Authentication does not automatically grant permission to perform every action.

---

# Authentication Options

API Gateway supports multiple authentication mechanisms.

```text
                API Gateway
                     │
     ┌───────────────┼───────────────┐
     ▼               ▼               ▼
    IAM         Amazon Cognito    Lambda
                                    Authorizer
                     │
                     ▼
                JWT Authorizer
```

Each option is suitable for different scenarios.

---

# Authorization Options

After authentication succeeds, API Gateway determines whether access should be granted.

Authorization can be based on:

- IAM Policies
- Resource Policies
- Lambda Authorizers
- Cognito User Groups
- JWT Claims

---

# Encryption in Transit

API Gateway supports HTTPS only.

```text
Client

↓

HTTPS

↓

API Gateway
```

Data is encrypted using TLS.

This protects:

- Login credentials
- Access tokens
- Customer information
- Payment data

Never expose production APIs over plain HTTP.

---

# Resource Protection

API Gateway provides mechanisms to reduce abuse.

These include:

- Rate limiting
- Throttling
- API Keys
- Usage Plans
- AWS WAF

Example:

```text
100 Requests / Second

↓

API Gateway

↓

Backend
```

Excess requests receive:

```http
429 Too Many Requests
```

---

# Identity Providers

API Gateway can authenticate users through different identity providers.

Examples:

- Amazon Cognito
- Auth0
- Okta
- Azure Active Directory
- Google Identity
- Any OpenID Connect (OIDC) provider

Most modern applications use JWT tokens issued by these providers.

---

# Resource Policies

Resource Policies determine **who can invoke an API**.

Examples:

- Allow only one AWS account
- Allow specific IAM roles
- Restrict access by IP address
- Restrict access by VPC Endpoint

Example:

```text
Only Corporate Network

↓

API Gateway

↓

Backend
```

Requests from unauthorized locations are rejected before reaching the backend.

---

# AWS WAF

AWS Web Application Firewall (WAF) protects APIs from common web attacks.

Examples include:

- SQL Injection
- Cross-Site Scripting (XSS)
- Bot traffic
- IP reputation lists
- Rate-based attacks

Architecture:

```text
Internet

↓

AWS WAF

↓

API Gateway

↓

Backend
```

---

# API Keys and Usage Plans

For REST APIs, API Gateway supports API Keys.

API Keys help:

- Identify clients
- Track API usage
- Apply quotas
- Apply throttling

Example:

```text
Developer

↓

API Key

↓

API Gateway
```

API Keys identify consumers but **are not an authentication mechanism**. They should be combined with proper authentication.

---

# Logging and Monitoring

Security also involves visibility.

API Gateway integrates with:

- Amazon CloudWatch
- AWS X-Ray
- Access Logs
- CloudTrail

This enables teams to:

- Detect suspicious activity
- Audit API access
- Troubleshoot failures
- Monitor traffic patterns

---

# Shared Responsibility Model

Security responsibilities are shared.

| AWS | Customer |
|-----|----------|
| API Gateway infrastructure | API design |
| Network infrastructure | IAM configuration |
| Physical security | Authorization rules |
| Service availability | Backend security |
| TLS infrastructure | Input validation |

API Gateway secures the platform, but application developers remain responsible for securing their APIs.

---

# Real-World Architecture

```text
                Internet
                    │
                    ▼
            AWS WAF
                    │
                    ▼
         Amazon API Gateway
                    │
    Cognito Authentication
                    │
      JWT Authorization
                    │
         Rate Limiting
                    │
                    ▼
          Lambda / ECS / EC2
                    │
                    ▼
              Database
```

This layered approach provides defense in depth.

---

# Security Best Practices

- Always use HTTPS.
- Enable authentication for all sensitive APIs.
- Follow the Principle of Least Privilege.
- Use JWT tokens instead of custom authentication whenever possible.
- Protect public APIs with AWS WAF.
- Enable CloudWatch logging and monitoring.
- Apply throttling to protect backend services.
- Never expose sensitive information in API responses.
- Validate all client input, even after API Gateway validation.
- Rotate credentials and API keys regularly.

---

# Common Interview Questions

### Why shouldn't backend services handle all authentication?

Centralizing authentication in API Gateway provides consistent security, reduces duplicated logic, and prevents unauthorized requests from reaching backend services.

---

### What is the difference between authentication and authorization?

Authentication verifies identity ("Who are you?"), while authorization determines permissions ("What are you allowed to do?").

---

### Is an API Key sufficient to secure an API?

No.

API Keys identify API consumers and enable usage tracking, but they do not authenticate users or authorize access. Sensitive APIs should use IAM, Cognito, JWT, or Lambda Authorizers.

---

### Why should AWS WAF be placed in front of API Gateway?

AWS WAF blocks malicious traffic such as SQL injection, XSS, and abusive requests before they reach API Gateway or backend services, reducing attack surface and backend load.

---

# Key Takeaways

- API Gateway provides multiple security layers, including authentication, authorization, throttling, resource policies, logging, and WAF integration.
- Authentication verifies identity, while authorization determines access permissions.
- HTTPS should always be used to encrypt communication.
- API Keys help identify consumers but are not a replacement for authentication.
- A layered security approach combining API Gateway, WAF, IAM, Cognito, and backend validation provides the strongest protection for production APIs.