# Common Interview Questions

## Beginner

**Q1. What's the difference between horizontal and vertical scaling?**
Vertical scaling means a bigger instance (more CPU/RAM), with a hard ceiling. Horizontal scaling means more instances running in parallel, requiring the application to be stateless.

**Q2. What is exponential backoff, and why add jitter to it?**
Backoff increases the wait time between retries to avoid overwhelming a struggling service. Jitter adds randomness so many clients don't all retry at the exact same synchronized moments (thundering herd).

**Q3. What problem does a message queue solve between two services?**
It decouples them — the producer doesn't need the consumer to be available at that instant, and it absorbs traffic bursts so the consumer processes at a sustainable rate (queue-based load leveling).

**Q4. What's the difference between Multi-AZ and Multi-Region?**
Multi-AZ protects against a single data center-level failure within one Region. Multi-Region protects against an entire Region-level event, at significantly higher cost and complexity.

**Q5. Why does idempotency matter for retries?**
Because retrying a non-idempotent operation (like a payment charge) can cause duplicate side effects if the first attempt actually succeeded but the response was lost before the caller saw it.

## Intermediate

**Q6. Explain the circuit breaker pattern and how it differs from a retry.**
A retry handles a single transient failure. A circuit breaker detects a *persistently* unhealthy dependency and stops sending requests to it entirely for a cooldown period, to avoid piling load onto something that's already struggling and to let the caller fail fast instead of hanging.

**Q7. What is the Saga pattern, and why is it needed in microservices?**
A way to manage a multi-step business transaction that spans multiple services (each with its own database), using compensating transactions to undo completed steps if a later step fails — since no single ACID transaction can span multiple independent databases.

**Q8. What's the difference between choreography and orchestration in a Saga?**
Choreography: each service reacts to events from the previous step, with no central coordinator. Orchestration: a central coordinator (e.g., Step Functions) explicitly calls each step and handles failure/compensation logic itself.

**Q9. What is CQRS, and what problem does it solve?**
Separating the write model from the read model so each can be optimized independently — useful when read and write access patterns, or scaling needs, genuinely diverge. Introduces eventual consistency between the two sides.

**Q10. When would you choose Pilot Light over Warm Standby for disaster recovery?**
When the business can tolerate a longer RTO (tens of minutes rather than minutes) in exchange for meaningfully lower standing infrastructure cost — Pilot Light only keeps a minimal core (often just data replication) running, scaling up the rest only when a failover is actually triggered.

## Senior / Advanced

**Q11. How would you design a system to prevent cascading failure across microservices?**
Combine circuit breakers (stop calling an unhealthy dependency), bulkheads (isolate resource pools per dependency so one slow dependency can't starve calls to an unrelated one), timeouts on every network call, and async/queue-based decoupling wherever a synchronous dependency chain can be avoided.

**Q12. What's the risk of using DLQs without monitoring them?**
Failed messages get isolated from the healthy queue (good), but if nobody monitors DLQ depth, real bugs or data-quality issues can go undetected indefinitely — a DLQ prevents blocking, it doesn't prevent silent data loss on its own.

**Q13. Explain the trade-off between eventual consistency and strong consistency in a distributed system.**
Strong consistency guarantees every read sees the latest write, but typically requires more coordination (and therefore latency, and often reduced availability during partitions). Eventual consistency allows temporary staleness in exchange for higher availability and lower latency — the right choice depends on whether the specific data can tolerate being briefly stale (e.g., a "likes" counter usually can; an account balance often can't).

**Q14. How do you decide whether a given interaction between two services should be synchronous or asynchronous?**
Ask whether the caller genuinely needs the result before it can proceed (synchronous — e.g., authentication), or whether it just needs to know the request was accepted and can continue without waiting for the outcome (asynchronous — e.g., triggering an email). Availability requirements matter too: sync calls couple the caller's availability to the callee's.

**Q15. What's wrong with a "redundant" architecture that still has a single point of failure?**
Redundancy has to be verified end-to-end, not assumed from a diagram — a system can have multiple AZs, instances, and load balancers, and still funnel everything through one un-replicated NAT gateway, one self-managed database with no standby, or one hardcoded dependency that quietly breaks the whole redundancy story during the exact failure it was meant to survive.
