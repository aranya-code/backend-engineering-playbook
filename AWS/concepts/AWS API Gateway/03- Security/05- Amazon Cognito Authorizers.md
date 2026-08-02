# Amazon Cognito Authorizers

## Overview

Amazon Cognito is AWS's fully managed identity service that provides **user authentication**, **authorization**, and **user management** for web and mobile applications.

When integrated with Amazon API Gateway, Cognito allows authenticated users to access protected APIs using **JSON Web Tokens (JWTs)**.

Unlike Lambda Authorizers, where you write and maintain custom authentication logic, Cognito handles:

- User registration
- User login
- Password management
- Multi-Factor Authentication (MFA)
- Token generation
- Token validation
- User groups
- Social login
- Federation

This makes Cognito the recommended authentication solution for most customer-facing applications.

---

# Why Use Cognito?

Suppose you're building an e-commerce application.

Users should:

- Register
- Login
- Reset passwords
- Verify email
- Receive JWT tokens
- Access protected APIs

Without Cognito:

```text
Developer

↓

Build Authentication System

↓

Store Passwords

↓

Generate Tokens

↓

Validate Tokens

↓

Reset Passwords

↓

MFA

↓

User Management
```

A significant amount of development effort is required.

With Cognito:

```text
Developer

↓

Amazon Cognito

↓

Authentication Ready
```

AWS manages the entire authentication lifecycle.

---

# Architecture

```text
               Mobile App

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

          Lambda / ECS / EC2
```

The backend only receives requests from authenticated users.

---

# Authentication Flow

```text
User

↓

Login

↓

Amazon Cognito

↓

Generate JWT

↓

API Gateway

↓

Validate JWT

↓

Backend
```

API Gateway validates the JWT before invoking the backend.

---

# Cognito Components

Amazon Cognito consists of two major components.

| Component | Purpose |
|-----------|----------|
| User Pool | Authentication and User Management |
| Identity Pool | Temporary AWS Credentials |

Most API Gateway integrations use **User Pools**.

---

# User Pools

A User Pool is a managed user directory.

It provides:

- User Registration
- User Login
- Password Reset
- Email Verification
- MFA
- JWT Generation
- User Groups

Example:

```text
Customer

↓

Cognito User Pool

↓

JWT Token
```

---

# Identity Pools

Identity Pools provide temporary AWS credentials.

Architecture:

```text
User

↓

Identity Pool

↓

Temporary IAM Credentials

↓

Amazon S3

DynamoDB

Other AWS Services
```

Identity Pools are typically used when users need direct access to AWS services.

---

# JWT Tokens

After successful authentication, Cognito returns JWT tokens.

Typically:

```text
ID Token

Access Token

Refresh Token
```

Each token has a different purpose.

---

# Access Token

Used to authorize API requests.

Example:

```http
Authorization:

Bearer eyJhbGc...
```

API Gateway validates this token before forwarding the request.

---

# ID Token

Contains user profile information.

Example claims:

```text
Username

Email

User ID

Groups
```

Primarily used by client applications.

---

# Refresh Token

Access Tokens eventually expire.

Instead of asking the user to log in again:

```text
Refresh Token

↓

New Access Token
```

This improves user experience.

---

# JWT Validation

When API Gateway receives a request:

```text
Client

↓

JWT Token

↓

API Gateway

↓

Validate Signature

↓

Validate Expiration

↓

Validate Issuer

↓

Validate Audience

↓

Backend
```

If validation fails:

```http
401 Unauthorized
```

The backend is never invoked.

---

# Cognito User Groups

Users can belong to groups.

Example:

```text
Admin

Manager

Customer

Support
```

Group membership is included inside the JWT.

Applications can authorize users based on these groups.

---

# Example JWT Claims

Decoded JWT:

```json
{
    "sub": "12345",
    "email": "john@example.com",
    "username": "john",
    "cognito:groups": [
        "Admin"
    ]
}
```

Backend services can use these claims for authorization.

---

# Social Login

Cognito supports identity federation.

Examples:

```text
Google

Facebook

Apple

Amazon

Microsoft
```

Users can log in without creating a separate account.

---

# Enterprise Login

Cognito also supports enterprise identity providers.

Examples:

- SAML
- OpenID Connect (OIDC)

This allows organizations to integrate:

```text
Azure AD

Okta

Ping Identity

Auth0
```

---

# Multi-Factor Authentication (MFA)

Cognito supports MFA.

Options include:

- SMS
- Authenticator Apps
- TOTP

Authentication flow:

```text
Password

↓

OTP

↓

JWT Token
```

This significantly improves account security.

---

# Password Policies

User Pools support configurable password policies.

Example:

```text
Minimum Length

Uppercase

Lowercase

Numbers

Special Characters
```

Password strength is enforced automatically.

---

# Hosted UI

Cognito provides a hosted login page.

Instead of building your own authentication screens:

```text
Application

↓

Redirect

↓

Hosted Login

↓

JWT Token
```

This accelerates application development.

---

# Architecture Example

```text
                Mobile App

                     │

                     ▼

           Amazon Cognito

                     │

             JWT Token

                     │

                     ▼

          Amazon API Gateway

                     │

                     ▼

          Lambda Function

                     │

                     ▼

             Amazon DynamoDB
```

---

# Advantages

## Fully Managed

AWS manages authentication infrastructure.

---

## Secure

Supports:

- MFA
- Password Policies
- JWT
- OAuth 2.0
- OpenID Connect

---

## Scalable

Millions of users can authenticate simultaneously.

---

## Social Login

Built-in support for major identity providers.

---

## Enterprise Federation

Supports SAML and OIDC providers.

---

# Disadvantages

## AWS Ecosystem

Best suited for applications already running on AWS.

---

## Learning Curve

Understanding User Pools, Identity Pools, OAuth, and JWT requires some initial learning.

---

## Limited Custom Authentication

For highly specialized authentication flows, Lambda Authorizers may provide greater flexibility.

---

# Common Use Cases

Cognito Authorizers are ideal for:

- Mobile applications
- Web applications
- SaaS platforms
- Customer portals
- Public APIs
- Consumer authentication
- Enterprise applications

---

# Cognito vs IAM

| Feature | Cognito | IAM |
|----------|----------|-----|
| Intended Users | Customers | AWS Services |
| JWT Authentication | ✅ | ❌ |
| AWS Credentials | ❌ | ✅ |
| Social Login | ✅ | ❌ |
| Mobile Applications | ✅ | ❌ |

---

# Cognito vs Lambda Authorizer

| Feature | Cognito | Lambda Authorizer |
|----------|----------|-------------------|
| Managed by AWS | ✅ | ❌ |
| JWT Validation | Built-in | Custom |
| Maintenance | Low | High |
| Custom Logic | Limited | Unlimited |
| Performance | Higher | Slightly Lower |

For standard authentication, Cognito is usually the preferred choice.

---

# Real-World Example

A shopping application.

```text
Customer

↓

Login

↓

Amazon Cognito

↓

JWT

↓

API Gateway

↓

Order Service

↓

Database
```

The Order Service never needs to validate passwords or tokens.

API Gateway ensures only authenticated users reach the backend.

---

# Security Best Practices

- Enable Multi-Factor Authentication (MFA).
- Use strong password policies.
- Use HTTPS for all authentication flows.
- Keep Access Tokens short-lived.
- Protect Refresh Tokens securely.
- Validate user roles before performing sensitive operations.
- Use Cognito User Groups for role-based authorization.
- Enable CloudWatch logging and monitoring.

---

# Common Interview Questions

### What is a Cognito Authorizer?

A Cognito Authorizer allows API Gateway to authenticate requests using JWT tokens issued by an Amazon Cognito User Pool.

---

### What is the difference between a User Pool and an Identity Pool?

A **User Pool** manages user authentication and issues JWT tokens, while an **Identity Pool** provides temporary AWS credentials that allow authenticated users to access AWS services.

---

### What happens when a request reaches API Gateway?

API Gateway validates the JWT by checking:

- Signature
- Expiration
- Issuer
- Audience

If the token is valid, the request proceeds to the backend.

---

### When should you choose Cognito instead of a Lambda Authorizer?

Choose Cognito when you need a fully managed authentication solution with JWT support, user management, MFA, password policies, and social or enterprise login. Choose a Lambda Authorizer only when custom authentication logic is required.

---

# Key Takeaways

- Amazon Cognito provides fully managed authentication and user management for web and mobile applications.
- API Gateway integrates with Cognito User Pools to validate JWT tokens before invoking backend services.
- Cognito supports features such as MFA, password policies, social login, enterprise federation, and user groups.
- User Pools handle authentication, while Identity Pools provide temporary AWS credentials.
- Cognito is the recommended authentication solution for most customer-facing APIs because it reduces operational overhead while providing secure, scalable authentication.