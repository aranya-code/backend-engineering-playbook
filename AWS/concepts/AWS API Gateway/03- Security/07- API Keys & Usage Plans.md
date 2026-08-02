# API Keys & Usage Plans

## Overview

Amazon API Gateway provides **API Keys** and **Usage Plans** to identify API consumers, control API consumption, and protect backend services from excessive traffic.

Although API Keys are often associated with API security, **they are not an authentication or authorization mechanism**.

Instead, API Keys are primarily used for:

- Identifying API consumers
- Applying rate limits
- Applying request quotas
- Tracking API usage
- Supporting subscription-based APIs

They are commonly used in public APIs, partner APIs, and SaaS platforms.

> **Important:** API Keys are supported for **REST APIs**. They are **not supported for HTTP APIs**.

---

# What is an API Key?

An API Key is a unique identifier assigned to an API consumer.

Example:

```text
API Key

↓

abc123xyz789
```

The client includes the key with every request.

```http
GET /products

x-api-key: abc123xyz789
```

API Gateway identifies which consumer made the request.

---

# API Key Architecture

```text
            Client

               │

               ▼

        x-api-key Header

               │

               ▼

      Amazon API Gateway

               │

        Usage Plan Check

               │

               ▼

          Backend API
```

API Gateway validates the API Key before forwarding the request.

---

# API Keys Are NOT Authentication

One of the most common interview questions.

Many beginners assume:

```text
API Key

↓

Authenticated User
```

This is **incorrect**.

API Keys only identify the client.

They do **not** verify:

- User identity
- Permissions
- Roles
- Ownership

For authentication, use:

- IAM
- Amazon Cognito
- JWT Authorizers
- Lambda Authorizers

API Keys should be combined with these mechanisms when protecting sensitive APIs.

---

# How API Keys Work

Client request:

```http
GET /orders

x-api-key:
abc123xyz789
```

Flow:

```text
Client

↓

API Key

↓

API Gateway

↓

Usage Plan

↓

Backend
```

If the API Key is valid, the request continues.

Otherwise:

```http
403 Forbidden
```

---

# What is a Usage Plan?

A Usage Plan defines how an API Key is allowed to use an API.

It controls:

- Rate Limits
- Burst Limits
- Request Quotas

Architecture:

```text
API Key

↓

Usage Plan

↓

API
```

Multiple API Keys can share the same Usage Plan.

---

# Usage Plan Components

A Usage Plan consists of:

```text
API Key

↓

Usage Plan

↓

Rate Limit

↓

Burst Limit

↓

Quota
```

Each component protects backend services from abuse.

---

# Rate Limit

A rate limit defines the **steady request rate** allowed.

Example:

```text
100 Requests

Per Second
```

If a client continuously exceeds this limit:

```http
429 Too Many Requests
```

---

# Burst Limit

Traffic often arrives in short spikes.

The burst limit allows temporary bursts above the steady rate.

Example:

```text
Rate

100/sec

Burst

200
```

Clients can briefly exceed the steady rate before throttling begins.

---

# Quotas

Quotas define the maximum number of requests allowed during a time period.

Examples:

```text
10,000 Requests

Per Day
```

or

```text
500,000 Requests

Per Month
```

Once the quota is exhausted:

```http
429 Too Many Requests
```

until the quota resets.

---

# API Key Example

Developer receives:

```text
Developer Portal

↓

API Key

↓

abc123xyz789
```

Every request:

```http
GET /products

x-api-key:
abc123xyz789
```

API Gateway associates the request with that developer.

---

# Subscription Model Example

Many SaaS platforms offer subscription tiers.

```text
Free

↓

100 Requests/Day

---------------------

Pro

↓

10,000 Requests/Day

---------------------

Enterprise

↓

Unlimited
```

Each subscription tier uses a different Usage Plan.

---

# Architecture Example

```text
              Developer

                   │

                   ▼

              API Key

                   │

                   ▼

           Amazon API Gateway

                   │

            Usage Plan

                   │

                   ▼

        Lambda / ECS / EC2
```

---

# Multiple API Keys

Many clients can access the same API.

```text
Developer A

↓

API Key A

↓

Usage Plan

-------------------

Developer B

↓

API Key B

↓

Usage Plan
```

Each consumer is tracked independently.

---

# Monitoring API Usage

API Gateway records usage statistics.

Examples:

- Total Requests
- Throttled Requests
- Quota Usage
- Consumer Activity

This information is available through:

- CloudWatch
- API Gateway Metrics
- Usage Reports

---

# API Key Rotation

API Keys should be rotated periodically.

Example:

```text
Old API Key

↓

New API Key

↓

Deactivate Old Key
```

Rotation reduces the impact of leaked credentials.

---

# Advantages

## Consumer Identification

Track which client made each request.

---

## Traffic Control

Protect backend services from excessive traffic.

---

## Subscription Support

Different customers can receive different rate limits.

---

## Usage Analytics

Understand API consumption patterns.

---

## Easy Management

API Keys can be created, revoked, and rotated independently.

---

# Disadvantages

## Not Authentication

API Keys cannot verify user identity.

---

## Can Be Shared

Anyone possessing the key can use it.

---

## REST APIs Only

Usage Plans and API Keys are available for REST APIs.

HTTP APIs do not support this feature.

---

# Common Use Cases

API Keys are commonly used for:

- Partner APIs
- Public Developer APIs
- SaaS Platforms
- Billing Systems
- Rate Limiting
- API Monetization
- Subscription Services

---

# API Keys vs JWT

| Feature | API Key | JWT |
|----------|---------|-----|
| Identifies Client | ✅ | ✅ |
| Authenticates User | ❌ | ✅ |
| Contains User Claims | ❌ | ✅ |
| Expires Automatically | Usually No | Yes |
| Role-Based Access | ❌ | ✅ |

JWT is for authentication.

API Keys are for consumer identification and traffic management.

---

# API Keys vs IAM

| Feature | API Key | IAM |
|----------|----------|-----|
| AWS Credentials | ❌ | ✅ |
| Authentication | ❌ | ✅ |
| Usage Tracking | ✅ | Limited |
| Public APIs | ✅ | Limited |
| Internal APIs | Limited | ✅ |

---

# API Keys vs Resource Policies

| Feature | API Key | Resource Policy |
|----------|----------|----------------|
| Identify Consumer | ✅ | ❌ |
| Restrict Access | ❌ | ✅ |
| Usage Tracking | ✅ | ❌ |
| Rate Limiting | ✅ | ❌ |

These features complement each other rather than replace one another.

---

# Real-World Example

A weather API offers three subscription plans.

```text
Free Users

↓

1,000 Requests/Month

---------------------

Business Users

↓

100,000 Requests/Month

---------------------

Enterprise

↓

Unlimited
```

Each customer receives a different API Key associated with the appropriate Usage Plan.

---

# Security Best Practices

- Never use API Keys as the sole security mechanism.
- Combine API Keys with IAM, Cognito, JWT, or Lambda Authorizers for sensitive APIs.
- Rotate API Keys periodically.
- Store API Keys securely and never commit them to source control.
- Monitor usage for unusual traffic patterns.
- Configure appropriate rate limits and quotas to protect backend services.
- Use different Usage Plans for different customer tiers.

---

# Common Interview Questions

### What is an API Key?

An API Key is a unique identifier that API Gateway uses to identify API consumers, apply usage limits, and collect usage metrics.

---

### Are API Keys used for authentication?

No.

API Keys identify clients but do not authenticate users or authorize access. They should be combined with proper authentication mechanisms.

---

### What is a Usage Plan?

A Usage Plan defines how an API Key can access an API by configuring rate limits, burst limits, and request quotas.

---

### What happens when a client exceeds its Usage Plan?

API Gateway throttles requests and typically returns:

```http
429 Too Many Requests
```

until traffic falls within configured limits or the quota resets.

---

### Are API Keys supported for HTTP APIs?

No.

API Keys and Usage Plans are supported only for **REST APIs**.

---

# Key Takeaways

- API Keys identify API consumers but do **not** authenticate or authorize users.
- Usage Plans control API consumption using rate limits, burst limits, and quotas.
- API Keys are commonly used for public APIs, partner integrations, SaaS platforms, and subscription-based services.
- API Keys should always be combined with proper authentication mechanisms for sensitive APIs.
- API Keys and Usage Plans are available only for Amazon API Gateway **REST APIs**.