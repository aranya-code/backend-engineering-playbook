# AWS CloudFront - Section 03: Origins

# What is an Origin?

An Origin is the backend location where CloudFront retrieves content when the requested object is not available in cache.

Think of CloudFront as a delivery service.

CloudFront does not create content.

Instead, it retrieves content from an origin and distributes it globally.

Architecture:

```text
User
  |
CloudFront
  |
Origin
```

The origin acts as the:

```text
Source of Truth
```

for all content.

---

# Why Origins Are Required

CloudFront is a caching service.

If content does not exist in cache:

```text
Cache Miss
```

CloudFront must retrieve the object from somewhere.

That "somewhere" is called the Origin.

Example:

```text
/logo.png
```

CloudFront requests the object from:

```text
S3 Bucket
```

stores it in cache, and serves it to users.

---

# Origin Types Supported by CloudFront

CloudFront supports three major origin categories:

```text
1. S3 Origins
2. Custom Origins
3. VPC Origins
```

Each serves different use cases.

---

# S3 Origins

## What is an S3 Origin?

An Amazon S3 bucket configured as a CloudFront origin.

Architecture:

```text
Users
   |
CloudFront
   |
S3 Bucket
```

---

## Common Use Cases

### Static Websites

Examples:

```text
HTML
CSS
JavaScript
Images
Fonts
```

---

### Video Content

Examples:

```text
MP4
HLS
DASH
```

---

### Downloads

Examples:

```text
Software Installers
Game Updates
PDF Documents
```

---

# Why S3 Is Popular With CloudFront

Benefits:

### Highly Durable

Amazon S3 provides:

```text
11 Nines Durability
```

---

### Highly Scalable

Supports virtually unlimited storage.

---

### Cost Effective

Ideal for static assets.

---

### Easy Integration

Native CloudFront support.

---

# S3 Origin Request Flow

First Request:

```text
User
  |
CloudFront
  |
S3
```

Object retrieved.

Object cached.

---

Subsequent Requests:

```text
User
  |
CloudFront
```

No S3 call required.

---

# Origin Access Control (OAC)

## Problem Without OAC

Consider:

```text
User
   |
CloudFront
   |
S3
```

If bucket permissions allow:

```text
User
   |
S3
```

Users can bypass CloudFront.

---

## Why Is This Bad?

Users bypass:

- WAF
- Logging
- Caching
- Geo Restrictions
- Security controls

---

# Solution: OAC

Origin Access Control ensures:

```text
Only CloudFront
Can Access S3
```

Architecture:

```text
User
  |
CloudFront
  |
S3 Bucket
```

Direct access blocked.

---

# Benefits of OAC

### Better Security

Blocks direct bucket access.

---

### Supports SigV4

Modern AWS signing.

---

### Recommended by AWS

Current best practice.

---

# OAC vs OAI

## OAI (Legacy)

Older mechanism.

Limitations:

- Older architecture
- Less flexible

---

## OAC (Modern)

Advantages:

- SigV4 support
- Better security
- AWS recommended

---

Interview Question:

### Q. Which should be used today?

Answer:

```text
Origin Access Control (OAC)
```

---

# Custom Origins

## What is a Custom Origin?

Any HTTP/HTTPS server that is not S3.

Examples:

```text
EC2
NGINX
Apache
On-Prem Servers
Third-Party Applications
```

---

# Architecture

```text
Users
   |
CloudFront
   |
NGINX Server
```

---

# Common Custom Origin Use Cases

## Dynamic Websites

```text
CloudFront
   |
ALB
   |
EC2
```

---

## APIs

```text
CloudFront
   |
API Server
```

---

## Legacy Applications

```text
CloudFront
   |
On-Prem Server
```

---

# Advantages of Custom Origins

### Dynamic Content

Not limited to static files.

---

### Existing Infrastructure

Can leverage existing systems.

---

### Flexible Architecture

Works with almost any web server.

---

# Challenges With Custom Origins

Unlike S3:

```text
Origin must scale itself.
```

CloudFront reduces traffic but cannot replace origin scalability.

---

# VPC Origins

## What Are VPC Origins?

CloudFront can connect to resources running inside a VPC.

Examples:

```text
Internal ALB
Private Applications
Private APIs
```

---

# Why Use VPC Origins?

Many organizations do not want applications exposed publicly.

Without VPC Origin:

```text
Internet
   |
Application
```

Risk:

```text
Direct Exposure
```

---

# With VPC Origin

```text
Internet
   |
CloudFront
   |
Private Application
```

Benefits:

- Better security
- Reduced attack surface
- Controlled access

---

# Typical Architecture

```text
Users
   |
CloudFront
   |
Internal ALB
   |
ECS
```

---

# Choosing the Right Origin

| Requirement | Recommended Origin |
|------------|-------------------|
| Static Files | S3 |
| Dynamic Website | ALB |
| API | API Gateway / ALB |
| Legacy App | Custom Origin |
| Private Workload | VPC Origin |

---

# Multiple Origins

CloudFront supports multiple origins in a single distribution.

Example:

```text
/images/* -> S3
/api/* -> ALB
/videos/* -> S3
```

Architecture:

```text
            CloudFront
            /        \
           /          \
          v            v
        S3            ALB
```

---

# Why Multiple Origins?

Benefits:

### Separation of Workloads

Static and dynamic traffic isolated.

---

### Better Performance

Optimize each workload separately.

---

### Better Scalability

Different backends for different needs.

---

# Origin Groups

## What Is an Origin Group?

Origin Groups provide:

```text
Automatic Failover
```

Architecture:

```text
Primary Origin
      |
      v
Secondary Origin
```

---

# Normal Flow

```text
User
  |
CloudFront
  |
Primary Origin
```

---

# Failure Flow

```text
User
  |
CloudFront
  |
Secondary Origin
```

CloudFront automatically switches.

---

# Real Example

Primary:

```text
S3 Bucket A
```

Backup:

```text
S3 Bucket B
```

If Bucket A fails:

```text
CloudFront uses Bucket B.
```

---

# Benefits of Origin Failover

### High Availability

Application remains online.

---

### Disaster Recovery

Supports business continuity.

---

### Reduced Downtime

Automatic switching.

---

# Origin Shield

## What Is Origin Shield?

An additional caching layer.

Architecture:

```text
Edge Location
      |
Origin Shield
      |
Origin
```

---

# Benefits

### Fewer Origin Requests

Reduces backend load.

---

### Better Cache Efficiency

Higher cache hit ratio.

---

### Improved Performance

Useful for large-scale workloads.

---

# Common Origin Issues

## 403 Forbidden

Possible Causes:

- Incorrect OAC configuration
- Bucket policy issue
- WAF block

---

## 404 Not Found

Possible Causes:

- Object missing
- Wrong path pattern
- Incorrect origin configuration

---

## 502 Bad Gateway

Possible Causes:

- Origin unavailable
- DNS issues
- SSL mismatch

---

## 504 Gateway Timeout

Possible Causes:

- Slow origin response
- Network issue
- Overloaded backend

---

# Troubleshooting Workflow

When origin issues occur:

### Step 1

Check CloudFront Metrics.

---

### Step 2

Review Access Logs.

---

### Step 3

Validate Origin Health.

---

### Step 4

Check Origin Security Settings.

---

### Step 5

Test Origin Directly.

---

# Architecture Best Practices

## For S3

Use:

```text
OAC
```

Never expose buckets publicly.

---

## For Custom Origins

Enable:

```text
HTTPS
```

between CloudFront and origin.

---

## For High Availability

Use:

```text
Origin Groups
```

---

## For Scale

Use:

```text
Origin Shield
```

when appropriate.

---

# Real-World Architectures

## Static Website

```text
Users
   |
CloudFront
   |
S3
```

---

## Enterprise Application

```text
Users
   |
CloudFront
   |
ALB
   |
ECS
```

---

## Private Application

```text
Users
   |
CloudFront
   |
Internal ALB
   |
Private Services
```

---

## Global Video Platform

```text
Users
   |
CloudFront
   |
S3
```

Security:

- OAC
- Signed URLs
- Signed Cookies

---

# Interview Questions

## Q1. What is an Origin?

The backend source from which CloudFront retrieves content.

---

## Q2. What origin types does CloudFront support?

- S3 Origin
- Custom Origin
- VPC Origin

---

## Q3. What is OAC?

Origin Access Control allows CloudFront to securely access S3 while blocking direct user access.

---

## Q4. Why is OAC preferred over OAI?

OAC supports modern security mechanisms such as SigV4 and is AWS's recommended approach.

---

## Q5. What is an Origin Group?

A configuration that provides automatic failover between primary and secondary origins.

---

## Q6. When would you use a Custom Origin?

When content is hosted on:

- EC2
- NGINX
- Apache
- On-Prem Servers

---

## Q7. What is Origin Shield?

An additional cache layer that reduces origin load and improves cache efficiency.

---

# Summary

Key Takeaways:

- Origins are the source of truth for CloudFront content.
- S3 is ideal for static content.
- Custom Origins support dynamic applications.
- VPC Origins enable secure private workloads.
- OAC secures S3 access.
- Origin Groups provide failover.
- Origin Shield improves cache efficiency.
- Proper origin design directly impacts performance, security, and availability.
