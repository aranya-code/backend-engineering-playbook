# Vertical vs Horizontal Scaling

## Overview

As applications grow, they eventually require more computing resources to handle increasing traffic, larger datasets, and more complex workloads.

There are two primary approaches to increasing a system's capacity:

- **Vertical Scaling (Scaling Up)**
- **Horizontal Scaling (Scaling Out)**

Choosing the right scaling strategy is one of the most important architectural decisions in System Design. While both approaches improve system capacity, they differ significantly in cost, complexity, reliability, scalability, and operational overhead.

Most modern distributed systems use a combination of both approaches depending on the component being scaled.

---

# Why Do Systems Need Scaling?

Consider an e-commerce website that initially serves 500 users per day.

As the business grows, it begins serving:

- 10,000 users
- 100,000 users
- 10 million users

Eventually, the existing infrastructure becomes insufficient.

Common symptoms include:

- High CPU utilization
- Memory exhaustion
- Slow response times
- Database bottlenecks
- Request timeouts
- Server crashes

Scaling provides additional resources so the system can continue serving users efficiently.

---

# What is Vertical Scaling?

Vertical Scaling means increasing the resources of an **existing server**.

Instead of adding more servers, the current server is upgraded.

Examples include:

- More CPU cores
- More RAM
- Faster SSD storage
- Better network bandwidth

Example:

```
Before

CPU : 4 Cores
RAM : 8 GB

↓

After

CPU : 16 Cores
RAM : 64 GB
```

The application continues running on a single machine, but that machine becomes significantly more powerful.

---

# Advantages of Vertical Scaling

## Simple Architecture

No distributed system is required.

The application continues running on one server.

---

## Minimal Code Changes

Most applications can benefit from additional hardware without requiring architectural modifications.

---

## Easier Database Management

Traditional relational databases often scale vertically because maintaining a single database server is simpler than managing multiple distributed nodes.

---

## Lower Operational Complexity

Since only one server is involved:

- Deployment is simpler.
- Monitoring is easier.
- Debugging becomes straightforward.

---

# Limitations of Vertical Scaling

## Hardware Limits

Every server has a maximum capacity.

Eventually, no larger hardware is available.

---

## Expensive Hardware

Powerful enterprise servers become increasingly expensive.

The cost does not scale linearly.

---

## Single Point of Failure

If the server crashes:

```
Users

↓

Server ❌
```

The entire application becomes unavailable unless redundancy is introduced.

---

## Limited Long-Term Growth

Vertical scaling works well initially but eventually reaches physical and financial limits.

---

# What is Horizontal Scaling?

Horizontal Scaling increases capacity by adding **more servers**.

Instead of upgrading one machine, multiple machines work together.

Example:

```
Users

↓

Load Balancer

│     │     │

▼     ▼     ▼

S1    S2    S3
```

Each server processes part of the incoming workload.

---

# Advantages of Horizontal Scaling

## Nearly Unlimited Growth

Additional servers can be added as demand increases.

```
2 Servers

↓

5 Servers

↓

20 Servers

↓

200 Servers
```

This makes horizontal scaling suitable for internet-scale applications.

---

## Better Availability

If one server fails:

```
Load Balancer

│     │

▼     ▼

S1 ❌  S2 ✅
```

Traffic is automatically routed to healthy servers.

Users experience little or no downtime.

---

## Improved Fault Tolerance

Failures are isolated.

The failure of one server does not necessarily affect the entire application.

---

## Flexible Resource Expansion

Resources can be added gradually instead of purchasing one very large server.

---

# Challenges of Horizontal Scaling

Adding servers introduces new architectural challenges.

Examples include:

- Load balancing
- Service discovery
- Distributed caching
- Session management
- Data consistency
- Network communication
- Database replication
- Monitoring multiple nodes

Horizontal scaling provides greater flexibility but increases architectural complexity.

---

# Visual Comparison

## Vertical Scaling

```
Users

↓

Large Server
```

Everything runs on one machine.

---

## Horizontal Scaling

```
Users

↓

Load Balancer

│    │    │

▼    ▼    ▼

S1   S2   S3
```

The workload is distributed across multiple machines.

---

# Comparing Vertical and Horizontal Scaling

| Feature | Vertical Scaling | Horizontal Scaling |
|---------|------------------|--------------------|
| Strategy | Upgrade one server | Add more servers |
| Architecture | Simple | Distributed |
| Maximum Capacity | Limited by hardware | Nearly unlimited |
| Cost | High-end hardware can be expensive | Incremental growth |
| Availability | Lower | Higher |
| Fault Tolerance | Limited | Excellent |
| Complexity | Low | High |
| Maintenance | Easier | More complex |
| Scaling Speed | Hardware upgrade required | Add new instances |
| Long-Term Growth | Limited | Excellent |

---

# Which Components Scale Vertically?

Some workloads benefit from vertical scaling.

Examples include:

- Small relational databases
- Development environments
- Internal tools
- Legacy applications
- Single-node analytics systems

These systems may not justify the complexity of distributed architectures.

---

# Which Components Scale Horizontally?

Modern internet applications commonly scale the following horizontally:

- Web servers
- API servers
- Microservices
- Background workers
- Cache servers
- Search clusters
- Object storage
- Message brokers

Horizontal scaling enables these services to support millions of users.

---

# Database Scaling

Databases often use both approaches.

Initially:

```
Database

↓

Increase CPU
Increase RAM
```

As demand grows:

```
Primary Database

│

├── Read Replica

├── Read Replica

└── Read Replica
```

Eventually, very large systems may adopt:

- Database sharding
- Distributed SQL databases
- NoSQL databases

---

# Session Management

Horizontal scaling requires applications to avoid storing user sessions locally.

Poor approach:

```
User

↓

Server A
(Session stored locally)
```

If the next request reaches Server B, the session is unavailable.

Better approaches include:

- Redis
- Database-backed sessions
- JWT-based authentication

These allow any server to process any request.

---

# Real-World Examples

## Startup Application

A new startup with a few thousand users may simply upgrade its existing server.

Vertical scaling is often sufficient.

---

## Netflix

Netflix operates thousands of servers across multiple regions.

It relies heavily on horizontal scaling to serve millions of concurrent users.

---

## Amazon

Amazon distributes incoming traffic across large fleets of application servers using load balancers and auto-scaling groups.

Horizontal scaling enables the platform to handle massive traffic spikes during major sales.

---

## Google Search

Google processes billions of search requests using thousands of distributed servers worldwide.

Horizontal scaling makes this possible.

---

# When to Choose Vertical Scaling

Vertical scaling is a good choice when:

- Traffic is relatively low.
- Simplicity is preferred.
- Budget allows larger hardware.
- The application is not yet distributed.
- Fast implementation is more important than long-term scalability.

---

# When to Choose Horizontal Scaling

Horizontal scaling is appropriate when:

- Millions of users must be supported.
- High availability is required.
- Fault tolerance is important.
- Traffic fluctuates significantly.
- Long-term growth is expected.
- Cloud infrastructure and auto-scaling are available.

---

# Common Mistakes

- Assuming vertical scaling can solve every performance problem.
- Introducing horizontal scaling before it is actually needed.
- Ignoring session management when adding multiple servers.
- Scaling application servers while leaving the database unchanged.
- Failing to identify the actual bottleneck before scaling.
- Underestimating the operational complexity of distributed systems.

---

# Best Practices

- Start with a simple architecture and scale only when necessary.
- Monitor CPU, memory, network, and database utilization before scaling.
- Prefer stateless application servers to simplify horizontal scaling.
- Use load balancers to distribute traffic evenly.
- Scale databases independently from application servers.
- Combine vertical and horizontal scaling when appropriate.
- Continuously evaluate cost, complexity, and business requirements before choosing a scaling strategy.

---

# Key Takeaways

- Vertical Scaling increases the resources of a single server, while Horizontal Scaling adds more servers.
- Vertical scaling is simpler but limited by hardware and introduces potential single points of failure.
- Horizontal scaling provides greater capacity, availability, and fault tolerance but requires a distributed architecture.
- Most modern cloud-native systems primarily rely on horizontal scaling for long-term growth.
- Choosing the right scaling strategy depends on application size, expected traffic, budget, and operational complexity.