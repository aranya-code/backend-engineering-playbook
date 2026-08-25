# README

## Overview

This section contains AWS architecture interview questions designed to develop practical system design and architecture reasoning for backend engineering roles.

The focus is not on memorizing AWS services. Questions are organized around the engineering decisions expected from a senior backend engineer: scalability, availability, resilience, security, data architecture, distributed communication, observability, disaster recovery, and operational trade-offs.

The material assumes familiarity with backend development, REST APIs, databases, Docker, CI/CD, and core AWS services.

---

## Interview Focus

AWS architecture interviews typically evaluate your ability to:

- Translate business requirements into technical requirements.
- Estimate traffic, storage, throughput, and capacity.
- Select appropriate AWS services based on workload characteristics.
- Design highly available and fault-tolerant systems.
- Scale applications horizontally.
- Identify and eliminate architectural bottlenecks.
- Design reliable data storage and access patterns.
- Handle synchronous and asynchronous communication.
- Design for partial failure and dependency outages.
- Apply security and least-privilege principles.
- Design observability into distributed systems.
- Plan disaster recovery using RTO and RPO.
- Explain architectural trade-offs clearly.
- Defend design decisions under changing requirements.

---

## Quick Navigation

| Topic | Description |
|---|---|
| [Common Architecture Interview Questions](./01-%20Common%20Architecture%20Interview%20Questions.md) | Core AWS architecture questions covering scalability, HA, microservices, caching, databases, messaging, security, observability, DR, and system design trade-offs |

---

## Question Categories

### Architecture Fundamentals

Focus on:

- Requirements gathering.
- Functional and non-functional requirements.
- High-level architecture.
- Component boundaries.
- Service selection.
- Data flow.
- Dependency analysis.
- Architectural trade-offs.

Typical questions:

- How would you design a highly available API?
- How would you choose between EC2, ECS, EKS, and Lambda?
- How would you design a scalable backend?
- How would you identify the first bottleneck?

---

### Scalability

Focus on:

- Horizontal scaling.
- Vertical scaling.
- Auto Scaling.
- Load balancing.
- Caching.
- Database scaling.
- Queue-based buffering.
- Read replicas.
- Partitioning.
- Global traffic distribution.

Important interview reasoning:

```text
Traffic Growth
     ↓
Application Capacity
     ↓
Database Capacity
     ↓
Cache Capacity
     ↓
Network Capacity
     ↓
External Dependency Limits
```

Scaling the application layer alone does not guarantee that the complete system can scale.

---

### High Availability

Focus on:

- Availability Zones.
- Multi-AZ architecture.
- Load balancing.
- Redundant compute.
- Managed database failover.
- Health checks.
- Failure detection.
- Capacity during failure.

A strong HA design asks:

> What happens when one component or failure domain disappears?

---

### Disaster Recovery

Focus on:

- Backups.
- Replication.
- RTO.
- RPO.
- Backup and restore.
- Pilot light.
- Warm standby.
- Active-passive.
- Active-active.
- Multi-region architectures.
- Recovery testing.

The key architectural distinction is:

```text
High Availability
→ Reduce impact of failures during normal operation

Disaster Recovery
→ Restore service after a major failure
```

---

### Microservices

Focus on:

- Service boundaries.
- Data ownership.
- REST.
- gRPC.
- Event-driven communication.
- SQS.
- Kafka.
- Service discovery.
- Failure isolation.
- Distributed tracing.
- Idempotency.
- Eventual consistency.

Do not equate microservices with simply deploying many containers.

The important architectural concerns are **ownership, coupling, independent scaling, deployment boundaries, and failure isolation**.

---

### Serverless

Focus on:

- Lambda.
- API-driven workloads.
- Event-driven processing.
- S3 events.
- Queues.
- Event buses.
- Asynchronous workflows.
- Scaling behavior.
- Cold starts.
- Execution limits.
- Cost characteristics.

Interview discussions should include when serverless is a poor fit rather than presenting it as a universal architecture.

---

### Data Architecture

Focus on:

- PostgreSQL.
- Managed relational databases.
- Read replicas.
- Caching.
- Redis.
- NoSQL.
- DynamoDB.
- Object storage.
- Database partitioning.
- Data ownership.
- Consistency models.
- Backup and recovery.

The correct database choice should follow:

```text
Access Patterns
      +
Consistency Requirements
      +
Scale
      +
Transaction Requirements
      +
Operational Constraints
```

---

### Messaging and Event-Driven Systems

Focus on:

- SQS.
- SNS.
- EventBridge.
- Kafka.
- Asynchronous workers.
- Celery.
- Dead-letter queues.
- Retry policies.
- Consumer scaling.
- Ordering.
- Duplicate delivery.
- Idempotency.
- Event schema evolution.

Important questions include:

- What happens if a consumer fails?
- What happens if messages are duplicated?
- What happens when the queue grows faster than consumers can process?
- How do you replay events?
- How do you prevent poison messages from repeatedly failing?

---

### Caching

Focus on:

- Redis.
- CDN caching.
- Application caching.
- Cache-aside.
- TTLs.
- Invalidation.
- Cache stampedes.
- Cache eviction.
- Cache failures.
- Consistency.

A strong answer should always discuss:

```text
What is cached?
Who owns the source of truth?
How long is it valid?
How is it invalidated?
What happens when the cache fails?
```

---

### Security

Focus on:

- IAM.
- IAM roles.
- Least privilege.
- Security groups.
- Private subnets.
- TLS.
- Encryption at rest.
- Encryption in transit.
- Secrets management.
- Authentication.
- Authorization.
- Network segmentation.
- Audit logging.

Avoid treating a VPC as a complete security boundary.

Application authorization and identity controls remain necessary even when services communicate through private networking.

---

### Reliability and Failure Handling

Focus on:

- Timeouts.
- Retries.
- Exponential backoff.
- Jitter.
- Circuit breakers.
- Bulkheads.
- Rate limiting.
- Backpressure.
- Graceful degradation.
- Idempotency.
- Failure isolation.

A useful failure model is:

```text
Dependency Failure
       ↓
Timeout
       ↓
Bounded Retry
       ↓
Circuit Breaker
       ↓
Fallback / Degradation
       ↓
Recovery
```

---

### Observability

Focus on:

- Metrics.
- Logs.
- Distributed traces.
- Correlation IDs.
- CloudWatch.
- Application-level telemetry.
- Error rates.
- Latency.
- Throughput.
- Saturation.
- Queue depth.
- Database connections.

A production architecture should make it possible to answer:

> What failed, where did it fail, why did it fail, and what was affected?

---

### Deployment and Operations

Focus on:

- CI/CD.
- Rolling deployments.
- Blue-green deployments.
- Canary releases.
- Health checks.
- Automated rollback.
- Infrastructure as Code.
- Database migrations.
- Configuration management.
- Secrets management.
- Operational runbooks.

A deployment strategy should account for both application and database compatibility.

---

## Recommended Interview Answer Structure

For open-ended AWS architecture questions, use the following sequence:

```text
Requirements
    ↓
Scale Estimation
    ↓
High-Level Architecture
    ↓
Data Architecture
    ↓
Communication
    ↓
Scalability
    ↓
Availability
    ↓
Failure Handling
    ↓
Security
    ↓
Observability
    ↓
Disaster Recovery
    ↓
Cost
    ↓
Trade-offs
```

Do not begin by listing AWS services.

Start by clarifying:

- Expected traffic.
- Read/write ratio.
- Latency requirements.
- Availability requirements.
- Data consistency requirements.
- Data volume.
- Geographic distribution.
- Security requirements.
- Recovery requirements.
- Budget or operational constraints.

---

## Architecture Reasoning Framework

For every major component, be able to explain:

| Question | Engineering Concern |
|---|---|
| Why is it needed? | Architectural purpose |
| Why this service? | Technology selection |
| What happens under load? | Scalability |
| What happens when it fails? | Resilience |
| What happens when a dependency fails? | Failure propagation |
| How is it secured? | Security |
| How is it monitored? | Observability |
| How is it recovered? | Disaster recovery |
| How much does it cost? | Economics |
| What are the alternatives? | Trade-offs |

This prevents service-name-driven architecture.

---

## Senior-Level Interview Signals

A strong answer should naturally discuss:

- Bottlenecks.
- Failure domains.
- Capacity planning.
- Connection limits.
- Backpressure.
- Idempotency.
- Eventual consistency.
- Data ownership.
- Retry storms.
- Cascading failures.
- Graceful degradation.
- p95/p99 latency.
- RTO and RPO.
- Security boundaries.
- Operational complexity.
- Cost trade-offs.

The ability to say **"it depends on the workload" and then explain exactly what it depends on** is an important senior-level architecture skill.

---

## Common Interview Mistakes

| Mistake | Better Approach |
|---|---|
| Listing AWS services immediately | Establish requirements first |
| Using Kubernetes for every problem | Match orchestration to workload and operational needs |
| Assuming Multi-AZ means zero downtime | Analyze dependencies and failure capacity |
| Scaling only application servers | Identify the actual system bottleneck |
| Ignoring database connection limits | Treat databases as finite-capacity dependencies |
| Using infinite retries | Use bounded retries with backoff and jitter |
| Ignoring idempotency | Design retry-safe operations |
| Treating Redis as durable storage | Define the actual source of truth |
| Recommending multi-region automatically | Justify regional redundancy using RTO/RPO |
| Ignoring observability | Design metrics, logs, and traces from the beginning |
| Ignoring cost | Include operational and infrastructure economics |
| Giving only one architecture | Explain alternatives and trade-offs |

---

## Practice Strategy

For each architecture question:

1. Clarify requirements.
2. Estimate scale.
3. Draw the simplest viable architecture.
4. Explain the request and data flow.
5. Identify the first bottleneck.
6. Add scalability mechanisms.
7. Introduce high availability.
8. Analyze component failures.
9. Add security controls.
10. Add observability.
11. Define disaster recovery.
12. Explain cost and trade-offs.

Then challenge your own design:

```text
What if traffic increases 10x?
What if one AZ fails?
What if the database becomes unavailable?
What if Redis fails?
What if an external API becomes slow?
What if messages are duplicated?
What if the queue grows rapidly?
What if a deployment fails?
What if an entire AWS Region becomes unavailable?
What would I change to reduce cost?
```

---

## Files

### Common Architecture Interview Questions

**[01- Common Architecture Interview Questions.md](./01-%20Common%20Architecture%20Interview%20Questions.md)**

Core interview reference covering:

- Highly available APIs.
- Microservices.
- REST vs gRPC.
- Synchronous vs asynchronous communication.
- Traffic spikes.
- Database bottlenecks.
- Redis and caching.
- Failure handling.
- Multi-AZ architecture.
- Multi-region architecture.
- Disaster recovery.
- Event-driven architecture.
- Idempotency.
- Duplicate messages.
- Cascading failures.
- AWS security.
- Observability.
- Zero-downtime deployment.
- Background processing.
- Large-scale system design.
- Multi-tenant architecture.
- Database migrations.
- Rapid-fire interview questions.
- Senior-level follow-up questions.

---

## Key Takeaways

- **AWS architecture interviews are primarily reasoning exercises:** requirements, constraints, failure modes, trade-offs, and operational consequences matter more than service memorization.
- **Organize answers systematically:** requirements → scale → architecture → data → scalability → availability → security → observability → disaster recovery → cost.
- **Think in failure domains and bottlenecks:** every critical component should have an explicit scaling strategy and failure-handling strategy.
- **Senior-level answers discuss trade-offs:** avoid presenting Multi-AZ, multi-region, microservices, Kubernetes, caching, or serverless as universally correct solutions.
- **Practice challenging your own architecture:** introduce traffic growth, dependency failures, data corruption, deployment failures, and regional outages to expose weaknesses in the design.