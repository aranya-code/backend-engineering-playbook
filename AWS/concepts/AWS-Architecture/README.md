# AWS Architecture

Cross-cutting architectural patterns and principles for designing resilient, scalable systems on AWS — distinct from single-service deep dives elsewhere in this repo. 20-part series.

---

## 🏛️ Foundation

| # | Topic | Description |
|---|-------|-------------|
| 01 | [Introduction](01-%20Introduction.md) | What this folder covers, and how architecture judgment differs from service knowledge |
| 02 | [The AWS Well-Architected Framework](02-%20The%20AWS%20Well-Architected%20Framework.md) | The six pillars, and why every real decision trades them against each other |

## 🛡️ Resilience

| # | Topic | Description |
|---|-------|-------------|
| 03 | [Retries, Backoff and Jitter](03-%20Resilience%20Patterns%20-%20Retries%2C%20Backoff%20and%20Jitter.md) | Exponential backoff, jitter strategies, and why idempotency is the prerequisite for safe retries |
| 04 | [Circuit Breaker and Bulkhead](04-%20Resilience%20Patterns%20-%20Circuit%20Breaker%20and%20Bulkhead.md) | Stopping cascading failure and isolating resource pools per dependency |
| 05 | [Dead Letter Queues and Failure Isolation](05-%20Resilience%20Patterns%20-%20Dead%20Letter%20Queues%20and%20Failure%20Isolation.md) | Isolating poison messages, plus cell-based architecture for blast-radius containment |

## 📈 Scalability

| # | Topic | Description |
|---|-------|-------------|
| 06 | [Horizontal Scaling and Auto Scaling](06-%20Scalability%20Patterns%20-%20Horizontal%20Scaling%20and%20Auto%20Scaling.md) | Vertical vs. horizontal scaling, and why scaling isn't instant |
| 07 | [Caching Strategies](07-%20Scalability%20Patterns%20-%20Caching%20Strategies.md) | Cache-aside, write-through, write-behind, and invalidation trade-offs |
| 08 | [Database Scaling](08-%20Scalability%20Patterns%20-%20Database%20Scaling.md) | Read replicas, connection pooling, and sharding |

## 🔌 Decoupling

| # | Topic | Description |
|---|-------|-------------|
| 09 | [Event-Driven Architecture and Queue-Based Load Leveling](09-%20Decoupling%20Patterns%20-%20Event-Driven%20Architecture%20and%20Queue-Based%20Load%20Leveling.md) | Breaking synchronous coupling, and absorbing traffic bursts with queues |
| 10 | [Pub/Sub and Fan-Out](10-%20Decoupling%20Patterns%20-%20Pub-Sub%20and%20Fan-Out.md) | The SNS + SQS fan-out pattern, and why it beats direct push |

## 🔀 Distributed Data

| # | Topic | Description |
|---|-------|-------------|
| 11 | [The Saga Pattern](11-%20Distributed%20Transactions%20-%20The%20Saga%20Pattern.md) | Multi-step transactions across services via compensating transactions |
| 12 | [CQRS and Event Sourcing](12-%20Data%20Architecture%20Patterns%20-%20CQRS%20and%20Event%20Sourcing.md) | Separating read/write models, and storing state as a sequence of events |

## 🌍 Availability

| # | Topic | Description |
|---|-------|-------------|
| 13 | [Multi-AZ vs Multi-Region](13-%20High%20Availability%20-%20Multi-AZ%20vs%20Multi-Region.md) | What each actually protects against, and why multi-region is a much bigger step |
| 14 | [Disaster Recovery Strategies](14-%20Disaster%20Recovery%20Strategies.md) | The four DR tiers — Backup & Restore through Multi-Site Active-Active |

## 🧱 System Style

| # | Topic | Description |
|---|-------|-------------|
| 15 | [Microservices Architecture on AWS](15-%20Microservices%20Architecture%20on%20AWS.md) | What microservices cost as well as buy, and the data-ownership rule that keeps them honest |
| 16 | [Serverless Architecture Patterns and Trade-offs](16-%20Serverless%20Architecture%20Patterns%20and%20Trade-offs.md) | Cold starts, connection limits, and when serverless is (and isn't) the right fit |

## 🎯 Judgment & Reference

| # | Topic | Description |
|---|-------|-------------|
| 17 | [Common Architecture Anti-Patterns](17-%20Common%20Architecture%20Anti-Patterns.md) | The distributed monolith, chatty services, and other reasonable-looking mistakes |
| 18 | [Architecture Decision Records](18-%20Architecture%20Decision%20Records.md) | Documenting *why* a decision was made, with a minimal ADR template |
| 19 | [Real-World Reference Architectures](19-%20Real-World%20Reference%20Architectures.md) | Six composite architectures showing these patterns combined |
| 20 | [Common Interview Questions](20-%20Common%20Interview%20Questions.md) | Beginner through senior-level Q&A |

---

## 🔗 See Also

- [`../`](../) — AWS concepts overview
- [`../../README.md`](../../README.md) — full AWS knowledge base
- [`../AWS-Security`](../AWS-Security) — security-specific architecture concerns (kept separate from this folder)

---

*Part of the [backend-engineering-playbook](../../../) knowledge base — Aranya Majumdar*
