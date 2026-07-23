# 30- Lambda@Edge and CloudFront Functions

# Introduction

Amazon CloudFront allows developers to execute code at AWS Edge Locations, bringing computation closer to users worldwide. AWS offers two technologies for this purpose:

- **CloudFront Functions**
- **Lambda@Edge**

Both execute code at the edge, but they are designed for very different workloads.

Understanding when to use each service is essential for building low-latency, globally distributed applications while controlling cost and complexity.

---

# Why Run Code at the Edge?

Normally, a request travels to the origin before any processing occurs.

```
User

↓

CloudFront

↓

Origin (Lambda/API Gateway/EC2)

↓

Response
```

This increases latency.

With edge computing:

```
User

↓

Edge Location

↓

Execute Logic

↓

Return Response
```

Requests can often be processed without contacting the origin.

---

# What is Lambda@Edge?

Lambda@Edge extends AWS Lambda by allowing functions to execute at **CloudFront Edge Locations** around the world.

Typical use cases:

- Authentication
- URL rewriting
- Dynamic content generation
- Image optimization
- Security headers
- Origin selection

---

# What are CloudFront Functions?

CloudFront Functions are lightweight JavaScript functions designed for **ultra-fast request and response manipulation**.

They execute in microseconds and are significantly cheaper than Lambda@Edge.

Typical use cases:

- URL redirects
- Header manipulation
- Geo-based routing
- Bot filtering
- Cache key normalization

---

# High-Level Architecture

```
                User

                  │

                  ▼

          CloudFront Edge

          ┌───────────────┐
          │               │
          │ CloudFront    │
          │ Function      │
          │               │
          └───────────────┘
                  │
        If More Logic Needed
                  │
                  ▼
          Lambda@Edge
                  │
                  ▼
             Origin Server
```

---

# CloudFront Request Lifecycle

```
Viewer Request

↓

CloudFront Function

↓

Lambda@Edge (Optional)

↓

Origin Request

↓

Origin

↓

Origin Response

↓

Lambda@Edge

↓

Viewer Response

↓

CloudFront Function
```

CloudFront Functions participate only in **viewer events**, while Lambda@Edge can execute at multiple stages.

---

# Lambda@Edge Trigger Points

Lambda@Edge supports four event types.

```
Viewer Request

↓

Origin Request

↓

Origin Response

↓

Viewer Response
```

This makes Lambda@Edge much more flexible.

---

# CloudFront Functions Trigger Points

CloudFront Functions support only:

```
Viewer Request

↓

Viewer Response
```

No access to origin events.

---

# Feature Comparison

| Feature | CloudFront Functions | Lambda@Edge |
|----------|----------------------|-------------|
| Runtime | JavaScript | Node.js / Python |
| Max Execution Time | < 1 ms | Up to several seconds |
| Memory | 2 MB | Up to Lambda limits |
| Package Size | Very Small | Up to Lambda package limits |
| Network Access | ❌ | ✅ |
| AWS SDK | ❌ | ✅ |
| Third-Party APIs | ❌ | ✅ |
| Request Body Access | ❌ | ✅ (Origin events) |
| Pricing | Lower | Higher |

---

# Execution Location

Both execute globally.

```
Users

↓

Nearest Edge Location

↓

Execute Function

↓

Response
```

This minimizes latency for worldwide users.

---

# When to Use CloudFront Functions

Ideal for lightweight operations.

Examples:

- Add security headers
- Redirect HTTP to HTTPS
- Normalize URLs
- Add/remove headers
- Basic authentication checks
- Block requests by country
- Rewrite cache keys

Example:

```
Incoming Request

↓

Convert URL to Lowercase

↓

Continue
```

---

# When to Use Lambda@Edge

Use Lambda@Edge when logic requires:

- External API calls
- Reading request bodies
- Dynamic HTML generation
- Authentication with external systems
- Image processing
- Origin selection
- Personalized responses

---

# Example: Redirect Users

Using CloudFront Functions:

```
User

↓

http://example.com

↓

301 Redirect

↓

https://example.com
```

Simple and extremely fast.

---

# Example: Country-Based Routing

```
User

↓

Country Header

↓

US?

↓

Yes

↓

US Origin

------------

No

↓

Global Origin
```

Can be implemented using either service depending on complexity.

---

# Example: Authentication

```
User

↓

JWT Token

↓

Lambda@Edge

↓

Validate

↓

Origin
```

Lambda@Edge is appropriate because it can perform complex validation and call external identity providers.

---

# Example: Image Optimization

```
Image Request

↓

Lambda@Edge

↓

Resize

↓

Return Optimized Image
```

CloudFront Functions cannot perform this workload.

---

# Security Headers

CloudFront Functions can efficiently add headers such as:

```
Strict-Transport-Security

Content-Security-Policy

X-Frame-Options

X-Content-Type-Options
```

Since no origin call is required, latency is minimal.

---

# URL Rewriting

```
Incoming

/products

↓

Rewrite

/index.html

↓

Origin
```

Useful for Single Page Applications (SPAs).

---

# Cache Key Normalization

```
URL

?page=1&utm_source=abc

↓

Remove Tracking Parameters

↓

Cache Lookup
```

Improves cache hit ratio.

---

# Performance Considerations

CloudFront Functions:

```
Execution

↓

Microseconds

↓

Minimal Latency
```

Lambda@Edge:

```
Initialization

↓

Execution

↓

Greater Flexibility

↓

Higher Latency
```

Choose the simplest solution that satisfies the requirement.

---

# Cost Considerations

CloudFront Functions are significantly cheaper because they:

- Execute faster
- Consume fewer resources
- Support only lightweight logic

Lambda@Edge incurs higher charges due to:

- Longer execution
- Greater resource allocation
- More capabilities

---

# Deployment

CloudFront Functions:

```
Write Code

↓

Publish

↓

Associate

↓

Deploy
```

Lambda@Edge:

```
Publish Lambda Version

↓

Associate with CloudFront

↓

Replicate Globally

↓

Deploy
```

Lambda@Edge requires **published versions**; `$LATEST` cannot be used.

---

# Monitoring

Both integrate with:

- CloudWatch Logs
- CloudWatch Metrics

Lambda@Edge also supports AWS X-Ray in supported scenarios through Lambda tracing capabilities.

---

# Common Mistakes

## Using Lambda@Edge for Simple Header Changes

Bad:

```
Lambda@Edge

↓

Add Header
```

Better:

```
CloudFront Function

↓

Add Header
```

---

## Calling External APIs from CloudFront Functions

Not supported.

Use Lambda@Edge instead.

---

## Large Business Logic at the Edge

Keep edge functions lightweight.

Complex workflows should execute in:

- Regional Lambda
- ECS
- API Gateway backends

---

# Best Practices

✅ Use CloudFront Functions for lightweight request/response manipulation.

✅ Use Lambda@Edge only when advanced processing is required.

✅ Keep edge execution time as short as possible.

✅ Minimize dependencies.

✅ Publish immutable Lambda versions.

✅ Monitor latency and error rates.

✅ Avoid unnecessary origin requests.

---

# Real-World Architecture

```
                 Users

                   │

           CloudFront CDN

                   │

      ┌────────────┴────────────┐

      │                         │

CloudFront Function       Lambda@Edge

(Header Rewrite)     (Authentication)

      │                         │

      └────────────┬────────────┘

                   │

              API Gateway

                   │

                Lambda

                   │

                 Aurora
```

CloudFront Functions handle simple request transformations, while Lambda@Edge performs advanced processing before forwarding traffic to the origin.

---

# Choosing Between CloudFront Functions and Lambda@Edge

| Requirement | Recommended Service |
|-------------|---------------------|
| URL Rewrite | CloudFront Functions |
| Redirects | CloudFront Functions |
| Security Headers | CloudFront Functions |
| Cache Key Normalization | CloudFront Functions |
| Authentication with External APIs | Lambda@Edge |
| Read Request Body | Lambda@Edge |
| Dynamic Content Generation | Lambda@Edge |
| Image Processing | Lambda@Edge |
| Origin Selection | Lambda@Edge |

---

# Senior Backend Engineering Perspective

CloudFront Functions and Lambda@Edge complement one another rather than compete.

Senior engineers start with **CloudFront Functions** because they offer the lowest latency and lowest cost for lightweight request manipulation. They move to **Lambda@Edge** only when application requirements demand capabilities such as network access, request body inspection, advanced authentication, or dynamic content generation.

The guiding principle is:

> **Execute the smallest amount of logic as close to the user as possible.**

This approach reduces latency, improves cache efficiency, minimizes origin load, and keeps operational costs under control.

---

# Key Takeaways

- CloudFront Functions are designed for ultra-fast, lightweight request and response manipulation at CloudFront Edge Locations.
- Lambda@Edge supports more complex workloads, including network access, request body inspection, origin selection, and dynamic content generation.
- CloudFront Functions support only viewer events, while Lambda@Edge supports viewer and origin request/response events.
- Choose CloudFront Functions whenever lightweight logic is sufficient; use Lambda@Edge for advanced processing.
- Selecting the appropriate edge compute service improves performance, reduces cost, and enhances the scalability of globally distributed applications.