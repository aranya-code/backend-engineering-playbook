# AWS WAF Integration

## Overview

Amazon API Gateway protects APIs using authentication, authorization, throttling, and resource policies. However, these mechanisms do not protect against common **web application attacks** such as SQL Injection (SQLi), Cross-Site Scripting (XSS), bot traffic, and malicious request patterns.

To defend against these threats, API Gateway integrates with **AWS Web Application Firewall (AWS WAF).**

AWS WAF sits in front of API Gateway and inspects incoming HTTP requests before they reach your APIs.

It helps protect applications from:

- SQL Injection (SQLi)
- Cross-Site Scripting (XSS)
- Bot traffic
- Malicious IP addresses
- HTTP Flood attacks
- Geographic attacks
- Custom attack patterns

For public APIs, integrating AWS WAF with API Gateway is considered a production best practice.

---

# Why AWS WAF?

Imagine a public API.

```text
Internet

↓

API Gateway

↓

Backend
```

Every request reaches API Gateway.

If attackers send:

- SQL Injection
- XSS Payloads
- Millions of Requests
- Malicious Bots

API Gateway still needs to process those requests.

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

Malicious requests are blocked before API Gateway processes them.

---

# Architecture

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

      Lambda / ECS / EC2
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

├── Yes

│      │

│      ▼

│  API Gateway

│

└── No

       │

       ▼

403 Forbidden
```

Blocked requests never reach API Gateway.

---

# What is a Web ACL?

AWS WAF uses a **Web Access Control List (Web ACL)**.

A Web ACL contains:

- Rules
- Rule Groups
- Default Action

Architecture:

```text
Web ACL

↓

Rule 1

↓

Rule 2

↓

Rule 3

↓

Allow / Block
```

API Gateway is associated with a Web ACL.

---

# Rule Evaluation

When a request arrives:

```text
Incoming Request

↓

Rule 1

↓

Rule 2

↓

Rule 3

↓

Allow

or

Block
```

Rules are evaluated in priority order.

The first matching rule determines the outcome.

---

# AWS Managed Rules

AWS provides prebuilt managed rule groups.

Examples:

- Core Rule Set
- Known Bad Inputs
- SQL Injection Protection
- Cross-Site Scripting Protection
- Linux Rule Set
- PHP Rule Set
- Amazon IP Reputation List
- Anonymous IP List

These rules are automatically updated by AWS.

---

# SQL Injection Protection

Suppose an attacker sends:

```text
GET /users?id=1 OR 1=1
```

AWS WAF detects SQL injection patterns.

```text
Request

↓

SQL Injection Rule

↓

Blocked
```

Response:

```http
403 Forbidden
```

Backend is never invoked.

---

# Cross-Site Scripting (XSS)

Attacker sends:

```html
<script>alert("Hacked")</script>
```

AWS WAF recognizes XSS signatures.

```text
Request

↓

XSS Rule

↓

Blocked
```

---

# IP Address Filtering

Allow only specific IP ranges.

Example:

```text
203.0.113.0/24
```

or block:

```text
198.51.100.0/24
```

Architecture:

```text
Incoming IP

↓

IP Rule

↓

Allow

or

Block
```

Useful for:

- Office Networks
- Partner Networks
- Blocking Attack Sources

---

# Geographic Restrictions

Restrict traffic by country.

Example:

```text
Allow

India

Singapore

United States
```

Block:

```text
All Others
```

Useful for region-specific applications.

---

# Rate-Based Rules

AWS WAF can block clients sending excessive requests.

Example:

```text
Limit

2,000 Requests

Every 5 Minutes
```

If exceeded:

```text
IP

↓

Blocked
```

Unlike API Gateway throttling, WAF rate-based rules can temporarily block abusive clients.

---

# Bot Protection

AWS WAF can identify:

- Scrapers
- Crawlers
- Automated Bots
- Credential Stuffing Attacks

Architecture:

```text
Bot

↓

AWS WAF

↓

Blocked
```

Legitimate users continue accessing the API.

---

# Custom Rules

Organizations can define custom rules.

Example:

Block requests when:

- Header is missing
- Suspicious User-Agent
- Invalid HTTP Method
- Oversized Payload
- Missing Authentication Header

This enables application-specific protection.

---

# Logging

AWS WAF supports detailed logging.

Logs include:

- Rule Matched
- Client IP
- Country
- URI
- Headers
- Request Method
- Action Taken

Logs can be sent to:

- CloudWatch Logs
- Amazon S3
- Amazon Kinesis Data Firehose

---

# Monitoring

Useful CloudWatch metrics:

- Allowed Requests
- Blocked Requests
- Counted Requests
- Rate-Based Blocks

Monitoring helps identify attack patterns.

---

# AWS WAF vs API Gateway Throttling

| AWS WAF | API Gateway Throttling |
|----------|------------------------|
| Blocks malicious traffic | Limits request rate |
| Protects against attacks | Protects backend capacity |
| Uses Web ACL rules | Uses rate and burst limits |
| Filters traffic before API Gateway | Applies after request reaches API Gateway |

Both should be used together.

---

# AWS WAF vs Resource Policies

| AWS WAF | Resource Policies |
|----------|-------------------|
| Detects malicious traffic | Controls who may access APIs |
| Uses security rules | Uses IAM policy conditions |
| Protects public APIs | Restricts trusted callers |
| Inspects request content | Evaluates access permissions |

These solve different security problems.

---

# Real-World Architecture

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

      Cognito / JWT Authorizer

                  │

                  ▼

      Lambda / ECS / EC2

                  │

                  ▼

            Amazon RDS
```

This layered architecture is commonly used for production internet-facing APIs.

---

# Common Attack Protection

| Attack | Protected By |
|----------|--------------|
| SQL Injection | AWS Managed Rules |
| Cross-Site Scripting | AWS Managed Rules |
| Bad Bots | Bot Control |
| Credential Stuffing | Bot Control + Rate Rules |
| HTTP Flood | Rate-Based Rules |
| Malicious IP | IP Sets |
| Geographic Abuse | Geo Match Rules |

---

# Best Practices

- Always place AWS WAF in front of public APIs.
- Enable AWS Managed Rule Groups before creating custom rules.
- Use rate-based rules to reduce abusive traffic.
- Block known malicious IP addresses.
- Restrict access by geography when appropriate.
- Monitor blocked requests using CloudWatch.
- Regularly review Web ACL logs.
- Combine WAF with API Gateway authentication and throttling.
- Use AWS Shield together with WAF for comprehensive protection.

---

# Common Interview Questions

### Why use AWS WAF with API Gateway?

AWS WAF protects APIs from common web attacks such as SQL Injection, Cross-Site Scripting, malicious bots, and abusive traffic before requests reach API Gateway.

---

### What is a Web ACL?

A Web ACL (Web Access Control List) is a collection of WAF rules that determine whether incoming requests should be allowed, blocked, or counted.

---

### What is the difference between AWS WAF and API Gateway throttling?

AWS WAF blocks malicious or suspicious traffic based on security rules, while API Gateway throttling limits the rate of requests to protect backend capacity.

---

### Can AWS WAF prevent SQL Injection attacks?

Yes.

AWS Managed Rule Groups include SQL Injection detection that blocks malicious requests before they reach API Gateway or backend services.

---

### Should AWS WAF replace authentication?

No.

AWS WAF protects against web attacks, but it does not authenticate users or authorize access. It should be combined with Cognito, JWT Authorizers, IAM, or Lambda Authorizers.

---

# Key Takeaways

- AWS WAF protects Amazon API Gateway from common web application attacks before requests reach your API.
- A **Web ACL** contains security rules that allow, block, or monitor incoming requests.
- AWS Managed Rule Groups provide protection against SQL Injection, XSS, malicious IPs, bots, and other common threats.
- Rate-based rules complement API Gateway throttling by blocking abusive clients at the edge.
- Combining AWS WAF with authentication, authorization, throttling, and monitoring provides a strong, layered security architecture for production APIs.