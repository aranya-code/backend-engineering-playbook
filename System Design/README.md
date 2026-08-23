# System Design

A comprehensive, structured knowledge base covering the theory, patterns, and practical skills required to design scalable, reliable, and maintainable software systems.

The material progresses from first principles through distributed systems theory, networking, data storage, caching, messaging, scalability patterns, microservices, real-world case studies, cloud architecture, architectural decision-making, and interview preparation.

> **150+ notes · 12 sections · From fundamentals to FAANG-level system design interviews**

---

## Quick Navigation

| # | Section | Coverage |
|---|---|---|
| 01 | [Fundamentals](01-%20Fundamentals/) | System design principles, requirements, latency, throughput, availability, reliability, scalability, stateful vs stateless, client-server, monolithic architecture, trade-offs, and the design process. |
| 02 | [Distributed Systems](02-%20Distributed%20Systems/) | CAP theorem, PACELC, consistency models, replication strategies, quorum, consensus algorithms, split brain, distributed transactions, 2PC, saga pattern, eventual consistency, and ordering. |
| 03 | [Networking](03-%20Networking/) | DNS, HTTP/HTTPS, TCP/UDP, WebSockets, long polling, SSE, REST, GraphQL, gRPC, API versioning, API gateway, service discovery, proxies, and CDN. |
| 04 | [Data Storage](04-%20Data%20Storage/) | SQL vs NoSQL, ACID, BASE, indexing, normalization, denormalization, sharding, partitioning, replication, read replicas, CQRS, event sourcing, bloom filters, and vector databases. |
| 05 | [Caching](05-%20Caching/) | Cache patterns, invalidation, eviction policies, distributed cache, Redis, cache stampede, cache penetration, and cache avalanche. |
| 06 | [Messaging Systems](06-%20Messaging%20Systems/) | Message queues, pub/sub, event-driven architecture, Kafka, RabbitMQ, Amazon SQS, dead letter queues, delivery guarantees, and idempotency. |
| 07 | [Scalability Patterns](07-%20Scalability%20Patterns/) | Load balancing, rate limiting, circuit breaker, retry, bulkhead, backpressure, async processing, batch processing, and streaming. |
| 08 | [Microservices](08-%20Microservices/) | Microservices vs monolith, service communication, API gateway, service discovery, distributed configuration, service mesh, observability, and deployment strategies. |
| 09 | [System Design Case Studies](09-%20System%20Design%20Case%20Studies/) | URL shortener, Pastebin, rate limiter, chat app, notification system, search autocomplete, news feed, YouTube, Netflix, Uber, WhatsApp, Twitter, Instagram, Dropbox, and Google Drive. |
| 10 | [Cloud Architecture](10-%20Cloud%20Architecture/) | Designing on AWS, high availability, Multi-AZ vs multi-region, disaster recovery, auto scaling, CDN, object storage, monitoring, and logging. |
| 11 | [Architecture Decision Records](11-%20Architecture%20Decision%20Records/) | Monolith vs microservices, SQL vs NoSQL, Kafka vs RabbitMQ, REST vs gRPC, Redis vs Memcached, sync vs async, Docker vs Kubernetes, and choosing the right architecture. |
| 12 | [Interview Preparation](12-%20Interview%20Preparation/) | System design interview framework, requirement gathering, capacity estimation, architecture templates, top 50 questions, senior backend interview, FAANG-style questions, mock interviews, and cheat sheet. |

---

## Learning Path

The sections are ordered to build knowledge progressively.

```text
Fundamentals
     │
     ▼
Distributed Systems
     │
     ▼
Networking
     │
     ▼
Data Storage
     │
     ▼
Caching
     │
     ▼
Messaging Systems
     │
     ▼
Scalability Patterns
     │
     ▼
Microservices
     │
     ▼
System Design Case Studies
     │
     ▼
Cloud Architecture
     │
     ▼
Architecture Decision Records
     │
     ▼
Interview Preparation
```

---

## Key Areas

### Theory and Foundations (01–03)

Covers the core building blocks of system design: principles, requirements, trade-offs, distributed systems theory, consistency models, replication, networking protocols, and API design. This is the prerequisite knowledge for everything that follows.

### Infrastructure and Data (04–06)

Covers the storage, caching, and messaging layers that backend systems depend on. Includes database selection, indexing, sharding, cache design, message queues, event-driven architecture, and delivery guarantees.

### Patterns and Architecture (07–08)

Covers the scalability and resilience patterns used in production systems: load balancing, circuit breakers, backpressure, microservices, service mesh, observability, and deployment strategies.

### Applied Design (09–10)

Covers real-world system design through 15 case studies and cloud architecture on AWS. This is where theory meets practice — designing systems like YouTube, Uber, WhatsApp, and Instagram from requirements to architecture.

### Decision-Making and Interview (11–12)

Covers architectural decision-making through structured comparisons (SQL vs NoSQL, Kafka vs RabbitMQ, REST vs gRPC) and a complete interview preparation section with frameworks, templates, and practice questions.

---

## Key Takeaways

- **Start with fundamentals:** requirements, trade-offs, and scalability principles are the foundation of every system design decision.
- **Distributed systems theory drives architecture:** CAP theorem, consistency models, and replication strategies determine how systems behave under failure and scale.
- **Infrastructure choices are trade-offs:** SQL vs NoSQL, caching strategies, and messaging patterns each introduce specific strengths and operational costs.
- **Patterns exist because problems repeat:** load balancing, circuit breakers, retries, and backpressure solve the same categories of failure across different systems.
- **Case studies connect theory to practice:** designing a URL shortener, a chat application, or a video platform requires combining concepts from every preceding section.
- **Interview preparation is structured practice:** a repeatable framework, capacity estimation, and architectural templates turn knowledge into clear, structured interview answers.
