# AWS CloudFront - Section 02: Architecture


# CloudFront Architecture Overview

CloudFront is built on a globally distributed infrastructure designed to deliver content with low latency and high availability.

High-Level Architecture:

```text
                User
                  |
                  v
         Edge Location
                  |
                  v
      Regional Edge Cache
                  |
                  v
               Origin
```

Each layer has a specific responsibility.

---

# Architecture Components

CloudFront architecture consists of:

```text
Users
Edge Locations
Regional Edge Caches
Origins
Distributions
Cache Behaviors
Origin Groups
```

Let's understand each component.

---

# Users

Users are the clients requesting content.

Examples:

```text
Web Browsers
Mobile Applications
APIs
Smart TVs
IoT Devices
```

When users access a CloudFront distribution:

```text
https://d123abc.cloudfront.net
```

DNS automatically routes them to the nearest Edge Location.

---

# Edge Locations

## What is an Edge Location?

An Edge Location is a physical AWS location that stores cached copies of content.

Think of it as:

```text
Mini Cache Server
Closer to Users
```

CloudFront uses Edge Locations to reduce the distance between users and content.

---

## Why Edge Locations Exist

Without Edge Locations:

```text
User (India)
      |
      |
      |
      v
Origin (Virginia)
```

Every request must travel to the origin.

This creates:

- High latency
- Slow downloads
- Increased origin load

---

With Edge Locations:

```text
User (India)
      |
      v
Mumbai Edge Location
      |
      v
Origin (Only if Needed)
```

Most requests are served locally.

---

## Responsibilities of Edge Locations

Edge Locations:

- Store cached content
- Serve user requests
- Perform SSL/TLS termination
- Execute CloudFront Functions
- Execute Lambda@Edge
- Enforce WAF rules
- Apply Geo Restrictions

---

## Example

A user requests:

```text
/logo.png
```

CloudFront checks:

```text
Mumbai Edge Location
```

If found:

```text
Cache Hit
```

Response is immediate.

---

# Regional Edge Cache

## What is a Regional Edge Cache?

A Regional Edge Cache is a larger cache layer between Edge Locations and Origins.

Architecture:

```text
User
  |
Edge Location
  |
Regional Edge Cache
  |
Origin
```

---

## Why AWS Introduced Regional Edge Cache

Imagine:

```text
100 Edge Locations
```

Without Regional Edge Cache:

```text
100 Edge Locations
      |
      v
Origin
```

Origin receives many requests.

With Regional Edge Cache:

```text
100 Edge Locations
      |
Regional Edge Cache
      |
Origin
```

The origin receives significantly fewer requests.

---

## Benefits

### Better Cache Efficiency

Objects stay cached longer.

### Reduced Origin Traffic

Fewer requests reach the origin.

### Improved Scalability

Better support for global traffic.

---

# Origin

## What is an Origin?

An Origin is the backend source where content is stored.

CloudFront retrieves content from origins whenever required.

Examples:

```text
S3
ALB
EC2
API Gateway
On-Prem Server
```

CloudFront does NOT create content.

It only caches and distributes content.

---

# Request Lifecycle

Let's understand how CloudFront processes requests.

---

# Cache Hit Flow

## What is a Cache Hit?

A Cache Hit occurs when the requested object already exists in the Edge Location.

---

### Flow

```text
User
  |
Edge Location
  |
Object Found
  |
Response
```

---

### Detailed Process

Step 1:

User requests:

```text
/logo.png
```

Step 2:

CloudFront checks cache.

Step 3:

Object found.

Step 4:

Response returned immediately.

---

### Benefits

- Fast response
- Lower latency
- Reduced origin traffic
- Lower costs

---

# Cache Miss Flow

## What is a Cache Miss?

A Cache Miss occurs when the requested object is not available in cache.

---

### Flow

```text
User
  |
Edge Location
  |
Object Not Found
  |
Regional Edge Cache
  |
Origin
```

---

### Detailed Process

Step 1:

User requests:

```text
/logo.png
```

Step 2:

Edge Location checks cache.

Object missing.

Step 3:

Regional Edge Cache checked.

Object missing.

Step 4:

Request sent to origin.

Step 5:

Origin returns object.

Step 6:

CloudFront caches object.

Step 7:

Response returned.

---

# CloudFront Distribution

## What is a Distribution?

A Distribution is the main CloudFront configuration object.

Think of it as:

```text
CloudFront Application
```

---

## Distribution Contains

```text
Origins
Cache Behaviors
Security Settings
Certificates
Logging
Policies
```

---

## Example

```text
Distribution
    |
    +-- S3 Origin
    |
    +-- ALB Origin
```

One distribution can contain multiple origins.

---

# Multi-Origin Architecture

CloudFront supports multiple origins.

Example:

```text
/images/*  --> S3
/api/*     --> ALB
/videos/*  --> S3
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

## Benefits

- Better separation of workloads
- Improved scalability
- Flexible routing

---

# Cache Behaviors

Cache Behaviors determine:

```text
Which requests match
Which origin is used
How caching works
```

---

## Example

```text
/images/*
```

Route to:

```text
S3
```

---

```text
/api/*
```

Route to:

```text
ALB
```

---

## Why Important?

Different workloads require different settings.

Example:

Images:

```text
TTL = 24 Hours
```

API:

```text
TTL = 0
```

---

# Origin Groups

## What are Origin Groups?

Origin Groups provide automatic failover.

Architecture:

```text
Primary Origin
      |
      v
Secondary Origin
```

---

## Example

Primary:

```text
ALB A
```

Backup:

```text
ALB B
```

If ALB A fails:

```text
CloudFront switches automatically.
```

---

# Origin Failover Flow

Normal:

```text
User
  |
CloudFront
  |
Primary Origin
```

Failure:

```text
User
  |
CloudFront
  |
Backup Origin
```

---

## Benefits

- High availability
- Disaster recovery
- Business continuity

---

# CloudFront and DNS

CloudFront distributions receive DNS names.

Example:

```text
d123456abcdef.cloudfront.net
```

Organizations often use:

```text
cdn.company.com
```

using Route 53.

---

# CloudFront and TLS

CloudFront can terminate HTTPS connections.

Process:

```text
User
  |
HTTPS
  |
CloudFront
  |
HTTP or HTTPS
  |
Origin
```

Benefits:

- Encryption
- Improved security
- Certificate management

---

# Real-World Architecture Examples

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

## API Platform

```text
Users
   |
CloudFront
   |
API Gateway
```

---

## Streaming Platform

```text
Users
   |
CloudFront
   |
S3
```

---

# Common Architecture Mistakes

## Public S3 Buckets

Bad:

```text
Users
  |
S3
```

Better:

```text
Users
  |
CloudFront
  |
S3
```

with OAC.

---

## Low TTL Values

Results:

- More cache misses
- More origin traffic

---

## Single Origin Design

Creates:

```text
Single Point of Failure
```

Use:

```text
Origin Groups
```

---

# Architecture Best Practices

1. Use OAC for S3.
2. Use Origin Groups for HA.
3. Optimize TTL values.
4. Use multiple origins when required.
5. Keep cache hit ratio high.
6. Use HTTPS everywhere.
7. Enable WAF.

---

# Interview Questions

## Q1. What happens during a Cache Miss?

CloudFront checks the Edge Location, then Regional Edge Cache, then retrieves content from the origin and caches it.

---

## Q2. What is the purpose of Regional Edge Cache?

To reduce origin traffic and improve cache efficiency.

---

## Q3. What is an Origin?

The backend source from which CloudFront retrieves content.

---

## Q4. Can a Distribution have multiple origins?

Yes.

Example:

```text
/images/* -> S3
/api/* -> ALB
```

---

## Q5. What is Origin Failover?

The ability to automatically switch to a secondary origin when the primary origin becomes unavailable.

---

## Q6. What is the difference between an Edge Location and an Origin?

| Edge Location | Origin |
|--------------|---------|
| Stores cached content | Stores original content |
| Closer to users | Backend source |
| Improves performance | Source of truth |

---

# Summary

CloudFront architecture consists of:

```text
Users
Edge Locations
Regional Edge Cache
Origins
Distributions
Origin Groups
```

Key Takeaways:

- Edge Locations reduce latency.
- Regional Edge Caches reduce origin traffic.
- Distributions control CloudFront behavior.
- Origins store original content.
- Origin Groups provide failover.
- Multi-origin architectures improve flexibility and scalability.

