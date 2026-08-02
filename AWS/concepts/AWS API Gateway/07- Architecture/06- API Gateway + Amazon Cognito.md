# API Gateway + Amazon Cognito

## Overview

Securing APIs is one of the most important responsibilities in any production system. Instead of implementing user authentication inside every backend service, Amazon API Gateway can integrate directly with **Amazon Cognito**.

Amazon Cognito is AWS's fully managed identity service that provides:

- User Registration
- User Login
- JWT Token Generation
- User Management
- Multi-Factor Authentication (MFA)
- Social Login
- OAuth 2.0 / OpenID Connect (OIDC)

When integrated with API Gateway, Cognito authenticates users before requests reach backend services.

This architecture is widely used in:

- Mobile Applications
- Single Page Applications (SPA)
- SaaS Platforms
- Enterprise APIs
- Customer Portals

---

# Why Use Cognito?

Without Cognito:

```text
Client

↓

API Gateway

↓

Backend

↓

Validate JWT

↓

Business Logic
```

Every backend service performs authentication.

Problems:

- Duplicate authentication logic
- Increased latency
- Security inconsistencies
- More application code

With Cognito:

```text
Client

↓

Amazon Cognito

↓

JWT Token

↓

API Gateway

↓

Backend
```

API Gateway validates the JWT before invoking backend services.

---

# High-Level Architecture

```text
               User

                 │

                 ▼

          Amazon Cognito

                 │

          JWT Access Token

                 │

                 ▼

         Amazon API Gateway

                 │

         JWT Validation

                 │

                 ▼

      Lambda / ECS / EC2 Backend
```

Authentication is centralized.

---

# Authentication Flow

```text
User Login

↓

Amazon Cognito

↓

JWT Token

↓

API Request

↓

API Gateway

↓

JWT Validation

↓

Backend
```

Only authenticated requests reach the application.

---

# Components

Amazon Cognito consists of:

```text
Cognito

│

├── User Pool

└── Identity Pool
```

Each serves a different purpose.

---

# User Pool

A **User Pool** manages:

- User accounts
- Passwords
- Authentication
- JWT Tokens
- MFA
- Password Policies

Think of it as an authentication database.

---

# Identity Pool

An **Identity Pool** provides temporary AWS credentials.

Example:

```text
User

↓

Cognito

↓

Temporary IAM Credentials

↓

Amazon S3
```

Identity Pools are used when users need direct access to AWS services.

---

# JWT Token

After login:

```text
Username

+

Password

↓

Cognito

↓

JWT Token
```

The client includes the token:

```http
Authorization: Bearer <JWT>
```

---

# API Request

Example:

```http
GET /orders

Authorization: Bearer eyJhb...
```

API Gateway extracts the token automatically.

---

# JWT Validation

API Gateway validates:

- Signature
- Expiration
- Issuer
- Audience

If validation succeeds:

```text
Request

↓

Backend
```

Otherwise:

```http
401 Unauthorized
```

---

# Authorization Flow

```text
JWT

↓

API Gateway

↓

Claims

↓

Authorization

↓

Backend
```

Authorization decisions can use JWT claims.

---

# JWT Claims

Example:

```json
{
  "sub": "12345",
  "email": "john@example.com",
  "role": "admin"
}
```

Backend services can use claims for authorization.

---

# Token Types

Cognito generates:

- ID Token
- Access Token
- Refresh Token

### ID Token

Contains user identity information.

### Access Token

Used to authorize API requests.

### Refresh Token

Obtains new access tokens without requiring the user to log in again.

---

# Expired Tokens

```text
Expired JWT

↓

API Gateway

↓

401 Unauthorized
```

The client should use the Refresh Token to obtain a new Access Token.

---

# Multi-Factor Authentication

Cognito supports:

```text
Password

+

OTP

↓

Login
```

Supported MFA methods include:

- SMS
- TOTP Authenticator Apps

---

# Social Login

Users can authenticate using:

- Google
- Apple
- Facebook
- Amazon
- OIDC Providers
- SAML Providers

```text
Google Login

↓

Amazon Cognito

↓

JWT

↓

API Gateway
```

---

# Password Policies

User Pools support:

- Minimum password length
- Uppercase letters
- Lowercase letters
- Numbers
- Special characters

Example:

```text
Minimum Length

↓

12 Characters
```

---

# Authorization Architecture

```text
Client

↓

Cognito

↓

JWT

↓

API Gateway

↓

Lambda

↓

Database
```

Authentication happens once before backend execution.

---

# Monitoring

Monitor:

API Gateway:

- 4XX Errors
- 5XX Errors
- Latency

Cognito:

- Sign-ins
- Failed Logins
- MFA Usage
- Token Requests

CloudWatch provides operational visibility.

---

# Logging

```text
API Gateway

↓

CloudWatch Logs

--------------------

Application Logs

↓

CloudWatch Logs
```

Authentication failures are visible in API Gateway metrics and logs.

---

# Common Use Cases

API Gateway + Cognito is commonly used for:

- Customer portals
- Mobile apps
- React applications
- Angular applications
- Vue.js applications
- SaaS products
- Internal employee portals
- Partner APIs

---

# Advantages

- Fully managed authentication
- JWT-based authorization
- OAuth 2.0 support
- OpenID Connect support
- MFA support
- Social login
- Centralized user management
- Seamless API Gateway integration

---

# Limitations

- AWS-specific identity solution
- Learning curve for OAuth flows
- User Pool customization has limits
- Advanced enterprise identity requirements may require external IdPs

---

# Production Architecture

```text
                  User

                    │

                    ▼

             Amazon Cognito

                    │

               JWT Token

                    │

                    ▼

              Amazon API Gateway

                    │

        JWT Authentication

                    │

                    ▼

         Lambda / ECS / EC2 Services

                    │

                    ▼

          DynamoDB / Aurora / Redis
```

This architecture is commonly used for secure production APIs.

---

# Cognito vs IAM

| Cognito | IAM |
|----------|-----|
| End Users | AWS Users |
| Mobile Apps | AWS Administrators |
| JWT Authentication | AWS Credentials |
| User Login | Infrastructure Access |

IAM manages AWS identities, while Cognito manages application users.

---

# Cognito vs Lambda Authorizer

| Cognito | Lambda Authorizer |
|----------|-------------------|
| Managed JWT Validation | Fully Custom Logic |
| Lower Latency | More Flexible |
| Easy Setup | More Development |
| Standard Authentication | Custom Authentication Rules |

Choose Lambda Authorizers when authentication requirements cannot be met using standard JWT validation.

---

# Best Practices

- Use User Pools for application authentication.
- Use Identity Pools only when users require direct AWS resource access.
- Validate JWTs in API Gateway rather than in backend services.
- Enable Multi-Factor Authentication for sensitive applications.
- Use HTTPS for every authentication request.
- Store tokens securely on the client.
- Configure appropriate token expiration periods.
- Follow the principle of least privilege for IAM roles.
- Monitor authentication failures using CloudWatch.

---

# Common Interview Questions

### Why integrate API Gateway with Amazon Cognito?

API Gateway can authenticate users by validating Cognito-issued JWT tokens before requests reach backend services, reducing application complexity and improving security.

---

### What is the difference between a User Pool and an Identity Pool?

A **User Pool** manages user authentication and issues JWT tokens, while an **Identity Pool** provides temporary AWS credentials that allow authenticated users to access AWS resources.

---

### Which Cognito token should be sent to API Gateway?

The **Access Token** is typically used to authorize API requests.

---

### Does API Gateway validate JWT tokens automatically?

Yes.

When configured with a Cognito JWT Authorizer, API Gateway automatically validates the token's signature, issuer, audience, and expiration before invoking the backend.

---

### When would you use a Lambda Authorizer instead of Cognito?

Use a Lambda Authorizer when custom authentication logic, third-party identity providers, or complex authorization rules are required beyond standard JWT validation.

---

# Key Takeaways

- Amazon Cognito provides a fully managed authentication solution for applications using Amazon API Gateway.
- User Pools manage users and issue JWT tokens, while Identity Pools provide temporary AWS credentials.
- API Gateway validates Cognito JWT tokens before forwarding requests to backend services, centralizing authentication.
- Cognito supports OAuth 2.0, OpenID Connect, Multi-Factor Authentication, and social identity providers.
- Combining Cognito, API Gateway, CloudWatch, and secure backend services results in a scalable and production-ready authentication architecture.