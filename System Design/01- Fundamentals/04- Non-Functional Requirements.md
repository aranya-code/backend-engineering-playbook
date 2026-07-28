# Non-Functional Requirements

## Overview

While Functional Requirements define **what a system should do**, **Non-Functional Requirements (NFRs)** define **how well the system should perform those functions**.

Two applications may provide exactly the same features, yet one feels fast, reliable, and secure while the other is slow and frequently unavailable.

The difference lies in their Non-Functional Requirements.

In modern System Design, Non-Functional Requirements are often more challenging than Functional Requirements because they directly influence the system architecture, infrastructure, and technology choices.

---

# What are Non-Functional Requirements?

Non-Functional Requirements describe the quality attributes and operational characteristics of a system.

They define how the system should behave under different conditions rather than what features it provides.

In simple terms:

> Non-Functional Requirements define **how the system should perform**.

They answer questions such as:

- How many users should the system support?
- How quickly should requests be processed?
- How reliable should the application be?
- How secure should the system be?
- How much downtime is acceptable?
- How easily should the system scale?

---

# Why Non-Functional Requirements Matter

A feature-rich application can still fail if it cannot meet user expectations.

Consider an online shopping website.

Suppose it supports:

- User Registration
- Login
- Product Search
- Shopping Cart
- Online Payments

These Functional Requirements are complete.

However, imagine:

- Pages take 15 seconds to load.
- The website crashes during sales.
- Payments frequently fail.
- User passwords are stored in plain text.

Although the application has all the required features, it is unusable because it fails to satisfy its Non-Functional Requirements.

---

# Characteristics of Good Non-Functional Requirements

A good Non-Functional Requirement should be:

- Measurable
- Specific
- Testable
- Quantifiable
- Realistic
- Business-driven

For example:

Poor Requirement

> The application should be fast.

Better Requirement

> The application should respond within 200 milliseconds for 95% of requests.

The second requirement is measurable and can be validated.

---

# Common Non-Functional Requirements

Modern distributed systems typically focus on the following quality attributes.

## Scalability

The system should continue performing efficiently as workload increases.

Examples include:

- Supporting 10 million users.
- Handling 100,000 concurrent requests.
- Scaling without downtime.

Scalability is achieved through techniques such as:

- Horizontal Scaling
- Load Balancing
- Caching
- Database Sharding

---

## Availability

Availability measures how often a system remains operational.

Example requirements:

- 99.9% uptime
- 99.99% uptime
- Multi-region deployment
- Automatic failover

High availability minimizes service interruptions.

---

## Reliability

Reliability ensures the system consistently performs its intended functions.

Reliable systems:

- Recover from failures
- Prevent data corruption
- Minimize service interruptions
- Maintain consistent behavior

Examples include:

- Database replication
- Retry mechanisms
- Backup systems
- Health monitoring

---

## Performance

Performance focuses on how efficiently the application processes requests.

Common metrics include:

- Response Time
- Latency
- Throughput
- CPU Utilization
- Memory Usage

Performance improvements may involve:

- Caching
- Query Optimization
- Efficient Algorithms
- Parallel Processing

---

## Security

Security protects users, applications, and business data.

Security requirements include:

- Authentication
- Authorization
- Encryption
- Secure APIs
- Data Privacy
- Audit Logging

Security should be built into the architecture from the beginning.

---

## Maintainability

Software systems evolve continuously.

A maintainable application should allow developers to:

- Add new features
- Fix bugs
- Replace components
- Upgrade technologies

without requiring significant architectural changes.

---

## Fault Tolerance

Failures are inevitable.

The system should continue operating even when components fail.

Examples include:

- Retry Logic
- Circuit Breakers
- Replication
- Backup Servers
- Graceful Degradation

Fault tolerance minimizes the impact of unexpected failures.

---

## Consistency

Consistency ensures users observe correct and expected data.

Example:

After transferring money between two bank accounts, both balances should immediately reflect the transaction.

Maintaining consistency becomes increasingly challenging in distributed systems.

---

## Durability

Once data is successfully stored, it should not be lost.

Examples include:

- Database Transactions
- Persistent Storage
- Replication
- Backup Strategies

Durability is especially important for financial and healthcare applications.

---

# Examples of Non-Functional Requirements

## Food Delivery Platform

Possible Non-Functional Requirements:

- Support 5 million registered users.
- Handle 100,000 concurrent users.
- Complete searches within 300 ms.
- Achieve 99.99% uptime.
- Encrypt all payment information.
- Recover automatically from server failures.

---

## URL Shortener

Possible Non-Functional Requirements:

- Redirect users within 100 ms.
- Handle millions of redirects per day.
- Maintain 99.99% availability.
- Generate globally unique short URLs.
- Prevent duplicate URL generation.

---

## Video Streaming Platform

Possible Non-Functional Requirements:

- Stream videos with minimal buffering.
- Deliver content globally.
- Support millions of simultaneous viewers.
- Continue streaming during server failures.
- Scale automatically during peak traffic.

---

# Functional vs Non-Functional Requirements

| Functional Requirements | Non-Functional Requirements |
|--------------------------|-----------------------------|
| Describe what the system does | Describe how the system performs |
| Focus on features | Focus on quality attributes |
| Business functionality | Operational behavior |
| Login | Login within 2 seconds |
| Search products | Search results returned within 300 ms |
| Upload videos | Support 1 million uploads daily |
| Send notifications | Deliver notifications within 5 seconds |

Both are equally important and complement each other.

---

# How Non-Functional Requirements Influence Architecture

Consider the requirement:

> The application should support 100 million users.

This single requirement may require:

- Load Balancers
- CDN
- Distributed Caching
- Database Sharding
- Replication
- Auto Scaling
- Multiple Data Centers

Another requirement:

> The system should achieve 99.99% uptime.

Possible architectural solutions:

- Multi-region deployment
- Redundant servers
- Automatic failover
- Health checks
- Disaster recovery

This demonstrates how Non-Functional Requirements directly influence architectural decisions.

---

# Non-Functional Requirements in System Design Interviews

During interviews, candidates are expected to ask questions such as:

- How many users will use the system?
- What is the expected traffic?
- What is the expected response time?
- How much data will be stored?
- Is high availability required?
- Is strong consistency necessary?
- Are there any security or compliance requirements?

These questions help establish the system's design constraints before discussing architecture.

---

# Common Mistakes

- Ignoring scalability requirements.
- Assuming unlimited infrastructure.
- Designing without performance goals.
- Treating security as an afterthought.
- Failing to define measurable objectives.
- Confusing Functional and Non-Functional Requirements.
- Ignoring disaster recovery and fault tolerance.

---

# Best Practices

- Define measurable quality goals.
- Gather Non-Functional Requirements before designing the architecture.
- Prioritize requirements based on business needs.
- Consider scalability from the beginning.
- Design for failures rather than assuming perfect conditions.
- Continuously monitor whether the system meets its quality objectives.
- Revisit Non-Functional Requirements as the application grows.

---

# Key Takeaways

- Non-Functional Requirements define **how well a system should perform its functions**.
- They describe quality attributes such as scalability, availability, reliability, performance, security, and maintainability.
- Non-Functional Requirements directly influence architectural and infrastructure decisions.
- Clearly defining measurable quality goals leads to better system designs.
- Successful systems satisfy both Functional and Non-Functional Requirements to deliver a reliable user experience.