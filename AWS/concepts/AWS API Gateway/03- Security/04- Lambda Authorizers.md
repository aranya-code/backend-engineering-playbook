# Lambda Authorizers

## Overview

A **Lambda Authorizer** is a custom authorization mechanism in Amazon API Gateway that allows you to implement your own authentication and authorization logic using an AWS Lambda function.

Unlike IAM Authorization or Amazon Cognito, where AWS manages the authorization process, Lambda Authorizers allow you to:

- Validate custom tokens
- Validate JWT tokens from any provider
- Authenticate API Keys stored in databases
- Integrate with legacy authentication systems
- Implement custom authorization logic
- Support proprietary authentication mechanisms

Lambda Authorizers are useful when the built-in authorization mechanisms do not meet your application's requirements.

---

# When Should You Use Lambda Authorizers?

Suppose your company already has an authentication system.

```text
Employee Portal

↓

Custom Authentication Server

↓

Employee Database
```

Instead of migrating users to Amazon Cognito, API Gateway can invoke a Lambda function to validate existing authentication tokens.

---

# Architecture

```text
                Client
                   │
                   ▼
          Amazon API Gateway
                   │
                   ▼
          Lambda Authorizer
                   │
         Validate Credentials
                   │
          Allow / Deny Policy
                   │
                   ▼
             Backend Service
```

The backend service is invoked **only if** the Lambda Authorizer grants access.

---

# Authorization Flow

```text
Client

↓

Authorization Header

↓

API Gateway

↓

Lambda Authorizer

↓

Validate Token

↓

Generate IAM Policy

↓

Allow or Deny

↓

Backend
```

The Lambda function returns an IAM policy that tells API Gateway whether to allow or deny the request.

---

# What Does a Lambda Authorizer Receive?

The Lambda function receives information about the incoming request.

Example:

```json
{
    "type": "TOKEN",
    "authorizationToken": "Bearer eyJhbGciOiJIUzI1NiIs...",
    "methodArn": "arn:aws:execute-api:..."
}
```

For REQUEST authorizers, the event can also include:

- Headers
- Query Parameters
- Path Parameters
- Stage Variables
- Request Context

---

# Types of Lambda Authorizers

API Gateway supports two Lambda Authorizer types.

| Type | Uses |
|------|------|
| TOKEN Authorizer | Authorization header or bearer token |
| REQUEST Authorizer | Multiple request attributes |

---

# TOKEN Authorizer

A TOKEN Authorizer validates a single token.

Example request:

```http
GET /orders

Authorization: Bearer abc123
```

Flow:

```text
Authorization Header

↓

Lambda Authorizer

↓

Validate Token

↓

Allow

↓

Backend
```

This is the simplest Lambda Authorizer.

---

# REQUEST Authorizer

A REQUEST Authorizer can examine multiple parts of the request.

For example:

- Headers
- Query Parameters
- Path Parameters
- Cookies
- HTTP Method
- Stage Variables

Example:

```http
GET /orders?region=us

Authorization: Bearer abc

X-Department: Finance
```

The Lambda Authorizer can use all these values when making an authorization decision.

---

# IAM Policy Response

The Lambda function must return an IAM policy.

Example:

```json
{
    "principalId": "user123",
    "policyDocument": {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Action": "execute-api:Invoke",
                "Effect": "Allow",
                "Resource": "*"
            }
        ]
    }
}
```

API Gateway evaluates this policy before invoking the backend.

---

# Denying Access

Example response:

```json
{
    "principalId": "anonymous",
    "policyDocument": {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Action": "execute-api:Invoke",
                "Effect": "Deny",
                "Resource": "*"
            }
        ]
    }
}
```

Client receives:

```http
403 Forbidden
```

---

# Custom Authentication

A Lambda Authorizer can validate almost anything.

Examples:

```text
JWT Token

OAuth Token

API Key

Database Lookup

LDAP

Active Directory

Legacy Authentication

Third-Party Identity Provider
```

This flexibility is the primary advantage of Lambda Authorizers.

---

# Example Architecture

```text
             Mobile App

                  │

                  ▼

           API Gateway

                  │

                  ▼

         Lambda Authorizer

                  │

      Customer Database

                  │

                  ▼

        Business Lambda
```

The Lambda Authorizer validates the customer before allowing access.

---

# Authorization Caching

To improve performance, API Gateway can cache authorizer results.

Without caching:

```text
Every Request

↓

Lambda Authorizer

↓

Backend
```

With caching:

```text
First Request

↓

Lambda Authorizer

↓

Cache Result

↓

Backend

--------------------

Future Requests

↓

Cache

↓

Backend
```

This reduces Lambda invocations and improves response times.

---

# Cache TTL

The cache duration is configurable.

Example:

```text
TTL

300 Seconds
```

During this period, API Gateway reuses the cached authorization result.

---

# Advantages

## Complete Flexibility

Any authentication system can be integrated.

---

## Legacy Support

Works with existing authentication infrastructures.

---

## Custom Authorization Logic

Authorization decisions can be based on:

- User Roles
- Subscription Plans
- Departments
- Time of Day
- Geographic Location
- Business Rules

---

## Multiple Identity Sources

REQUEST Authorizers can inspect multiple request components.

---

# Disadvantages

## Higher Latency

Every uncached request invokes a Lambda function.

---

## Additional Cost

Lambda execution charges apply.

---

## More Maintenance

You are responsible for maintaining the authorization logic.

---

# Common Use Cases

Lambda Authorizers are commonly used for:

- Legacy authentication systems
- Enterprise SSO
- Custom JWT validation
- API subscription management
- Multi-tenant SaaS applications
- Database-backed authentication
- Fine-grained authorization

---

# Lambda Authorizer vs IAM

| Feature | Lambda Authorizer | IAM |
|----------|------------------|-----|
| Custom Logic | ✅ | ❌ |
| AWS Credentials Required | ❌ | ✅ |
| Supports Legacy Systems | ✅ | ❌ |
| Uses SigV4 | ❌ | ✅ |
| Best For | Public APIs | Internal AWS Services |

---

# Lambda Authorizer vs Cognito

| Feature | Lambda Authorizer | Cognito |
|----------|------------------|----------|
| Managed by AWS | ❌ | ✅ |
| Custom Authentication | ✅ | Limited |
| JWT Validation | ✅ | ✅ |
| Legacy Systems | ✅ | Limited |
| Operational Overhead | Higher | Lower |

Use Cognito when AWS-managed user authentication is sufficient.

Use Lambda Authorizers when custom authentication is required.

---

# Real-World Example

A SaaS application stores customer subscriptions in PostgreSQL.

```text
Customer

↓

API Gateway

↓

Lambda Authorizer

↓

Check Subscription

↓

Allow

↓

Backend
```

If the subscription has expired:

```http
403 Forbidden
```

The backend is never invoked.

---

# Security Best Practices

- Enable authorization result caching where appropriate.
- Keep Lambda Authorizers lightweight.
- Avoid expensive database queries.
- Validate JWT expiration times.
- Return least-privilege IAM policies.
- Log authorization failures using CloudWatch.
- Separate authentication logic from business logic.

---

# Common Interview Questions

### What is a Lambda Authorizer?

A Lambda Authorizer is a Lambda function that performs custom authentication and authorization for API Gateway by returning an IAM policy that allows or denies access.

---

### What are the two types of Lambda Authorizers?

- TOKEN Authorizer
- REQUEST Authorizer

TOKEN Authorizers validate a token, while REQUEST Authorizers can inspect multiple request attributes.

---

### Why would you choose a Lambda Authorizer instead of Cognito?

Choose a Lambda Authorizer when integrating with existing authentication systems, implementing custom authorization rules, or supporting identity providers that are not directly supported by API Gateway.

---

### How can Lambda Authorizer performance be improved?

By enabling **authorization caching**, which allows API Gateway to reuse authorization results for a configurable time-to-live (TTL), reducing Lambda invocations and latency.

---

# Key Takeaways

- Lambda Authorizers provide custom authentication and authorization using AWS Lambda.
- API Gateway supports **TOKEN** and **REQUEST** Lambda Authorizers.
- The Lambda function returns an IAM policy that determines whether the request is allowed or denied.
- Authorization caching significantly improves performance by reducing repeated Lambda executions.
- Lambda Authorizers are ideal for legacy authentication systems, custom business rules, and advanced authorization scenarios that go beyond built-in IAM or Cognito capabilities.