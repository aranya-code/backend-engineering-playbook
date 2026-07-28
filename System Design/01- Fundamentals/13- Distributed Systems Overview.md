# Distributed Systems Overview

## Overview

As applications grow beyond the capabilities of a single machine, they must distribute their workload across multiple computers. This approach forms the foundation of **Distributed Systems**.

Modern applications such as Netflix, Amazon, Google, WhatsApp, Uber, and Spotify all operate as distributed systems because no single server can efficiently handle their scale, availability, and performance requirements.

Distributed systems enable applications to process massive workloads, tolerate failures, and serve users across the globe. However, they also introduce significant architectural challenges, including network failures, data consistency, synchronization, and coordination.

Understanding distributed systems is fundamental to modern System Design because almost every large-scale application relies on distributed architecture.

---

# What is a Distributed System?

A **Distributed System** is a collection of independent computers that work together to appear as a single system to users.

In simple terms:

> Multiple computers cooperate to solve a problem that would be difficult or impossible for a single machine to handle.

Although many machines are involved, users interact with the system as if it were a single application.

---

# Basic Architecture

```
                 Users
                    │
                    ▼
             Load Balancer
          ┌──────┼──────┐
          ▼      ▼      ▼
      Server A Server B Server C
          │      │      │
          └──────┼──────┘
                 ▼
        Shared Storage / Database
```

The workload is distributed across multiple servers.

---

# Why Do We Need Distributed Systems?

A single server eventually reaches its limits.

As applications grow, they encounter problems such as:

- Increasing user traffic
- Growing datasets
- High CPU utilization
- Memory limitations
- Storage limitations
- Hardware failures
- Geographic latency

Instead of upgrading one machine indefinitely, engineers distribute the workload across multiple machines.

---

# Characteristics of Distributed Systems

Distributed systems typically have the following characteristics:

- Multiple independent machines
- Network communication
- Shared responsibility
- Concurrent execution
- Resource sharing
- Fault tolerance
- Horizontal scalability

Each machine contributes part of the overall workload.

---

# Goals of a Distributed System

A distributed system is designed to achieve several objectives.

## Scalability

Support increasing numbers of:

- Users
- Requests
- Services
- Data

without requiring major architectural changes.

---

## Availability

Continue serving users even when individual machines fail.

Users should experience minimal disruption.

---

## Reliability

Ensure that the system continues producing correct results despite failures.

---

## Performance

Distribute workloads efficiently to reduce latency and increase throughput.

---

## Fault Tolerance

Failures should affect only a small part of the system rather than causing a complete outage.

---

# Components of a Distributed System

Most distributed systems consist of multiple specialized components.

## Clients

Initiate requests.

Examples:

- Browsers
- Mobile Apps
- Desktop Applications

---

## Load Balancers

Distribute incoming traffic across multiple servers.

Benefits include:

- Better availability
- Improved scalability
- Efficient resource utilization

---

## Application Servers

Execute business logic.

Examples:

- Authentication
- Order Processing
- Recommendation Engine
- Payment Processing

---

## Databases

Store persistent data.

Examples:

- PostgreSQL
- MySQL
- MongoDB
- Cassandra

---

## Cache

Stores frequently accessed data.

Examples:

- Redis
- Memcached

Caching reduces latency and decreases database load.

---

## Message Brokers

Enable asynchronous communication between services.

Examples:

- Apache Kafka
- RabbitMQ
- Amazon SQS

---

## Monitoring Systems

Track system health and performance.

Examples:

- Prometheus
- Grafana
- ELK Stack

---

# Communication Between Nodes

Machines communicate over a network rather than through local function calls.

Common communication methods include:

- HTTP
- HTTPS
- REST APIs
- gRPC
- WebSockets
- Message Queues

Unlike local method calls, network communication is slower and less reliable.

---

# Distributed vs Centralized Systems

## Centralized System

```
Users

↓

Single Server

↓

Database
```

One server performs all processing.

---

## Distributed System

```
Users

↓

Load Balancer

│     │     │

▼     ▼     ▼

Server A
Server B
Server C
```

Multiple servers share the workload.

---

# Advantages of Distributed Systems

## High Scalability

Additional servers can be added as demand increases.

```
2 Servers

↓

10 Servers

↓

100 Servers
```

---

## Improved Availability

If one server fails, others continue serving requests.

```
Server A ❌

Server B ✅

Server C ✅
```

---

## Better Fault Tolerance

Failures remain isolated.

A single hardware failure does not necessarily bring down the entire application.

---

## Better Resource Utilization

Workloads are distributed across multiple machines.

This prevents individual servers from becoming overloaded.

---

## Geographic Distribution

Servers can be deployed closer to users.

Benefits include:

- Lower latency
- Faster responses
- Improved user experience

---

# Challenges of Distributed Systems

Distributed systems introduce new problems that do not exist in single-server applications.

## Network Failures

Servers communicate over networks.

Networks can experience:

- Packet loss
- High latency
- Connection failures
- Timeouts

Applications must be designed to handle these situations gracefully.

---

## Partial Failures

One server may fail while others continue operating.

```
Server A ✅

Server B ❌

Server C ✅
```

Unlike monolithic systems, failures are often partial rather than total.

---

## Data Consistency

Keeping data synchronized across multiple machines is difficult.

Examples include:

- Database replication
- Distributed caches
- Multi-region deployments

Consistency becomes a major architectural concern.

---

## Clock Synchronization

Different servers have different system clocks.

Even slight differences can cause issues with:

- Ordering events
- Logging
- Transactions

Distributed systems often rely on coordinated time synchronization.

---

## Increased Complexity

Compared with monolithic applications, distributed systems require additional infrastructure such as:

- Load Balancers
- Service Discovery
- Monitoring
- Distributed Tracing
- Message Brokers
- Configuration Management

Operational complexity increases significantly.

---

# CAP Theorem (Introduction)

One of the most important concepts in distributed systems is the **CAP Theorem**.

It states that during a network partition, a distributed system can guarantee at most two of the following:

- Consistency
- Availability
- Partition Tolerance

CAP Theorem will be explored in detail in a later chapter.

---

# Examples of Distributed Systems

## Netflix

Netflix distributes:

- Streaming
- Recommendations
- User Profiles
- Billing

across numerous independent services running worldwide.

---

## Amazon

Amazon's platform consists of thousands of distributed services responsible for:

- Orders
- Payments
- Inventory
- Recommendations
- Shipping

---

## Google Search

Google processes billions of searches using distributed data centers spread across the globe.

---

## WhatsApp

WhatsApp distributes messaging services across many servers to support billions of messages every day.

---

# When Should You Use Distributed Systems?

Distributed systems are appropriate when applications require:

- High scalability
- High availability
- Fault tolerance
- Global deployment
- Independent service scaling
- Large datasets
- High request volumes

For small applications and startups, a distributed architecture is often unnecessary and may introduce avoidable complexity.

---

# Common Mistakes

- Assuming distributed systems automatically improve performance.
- Ignoring network latency.
- Treating network communication like local function calls.
- Underestimating operational complexity.
- Failing to design for partial failures.
- Assuming servers always remain synchronized.
- Building distributed systems before there is a genuine business need.

---

# Best Practices

- Start with a simple architecture and distribute only when necessary.
- Design assuming networks and servers will fail.
- Keep services loosely coupled.
- Monitor every component continuously.
- Use asynchronous communication where appropriate.
- Minimize unnecessary network calls.
- Plan for data consistency and fault recovery from the beginning.

---

# Key Takeaways

- A Distributed System consists of multiple independent computers working together as a single system.
- Distributed systems enable scalability, availability, fault tolerance, and global deployment.
- They introduce challenges such as network failures, data consistency, partial failures, and increased operational complexity.
- Communication between distributed components occurs over a network and is inherently less reliable than local function calls.
- Modern large-scale applications rely on distributed systems to handle massive workloads while maintaining reliability and performance.