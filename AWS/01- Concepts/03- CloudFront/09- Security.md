# AWS CloudFront - Section 06: Security

# Why Security Matters in CloudFront

CloudFront sits between:

```text
Users
  |
CloudFront
  |
Origin
```

Every request passes through CloudFront.

This makes CloudFront an ideal location for:

- Access Control
- DDoS Protection
- SSL Termination
- Request Filtering
- Content Protection
- Geographic Restrictions

---

# CloudFront Security Layers

CloudFront security can be viewed in layers.

```text
Layer 1: HTTPS/TLS
Layer 2: AWS Shield
Layer 3: AWS WAF
Layer 4: OAC
Layer 5: Signed URLs/Cookies
Layer 6: Geo Restriction
Layer 7: Field-Level Encryption
```

Each layer protects against different threats.

---

# HTTPS and SSL/TLS

## Why HTTPS?

Without HTTPS:

```text
User
  |
HTTP
  |
CloudFront
```

Data travels unencrypted.

Risks:

- Data interception
- Credential theft
- Session hijacking

---

## With HTTPS

```text
User
  |
HTTPS
  |
CloudFront
```

Data is encrypted.

Benefits:

- Confidentiality
- Integrity
- Authentication

---

# SSL/TLS Certificates

CloudFront supports:

```text
AWS Certificate Manager (ACM)
Third-Party Certificates
```

---

## Example

Domain:

```text
cdn.company.com
```

Certificate:

```text
*.company.com
```

CloudFront presents the certificate to users.

---

# Viewer Protocol Policies

CloudFront supports:

## HTTP and HTTPS

```text
Allow Both
```

Not recommended.

---

## Redirect HTTP to HTTPS

```text
HTTP
  |
Redirect
  |
HTTPS
```

Recommended.

---

## HTTPS Only

Reject HTTP requests.

Most secure option.

---

# Best Practice

Use:

```text
Redirect HTTP to HTTPS
```

or

```text
HTTPS Only
```

---

# AWS Shield

## What is AWS Shield?

AWS Shield protects CloudFront from DDoS attacks.

Enabled automatically.

---

# Types of DDoS Attacks

Examples:

```text
SYN Flood
UDP Flood
Reflection Attack
Volumetric Attack
```

---

# AWS Shield Standard

Included automatically.

Protects:

```text
Layer 3
Layer 4
```

attacks.

No extra cost.

---

# AWS Shield Advanced

Additional paid service.

Provides:

- Enhanced DDoS protection
- Detailed attack visibility
- Faster mitigation

Used by:

```text
Large Enterprises
Financial Systems
Critical Applications
```

---

# AWS WAF

## What is AWS WAF?

AWS Web Application Firewall filters malicious requests before they reach the origin.

Architecture:

```text
Users
  |
AWS WAF
  |
CloudFront
  |
Origin
```

---

# Why WAF Is Important

CloudFront handles traffic.

WAF inspects traffic.

Together they provide strong protection.

---

# Common Threats Blocked

## SQL Injection

Example:

```sql
' OR 1=1 --
```

---

## Cross Site Scripting (XSS)

Example:

```html
<script>alert('hack')</script>
```

---

## Bots

Examples:

```text
Scrapers
Credential Stuffing
Automated Scanners
```

---

## Geographic Threats

Block traffic from specific countries.

---

# WAF Rule Types

## Managed Rules

AWS-managed protections.

Examples:

```text
SQL Injection Rules
Known Bad Inputs
Linux Rules
WordPress Rules
```

---

## Custom Rules

Organization-specific rules.

Example:

```text
Block IP Range
Block Specific Paths
Rate Limit Requests
```

---

# Rate Limiting

Example:

```text
100 Requests Per Minute
```

If exceeded:

```text
Block Request
```

Useful against:

```text
Brute Force Attacks
Bot Traffic
```

---

# Origin Access Control (OAC)

## Why OAC Exists

Without OAC:

```text
Users
   |
CloudFront
   |
S3
```

But users may also access:

```text
Users
   |
S3
```

directly.

---

# Problems

Users bypass:

- WAF
- Logging
- Caching
- Geo Restrictions

---

# OAC Solution

```text
Users
   |
CloudFront
   |
S3
```

Only CloudFront can access S3.

---

# Benefits

## Better Security

Prevents direct bucket access.

---

## SigV4 Support

Uses modern AWS authentication.

---

## Recommended by AWS

Current best practice.

---

# OAC vs OAI

| Feature | OAC | OAI |
|----------|------|------|
| AWS Recommended | Yes | No |
| SigV4 Support | Yes | Limited |
| Modern Architecture | Yes | No |
| Future Support | Yes | Legacy |

---

# Geo Restriction

## What Is Geo Restriction?

Controls access based on country.

---

# Example

Allow:

```text
India
United States
United Kingdom
```

---

Block:

```text
All Others
```

---

# Use Cases

## Licensing

Video streaming rights.

---

## Compliance

Regional regulations.

---

## Business Restrictions

Country-specific services.

---

# Geo Restriction Modes

## Allow List

Only specified countries allowed.

---

## Block List

Specified countries blocked.

---

# Field-Level Encryption

## What Is Field-Level Encryption?

Encrypts specific fields before data reaches the origin.

---

# Why Needed?

HTTPS protects:

```text
Entire Connection
```

Field-Level Encryption protects:

```text
Specific Sensitive Fields
```

---

# Example

Payment Form:

```text
Name
Address
Credit Card Number
```

Encrypt:

```text
Credit Card Number
```

before forwarding.

---

# Flow

```text
User
  |
CloudFront
  |
Encrypt Sensitive Field
  |
Origin
```

---

# Benefits

- PCI Compliance
- Additional Security
- Reduced Exposure

---

# Signed URLs

## Purpose

Provide temporary access to specific content.

---

# Example

Protected File:

```text
premium-video.mp4
```

Generate:

```text
Signed URL
```

with expiration.

---

# Benefits

- Temporary access
- Fine-grained control
- Content protection

---

# Signed Cookies

## Purpose

Grant access to multiple protected files.

---

# Example

Streaming Platform:

```text
video1.mp4
video2.mp4
video3.mp4
```

One cookie grants access.

---

# Signed URL vs Signed Cookie

| Feature | Signed URL | Signed Cookie |
|----------|------------|---------------|
| Scope | Single File | Multiple Files |
| Best For | Downloads | Streaming Platforms |
| URL Modification | Required | Not Required |

---

# Security Headers

CloudFront can add security headers.

Examples:

```http
Strict-Transport-Security
```

---

```http
X-Frame-Options
```

---

```http
Content-Security-Policy
```

---

# Security Architecture Example

Secure Static Website:

```text
Users
  |
HTTPS
  |
CloudFront
  |
WAF
  |
OAC
  |
S3
```

---

# Enterprise Architecture

```text
Users
  |
HTTPS
  |
CloudFront
  |
AWS WAF
  |
ALB
  |
ECS
```

Protection Layers:

- HTTPS
- Shield
- WAF
- Security Groups

---

# Common Security Mistakes

## Public S3 Buckets

Bad:

```text
Users
   |
S3
```

Use:

```text
CloudFront + OAC
```

---

## HTTP Allowed

Risk:

```text
Traffic Interception
```

Always enforce HTTPS.

---

## No WAF

Increases exposure to:

```text
SQL Injection
XSS
Bots
```

---

## Long-Lived Signed URLs

Risk:

```text
Unauthorized Sharing
```

Use short expiration times.

---

# Troubleshooting Security Issues

## 403 Access Denied

Possible Causes:

- OAC misconfiguration
- Bucket policy issue
- WAF block
- Signed URL expired

---

## SSL Errors

Possible Causes:

- Invalid certificate
- Expired certificate
- Incorrect domain mapping

---

## Geo Restriction Failure

Check:

```text
Country Rules
Distribution Settings
```

---

## WAF Blocking Legitimate Users

Review:

```text
WAF Logs
Rule Configuration
```

---

# Interview Questions

## Q1. How does CloudFront improve security?

CloudFront integrates with:

- AWS Shield
- AWS WAF
- HTTPS
- OAC
- Signed URLs
- Signed Cookies
- Field-Level Encryption

---

## Q2. What is OAC?

Origin Access Control allows CloudFront to securely access S3 while preventing direct user access.

---

## Q3. Difference Between OAC and OAI?

OAC is AWS's modern and recommended mechanism.

---

## Q4. What is AWS Shield?

A DDoS protection service integrated with CloudFront.

---

## Q5. What is AWS WAF?

A web application firewall that filters malicious requests.

---

## Q6. Why Use Field-Level Encryption?

To protect sensitive data such as payment information before it reaches the origin.

---

## Q7. Difference Between HTTPS and Field-Level Encryption?

HTTPS:

```text
Encrypts Entire Connection
```

Field-Level Encryption:

```text
Encrypts Specific Fields
```

---

## Q8. When Should Signed Cookies Be Used?

When users require access to multiple protected resources.

---

# Summary

Key Takeaways:

- CloudFront is a major security layer between users and origins.
- HTTPS protects data in transit.
- AWS Shield protects against DDoS attacks.
- AWS WAF filters malicious traffic.
- OAC secures S3 origins.
- Geo Restriction controls country-based access.
- Field-Level Encryption protects sensitive fields.
- Signed URLs and Signed Cookies protect private content.
- Security is one of the most frequently tested CloudFront interview topics.

A production-grade CloudFront deployment should almost always include:

```text
HTTPS
AWS Shield
AWS WAF
OAC
Logging
Geo Restrictions (if needed)
Signed URLs/Cookies (if needed)
```