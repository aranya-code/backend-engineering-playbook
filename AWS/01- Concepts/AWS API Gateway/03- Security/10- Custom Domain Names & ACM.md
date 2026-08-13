# Custom Domain Names & ACM

## Overview

By default, every Amazon API Gateway API receives an AWS-generated endpoint.

Example:

```text
https://abc123.execute-api.us-east-1.amazonaws.com/prod
```

Although functional, these URLs are:

- Difficult to remember
- Not branded
- Hard to share with customers
- Not suitable for production applications

API Gateway allows you to replace the default endpoint with your own **Custom Domain Name**, such as:

```text
https://api.example.com
```

or

```text
https://orders.company.com
```

Custom domains improve usability, branding, security, and API version management.

To use a custom domain, API Gateway integrates with **AWS Certificate Manager (ACM)** to provide HTTPS using SSL/TLS certificates.

---

# Default Endpoint

Every API receives a unique endpoint.

Example:

```text
https://abc123.execute-api.us-east-1.amazonaws.com/prod
```

Components:

```text
abc123

↓

API ID

----------------------

execute-api

↓

AWS Domain

----------------------

prod

↓

Stage
```

This endpoint is immediately available after deployment.

---

# Custom Domain

Instead of exposing the AWS endpoint:

```text
https://abc123.execute-api.us-east-1.amazonaws.com/prod
```

Users access:

```text
https://api.example.com
```

The client never sees the AWS-generated URL.

---

# Architecture

```text
            Client

               │

               ▼

      api.example.com

               │

               ▼

      Amazon API Gateway

               │

               ▼

      Lambda / ECS / EC2
```

API Gateway continues serving the API, but through your own domain.

---

# Why Use Custom Domains?

Benefits include:

- Professional branding
- Easier URLs
- Better user experience
- API versioning
- Multi-environment support
- HTTPS certificates
- Mutual TLS support

---

# Domain Examples

Examples:

```text
api.example.com

orders.example.com

payments.company.com

v1.api.company.com
```

Large organizations often create separate domains for different business units.

---

# Base Path Mapping

A custom domain can expose multiple APIs.

Example:

```text
api.company.com

│

├── /orders

├── /payments

└── /users
```

Each base path maps to a different API.

---

# Example

```text
api.company.com/orders

↓

Orders API

-----------------------

api.company.com/payments

↓

Payments API

-----------------------

api.company.com/users

↓

Users API
```

Clients use one domain while API Gateway routes requests appropriately.

---

# Base Path Mapping Architecture

```text
                 api.company.com

                        │

        ┌───────────────┼───────────────┐

        ▼               ▼               ▼

    /orders        /payments        /users

        │               │               │

        ▼               ▼               ▼

    Orders API     Payments API     Users API
```

This simplifies API organization.

---

# API Versioning

Custom domains support clean versioning.

Example:

```text
api.company.com/v1

api.company.com/v2
```

Instead of:

```text
execute-api.amazonaws.com/prod
```

Different API versions can coexist.

---

# Multiple Environments

Organizations often create separate domains.

```text
dev-api.company.com

↓

Development

----------------------

test-api.company.com

↓

Testing

----------------------

api.company.com

↓

Production
```

Each environment uses its own API Gateway stage.

---

# What is AWS Certificate Manager (ACM)?

AWS Certificate Manager (ACM) is a managed service that provisions and manages SSL/TLS certificates.

ACM:

- Creates certificates
- Validates domain ownership
- Renews certificates automatically
- Integrates with AWS services

API Gateway uses ACM certificates to enable HTTPS.

---

# Why ACM?

Without ACM:

```text
Purchase Certificate

↓

Install Certificate

↓

Renew Certificate

↓

Configure HTTPS
```

With ACM:

```text
Request Certificate

↓

DNS Validation

↓

Automatic Renewal
```

AWS manages the certificate lifecycle.

---

# HTTPS Architecture

```text
Client

↓

HTTPS

↓

ACM Certificate

↓

API Gateway

↓

Backend
```

Communication is encrypted end-to-end.

---

# Certificate Validation

ACM supports:

- DNS Validation
- Email Validation

DNS validation is recommended because certificates renew automatically.

---

# Regional vs Edge-Optimized Domains

Custom domains depend on endpoint type.

| Endpoint Type | Certificate Region |
|---------------|-------------------|
| Regional API | Same AWS Region as the API |
| Edge-Optimized API | ACM certificate must be in **us-east-1** |

This is a common interview question.

---

# DNS Configuration

After creating the custom domain:

```text
api.example.com

↓

Route 53 Alias Record

↓

API Gateway
```

Alternatively, use a CNAME record if DNS is managed outside Route 53.

---

# Route 53 Integration

Typical architecture:

```text
Client

↓

Route 53

↓

api.example.com

↓

API Gateway

↓

Backend
```

Route 53 resolves the custom domain to API Gateway.

---

# Mutual TLS with Custom Domains

Mutual TLS is supported only on:

```text
Regional Custom Domains
```

Architecture:

```text
Client Certificate

↓

Regional Custom Domain

↓

API Gateway
```

This is why mTLS requires a custom domain.

---

# Custom Domain vs Default Endpoint

| Default Endpoint | Custom Domain |
|------------------|---------------|
| AWS-generated | Your domain |
| Difficult to remember | Easy to remember |
| Not branded | Branded |
| Limited flexibility | Supports base path mapping |
| Production-ready | Yes (recommended) |

---

# Real-World Example

A company exposes several APIs.

Instead of:

```text
orders.execute-api.amazonaws.com

payments.execute-api.amazonaws.com

users.execute-api.amazonaws.com
```

They expose:

```text
api.company.com/orders

api.company.com/payments

api.company.com/users
```

Benefits:

- Consistent branding
- Easier documentation
- Simplified client configuration
- Centralized API access

---

# Common Interview Questions

### Why use a Custom Domain Name in API Gateway?

A Custom Domain provides a branded, user-friendly URL, supports API versioning and base path mappings, and is the recommended approach for production APIs.

---

### What is AWS Certificate Manager (ACM)?

AWS Certificate Manager is a managed AWS service that provisions, validates, renews, and manages SSL/TLS certificates used by services such as API Gateway, CloudFront, and Application Load Balancers.

---

### What is Base Path Mapping?

Base Path Mapping allows multiple APIs or API stages to be exposed under a single custom domain.

Example:

```text
api.company.com/orders

api.company.com/payments

api.company.com/users
```

---

### Which ACM Region should be used for an Edge-Optimized API?

The ACM certificate must be created in:

```text
us-east-1
```

For Regional APIs, the certificate must be in the same Region as the API.

---

### Why does Mutual TLS require a Custom Domain?

Mutual TLS is supported only on **Regional Custom Domain Names**, because API Gateway validates client certificates during the TLS handshake associated with the custom domain.

---

# Best Practices

- Always use Custom Domain Names for production APIs.
- Use ACM-managed certificates instead of manually managed certificates.
- Prefer DNS validation for automatic certificate renewal.
- Use Route 53 Alias records when hosting DNS in AWS.
- Organize APIs using Base Path Mappings instead of creating multiple domains unnecessarily.
- Separate development, testing, and production using different custom domains.
- Use Regional Custom Domains when Mutual TLS is required.
- Monitor certificate expiration and DNS configuration even though ACM automates renewals.

---

# Key Takeaways

- Custom Domain Names replace AWS-generated API Gateway URLs with branded, user-friendly endpoints.
- AWS Certificate Manager (ACM) provides managed SSL/TLS certificates for secure HTTPS communication.
- Base Path Mappings allow multiple APIs to share a single custom domain.
- Regional APIs require ACM certificates in the same Region, while Edge-Optimized APIs require certificates in **us-east-1**.
- Custom Domain Names are a production best practice and are required for enabling Mutual TLS (mTLS) in API Gateway.