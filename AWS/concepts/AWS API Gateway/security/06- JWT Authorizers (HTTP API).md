# JWT Authorizers (HTTP API)

## Overview

A **JWT Authorizer** is the native authorization mechanism for **Amazon API Gateway HTTP APIs**.

Instead of invoking a Lambda function or using Amazon Cognito Authorizers directly, API Gateway validates a **JSON Web Token (JWT)** issued by a trusted Identity Provider (IdP).

JWT Authorizers are:

- Fully managed
- High performance
- Low latency
- Cost-effective

Because no Lambda function is invoked, JWT Authorizers are generally the preferred authentication mechanism for modern HTTP APIs.

---

# Why JWT Authorizers?

Modern applications commonly authenticate users using OAuth 2.0 or OpenID Connect (OIDC).

Instead of:

```text
Client

↓

Lambda Authorizer

↓

Validate JWT

↓

Backend
```

API Gateway can validate the token itself.

```text
Client

↓

API Gateway

↓

Validate JWT

↓

Backend
```

This eliminates an unnecessary Lambda invocation.

---

# Architecture

```text
                User

                 │

                 ▼

         Identity Provider

                 │

            JWT Token

                 │

                 ▼

         Amazon API Gateway

                 │

          JWT Validation

                 │

                 ▼

      Lambda / ECS / EC2
```

The backend only receives authenticated requests.

---

# Authentication Flow

```text
User

↓

Login

↓

Identity Provider

↓

JWT Token

↓

API Gateway

↓

JWT Validation

↓

Backend
```

The backend does not need to validate the JWT.

---

# Supported Identity Providers

JWT Authorizers support any OpenID Connect (OIDC) compliant provider.

Examples include:

- Amazon Cognito
- Auth0
- Okta
- Azure Active Directory
- Google Identity
- Keycloak
- Ping Identity

As long as the provider publishes a JWKS (JSON Web Key Set) endpoint, API Gateway can validate the JWT.

---

# JSON Web Token (JWT)

A JWT consists of three parts.

```text
Header

.

Payload

.

Signature
```

Example:

```text
xxxxx.yyyyy.zzzzz
```

Each section is Base64URL encoded.

---

# JWT Header

Example:

```json
{
    "alg":"RS256",
    "typ":"JWT"
}
```

The header specifies:

- Signing algorithm
- Token type

---

# JWT Payload

Contains claims about the user.

Example:

```json
{
    "sub":"12345",
    "email":"john@example.com",
    "role":"admin",
    "exp":1719999999
}
```

Common claims include:

- sub
- email
- username
- groups
- roles
- exp
- aud
- iss

---

# JWT Signature

The signature proves the token has not been modified.

API Gateway verifies it using the public key published by the Identity Provider.

If verification fails:

```http
401 Unauthorized
```

---

# JWT Validation Process

When a request reaches API Gateway:

```text
Receive Token

↓

Decode Header

↓

Find Public Key

↓

Verify Signature

↓

Check Expiration

↓

Check Issuer

↓

Check Audience

↓

Allow Request
```

If any validation step fails, access is denied.

---

# Issuer (iss)

Every JWT contains an **issuer** claim.

Example:

```text
https://cognito-idp.us-east-1.amazonaws.com/us-east-1_ABC123
```

API Gateway verifies that the issuer matches the configured Identity Provider.

---

# Audience (aud)

The audience identifies which application the token was issued for.

Example:

```json
{
    "aud":"shopping-api"
}
```

If the audience does not match the configured value:

```http
401 Unauthorized
```

---

# Token Expiration (exp)

JWTs contain an expiration timestamp.

Example:

```json
{
    "exp":1719999999
}
```

Expired tokens are automatically rejected.

---

# Public Key Verification

JWTs are usually signed using asymmetric cryptography.

```text
Identity Provider

Private Key

↓

Sign JWT

↓

Client

↓

API Gateway

↓

Public Key

↓

Verify Signature
```

API Gateway never needs access to the private key.

---

# JWKS Endpoint

API Gateway retrieves public keys from the Identity Provider's JWKS endpoint.

Example:

```text
https://example.com/.well-known/jwks.json
```

The keys are automatically cached and refreshed by API Gateway.

---

# Claims Available to Backend

After successful validation, API Gateway forwards JWT claims to the backend.

Example claims:

```text
sub

email

groups

scope

username

role
```

Applications can implement authorization based on these claims.

---

# Example Architecture

```text
Customer

↓

Google Login

↓

JWT

↓

API Gateway

↓

Validate JWT

↓

Lambda

↓

Database
```

The Lambda function focuses on business logic rather than authentication.

---

# JWT Authorizer vs Lambda Authorizer

| Feature | JWT Authorizer | Lambda Authorizer |
|----------|----------------|-------------------|
| Managed by AWS | ✅ | ❌ |
| Lambda Required | ❌ | ✅ |
| Performance | Higher | Lower |
| Cost | Lower | Higher |
| Custom Logic | ❌ | ✅ |
| JWT Validation | Built-in | Custom |

---

# JWT Authorizer vs Cognito Authorizer

| Feature | JWT Authorizer | Cognito Authorizer |
|----------|----------------|--------------------|
| HTTP APIs | ✅ Native | Uses JWT from Cognito User Pools |
| REST APIs | ❌ | ✅ |
| Any OIDC Provider | ✅ | ❌ (Cognito User Pools only) |
| Lambda Required | ❌ | ❌ |

A JWT Authorizer is more flexible because it is not limited to Cognito.

---

# Advantages

## No Lambda Invocation

Authentication occurs entirely within API Gateway.

---

## Lower Cost

No Lambda execution charges.

---

## Lower Latency

JWT validation is extremely fast.

---

## Standards-Based

Supports OAuth 2.0 and OpenID Connect.

---

## Scalable

API Gateway handles validation automatically at scale.

---

# Disadvantages

## Limited Custom Logic

Validation rules are predefined.

---

## JWT Only

Does not support proprietary authentication mechanisms.

---

## HTTP APIs Only

JWT Authorizers are available for HTTP APIs.

REST APIs use Cognito Authorizers or Lambda Authorizers instead.

---

# Common Use Cases

JWT Authorizers are commonly used for:

- Single Page Applications (SPA)
- Mobile applications
- SaaS platforms
- Public REST APIs
- Microservices
- OAuth 2.0 applications
- Enterprise identity providers

---

# Real-World Example

A SaaS platform uses Auth0 for authentication.

```text
Customer

↓

Auth0

↓

JWT

↓

HTTP API

↓

JWT Authorizer

↓

Order Service
```

No Lambda Authorizer is required.

Authentication is completely managed by API Gateway.

---

# Best Practices

- Prefer JWT Authorizers for new HTTP APIs.
- Use short-lived Access Tokens.
- Always validate both the **issuer** and **audience** claims.
- Use HTTPS for all authentication flows.
- Implement authorization using JWT claims such as roles or scopes.
- Rotate signing keys through the Identity Provider.
- Keep authentication separate from business logic.

---

# Common Interview Questions

### What is a JWT Authorizer?

A JWT Authorizer is a native API Gateway authorization mechanism for HTTP APIs that validates JSON Web Tokens issued by trusted OpenID Connect (OIDC) identity providers.

---

### Does a JWT Authorizer require Lambda?

No.

API Gateway validates JWTs internally, eliminating the need for a Lambda function.

---

### Which identity providers are supported?

Any provider that supports OpenID Connect (OIDC) and publishes a JWKS endpoint, including Amazon Cognito, Auth0, Okta, Azure AD, Google Identity, and Keycloak.

---

### What claims does API Gateway validate?

API Gateway validates:

- Signature
- Issuer (`iss`)
- Audience (`aud`)
- Expiration (`exp`)

If any validation fails, the request is rejected.

---

### When should you use a JWT Authorizer instead of a Lambda Authorizer?

Use a JWT Authorizer when standard JWT validation is sufficient. Use a Lambda Authorizer only when custom authentication or authorization logic is required.

---

# Key Takeaways

- JWT Authorizers provide built-in JWT validation for Amazon API Gateway HTTP APIs.
- They support any OpenID Connect (OIDC) compliant identity provider that exposes a JWKS endpoint.
- API Gateway validates the token's signature, issuer, audience, and expiration before invoking the backend.
- JWT Authorizers eliminate Lambda invocations, reducing both latency and cost.
- For modern HTTP APIs using OAuth 2.0 or OpenID Connect, JWT Authorizers are the recommended authentication mechanism.