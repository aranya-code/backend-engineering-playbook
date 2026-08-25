# API Gateway + AWS WAF

## Overview

Security is one of the most critical aspects of any public API. Even if an API is protected with authentication and authorization, it can still be vulnerable to attacks such as:

- SQL Injection (SQLi)
- Cross-Site Scripting (XSS)
- HTTP Flood Attacks
- Bot Traffic
- Malicious IP Addresses
- API Abuse
- DDoS Attacks

To protect APIs from these threats, Amazon API Gateway integrates with **AWS WAF (Web Application Firewall)**.

AWS WAF filters and inspects incoming HTTP requests before they reach API Gateway, allowing organizations to block malicious traffic while permitting legitimate users.

This architecture is commonly used for:

- Public REST APIs
- Banking Applications
- E-commerce Platforms
- Healthcare Systems
- SaaS Applications
- Enterprise APIs

---

# Why AWS WAF?

Without WAF:

```text
Internet

↓

API Gateway

↓

Backend
```

Every request reaches API Gateway.

Even malicious requests consume resources.

---

With AWS WAF:

```text
Internet

↓

AWS WAF

↓

API Gateway

↓

Backend
```

Malicious requests are blocked immediately.

---

# High-Level Architecture

```text
                 Internet

                    │

                    ▼

                 AWS WAF

                    │

                    ▼

           Amazon API Gateway

                    │

                    ▼

      Lambda / ECS / EC2 Backend
```

WAF becomes the first security layer.

---

# Request Flow

```text
Client

↓

AWS WAF

↓

Rule Evaluation

↓

Allowed?

│

├── No

│      │

│      ▼

│   Block Request

│

└── Yes

       │

       ▼

API Gateway

↓

Backend
```

Only approved traffic reaches API Gateway.

---

# What is AWS WAF?

AWS WAF is a managed Web Application Firewall that filters HTTP and HTTPS requests.

It protects applications against:

- Injection attacks
- Common web exploits
- Automated bots
- Malicious IPs
- Excessive request rates

---

# Web ACL

The primary AWS WAF resource is a **Web ACL (Access Control List).**

```text
Web ACL

│

├── Rule 1

├── Rule 2

├── Rule 3
```

The Web ACL is associated with API Gateway.

---

# Rule Evaluation

Rules are evaluated in order.

```text
Incoming Request

↓

Rule 1

↓

Rule 2

↓

Rule 3

↓

Allow / Block
```

The first matching rule determines the action.

---

# Allow Rule

Example:

```text
Corporate IP

↓

Allow
```

Trusted traffic proceeds normally.

---

# Block Rule

Example:

```text
Known Malicious IP

↓

Block
```

The request never reaches API Gateway.

---

# IP Filtering

Example:

```text
Allowed

203.0.113.10

-------------------

Blocked

198.51.100.25
```

Useful for:

- Internal APIs
- Regional restrictions
- Threat mitigation

---

# Geo Match Rules

Requests can be filtered by country.

Example:

```text
India

↓

Allow

-------------------

Unknown Region

↓

Block
```

Useful for compliance and fraud prevention.

---

# Rate-Based Rules

Suppose a client sends:

```text
100 Requests

↓

Allowed
```

Suddenly:

```text
20,000 Requests

↓

Rate Limit

↓

Blocked
```

This helps mitigate API abuse.

---

# SQL Injection Protection

Malicious request:

```sql
' OR 1=1 --
```

AWS WAF detects the SQL injection pattern and blocks the request before it reaches the backend.

---

# Cross-Site Scripting (XSS)

Example attack:

```html
<script>alert("Attack")</script>
```

AWS WAF identifies common XSS patterns and blocks the request automatically.

---

# Bot Protection

Examples:

- Credential stuffing
- Web scraping
- Automated login attempts

AWS WAF Bot Control helps distinguish automated traffic from legitimate users.

---

# AWS Managed Rules

AWS provides managed rule groups such as:

- Core Rule Set
- SQL Injection Rules
- Known Bad Inputs
- Linux Rules
- Amazon IP Reputation List
- Anonymous IP List

These rules are maintained automatically by AWS.

---

# Custom Rules

Organizations can define custom rules.

Example:

```text
URI

/admin

↓

Block
```

or

```text
Header

↓

Missing API Key

↓

Block
```

---

# Rule Priority

Example:

```text
Allow Corporate IP

↓

Block SQL Injection

↓

Rate Limit

↓

Default Action
```

Rule order affects request processing.

---

# Default Action

If no rules match:

```text
Default

↓

Allow
```

or

```text
Default

↓

Block
```

Choose carefully based on security requirements.

---

# Logging

AWS WAF supports detailed request logging.

Logs include:

- Client IP
- URI
- Rule matched
- Action taken
- Timestamp

Logs can be sent to:

- Amazon CloudWatch Logs
- Amazon S3
- Amazon Kinesis Data Firehose

---

# Monitoring

Monitor:

- Allowed Requests
- Blocked Requests
- Rate-Limited Requests
- Top IP Addresses
- Rule Matches

CloudWatch Metrics provide visibility into WAF activity.

---

# AWS Shield Integration

CloudFront and API Gateway benefit from:

```text
AWS Shield Standard
```

For advanced DDoS protection:

```text
AWS Shield Advanced
```

can be combined with WAF.

---

# Common Use Cases

AWS WAF is commonly used for:

- Public APIs
- Banking applications
- E-commerce websites
- Healthcare platforms
- Government portals
- SaaS products
- Login APIs
- Payment APIs

---

# Advantages

- Managed security rules
- Automatic updates
- SQL Injection protection
- XSS protection
- Rate limiting
- IP filtering
- Geographic filtering
- Bot mitigation
- CloudWatch integration

---

# Limitations

- Additional AWS cost
- Rule tuning may be required
- False positives are possible
- Does not replace application-level validation
- Business logic security must still be implemented by the application

---

# Production Architecture

```text
                    Users

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

            Authentication

                       │

             Request Validation

                       │

                       ▼

          Lambda / ECS / EC2 Backend

                       │

                       ▼

       DynamoDB • Aurora • Redis
```

This layered architecture provides strong protection against common web attacks.

---

# AWS WAF vs API Gateway Authentication

| AWS WAF | API Gateway |
|----------|-------------|
| Filters malicious HTTP traffic | Authenticates users |
| Blocks SQL Injection | Validates JWT |
| Blocks XSS | Authorizes requests |
| Rate limits requests | Validates request models |
| IP filtering | API Keys & Usage Plans |

They protect different layers of the application.

---

# Best Practices

- Place AWS WAF in front of every public API.
- Use AWS Managed Rule Groups before creating custom rules.
- Enable rate-based rules to mitigate abuse.
- Restrict access using IP and geographic rules when appropriate.
- Enable WAF logging for security investigations.
- Monitor blocked requests using CloudWatch.
- Combine AWS WAF with AWS Shield and API Gateway authentication.
- Continue validating requests in API Gateway and backend applications.

---

# Common Interview Questions

### Why use AWS WAF with API Gateway?

AWS WAF protects APIs from common web attacks such as SQL Injection, Cross-Site Scripting, malicious bots, abusive traffic, and DDoS attempts before requests reach API Gateway.

---

### What is a Web ACL?

A Web ACL (Access Control List) is a collection of WAF rules that determines whether incoming requests should be allowed, blocked, counted, or rate-limited.

---

### Does AWS WAF replace authentication?

No.

AWS WAF filters malicious HTTP requests, while API Gateway authentication verifies the identity of legitimate users.

---

### Can AWS WAF prevent SQL Injection attacks?

Yes.

AWS Managed Rules include protections against common SQL Injection patterns and can block malicious requests before they reach the backend.

---

### Why combine AWS WAF with CloudFront and API Gateway?

CloudFront provides global edge delivery, AWS WAF filters malicious requests at the edge, and API Gateway handles API management, authentication, authorization, and routing. Together they form a secure, scalable, and production-ready API architecture.

---

# Key Takeaways

- AWS WAF provides a managed Web Application Firewall that protects Amazon API Gateway from common web attacks.
- Web ACLs use managed and custom rules to inspect, allow, block, or rate-limit incoming requests.
- AWS WAF protects against SQL Injection, Cross-Site Scripting, malicious bots, abusive traffic, and unwanted IP addresses.
- WAF complements API Gateway by securing the HTTP layer, while API Gateway handles authentication, authorization, and API management.
- Combining Route 53, CloudFront, AWS WAF, API Gateway, and secure backend services creates a layered defense suitable for enterprise-grade production APIs.