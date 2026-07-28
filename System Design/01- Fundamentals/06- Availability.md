# Availability

## Overview

Availability is one of the most important quality attributes in System Design. Users expect applications to be accessible whenever they need them, whether they are shopping online, streaming videos, transferring money, or sending messages.

Even a highly scalable and performant system provides little value if users cannot access it.

Designing highly available systems requires eliminating single points of failure, introducing redundancy, and ensuring that failures can be detected and recovered from automatically.

---

# What is Availability?

Availability measures **how often a system is operational and accessible to users**.

In simple terms:

> Availability answers the question: **"Can users access the system when they need it?"**

A highly available system continues serving requests despite hardware failures, software crashes, or network issues.

---

# Availability Formula

Availability is calculated as:

```
Availability =
Successful Uptime
---------------------- × 100%
Total Time
```

Or equivalently,

```
Availability =
(Total Time − Downtime)
------------------------ × 100%
        Total Time
```

Example:

Suppose a service is unavailable for 2 hours during an entire year.

```
Total Time = 8760 hours

Downtime = 2 hours
```

```
Availability =

(8760 − 2)
---------- × 100
   8760

≈ 99.98%
```

---

# Why Availability Matters

Imagine trying to:

- Pay using an online banking app
- Book a flight
- Order food
- Attend an online meeting
- Watch a live sports event

If the service is unavailable, users cannot complete these activities regardless of how many features the application offers.

High availability improves:

- Customer satisfaction
- Business continuity
- Revenue
- Brand reputation
- User trust

---

# Availability vs Reliability

Although these terms are related, they are not identical.

| Availability | Reliability |
|--------------|-------------|
| Measures whether the system is accessible | Measures whether the system works correctly |
| Focuses on uptime | Focuses on correctness over time |
| Answers "Can users access it?" | Answers "Will it perform correctly?" |
| Prioritizes continuous service | Prioritizes consistent behavior |

Example:

A website that is always online but frequently returns incorrect data has:

- High Availability
- Low Reliability

A website that always returns correct data but is frequently offline has:

- High Reliability
- Low Availability

An excellent system requires both.

---

# Availability Levels

Availability is usually expressed as a percentage.

| Availability | Maximum Downtime per Year |
|--------------|--------------------------:|
| 99% | ~3.65 days |
| 99.9% | ~8.76 hours |
| 99.99% | ~52.6 minutes |
| 99.999% | ~5.26 minutes |

Higher availability generally requires significantly greater architectural complexity and infrastructure costs.

---

# Causes of Downtime

Applications become unavailable for many reasons.

Common causes include:

- Hardware failures
- Server crashes
- Database failures
- Network outages
- Software bugs
- Configuration errors
- Cloud provider issues
- Human mistakes
- Power failures
- Security attacks

System designers assume failures will occur and build architectures that can recover automatically.

---

# Single Point of Failure (SPOF)

A **Single Point of Failure (SPOF)** is any component whose failure causes the entire system to become unavailable.

Example:

```
Users
   │
   ▼
Application Server
   │
   ▼
Database
```

If the only database crashes, the entire application stops working.

This database is a Single Point of Failure.

---

# Eliminating Single Points of Failure

A common solution is redundancy.

```
              Users
                 │
                 ▼
          Load Balancer
           │         │
           ▼         ▼
      App Server  App Server
           │         │
           └────┬────┘
                ▼
      Primary Database
                │
                ▼
      Replica Database
```

If one application server fails, traffic is redirected to the remaining healthy server.

If the primary database fails, a replica may be promoted to become the new primary.

---

# Redundancy

Redundancy means having multiple copies of critical components.

Examples include:

- Multiple application servers
- Database replicas
- Multiple network paths
- Backup power supplies
- Duplicate storage systems

Redundancy prevents a single failure from bringing down the entire system.

---

# Load Balancing

Load balancers distribute incoming traffic across multiple servers.

```
Users
   │
   ▼
Load Balancer
  │   │   │
  ▼   ▼   ▼
 S1  S2  S3
```

Benefits include:

- Higher availability
- Better fault tolerance
- Improved scalability
- Better resource utilization

If one server becomes unhealthy, the load balancer stops sending traffic to it.

---

# Health Checks

Health checks continuously monitor application components.

Typical checks include:

- HTTP endpoint availability
- CPU utilization
- Memory usage
- Database connectivity
- Disk space
- Service responsiveness

If a server fails its health check, it is removed from service until it recovers.

---

# Failover

Failover is the automatic transfer of workload from a failed component to a healthy one.

Example:

```
Primary Database
       │
       │ Failure
       ▼
Replica Database
```

The application continues operating with minimal interruption.

Automatic failover is essential for highly available systems.

---

# Multi-Availability Zone Deployment

Cloud providers divide regions into multiple Availability Zones (AZs).

Example:

```
Region

├── AZ-1
├── AZ-2
└── AZ-3
```

Deploying resources across multiple AZs protects against failures affecting an individual data center.

If one Availability Zone becomes unavailable, the others continue serving traffic.

---

# Multi-Region Deployment

Some mission-critical applications are deployed across multiple geographic regions.

Example:

```
North America
       │
Europe
       │
Asia
```

Benefits include:

- Disaster recovery
- Lower latency for global users
- Regional fault isolation
- Improved availability

However, multi-region architectures introduce challenges such as data synchronization and consistency.

---

# Graceful Degradation

Sometimes maintaining partial functionality is better than complete failure.

Example:

An e-commerce platform may:

- Allow product browsing
- Disable recommendations
- Temporarily disable customer reviews

Users can still make purchases even though some features are unavailable.

---

# Designing for High Availability

Engineers commonly use the following techniques:

- Eliminate Single Points of Failure
- Deploy redundant servers
- Replicate databases
- Configure automatic failover
- Use load balancers
- Perform continuous health checks
- Deploy across multiple Availability Zones
- Create disaster recovery plans
- Monitor infrastructure continuously

---

# Real-World Examples

## Netflix

Netflix runs services across multiple servers and Availability Zones.

If one server or zone fails, traffic is automatically redirected to healthy instances.

---

## Amazon

Amazon's shopping platform uses redundant infrastructure, replicated databases, and automatic failover to remain operational during hardware failures.

---

## Banking Systems

Banks often deploy applications across multiple data centers to ensure financial transactions remain available even during infrastructure failures.

---

## Messaging Applications

Applications such as WhatsApp maintain high availability by distributing services across numerous servers and automatically replacing failed instances.

---

# Common Mistakes

- Relying on a single application server.
- Using only one database instance.
- Ignoring health checks.
- Performing manual failover for critical systems.
- Not testing disaster recovery procedures.
- Assuming cloud infrastructure never fails.
- Ignoring regional outages.

---

# Best Practices

- Remove all Single Points of Failure.
- Design systems assuming components will fail.
- Use redundancy for critical infrastructure.
- Configure automatic failover wherever possible.
- Continuously monitor system health.
- Test failure scenarios regularly.
- Balance availability goals with operational cost and complexity.

---

# Key Takeaways

- Availability measures how often a system is operational and accessible to users.
- High availability is achieved by eliminating Single Points of Failure and introducing redundancy.
- Techniques such as load balancing, health checks, failover, and multi-zone deployments improve availability.
- Availability and reliability are related but measure different aspects of system quality.
- Designing for failure is a fundamental principle of building resilient distributed systems.