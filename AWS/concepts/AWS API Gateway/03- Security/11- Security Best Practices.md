# Security Best Practices

## Overview

Building secure APIs involves much more than enabling authentication. A production-grade API should implement **multiple layers of security**, ensuring that even if one layer is compromised, additional controls continue protecting the application.

This concept is known as **Defense in Depth**.

Amazon API Gateway provides numerous security features that work together:

- HTTPS
- Mutual TLS (mTLS)
- Authentication
- Authorization
- Resource Policies
- API Keys
- Usage Plans
- Throttling
- AWS WAF
- CloudWatch Monitoring

Combining these features with secure backend development results in resilient and secure APIs.

---

# Defense in Depth

A secure API should have multiple independent security layers.

```text
                 Internet
                     │
                     ▼
              AWS Shield
                     │
                     ▼
               AWS WAF
                     │
                     ▼
            Amazon API Gateway
                     │
       Authentication & Authorization
                     │
             Resource Policies
                     │
        Throttling & Rate Limiting
                     │
                     ▼
              Backend Service
                     │
                     ▼
               Database
```

Each layer protects against a different category of threat.

---

# Principle of Least Privilege

Always grant the minimum permissions required.

Bad:

```text
AdministratorAccess
```

Good:

```text
execute-api:Invoke

Only

GET /orders
```

Every IAM policy should be as restrictive as possible.

---

# Always Use HTTPS

Never expose APIs over HTTP.

Correct:

```text
https://api.example.com
```

Incorrect:

```text
http://api.example.com
```

HTTPS encrypts:

- Passwords
- Tokens
- Customer Data
- Payment Information

API Gateway supports HTTPS by default.

---

# Use Strong Authentication

Choose the correct authentication mechanism.

| Scenario | Recommendation |
|----------|----------------|
| Internal AWS Services | IAM Authorization |
| Public Web Applications | Cognito or JWT |
| Enterprise Authentication | Lambda Authorizer |
| B2B APIs | Mutual TLS + JWT |

Authentication should occur before backend services process requests.

---

# Use Authorization

Authentication alone is insufficient.

Example:

```text
User

↓

Authenticated

↓

Can Delete Customer?

↓

No

↓

403 Forbidden
```

Always validate permissions after authentication.

---

# Protect Public APIs with AWS WAF

AWS WAF protects against:

- SQL Injection
- Cross-Site Scripting
- Bot Traffic
- HTTP Floods
- Malicious IP Addresses

Architecture:

```text
Internet

↓

AWS WAF

↓

API Gateway
```

Every internet-facing production API should consider AWS WAF.

---

# Apply Resource Policies

Restrict access whenever possible.

Examples:

- Corporate IP ranges
- Specific AWS Accounts
- IAM Roles
- VPC Endpoints

Example:

```text
Internet

↓

Corporate Network Only

↓

API Gateway
```

Never expose internal APIs publicly unless required.

---

# Enable Throttling

Protect backend systems from excessive traffic.

Example:

```text
Rate

500 Requests/sec

Burst

1000 Requests
```

Clients exceeding limits receive:

```http
429 Too Many Requests
```

---

# Use Usage Plans

For REST APIs:

Different customers should have different limits.

Example:

```text
Free

↓

100 Requests/Day

-------------------

Premium

↓

10000 Requests/Day
```

Usage Plans prevent one customer from affecting others.

---

# Never Trust Client Input

Even after API Gateway validation:

Always validate:

- JSON payloads
- Path parameters
- Query parameters
- Headers

Backend applications should never assume requests are safe.

---

# Protect Sensitive Data

Never expose:

- Internal IDs
- Passwords
- Database Errors
- Stack Traces
- Secrets
- Access Tokens

Bad:

```json
{
    "error":"SQL Exception at line 45"
}
```

Better:

```json
{
    "message":"Internal Server Error"
}
```

---

# Use Proper HTTP Status Codes

Return meaningful status codes.

| Status | Meaning |
|---------|----------|
| 200 | Success |
| 201 | Resource Created |
| 204 | No Content |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 409 | Conflict |
| 429 | Too Many Requests |
| 500 | Internal Server Error |

Avoid returning:

```text
200 OK

for every request
```

---

# Enable Logging

CloudWatch logs help detect:

- Unauthorized access
- Repeated failures
- Suspicious IP addresses
- Performance issues

Recommended:

```text
CloudWatch Logs

Enabled
```

Do not log:

- Passwords
- JWT Tokens
- API Keys
- Secrets

---

# Enable CloudTrail

CloudTrail records management operations.

Examples:

- API deployments
- Configuration changes
- IAM changes
- Stage updates

Useful for:

- Auditing
- Compliance
- Incident investigation

---

# Monitor Metrics

Useful CloudWatch metrics include:

- Request Count
- 4XX Errors
- 5XX Errors
- Latency
- Integration Latency
- Throttled Requests

Alerts should be configured for unusual spikes.

---

# Rotate Credentials

Rotate:

- API Keys
- IAM Credentials
- Client Certificates
- JWT Signing Keys

Never use permanent credentials when temporary credentials are available.

---

# Secure Backend Services

API Gateway should not be the only security layer.

Backend services should also:

- Validate inputs
- Verify authorization
- Sanitize data
- Protect databases
- Encrypt sensitive data

Defense in depth continues beyond API Gateway.

---

# Protect Secrets

Never hardcode:

```text
Database Password

AWS Keys

JWT Secret

API Key
```

Use:

- AWS Secrets Manager
- AWS Systems Manager Parameter Store

instead.

---

# Use Mutual TLS for Partner APIs

For B2B communication:

```text
Partner

↓

mTLS

↓

API Gateway
```

Only trusted organizations possessing valid client certificates can connect.

---

# Use JWT Expiration

JWTs should have short lifetimes.

Example:

```text
Access Token

15 Minutes

--------------------

Refresh Token

Several Days
```

Short-lived tokens reduce risk if compromised.

---

# Validate Everything

Backend validation should include:

```text
Authentication

↓

Authorization

↓

Request Validation

↓

Business Rules

↓

Database Constraints
```

Never rely solely on client-side validation.

---

# Production Security Checklist

Before deploying an API:

- HTTPS enabled
- Authentication configured
- Authorization configured
- AWS WAF enabled
- Throttling configured
- Logging enabled
- Monitoring enabled
- Least privilege IAM policies
- Secrets stored securely
- Input validation implemented
- Proper error handling
- Resource Policies reviewed

---

# Real-World Secure Architecture

```text
                Internet

                    │

                    ▼

              AWS Shield

                    │

                    ▼

               AWS WAF

                    │

                    ▼

          Amazon API Gateway

                    │

          JWT Authorizer

                    │

          Resource Policy

                    │

             Throttling

                    │

                    ▼

          Lambda / ECS / EC2

                    │

                    ▼

          Amazon RDS
```

This layered architecture minimizes attack surface and improves resilience.

---

# Common Security Mistakes

Avoid:

- Public APIs without authentication
- Using API Keys as authentication
- Excessive IAM permissions
- Hardcoded secrets
- Returning internal error messages
- Disabling HTTPS
- Ignoring CloudWatch alarms
- Unlimited request rates
- Logging sensitive information

---

# Common Interview Questions

### What is Defense in Depth?

Defense in Depth is the practice of applying multiple independent security layers so that compromising one control does not compromise the entire system.

---

### Why shouldn't API Keys be used for authentication?

API Keys identify API consumers but do not verify identity or permissions. They should be combined with IAM, Cognito, JWT, or Lambda Authorizers.

---

### Why validate input in the backend if API Gateway already validates requests?

API Gateway validation is an additional protection layer. Backend services should always validate requests because clients, integrations, or configurations may change over time.

---

### What AWS services are commonly used to secure API Gateway?

Common services include:

- AWS WAF
- AWS Shield
- Amazon Cognito
- IAM
- AWS Secrets Manager
- CloudWatch
- CloudTrail

---

# Key Takeaways

- Production APIs should implement multiple independent security layers following the Defense in Depth principle.
- Use HTTPS, strong authentication, authorization, throttling, Resource Policies, AWS WAF, and monitoring together.
- Follow the Principle of Least Privilege for IAM and API access.
- Never trust client input, expose sensitive information, or hardcode secrets.
- Secure API Gateway is only one part of a secure application—backend services must also enforce validation, authorization, and data protection.