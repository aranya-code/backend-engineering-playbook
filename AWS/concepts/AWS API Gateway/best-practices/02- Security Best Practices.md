# Security Best Practices

## Overview

Security should never be treated as an afterthought. A production API must assume that every public endpoint will eventually receive:

- Malicious requests
- Automated bot traffic
- Credential stuffing attacks
- SQL Injection attempts
- Cross-Site Scripting (XSS)
- Denial-of-Service (DoS) attacks
- Unauthorized access attempts

Amazon API Gateway provides numerous security features, but a secure API requires **multiple layers of defense** rather than relying on a single mechanism.

This chapter covers the security practices commonly used in enterprise API deployments.

---

# Apply Defense in Depth

Never rely on a single security control.

Instead:

```text
Internet

↓

CloudFront

↓

AWS WAF

↓

API Gateway

↓

Authentication

↓

Authorization

↓

Backend Validation

↓

Database
```

Every layer provides additional protection.

---

# Always Use HTTPS

Never expose production APIs over HTTP.

Good:

```text
https://api.company.com
```

Avoid:

```text
http://api.company.com
```

HTTPS provides:

- Encryption
- Integrity
- Authentication

---

# Use Strong Authentication

Every protected endpoint should require authentication.

Supported options include:

- Amazon Cognito
- JWT Authorizers
- IAM Authentication
- Lambda Authorizers
- Mutual TLS

Authentication verifies:

```text
Who are you?
```

---

# Implement Authorization

Authentication alone is not sufficient.

Authorization determines:

```text
What are you allowed to do?
```

Example:

```text
Admin

↓

Delete User

↓

Allowed

--------------------

Regular User

↓

Delete User

↓

Forbidden
```

Always follow the principle of least privilege.

---

# Validate JWT Tokens

API Gateway should validate:

- Signature
- Issuer
- Audience
- Expiration

Invalid tokens should return:

```http
401 Unauthorized
```

before reaching backend services.

---

# Never Trust Client Input

Every request should be validated.

Validate:

- JSON body
- Headers
- Query parameters
- Path parameters

Never assume client input is safe.

---

# Enable Request Validation

Example:

Expected:

```json
{
    "email":"john@example.com"
}
```

Received:

```json
{
}
```

API Gateway should reject the request with:

```http
400 Bad Request
```

Backend services should never process invalid requests.

---

# Protect Against SQL Injection

Never concatenate user input into SQL queries.

Bad:

```sql
SELECT * FROM users WHERE id = " + userInput
```

Good:

```text
Parameterized Queries
```

Use:

- Prepared Statements
- ORM frameworks
- Parameterized SQL

---

# Protect Against XSS

Never trust user-generated HTML.

Always:

- Escape output
- Sanitize HTML
- Validate input

Use AWS WAF Managed Rules to detect common XSS attacks.

---

# Use AWS WAF

Place AWS WAF before API Gateway.

```text
Internet

↓

AWS WAF

↓

API Gateway
```

WAF protects against:

- SQL Injection
- XSS
- Bot traffic
- Malicious IPs
- Rate abuse

---

# Enable Rate Limiting

Protect backend services from abuse.

Example:

```text
100 Requests/minute

↓

Allowed

-------------------

10,000 Requests/minute

↓

429 Too Many Requests
```

Use:

- Usage Plans
- API Keys
- Throttling
- AWS WAF Rate-Based Rules

---

# Hide Backend Services

Clients should never access backend services directly.

Instead:

```text
Client

↓

API Gateway

↓

Private Backend
```

Keep:

- ECS
- EC2
- Databases

inside private subnets whenever possible.

---

# Use Private APIs

Internal APIs should use:

```text
Private API

↓

AWS PrivateLink

↓

VPC Endpoint
```

Avoid exposing internal services to the public internet.

---

# Protect Secrets

Never hardcode:

- API Keys
- Passwords
- Database Credentials
- AWS Keys

Use:

- AWS Secrets Manager
- AWS Systems Manager Parameter Store

---

# Encrypt Sensitive Data

Sensitive data should be encrypted:

In transit:

```text
HTTPS
```

At rest:

```text
AWS KMS
```

Examples:

- S3
- RDS
- DynamoDB
- EBS

---

# Use Least Privilege IAM

Example:

Bad:

```text
AdministratorAccess
```

Good:

```text
Read Product Table Only
```

Grant only the permissions required for each workload.

---

# Secure Lambda Functions

Lambda execution roles should:

- Have minimal permissions
- Access only required resources
- Avoid wildcard IAM policies

Example:

```text
Allow

↓

Read Orders Table

-------------------

Deny

↓

Everything Else
```

---

# Secure Containers

For ECS/EKS/EC2:

- Use private container registries
- Scan container images
- Keep base images updated
- Avoid running as root
- Patch operating systems regularly

---

# Enable Logging

Log:

- Authentication failures
- Authorization failures
- Blocked requests
- Rate-limited requests
- Unexpected errors

Use:

- CloudWatch Logs
- AWS CloudTrail

Avoid logging sensitive information.

---

# Monitor Security Events

Monitor:

- 401 responses
- 403 responses
- WAF blocked requests
- API throttling
- Login failures
- Unusual request spikes

Configure CloudWatch Alarms for critical events.

---

# Protect Against DDoS

Use:

```text
CloudFront

↓

AWS Shield

↓

AWS WAF

↓

API Gateway
```

AWS Shield Standard is included automatically with CloudFront and API Gateway.

---

# Secure Custom Domains

Use:

- ACM Certificates
- TLS 1.2+
- Strong cipher suites

Disable outdated TLS versions whenever possible.

---

# Use Idempotency for Sensitive Operations

Example:

```text
POST /payments
```

Client retries:

```text
Payment

↓

Processed Once
```

Use an **Idempotency-Key** to prevent duplicate transactions.

---

# Secure Error Messages

Good:

```json
{
    "error":"Invalid credentials."
}
```

Avoid:

```json
{
    "database":"Connection failed at db-prod-01"
}
```

Never expose internal implementation details.

---

# Secure File Uploads

For uploads:

```text
Client

↓

Pre-Signed URL

↓

Amazon S3
```

Avoid routing large files through API Gateway.

Always validate:

- File type
- File size
- Malware (if applicable)

---

# Security Testing

Regularly perform:

- Penetration testing
- Vulnerability scanning
- Dependency scanning
- IAM policy reviews
- Secret rotation
- Container image scanning

Security is an ongoing process.

---

# Production Security Architecture

```text
                   Internet

                      │

                      ▼

                Amazon Route 53

                      │

                      ▼

                 CloudFront

                      │

                      ▼

                   AWS WAF

                      │

                      ▼

              Amazon API Gateway

                      │

        Authentication & Authorization

                      │

               Request Validation

                      │

                Private Backend

                      │

                      ▼

       DynamoDB • Aurora • Redis
```

This layered architecture provides defense in depth.

---

# Security Checklist

Before production:

- HTTPS enabled
- Authentication configured
- Authorization implemented
- JWT validation enabled
- AWS WAF configured
- Rate limiting enabled
- Request validation enabled
- Secrets stored securely
- IAM least privilege applied
- CloudWatch monitoring enabled
- CloudTrail enabled
- Data encrypted at rest
- Data encrypted in transit
- Private networking used where possible

---

# Common Security Mistakes

Avoid:

- Hardcoded credentials
- Public databases
- Administrator IAM roles
- Missing authentication
- Logging passwords
- No request validation
- Returning internal error details
- Using HTTP instead of HTTPS
- Trusting client input
- Exposing backend services directly

---

# Common Interview Questions

### Why is authentication alone insufficient?

Authentication verifies identity, while authorization determines what an authenticated user is allowed to access. Both are required to secure APIs.

---

### Why should API Gateway validate JWT tokens instead of backend services?

Centralizing JWT validation in API Gateway reduces duplicated code, improves consistency, and prevents unauthorized requests from reaching backend services.

---

### What is the principle of least privilege?

Every user, service, or application should receive only the permissions required to perform its intended tasks and nothing more.

---

### Why should backend services remain private?

Keeping backend services in private subnets reduces the attack surface and ensures that all external traffic passes through controlled entry points such as API Gateway.

---

### How does AWS WAF complement API Gateway?

AWS WAF blocks malicious HTTP requests such as SQL Injection, XSS, bot traffic, and abusive request patterns before they reach API Gateway, while API Gateway focuses on authentication, authorization, and API management.

---

# Key Takeaways

- Security should be implemented using multiple layers rather than a single mechanism.
- HTTPS, authentication, authorization, request validation, and least-privilege IAM form the foundation of secure APIs.
- AWS WAF, CloudFront, API Gateway, and private networking work together to protect production workloads.
- Secrets should be stored securely, data should be encrypted, and backend services should remain private whenever possible.
- Continuous monitoring, logging, security testing, and regular reviews are essential for maintaining a secure production API.