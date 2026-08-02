# Endpoint Types

## Overview

When creating an API in Amazon API Gateway, one of the first decisions you must make is **how clients will access your API**.

API Gateway offers three endpoint types:

- Edge-Optimized Endpoint
- Regional Endpoint
- Private Endpoint

Each endpoint type is designed for different networking requirements, latency expectations, and security needs.

Choosing the correct endpoint type is important for both performance and architecture.

---

# Endpoint Types at a Glance

| Endpoint Type | Accessible From | Uses CloudFront | Typical Use Case |
|---------------|-----------------|-----------------|------------------|
| Edge-Optimized | Internet | ✅ Managed by AWS | Global public APIs |
| Regional | Internet | ❌ (Optional) | Regional applications |
| Private | Inside VPC | ❌ | Internal enterprise APIs |

---

# 1. Edge-Optimized Endpoint

## Overview

An **Edge-Optimized API** is designed for applications whose users are distributed across the world.

When you create an Edge-Optimized endpoint, AWS automatically provisions a **CloudFront distribution** in front of your API.

Clients connect to the nearest CloudFront Edge Location, reducing network latency.

---

## Architecture

```text
                Global Users
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
   London        Singapore      New York
        │             │             │
        └─────────────┼─────────────┘
                      ▼
        CloudFront Edge Location
                      │
                      ▼
             Amazon API Gateway
                      │
                      ▼
               Backend Services
```

---

## How It Works

Instead of every request traveling directly to the AWS Region, users connect to the nearest CloudFront Edge Location.

CloudFront forwards the request over the AWS global network to API Gateway.

Benefits include:

- Lower latency
- Better global performance
- Improved user experience
- No CloudFront configuration required

---

## Advantages

- Best performance for global users
- CloudFront is managed automatically
- Built-in DDoS protection via AWS Shield Standard
- Optimized routing over the AWS global network

---

## Disadvantages

- Slightly more expensive than Regional endpoints
- Less control over CloudFront configuration
- Not suitable for private APIs

---

## Best Use Cases

- Public REST APIs
- SaaS platforms
- Mobile applications
- Worldwide customer-facing APIs
- Public developer APIs

---

# 2. Regional Endpoint

## Overview

A **Regional Endpoint** exposes your API directly within a specific AWS Region.

Unlike Edge-Optimized endpoints, no CloudFront distribution is created automatically.

Clients connect directly to API Gateway in the selected Region.

---

## Architecture

```text
          Users
             │
             ▼
      API Gateway (Mumbai)
             │
             ▼
      Lambda / ECS / EC2
```

---

## How It Works

Requests travel directly to the API Gateway endpoint in the configured AWS Region.

If global acceleration is required, you can place your own CloudFront distribution in front of the Regional API.

```text
Users
   │
   ▼
CloudFront (Optional)
   │
   ▼
Regional API Gateway
   │
   ▼
Backend
```

This approach provides greater flexibility than an Edge-Optimized endpoint.

---

## Advantages

- Lower cost than Edge-Optimized
- Greater control over CloudFront configuration
- Better suited for region-specific workloads
- Easier integration with regional AWS services

---

## Disadvantages

- Higher latency for users far from the Region
- No automatic global edge caching

---

## Best Use Cases

- Internal company applications
- Country-specific applications
- APIs consumed from one geographic region
- Applications already using a custom CloudFront distribution

---

# 3. Private Endpoint

## Overview

A **Private API** is accessible **only from within an Amazon VPC**.

It is not exposed to the public Internet.

Private APIs use **AWS PrivateLink (Interface VPC Endpoints)** to provide secure connectivity.

---

## Architecture

```text
            EC2 Instance
                 │
                 ▼
       Interface VPC Endpoint
                 │
                 ▼
      Private API Gateway
                 │
                 ▼
         Internal Services
```

The API cannot be accessed directly from the Internet.

---

## How It Works

Instead of using public internet connectivity, requests remain entirely within the AWS network.

This improves both security and compliance.

---

## Advantages

- No public exposure
- Highly secure
- Traffic remains within AWS
- Suitable for regulated environments
- Supports VPC endpoint policies

---

## Disadvantages

- Cannot be accessed directly from the Internet
- Requires Interface VPC Endpoints
- Slightly more complex networking configuration

---

## Best Use Cases

- Banking applications
- Healthcare systems
- Internal enterprise APIs
- Backend microservices
- Government workloads
- Corporate internal platforms

---

# Comparison

| Feature | Edge-Optimized | Regional | Private |
|---------|----------------|----------|----------|
| Public Internet | ✅ | ✅ | ❌ |
| CloudFront Managed by AWS | ✅ | ❌ | ❌ |
| Global Performance | Excellent | Moderate | Not Applicable |
| VPC Only | ❌ | ❌ | ✅ |
| Custom CloudFront | Limited | ✅ | ❌ |
| Best for Global Users | ✅ | ❌ | ❌ |
| Lowest Cost | ❌ | ✅ | Depends on VPC Endpoint usage |

---

# Which Endpoint Should You Choose?

### Choose Edge-Optimized when:

- Users are spread across multiple continents.
- You need the lowest possible latency worldwide.
- You want AWS to manage CloudFront automatically.

---

### Choose Regional when:

- Most users are in one AWS Region.
- You already use CloudFront.
- You need more control over caching and routing.

---

### Choose Private when:

- The API should never be exposed to the Internet.
- Only AWS resources inside a VPC should access the API.
- Security and compliance are top priorities.

---

# Real-World Examples

## Example 1: Global E-Commerce Website

Customers access the API from North America, Europe, Asia, and Australia.

**Recommended Endpoint:** Edge-Optimized

Reason:
CloudFront routes users to the nearest Edge Location, reducing latency worldwide.

---

## Example 2: Internal HR Portal

Only employees connected through the company's AWS network can access the API.

**Recommended Endpoint:** Private

Reason:
The API remains inaccessible from the public Internet.

---

## Example 3: India-Only Food Delivery Application

Most users are located in India, and the backend is deployed in the Mumbai Region.

**Recommended Endpoint:** Regional

Reason:
A Regional endpoint provides low latency without the additional cost of an Edge-Optimized endpoint.

---

# Interview Questions

### What is the difference between Edge-Optimized and Regional APIs?

**Answer:**

An Edge-Optimized API automatically uses an AWS-managed CloudFront distribution to improve latency for global users. A Regional API exposes the API directly in an AWS Region and can optionally be placed behind a custom CloudFront distribution.

---

### Can a Private API be accessed from the Internet?

**Answer:**

No. Private APIs are accessible only through Interface VPC Endpoints (AWS PrivateLink) from within a VPC.

---

### Which endpoint type should you use for a banking application?

**Answer:**

Private Endpoint, because it prevents public Internet access and keeps all traffic within the AWS network.

---

# Best Practices

- Use **Edge-Optimized** for globally distributed public APIs.
- Use **Regional** for region-specific applications or when you need custom CloudFront behavior.
- Use **Private** for internal services that should never be publicly accessible.
- Choose the endpoint type based on latency, security, compliance, and networking requirements rather than defaulting to one option.

---

# Key Takeaways

- API Gateway supports **Edge-Optimized**, **Regional**, and **Private** endpoints.
- Edge-Optimized endpoints use an AWS-managed CloudFront distribution for low-latency global access.
- Regional endpoints are ideal for applications serving users in a single AWS Region and allow optional custom CloudFront integration.
- Private endpoints use AWS PrivateLink and are accessible only from within a VPC.
- Selecting the appropriate endpoint type improves application performance, security, and cost efficiency.