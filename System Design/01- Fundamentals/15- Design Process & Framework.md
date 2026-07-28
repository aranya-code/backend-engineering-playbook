# Design Process & Framework

## Overview

Designing a software system is not about immediately drawing architecture diagrams or selecting technologies. Experienced software architects follow a structured process that helps them understand the problem, gather requirements, evaluate constraints, and make informed architectural decisions.

This systematic approach reduces the risk of overengineering, ensures that business requirements remain the primary focus, and provides a repeatable framework for designing systems of any size.

Whether designing a URL shortener in an interview or building a global e-commerce platform, the overall thought process remains remarkably similar.

---

# Why Follow a Design Process?

Many engineers make the mistake of jumping directly into discussions about:

- Microservices
- Kubernetes
- Redis
- Kafka
- Load Balancers

before understanding the actual problem.

A structured design process helps architects:

- Understand the business problem
- Identify constraints
- Clarify requirements
- Evaluate trade-offs
- Choose appropriate technologies
- Design scalable solutions

Good architecture is driven by requirements—not by technology.

---

# High-Level Design Process

A practical system design process consists of the following steps:

```
Understand the Problem
        │
        ▼
Gather Requirements
        │
        ▼
Estimate Scale
        │
        ▼
Design High-Level Architecture
        │
        ▼
Design Data Model
        │
        ▼
Identify Bottlenecks
        │
        ▼
Improve the Design
```

Each step builds upon the previous one.

---

# Step 1: Understand the Problem

Never begin designing immediately.

First, understand:

- What problem is being solved?
- Who are the users?
- What are the primary use cases?
- What is outside the scope?

Example questions:

- Is this a web application?
- Is it mobile only?
- Is it public or internal?
- Who are the primary users?

A clear understanding of the problem prevents incorrect assumptions.

---

# Step 2: Gather Functional Requirements

Determine what the system must do.

Example:

For a URL Shortener:

Functional Requirements:

- Create short URLs
- Redirect users
- Delete URLs
- View analytics

Do not discuss implementation yet.

Focus only on business functionality.

---

# Step 3: Gather Non-Functional Requirements

Next, determine how well the system should perform.

Questions include:

- Expected traffic?
- Target latency?
- Availability requirements?
- Security requirements?
- Data retention?
- Geographic distribution?

Example:

- Support 50 million users
- 99.99% availability
- Response time under 200 ms

These requirements strongly influence the architecture.

---

# Step 4: Estimate Scale

Before selecting technologies, estimate the expected workload.

Common estimates include:

- Daily Active Users (DAU)
- Requests per Second (RPS)
- Storage requirements
- Network bandwidth
- Database growth
- Concurrent users

Example:

```
Users

10 Million

↓

100 Requests/User/Day

↓

1 Billion Requests/Day
```

Estimating scale helps determine whether simple or distributed solutions are appropriate.

---

# Step 5: Identify Core Components

Determine the major building blocks.

Typical components include:

- Client
- API Server
- Database
- Cache
- Load Balancer
- Object Storage
- CDN
- Message Queue
- Background Workers

Avoid discussing implementation details too early.

---

# Step 6: Design the High-Level Architecture

Create a simple architecture diagram.

Example:

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

At this stage, focus on:

- Data flow
- Major services
- System boundaries

Keep the design simple.

---

# Step 7: Design the Data Model

Identify the important entities.

Example:

Food Delivery System

```
User

Restaurant

Menu

Order

Payment

Delivery
```

Define:

- Relationships
- Primary identifiers
- Important attributes

A good data model simplifies later architectural decisions.

---

# Step 8: Design APIs

Identify the major API endpoints.

Example:

```
POST /orders

GET /orders/{id}

PUT /orders/{id}

DELETE /orders/{id}
```

API design clarifies how clients interact with the system.

---

# Step 9: Identify Bottlenecks

Analyze the architecture for potential limitations.

Examples:

- Database overload
- Slow queries
- Large file uploads
- Network latency
- Cache misses
- External API dependencies

Every system has bottlenecks.

The goal is to identify them before they become production problems.

---

# Step 10: Improve the Architecture

Once bottlenecks are identified, improve the design.

Possible improvements include:

- Add caching
- Introduce a CDN
- Scale horizontally
- Add read replicas
- Use asynchronous messaging
- Partition the database
- Add monitoring

Each improvement should solve a specific problem.

Avoid adding unnecessary complexity.

---

# Design Framework Checklist

A useful checklist when designing any system:

```
✓ Understand the problem

✓ Functional Requirements

✓ Non-Functional Requirements

✓ Scale estimation

✓ High-Level Architecture

✓ Database Design

✓ API Design

✓ Bottleneck Analysis

✓ Scalability Improvements

✓ Security

✓ Monitoring

✓ Trade-offs
```

Following the same framework ensures important topics are not overlooked.

---

# Example: URL Shortener

Applying the framework:

### Requirements

- Create short URLs
- Redirect users

---

### Scale

- Millions of redirects per day

---

### Components

- API Server
- Database
- Cache

---

### Architecture

```
Client

↓

API

↓

Redis

↓

Database
```

---

### Improvements

- Cache popular URLs
- Add read replicas
- Use load balancers

The framework transforms an abstract problem into a structured design.

---

# Example: Online Shopping Platform

Following the same process:

Requirements:

- Browse products
- Add to cart
- Checkout
- Payments

↓

Estimate traffic

↓

Design architecture

↓

Design database

↓

Add caching

↓

Scale services

↓

Monitor production

The framework remains the same regardless of application type.

---

# Why This Framework Works

This approach helps architects:

- Avoid premature optimization
- Ask the right questions
- Build requirement-driven architectures
- Explain decisions clearly
- Identify risks early
- Produce consistent designs

It is equally useful for production systems and system design interviews.

---

# System Design Interview Framework

During interviews, a simplified version of the framework is often used:

```
Clarify Requirements

↓

Estimate Scale

↓

High-Level Design

↓

Database Design

↓

API Design

↓

Deep Dive

↓

Identify Bottlenecks

↓

Discuss Improvements

↓

Explain Trade-offs
```

Interviewers generally evaluate your thought process more than the final diagram.

---

# Common Mistakes

- Jumping directly into technology choices.
- Ignoring requirements.
- Skipping scale estimation.
- Designing without understanding users.
- Overengineering simple systems.
- Ignoring bottlenecks.
- Forgetting to discuss trade-offs.
- Failing to justify architectural decisions.

---

# Best Practices

- Always begin with requirements.
- Keep the first design simple.
- Validate assumptions before making decisions.
- Let scale determine architecture.
- Improve the design incrementally.
- Explain why each component exists.
- Continuously evaluate trade-offs throughout the design process.

---

# Key Takeaways

- A structured design process produces more reliable and maintainable architectures.
- Requirements should always drive architectural decisions.
- Estimating scale helps determine the appropriate level of complexity.
- Architecture should evolve by identifying bottlenecks and improving specific areas.
- Following a consistent framework leads to better system designs and stronger performance in system design interviews.