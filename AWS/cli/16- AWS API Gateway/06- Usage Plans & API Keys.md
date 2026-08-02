# Usage Plans & API Keys

## Overview

Not every API should be publicly accessible without restrictions.

Amazon API Gateway provides **API Keys** and **Usage Plans** to control how consumers access your APIs.

These features help you:

- Identify API consumers
- Apply request quotas
- Configure throttling
- Differentiate customer tiers
- Protect backend services
- Implement subscription-based APIs

Using the AWS CLI, you can automate the creation and management of API Keys and Usage Plans, making them easy to integrate into CI/CD pipelines.

> **Important:** API Keys are **not an authentication mechanism**. They identify the client application but do **not** verify the identity of the user. For authentication, use IAM, Cognito, or JWT/Lambda Authorizers.

---

# How Usage Plans Work

```text
Client

↓

API Key

↓

Usage Plan

↓

Throttle

↓

Quota

↓

API Gateway

↓

Backend
```

Every request is checked against its Usage Plan before reaching the backend.

---

# Components

```text
API Key

↓

Usage Plan

↓

API Stage

↓

API Gateway
```

All three components work together.

---

# API Key vs Authentication

| API Key | Authentication |
|----------|----------------|
| Identifies client application | Verifies user identity |
| Supports quotas | Supports access control |
| Enables throttling | Determines permissions |
| Not secure by itself | Security mechanism |

---

# Create an API Key

```bash
aws apigateway create-api-key \
    --name MobileAppKey \
    --enabled
```

Example output:

```json
{
    "id": "apikey123",
    "name": "MobileAppKey"
}
```

---

# Create an API Key with Value

```bash
aws apigateway create-api-key \
    --name ProductionKey \
    --value MySecretApiKey123 \
    --enabled
```

Normally, API Gateway generates the key automatically.

---

# List API Keys

```bash
aws apigateway get-api-keys
```

Example:

```json
{
    "items": [
        {
            "id": "apikey123",
            "name": "MobileAppKey"
        }
    ]
}
```

---

# View an API Key

```bash
aws apigateway get-api-key \
    --api-key apikey123 \
    --include-value
```

---

# Delete an API Key

```bash
aws apigateway delete-api-key \
    --api-key apikey123
```

Deletion is permanent.

---

# Create a Usage Plan

```bash
aws apigateway create-usage-plan \
    --name FreeTier
```

Example output:

```json
{
    "id": "plan123",
    "name": "FreeTier"
}
```

---

# Configure Throttling

Example:

```bash
aws apigateway create-usage-plan \
    --name Standard \
    --throttle burstLimit=100,rateLimit=50
```

Configuration:

```text
Burst Limit

↓

100

------------------

Rate Limit

↓

50 Requests/Second
```

---

# Configure Quotas

Example:

```bash
aws apigateway create-usage-plan \
    --name MonthlyPlan \
    --quota limit=100000,period=MONTH
```

Quota:

```text
100,000 Requests

↓

Per Month
```

---

# List Usage Plans

```bash
aws apigateway get-usage-plans
```

---

# View a Usage Plan

```bash
aws apigateway get-usage-plan \
    --usage-plan-id plan123
```

---

# Delete a Usage Plan

```bash
aws apigateway delete-usage-plan \
    --usage-plan-id plan123
```

---

# Associate API with Usage Plan

```bash
aws apigateway create-usage-plan-key \
    --usage-plan-id plan123 \
    --key-id apikey123 \
    --key-type API_KEY
```

Now the API Key belongs to the Usage Plan.

---

# Attach API Stage

Associate a stage with the Usage Plan.

```bash
aws apigateway update-usage-plan \
    --usage-plan-id plan123 \
    --patch-operations \
    op=add,path=/apiStages,value=abc123:prod
```

Example:

```text
REST API

↓

prod Stage

↓

FreeTier Plan
```

---

# Require API Key on a Method

```bash
aws apigateway update-method \
    --rest-api-id abc123 \
    --resource-id resource123 \
    --http-method GET \
    --patch-operations \
    op=replace,path=/apiKeyRequired,value=true
```

The client must now send:

```http
x-api-key
```

---

# Test API Key

Request:

```http
GET /products
```

Headers:

```http
x-api-key: MySecretApiKey123
```

Response:

```http
200 OK
```

---

# Missing API Key

Request:

```http
GET /products
```

Without:

```http
x-api-key
```

Response:

```http
403 Forbidden
```

---

# View Usage

Retrieve usage statistics.

```bash
aws apigateway get-usage \
    --usage-plan-id plan123 \
    --start-date 2025-01-01 \
    --end-date 2025-01-31
```

Example output:

```json
{
    "items": {
        "apikey123": [
            [2500]
        ]
    }
}
```

---

# Update Usage Plan

Increase quota.

```bash
aws apigateway update-usage-plan \
    --usage-plan-id plan123 \
    --patch-operations \
    op=replace,path=/quota/limit,value=500000
```

---

# Multi-Tier Example

```text
Free Plan

↓

100 Requests/Day

-----------------------

Standard

↓

10,000 Requests/Day

-----------------------

Enterprise

↓

Unlimited
```

Each customer receives a different API Key.

---

# Architecture

```text
Application

↓

API Key

↓

Usage Plan

↓

API Gateway

↓

Lambda

↓

Backend
```

---

# Automation Example

```bash
PLAN_ID=$(aws apigateway create-usage-plan \
--name Standard \
--query id \
--output text)

KEY_ID=$(aws apigateway create-api-key \
--name ClientA \
--enabled \
--query id \
--output text)

aws apigateway create-usage-plan-key \
--usage-plan-id $PLAN_ID \
--key-id $KEY_ID \
--key-type API_KEY
```

This approach is commonly used during customer onboarding.

---

# Common Errors

## ForbiddenException

Cause:

```text
Missing API Key
```

Verify:

```http
x-api-key
```

header is present.

---

## Invalid API Key

Verify:

```bash
aws apigateway get-api-key \
--api-key apikey123 \
--include-value
```

---

## Quota Exceeded

Response:

```text
429 Too Many Requests
```

The client has exceeded its allocated quota.

---

## Throttling

Response:

```text
429 Too Many Requests
```

Reduce request rate or increase the throttle limits.

---

# CLI Best Practices

- Generate API Keys automatically rather than supplying custom values.
- Use Usage Plans for client-specific throttling and quotas.
- Rotate API Keys periodically.
- Never store API Keys in source code.
- Use Secrets Manager or Parameter Store for secure storage.
- Combine API Keys with authentication mechanisms for production systems.
- Monitor API usage using CloudWatch and Usage Reports.

---

# Common Interview Questions

### What is an API Key used for?

An API Key identifies the calling application and enables throttling, quotas, and usage tracking. It does **not** authenticate users.

---

### What is a Usage Plan?

A Usage Plan defines how clients consume an API by specifying request throttling limits and usage quotas.

---

### Can API Keys replace authentication?

No.

API Keys identify applications but do not verify user identity. Production APIs should use IAM, Cognito, or JWT/Lambda Authorizers for authentication.

---

### What happens when a client exceeds its quota?

API Gateway rejects additional requests and returns:

```http
429 Too Many Requests
```

until the quota period resets.

---

### Why use different Usage Plans?

Different Usage Plans allow organizations to implement service tiers (such as Free, Standard, and Enterprise) with different request limits and quotas.

---

# Key Takeaways

- API Keys identify client applications and enable usage tracking, but they are not authentication mechanisms.
- Usage Plans enforce throttling and quotas, protecting backend services from excessive traffic.
- API Keys, Usage Plans, and API Stages work together to control API consumption.
- The AWS CLI supports complete automation of API Key and Usage Plan management.
- Combining Usage Plans with proper authentication and monitoring provides a scalable and secure approach to managing API consumers.