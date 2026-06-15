# AWS CloudFront - Section 01: Introduction

# What is Amazon CloudFront?

Amazon CloudFront is AWS's fully managed **Content Delivery Network (CDN)** service that securely delivers content to users through a global network of Edge Locations.

CloudFront caches content closer to users and serves requests from the nearest Edge Location whenever possible.

This significantly reduces latency and improves application performance.

CloudFront can deliver:

- Static content
- Dynamic content
- APIs
- Video streams
- Software downloads
- Web applications

---

# Why Do We Need a CDN?

Before understanding CloudFront, it is important to understand the problem it solves.

Imagine a web application hosted in:

```text
us-east-1 (Virginia)
```

A user accesses the application from:

```text
Mumbai, India
```

Without a CDN:

```text
User (Mumbai)
      |
      |
      |
      |
      v
Origin Server (Virginia)
```

Every request must travel thousands of kilometers to reach the origin server.

Problems:

- High latency
- Slow page loads
- Increased origin traffic
- Higher bandwidth consumption
- Poor user experience

---

## Real-World Example

Suppose your company hosts:

```text
logo.png
```

inside an S3 bucket in:

```text
us-east-1
```

If 1 million users request that image:

```text
1,000,000 Requests
          |
          v
       S3 Bucket
```

The origin must process every request.

This creates:

- Increased costs
- Increased load
- Reduced scalability

---

# What is a CDN?

A CDN (Content Delivery Network) is a globally distributed network of servers that caches content closer to users.

Instead of retrieving content from the origin every time:

```text
User
  |
  v
Origin
```

Content is stored at edge locations:

```text
User
  |
  v
Edge Location
  |
  v
Origin (Only if Needed)
```

Benefits:

- Faster delivery
- Lower latency
- Reduced origin load
- Better scalability

---

# How CloudFront Solves the Problem

CloudFront places copies of content in AWS Edge Locations around the world.

When a user requests content:

```text
User
  |
  v
Nearest Edge Location
```

CloudFront checks:

```text
Is object already cached?
```

### If Yes

```text
Cache Hit
```

Content is immediately served.

### If No

```text
Cache Miss
```

CloudFront retrieves the object from the origin and stores it in cache.

---

# CloudFront Global Infrastructure

CloudFront operates using three major components:

```text
Users
  |
Edge Locations
  |
Regional Edge Cache
  |
Origin
```

---

## Edge Locations

Edge Locations are physical AWS locations where CloudFront caches content.

Examples:

```text
Mumbai
Singapore
London
Sydney
Tokyo
Frankfurt
New York
```

Purpose:

- Deliver content closer to users.
- Reduce latency.
- Improve response times.

---

## Regional Edge Cache

Regional Edge Caches sit between Edge Locations and Origins.

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

Benefits:

- Higher cache efficiency
- Reduced origin requests
- Improved scalability

---

## Origin

The Origin is the backend source of content.

Examples:

```text
Amazon S3
Application Load Balancer
EC2
API Gateway
On-Premises Server
```

CloudFront does not create content.

It only caches and distributes content from origins.

---

# Core CloudFront Components

## Distribution

A Distribution is the CloudFront configuration object.

Think of it as the CloudFront application itself.

A Distribution defines:

- Origins
- Cache behavior
- Security settings
- SSL/TLS configuration
- Logging settings

Every CloudFront deployment begins with creating a Distribution.

---

## Origin

Source of content.

Examples:

```text
S3 Bucket
ALB
EC2
API Gateway
```

---

## Cache Behavior

Cache Behaviors determine:

- Which requests match a path pattern.
- Which origin receives the request.
- How caching works.
- Security settings.

Example:

```text
/images/*
```

```text
/api/*
```

Different behaviors can use different origins.

---

## Cache

A cache is a temporary copy of content stored in Edge Locations.

Examples:

```text
logo.png
style.css
app.js
video.mp4
```

---

## TTL (Time To Live)

TTL defines how long CloudFront stores an object in cache.

Example:

```text
TTL = 3600 seconds
```

CloudFront keeps the object cached for:

```text
1 hour
```

before checking the origin again.

---

# CloudFront Use Cases

## Static Website Hosting

Architecture:

```text
Users
  |
CloudFront
  |
S3 Bucket
```

Used for:

- HTML
- CSS
- JavaScript
- Images

---

## Dynamic Applications

Architecture:

```text
Users
  |
CloudFront
  |
ALB
  |
EC2/ECS/EKS
```

Benefits:

- Lower latency
- Additional security layer

---

## API Acceleration

Architecture:

```text
Users
  |
CloudFront
  |
API Gateway
```

Benefits:

- Faster API responses
- Global delivery

---

## Video Streaming

Used by:

- OTT Platforms
- E-Learning Platforms
- Corporate Training Portals

Examples:

```text
Recorded videos
Live streams
Premium content
```

---

## Software Distribution

Used for:

- Mobile apps
- Desktop software
- Game patches
- Firmware updates

---

# Benefits of CloudFront

## Performance

Content is delivered from locations close to users.

Result:

- Lower latency
- Faster page loads

---

## Scalability

CloudFront absorbs massive traffic spikes.

Example:

```text
Black Friday Sale
Product Launch
Marketing Campaign
```

---

## Availability

AWS global infrastructure improves reliability.

Even if one Edge Location has issues:

```text
Traffic can be redirected.
```

---

## Security

CloudFront integrates with:

### AWS Shield

Protects against:

```text
DDoS Attacks
```

---

### AWS WAF

Protects against:

```text
SQL Injection
Cross Site Scripting (XSS)
Bot Traffic
```

---

### HTTPS

Supports:

```text
TLS Encryption
Custom Certificates
```

---

# CloudFront vs Direct S3 Access

## Direct S3

```text
User
  |
S3 Bucket
```

Problems:

- Higher latency
- No edge caching
- No WAF protection
- No DDoS mitigation layer

---

## CloudFront + S3

```text
User
  |
CloudFront
  |
S3
```

Benefits:

- Faster delivery
- Security controls
- Better scalability
- Lower S3 request load

---

# Common Misconceptions

## CloudFront Only Works With S3

Incorrect.

CloudFront can work with:

- S3
- ALB
- EC2
- API Gateway
- On-Prem Servers

---

## CloudFront Only Caches Static Content

Incorrect.

CloudFront also supports:

- Dynamic content
- APIs
- Streaming content

---

## CloudFront Replaces Load Balancers

Incorrect.

CloudFront and Load Balancers solve different problems.

CloudFront:

```text
Global content delivery
```

ALB:

```text
Traffic distribution
```

---

# Real-World Example

Consider Netflix.

Simplified architecture:

```text
Users
   |
CloudFront
   |
S3
```

Millions of users request the same video segments.

Instead of every request reaching S3:

```text
CloudFront caches video segments globally.
```

Benefits:

- Lower cost
- Better performance
- Massive scalability

---

# Interview Questions

## Q1. What is Amazon CloudFront?

CloudFront is AWS's Content Delivery Network (CDN) service that delivers content through globally distributed Edge Locations.

---

## Q2. Why use CloudFront?

To:

- Reduce latency
- Improve performance
- Reduce origin load
- Improve security
- Increase availability

---

## Q3. What is an Edge Location?

An AWS location where CloudFront caches content closer to users.

---

## Q4. What is a Distribution?

A CloudFront configuration that defines origins, cache behavior, and security settings.

---

## Q5. Can CloudFront work without S3?

Yes.

CloudFront supports:

- ALB
- EC2
- API Gateway
- On-Prem Servers
- S3

---

## Q6. What is a CDN?

A globally distributed network that caches content closer to users to reduce latency and improve performance.

---

# Summary

CloudFront is AWS's global CDN service.

Key takeaways:

- Uses Edge Locations to cache content.
- Reduces latency.
- Improves scalability.
- Integrates with AWS security services.
- Supports S3, ALB, EC2, API Gateway, and custom origins.
- Commonly used for websites, APIs, streaming, and software distribution.
