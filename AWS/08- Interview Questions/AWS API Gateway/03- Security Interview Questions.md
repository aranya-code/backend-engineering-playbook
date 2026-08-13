# Security Interview Questions

## Overview

Security is one of the most frequently tested topics in Senior Backend Developer and AWS interviews.

Interviewers expect you to understand not only **how API Gateway secures APIs**, but also **why certain security mechanisms should be chosen**.

This chapter contains production-oriented interview questions covering:

- Authentication
- Authorization
- IAM
- Cognito
- JWT
- Lambda Authorizers
- Resource Policies
- API Keys
- Usage Plans
- mTLS
- Private APIs

---

# Question 1

## How do you secure an API Gateway API?

### Answer

Security should be implemented in multiple layers.

Example:

```text
Client

↓

CloudFront

↓

AWS WAF

↓

HTTPS

↓

API Gateway

↓

JWT Authorizer

↓

Lambda

↓

Database
```

Layers include:

- HTTPS
- Authentication
- Authorization
- Rate Limiting
- Logging
- Monitoring

This approach follows the principle of **Defense in Depth**.

---

# Question 2

## What is the difference between Authentication and Authorization?

### Answer

Authentication answers:

```text
Who are you?
```

Authorization answers:

```text
What are you allowed to do?
```

Example:

```text
JWT

↓

Authentication

↓

IAM Policy

↓

Authorization
```

Authentication always happens before authorization.

---

# Question 3

## What authentication methods does API Gateway support?

### Answer

API Gateway supports:

- IAM Authorization
- JWT Authorizers
- Lambda Authorizers
- Amazon Cognito
- Mutual TLS (mTLS)
- API Keys (identification only)

---

# Question 4

## JWT Authorizer vs Lambda Authorizer

### Answer

| JWT Authorizer | Lambda Authorizer |
|---------------|-------------------|
| Built into API Gateway | Custom Lambda |
| Faster | Slightly slower |
| Lower cost | Lambda invocation cost |
| Standard JWT validation | Custom authorization logic |
| OIDC / Cognito | Any identity provider |

---

### When would you choose Lambda Authorizer?

When:

- Custom business rules
- External Identity Provider
- Database lookup
- Tenant resolution
- Dynamic permissions

---

# Question 5

## Why is JWT Authorizer usually preferred?

### Answer

Because API Gateway validates the token itself.

Advantages:

- Lower latency

- Lower cost

- No Lambda execution

- Better scalability

Use Lambda Authorizers only when custom logic is required.

---

# Question 6

## Explain IAM Authorization.

### Answer

IAM Authorization uses:

```text
AWS Signature Version 4
```

Every request is cryptographically signed.

Best suited for:

- AWS services
- Internal APIs
- Service-to-service communication

---

### Example

```text
Lambda

↓

API Gateway

↓

IAM
```

No JWT required.

---

# Question 7

## What is Amazon Cognito?

### Answer

Amazon Cognito is a managed identity service.

Features include:

- User Management
- OAuth2
- OpenID Connect
- MFA
- Password Policies
- Social Login
- User Pools

API Gateway integrates directly with Cognito.

---

# Question 8

## Why use Cognito instead of implementing authentication yourself?

### Answer

Because Cognito provides:

- Security best practices
- MFA
- Password reset
- Token management
- OAuth
- Compliance

without requiring custom authentication code.

---

# Question 9

## What are Resource Policies?

### Answer

Resource Policies determine:

```text
Who can invoke the API
```

Examples:

- AWS Account
- VPC
- VPC Endpoint
- IP Address

They provide an additional security layer.

---

# Question 10

## IAM Policy vs Resource Policy

### Answer

| IAM Policy | Resource Policy |
|------------|-----------------|
| Attached to users, roles, or groups | Attached to the API |
| Defines what identities can do | Defines who can access the API |
| Identity-based | Resource-based |

Production systems often use both together.

---

# Question 11

## What is Mutual TLS (mTLS)?

### Answer

Normally:

```text
Server

↓

Certificate

↓

Client Trusts Server
```

With mTLS:

```text
Client

↓

Certificate

↓

Server Trusts Client
```

Both parties authenticate each other.

---

### When is mTLS used?

- Banking
- Healthcare
- Enterprise APIs
- Partner integrations

---

# Question 12

## What is an API Key?

### Answer

API Keys identify:

```text
Applications
```

They do **not** authenticate users.

Typical uses:

- Usage tracking
- Quotas
- Throttling

---

# Question 13

## Can API Keys replace JWT?

### Answer

No.

JWT:

```text
Identity
```

API Key:

```text
Application Identification
```

Production APIs usually combine:

```text
JWT

+

Usage Plan
```

---

# Question 14

## What is a Usage Plan?

### Answer

Usage Plans control:

- Request rate
- Burst limit
- Daily quota
- Monthly quota

Different plans can be assigned to different clients.

---

# Question 15

## How would you prevent API abuse?

### Answer

I would implement:

- AWS WAF
- JWT Authentication
- Rate Limiting
- Usage Plans
- API Keys
- CloudWatch Alarms
- Request Validation

No single control is sufficient.

---

# Question 16

## Why use AWS WAF?

### Answer

WAF protects APIs from:

- SQL Injection
- XSS
- Bots
- IP reputation threats
- Rate-based attacks

It filters malicious requests before they reach API Gateway.

---

# Question 17

## How do you secure Private APIs?

### Answer

Architecture:

```text
Internal Users

↓

VPC Endpoint

↓

Private API Gateway

↓

Backend
```

Additional controls:

- Resource Policies
- IAM
- Security Groups

No internet exposure.

---

# Question 18

## How should secrets be managed?

### Answer

Never store:

- Passwords
- API Keys
- JWT Secrets

inside source code.

Use:

- AWS Secrets Manager
- AWS Systems Manager Parameter Store

---

# Question 19

## How do you secure communication?

### Answer

Always use:

```text
HTTPS
```

Enable:

- TLS 1.2+
- ACM Certificates
- Secure Ciphers

Never expose APIs over HTTP.

---

# Question 20

## What security monitoring would you enable?

### Answer

Monitor:

- CloudWatch Logs
- CloudWatch Metrics
- AWS X-Ray
- CloudTrail
- AWS WAF Logs

Create alarms for:

- 401 Errors
- 403 Errors
- 429 Errors
- 5XX Errors

---

# Scenario-Based Questions

## Scenario 1

An API suddenly returns:

```http
401 Unauthorized
```

What would you check?

### Answer

I would verify:

- Authorization header
- JWT expiration
- JWT issuer
- JWT audience
- Cognito configuration
- JWT Authorizer settings

---

## Scenario 2

Users receive:

```http
403 Forbidden
```

How would you troubleshoot?

### Answer

I would review:

- IAM permissions
- Resource Policies
- API Keys
- Usage Plans
- AWS WAF rules
- VPC Endpoint policies (for Private APIs)

---

## Scenario 3

A partner company needs secure API access.

Would you use an API Key?

### Answer

No.

API Keys only identify the client.

I would use:

- OAuth2 / JWT
- mTLS (if required)
- API Keys for usage tracking
- Usage Plans for rate limiting

---

## Scenario 4

How would you protect an API from DDoS attacks?

### Answer

I would combine:

- CloudFront
- AWS Shield
- AWS WAF
- API Gateway throttling
- Usage Plans
- CloudWatch alarms

---

## Scenario 5

A financial institution needs highly secure APIs.

How would you design them?

### Answer

Architecture:

```text
Users

↓

CloudFront

↓

AWS Shield

↓

AWS WAF

↓

API Gateway

↓

mTLS

↓

JWT

↓

Lambda

↓

Database
```

Additionally:

- Encryption at rest
- Encryption in transit
- Secrets Manager
- CloudTrail
- CloudWatch
- Least-privilege IAM

---

# Rapid Fire Questions

- JWT vs Lambda Authorizer?
- IAM vs Cognito?
- API Key vs JWT?
- IAM Policy vs Resource Policy?
- 401 vs 403?
- Why use WAF?
- Why use HTTPS?
- What is mTLS?
- What is Defense in Depth?
- Why use Secrets Manager?
- How do Private APIs work?
- What is SigV4?
- Why shouldn't API Keys authenticate users?
- Why monitor CloudTrail?

---

# Senior Interview Tips

Security interview questions are rarely about naming AWS services.

Interviewers want to know:

- Why you selected a particular authentication mechanism.
- The trade-offs between different approaches.
- How you would secure a production system.
- How you would respond to security incidents.
- How you would implement least-privilege access.

Whenever possible, explain both **why** you chose a solution and **what alternatives you considered**.

---

# Key Takeaways

- API Gateway supports multiple authentication and authorization mechanisms, each suited to different use cases.
- JWT Authorizers are generally preferred for modern APIs, while Lambda Authorizers are useful for custom authorization logic.
- API Keys identify client applications but do not authenticate users.
- Defense in Depth combines multiple security controls such as HTTPS, WAF, authentication, authorization, throttling, logging, and monitoring.
- Strong interview answers focus on security trade-offs, production practices, and layered protection rather than individual AWS features.