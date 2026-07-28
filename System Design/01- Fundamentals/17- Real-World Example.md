# Real-World Example

## Overview

Understanding individual System Design concepts is important, but applying them together is what makes someone a good software architect.

In this chapter, we'll walk through the design of a simple **URL Shortener**—one of the most common system design examples used in interviews. The goal is not to build the most scalable solution possible, but to demonstrate how the design framework introduced in the previous chapter can be applied to solve a real-world problem.

The same thought process can later be used for designing systems such as chat applications, ride-sharing platforms, social networks, video streaming services, and e-commerce platforms.

---

# Problem Statement

Design a URL shortening service similar to:

- bit.ly
- tinyurl.com

The system should:

- Accept a long URL.
- Generate a unique short URL.
- Redirect users to the original URL.
- Handle millions of requests reliably.

---

# Step 1: Understand the Requirements

Before designing anything, clarify the requirements.

## Functional Requirements

The system should allow users to:

- Create short URLs.
- Redirect short URLs to the original URL.
- Optionally set an expiration date.
- View basic click statistics (optional).

---

## Non-Functional Requirements

The system should provide:

- High availability
- Low latency
- High read throughput
- Scalability
- Reliability
- Unique short URLs

---

# Step 2: Estimate the Scale

Assume the following:

| Metric | Value |
|--------|-------|
| Daily Active Users | 10 Million |
| URLs Created Per Day | 5 Million |
| Redirect Requests Per Day | 500 Million |
| Average URL Size | 300 Bytes |

Observations:

- Reads greatly outnumber writes.
- Most traffic consists of redirects.
- Popular URLs will receive repeated requests.

These estimates influence our architectural decisions.

---

# Step 3: Identify Core Components

The system requires the following major components:

```
Users

↓

Load Balancer

↓

Application Servers

↓

Cache

↓

Database
```

Each component has a specific responsibility.

---

# Step 4: High-Level Architecture

```
                  Users
                     │
                     ▼
             Load Balancer
                     │
      ┌──────────────┴──────────────┐
      ▼                             ▼
 Application Server 1       Application Server 2
      │                             │
      └──────────────┬──────────────┘
                     ▼
                  Redis Cache
                     │
                     ▼
                 SQL Database
```

### Component Responsibilities

| Component | Responsibility |
|-----------|----------------|
| Load Balancer | Distributes incoming traffic |
| Application Server | Handles business logic |
| Redis | Stores frequently accessed URLs |
| Database | Stores permanent URL mappings |

---

# Step 5: Database Design

A simple relational schema:

| Column | Description |
|---------|-------------|
| id | Primary key |
| short_code | Unique shortened identifier |
| original_url | Original long URL |
| created_at | Creation timestamp |
| expires_at | Optional expiration time |
| click_count | Number of redirects |

Example:

| short_code | original_url |
|------------|--------------|
| abc123 | https://example.com/articles/system-design |
| xyz789 | https://openai.com |

---

# Step 6: API Design

## Create Short URL

```
POST /api/v1/shorten
```

Request

```json
{
  "url": "https://example.com/article"
}
```

Response

```json
{
  "short_url": "https://short.ly/AbC123"
}
```

---

## Redirect

```
GET /AbC123
```

The server returns:

```
HTTP 302 Redirect
```

to the original URL.

---

# Step 7: Request Flow

## Creating a Short URL

```
Client

↓

Load Balancer

↓

Application Server

↓

Generate Short Code

↓

Store in Database

↓

Return Short URL
```

---

## Redirecting a URL

```
Client

↓

Load Balancer

↓

Application Server

↓

Redis Cache

↓

Database (if cache miss)

↓

HTTP Redirect
```

---

# Step 8: Why Use a Cache?

Redirect requests happen much more frequently than URL creation requests.

Without caching:

```
Every Redirect

↓

Database
```

With caching:

```
Most Redirects

↓

Redis

↓

Database (Cache Miss Only)
```

Benefits:

- Lower latency
- Reduced database load
- Higher throughput

---

# Step 9: Scaling the System

As traffic grows:

```
Load Balancer

│

├── App 1

├── App 2

├── App 3

└── App N
```

Additional application servers can be added without changing the overall architecture.

---

# Step 10: Handling Failures

Suppose one application server crashes.

```
App 1 ❌

App 2 ✅

App 3 ✅
```

The Load Balancer automatically routes traffic to healthy servers.

The system remains available.

---

# Step 11: Identifying Bottlenecks

Potential bottlenecks include:

### Database

As the number of URLs grows, database performance may degrade.

Possible improvements:

- Read replicas
- Index optimization
- Database partitioning

---

### Cache

Cache memory may become full.

Possible improvements:

- Eviction policies
- Cache clustering
- Larger cache nodes

---

### Load Balancer

Although uncommon, the load balancer itself can become a bottleneck.

Possible improvements:

- Multiple load balancers
- DNS-based load balancing
- Health checks

---

# Step 12: Future Improvements

As the system evolves, additional features can be introduced.

Examples:

- URL analytics
- QR code generation
- Custom aliases
- User authentication
- URL expiration
- Rate limiting
- Abuse detection
- Geographic analytics

These features should be added only when business requirements justify them.

---

# Applying the Design Framework

Let's compare the completed design with the framework introduced in the previous chapter.

| Design Step | Completed |
|-------------|-----------|
| Understand the problem | ✅ |
| Functional requirements | ✅ |
| Non-functional requirements | ✅ |
| Estimate scale | ✅ |
| High-level architecture | ✅ |
| Database design | ✅ |
| API design | ✅ |
| Identify bottlenecks | ✅ |
| Improve the architecture | ✅ |
| Discuss trade-offs | ✅ |

This demonstrates that the same structured process can be applied to almost any system design problem.

---

# Lessons Learned

From this example, several important principles emerge:

- Requirements determine the architecture.
- High read traffic benefits from caching.
- Stateless application servers simplify scaling.
- Load balancers improve availability.
- Databases should be optimized only when necessary.
- Scaling should be incremental rather than premature.

The architecture starts simple and evolves as traffic and business needs grow.

---

# Common Mistakes

- Designing the most complex architecture before understanding requirements.
- Ignoring traffic estimates.
- Adding unnecessary technologies such as Kafka or Microservices without justification.
- Forgetting to identify bottlenecks.
- Optimizing for future problems instead of current needs.
- Failing to explain architectural decisions.

---

# Best Practices

- Begin with a simple architecture.
- Validate assumptions before making design decisions.
- Estimate workload early in the design process.
- Scale individual components only when necessary.
- Introduce caching to reduce database load.
- Keep application servers stateless.
- Always justify architectural choices based on business requirements.

---

# Key Takeaways

- A structured design framework can be applied consistently to real-world systems.
- Requirements, scale estimates, and constraints should guide architectural decisions.
- Simple architectures are often sufficient for initial versions of a system.
- Bottlenecks should be identified through analysis and addressed incrementally.
- The thought process demonstrated in this example forms the foundation for designing much larger and more complex distributed systems.