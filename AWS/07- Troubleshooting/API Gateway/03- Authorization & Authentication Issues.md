# Authorization & Authentication Issues

## Overview

Authentication and authorization issues are among the most common production problems in Amazon API Gateway.

Although they often appear similar, they represent different stages of request processing.

- **Authentication** verifies **who** the caller is.
- **Authorization** determines **what** the authenticated caller is allowed to do.

A misconfiguration in IAM, Cognito, JWT Authorizers, Lambda Authorizers, Resource Policies, or API Keys can prevent requests from reaching the backend.

This guide explains how to diagnose and resolve the most common authentication and authorization issues.

---

# Authentication Flow

```text
Client

↓

Authentication

↓

Authorization

↓

API Gateway

↓

Backend
```

If either authentication or authorization fails, API Gateway rejects the request.

---

# Common Security Errors

| HTTP Code | Meaning |
|-----------|---------|
| 401 | Authentication Failed |
| 403 | Authorization Failed |
| 429 | Usage Plan / API Key Limit |
| 500 | Lambda Authorizer Failure |
| 502 | Invalid Authorizer Response |

---

# 401 Unauthorized

## Example

```http
HTTP/1.1 401 Unauthorized
```

---

## Common Causes

- Missing JWT
- Expired JWT
- Invalid JWT
- Invalid Cognito Token
- Incorrect Authorization Header
- Wrong JWT Issuer
- Wrong JWT Audience

---

## Diagnose

Verify:

```http
Authorization

Bearer eyJhb...
```

Check:

- JWT Expiration
- JWT Audience
- JWT Issuer

---

## Solution

- Refresh Token
- Login Again
- Verify Cognito Configuration
- Verify JWT Authorizer

---

# Expired JWT Token

Example:

```text
exp

↓

Expired
```

---

## Symptoms

```http
401 Unauthorized
```

---

## Diagnose

Decode the JWT.

Check:

```text
exp
```

claim.

---

## Solution

Generate a new Access Token.

---

# Invalid JWT Audience

Example:

```text
Client ID

↓

Mismatch
```

---

## Symptoms

```http
401 Unauthorized
```

---

## Diagnose

Compare:

JWT

```text
aud
```

with:

Authorizer

```text
Audience
```

---

## Solution

Update:

- Cognito App Client
- JWT Authorizer

---

# Invalid JWT Issuer

Example:

```text
Issuer

↓

Incorrect Region
```

---

## Symptoms

```http
401 Unauthorized
```

---

## Diagnose

Compare:

```text
iss
```

claim with:

```text
https://cognito-idp.<region>.amazonaws.com/<pool-id>
```

---

## Solution

Configure the correct issuer.

---

# Missing Authorization Header

Example

Incorrect:

```http
GET /products
```

Correct:

```http
Authorization: Bearer eyJ...
```

---

## Solution

Always send:

```http
Authorization
```

header.

---

# 403 Forbidden

## Example

```http
HTTP/1.1 403 Forbidden
```

---

## Common Causes

- IAM Policy Denied
- Resource Policy Denied
- API Key Missing
- WAF Block
- Usage Plan Restriction
- Cognito Group Restriction

---

## Diagnose

Review:

- IAM Policy
- Resource Policy
- API Gateway Logs
- CloudWatch Logs

---

## Solution

Grant required permissions.

---

# IAM Authorization Failure

Example:

```text
AWS_IAM
```

configured

but

Client sends:

```text
Unsigned Request
```

---

## Symptoms

```http
403 Forbidden
```

---

## Diagnose

Verify:

```text
AWS Signature Version 4
```

---

## Solution

Sign requests using:

```text
SigV4
```

---

# Resource Policy Denied

Example:

```text
Allow

↓

Specific Account
```

Client:

```text
Different Account
```

---

## Symptoms

```http
403 Forbidden
```

---

## Diagnose

Review:

Resource Policy

```json
{
"Principal":"..."
}
```

---

## Solution

Update the Resource Policy.

---

# API Key Missing

Example:

```http
GET /products
```

without:

```http
x-api-key
```

---

## Response

```http
403 Forbidden
```

---

## Solution

Include:

```http
x-api-key
```

header.

---

# Usage Plan Limit

Example:

```text
Quota

↓

Exceeded
```

---

## Response

```http
429 Too Many Requests
```

---

## Diagnose

Check:

Usage Plan

↓

Quota

↓

CloudWatch

---

## Solution

Increase quota or wait for reset.

---

# Lambda Authorizer Failure

Example:

```http
500 Internal Server Error
```

---

## Common Causes

- Lambda Exception
- Timeout
- Invalid Response

---

## Diagnose

Check:

CloudWatch Logs

↓

Lambda Logs

---

## Solution

Fix Lambda logic.

---

# Invalid Lambda Authorizer Response

Incorrect:

```json
{
"name":"John"
}
```

Correct:

```json
{
"principalId":"user1",
"policyDocument":{}
}
```

---

## Symptoms

```http
502 Bad Gateway
```

---

## Solution

Return a valid IAM Policy document.

---

# Cognito User Not Confirmed

Example:

```text
User Status

↓

UNCONFIRMED
```

---

## Symptoms

Authentication fails.

---

## Solution

Confirm user.

or

Enable email verification.

---

# Wrong Cognito User Pool

Example:

API uses:

```text
Pool A
```

JWT issued by:

```text
Pool B
```

---

## Symptoms

```http
401 Unauthorized
```

---

## Solution

Use the correct User Pool.

---

# Lambda Permission Missing

Example:

API Gateway

↓

Lambda

↓

Access Denied

---

## Symptoms

```http
500 Internal Server Error
```

---

## Diagnose

```bash
aws lambda get-policy \
--function-name ProductAPI
```

---

## Solution

Grant invoke permission.

---

# Private API Access Denied

Example:

```http
403 Forbidden
```

---

## Common Causes

- Wrong VPC Endpoint
- Resource Policy
- Private DNS Disabled

---

## Diagnose

Verify:

- VPC Endpoint
- SourceVpce
- Resource Policy

---

## Solution

Update:

```json
aws:SourceVpce
```

---

# Mutual TLS Failure

Symptoms

```http
403 Forbidden
```

---

## Common Causes

- Invalid Certificate
- Expired Certificate
- Missing Client Certificate

---

## Solution

Verify:

- ACM
- Certificate Chain
- Trust Store

---

# WAF Blocking Requests

Symptoms

```http
403 Forbidden
```

---

## Diagnose

Review:

AWS WAF Logs

↓

Blocked Rules

---

## Solution

Adjust:

- Managed Rules
- Rate Limits
- IP Rules

---

# Authentication Debugging Workflow

```text
401?

↓

JWT

↓

Issuer

↓

Audience

↓

Expiration

↓

Authorizer

↓

Fixed
```

---

# Authorization Debugging Workflow

```text
403?

↓

IAM

↓

Resource Policy

↓

API Key

↓

Usage Plan

↓

WAF

↓

Fixed
```

---

# Security Troubleshooting Checklist

Verify:

- Authorization Header
- JWT Token
- JWT Expiration
- JWT Audience
- JWT Issuer
- Cognito User Pool
- Lambda Authorizer
- IAM Policy
- Resource Policy
- API Key
- Usage Plan
- WAF
- Lambda Permission
- VPC Endpoint

---

# Useful AWS Services

Use:

- CloudWatch Logs
- CloudWatch Metrics
- AWS X-Ray
- AWS WAF Logs
- AWS CloudTrail
- Amazon Cognito Console

for diagnosis.

---

# Common Interview Questions

### What is the difference between 401 and 403?

A **401 Unauthorized** response indicates that the client failed authentication (for example, a missing or invalid JWT).

A **403 Forbidden** response means the client is authenticated but does not have permission to perform the requested action.

---

### Why does a JWT Authorizer return 401?

Common reasons include an expired token, incorrect issuer, invalid audience, malformed token, or missing `Authorization` header.

---

### Why would API Gateway return 403 when using IAM authorization?

The request may not be signed with AWS Signature Version 4 (SigV4), or the IAM policy may not grant permission to invoke the API.

---

### How do you troubleshoot Lambda Authorizer failures?

Review CloudWatch Logs for the authorizer function, verify the response format, ensure the Lambda has invoke permissions, and confirm the authorizer is attached to the correct routes or methods.

---

### How do Resource Policies differ from IAM policies?

IAM policies define **what an IAM identity can do**, whereas Resource Policies define **who is allowed to access the API**, such as specific AWS accounts, VPCs, or VPC Endpoints.

---

# Key Takeaways

- Authentication verifies identity, while authorization determines permissions.
- Most `401 Unauthorized` errors are caused by JWT or Cognito configuration issues.
- Most `403 Forbidden` errors result from IAM policies, Resource Policies, API Keys, Usage Plans, or AWS WAF rules.
- CloudWatch Logs, WAF logs, Cognito, and AWS X-Ray provide the primary tools for diagnosing security-related issues.
- A structured troubleshooting approach significantly reduces the time required to identify and resolve authentication and authorization problems.