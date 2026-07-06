# High Availability Patterns

High Availability (HA) is the ability of a system to remain operational and accessible for a very high percentage of time, minimizing unplanned downtime. In production environments, HA is not optional — it is a contractual obligation codified in Service Level Agreements (SLAs) and measured in "nines" of uptime.

Availability is calculated as:

```
Availability % = (Total Time - Downtime) / Total Time × 100
```

AWS provides the building blocks for HA — Multi-AZ deployments, cross-region replication, health checks, and automated failover — but **you** are responsible for architecting them correctly. A single EC2 instance is not highly available. A managed service with Multi-AZ enabled is the baseline.

**Core HA Principles:**

* **Eliminate single points of failure** — every component must have a redundant counterpart
* **Automate failure detection and recovery** — human intervention is too slow
* **Test failover regularly** — untested failover is not failover, it is hope
* **Design for graceful degradation** — partial functionality beats total outage
* **Use multiple Availability Zones as the minimum** — a single AZ is a single failure domain

---

## Availability Tiers

Availability is expressed in "nines." Each additional nine dramatically reduces the acceptable downtime window and exponentially increases architecture complexity and cost.

| Availability | Common Name     | Downtime/Year | Downtime/Month | Downtime/Week | Typical Use Case                  |
|-------------|-----------------|---------------|----------------|---------------|-----------------------------------|
| 99.9%       | Three Nines     | 8h 45m 36s    | 43m 12s        | 10m 4.8s      | Internal tools, dev environments  |
| 99.95%      | Three and a Half| 4h 22m 48s    | 21m 36s        | 5m 2.4s       | Standard SaaS applications        |
| 99.99%      | Four Nines      | 52m 33.6s     | 4m 19.2s       | 6.05s         | E-commerce, financial platforms   |
| 99.999%     | Five Nines      | 5m 15.4s      | 25.9s          | 0.6s          | Healthcare, emergency services    |

**Key Insight:** Moving from 99.9% to 99.99% means reducing your annual downtime budget from ~8.75 hours to ~52 minutes. This requires multi-region architectures, automated failover, and zero-downtime deployments.

**AWS SLA Examples:**

* EC2 SLA: 99.99% for Multi-AZ deployment
* RDS Multi-AZ SLA: 99.95%
* S3 SLA: 99.9% (designed for 99.999999999% durability)
* DynamoDB SLA: 99.999% for Global Tables
* Route 53 SLA: 100%

---

## Active-Active Architecture

In an active-active architecture, **all regions or nodes actively serve traffic simultaneously**. There is no idle standby — every component processes requests in real time. This delivers the highest availability and lowest latency but introduces significant data synchronization complexity.

```text
                         ┌──────────────────┐
                         │  Global Accelerator│
                         │  / Route 53       │
                         └────────┬─────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
            ┌───────▼───────┐           ┌───────▼───────┐
            │  US-EAST-1    │           │  EU-WEST-1    │
            │               │           │               │
            │ ┌───────────┐ │           │ ┌───────────┐ │
            │ │    ALB     │ │           │ │    ALB     │ │
            │ └─────┬─────┘ │           │ └─────┬─────┘ │
            │       │       │           │       │       │
            │ ┌─────▼─────┐ │           │ ┌─────▼─────┐ │
            │ │  App Tier  │ │           │ │  App Tier  │ │
            │ │ (ASG + ECS)│ │           │ │ (ASG + ECS)│ │
            │ └─────┬─────┘ │           │ └─────┬─────┘ │
            │       │       │           │       │       │
            │ ┌─────▼─────┐ │           │ ┌─────▼─────┐ │
            │ │  Database  │◄├───────────├►│  Database  │ │
            │ │ (DynamoDB  │ │  Bi-Dir   │ │ (DynamoDB  │ │
            │ │  Global)   │ │  Repl.    │ │  Global)   │ │
            │ └───────────┘ │           │ └───────────┘ │
            └───────────────┘           └───────────────┘
```

**How It Works:**

* Traffic is distributed across regions using **Route 53 latency-based routing** or **Global Accelerator**
* Each region has a fully independent application stack (ALB → compute → database)
* Data is replicated bi-directionally between regions using DynamoDB Global Tables, Aurora Global Database, or application-level replication
* If one region fails, the other absorbs 100% of traffic with zero manual intervention

**Data Synchronization Challenges:**

* **Conflict resolution** — simultaneous writes to the same record in two regions require a conflict strategy (last-writer-wins, vector clocks, CRDTs)
* **Replication lag** — even milliseconds of lag can cause stale reads
* **Eventual consistency** — clients may read data that has not yet replicated
* **Cross-region latency** — replication adds 50-150ms depending on distance

**When to Use Active-Active:**

* Global user bases requiring low latency
* Systems requiring near-zero RTO
* Applications where availability trumps strict consistency

---

## Active-Passive Architecture

In an active-passive setup, one region handles all traffic while the secondary region remains on warm or hot standby. Failover occurs only when the primary region becomes unhealthy.

```text
                         ┌──────────────────┐
                         │   Route 53        │
                         │ (Failover Policy) │
                         └────────┬─────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │ (Primary)                 │ (Secondary - Standby)
            ┌───────▼───────┐           ┌───────▼───────┐
            │  US-EAST-1    │           │  US-WEST-2    │
            │  [ACTIVE]     │           │  [PASSIVE]    │
            │               │           │               │
            │ ┌───────────┐ │           │ ┌───────────┐ │
            │ │    ALB     │ │           │ │    ALB     │ │
            │ └─────┬─────┘ │           │ └─────┬─────┘ │
            │       │       │           │       │       │
            │ ┌─────▼─────┐ │           │ ┌─────▼─────┐ │
            │ │  App Tier  │ │           │ │  App Tier  │ │
            │ │ (Full Cap.)│ │           │ │ (Min Cap.) │ │
            │ └─────┬─────┘ │           │ └─────┬─────┘ │
            │       │       │           │       │       │
            │ ┌─────▼─────┐ │    Async  │ ┌─────▼─────┐ │
            │ │  Primary   │├───────────►│ │  Read      │ │
            │ │  Database  │ │   Repl.   │ │  Replica   │ │
            │ └───────────┘ │           │ └───────────┘ │
            └───────────────┘           └───────────────┘
```

**Failover Mechanisms:**

* **Route 53 health checks** detect primary region failure and update DNS to point to secondary
* **DNS TTL** determines how quickly clients pick up the change (60s TTL is common)
* **Promotion** of read replica to primary database (manual or automated)
* **ASG scaling** in the passive region from minimum to full capacity

**Standby Strategies:**

| Strategy      | Passive State               | RTO      | Cost      |
|--------------|----------------------------|----------|-----------|
| Pilot Light  | Minimal infrastructure running | 15-30 min | Low       |
| Warm Standby | Scaled-down but functional  | 5-15 min | Medium    |
| Hot Standby  | Full capacity, ready to serve | 1-5 min  | High      |

**RTO Implications:**

* Pilot light requires infrastructure provisioning and database promotion — RTO is 15-30 minutes
* Warm standby requires only scaling and DNS failover — RTO is 5-15 minutes
* Hot standby requires only DNS failover — RTO is 1-5 minutes (limited by DNS TTL)

---

## Multi-AZ Database Failover

Multi-AZ is the foundation of database HA on AWS. Each service implements it differently, but the principle is the same: maintain a synchronized replica in a separate Availability Zone and failover automatically.

### RDS Multi-AZ

* **Synchronous replication** to a standby instance in a different AZ
* Automatic failover triggered by: AZ outage, primary instance failure, OS patching, or manual reboot with failover
* Failover completes in **60-120 seconds** — DNS endpoint remains the same
* The standby is **not readable** — it exists purely for failover
* Supported engines: MySQL, PostgreSQL, MariaDB, Oracle, SQL Server

### Aurora Multi-AZ

* Uses a **shared distributed storage layer** replicated 6 ways across 3 AZs
* Up to **15 read replicas** that can be promoted to primary in under 30 seconds
* Storage is independent of compute — a compute failure does not affect data
* **Aurora Serverless v2** scales automatically and maintains Multi-AZ availability
* Failover priority is configurable via replica tiers (0-15)

### DynamoDB Global Tables

* **Multi-region, multi-active** replication out of the box
* All replicas are readable and writable
* Replication latency is typically **under 1 second**
* Uses last-writer-wins conflict resolution based on timestamps
* No application changes required — SDK handles routing

### ElastiCache Replication

* **Redis:** Multi-AZ with automatic failover via Redis replication groups; 1 primary + up to 5 read replicas
* **Memcached:** No native replication — HA requires client-side sharding and application-level redundancy
* Redis Global Datastore provides cross-region replication with sub-second latency

---

## Cross-Region Failover

Cross-region architectures protect against region-level failures. AWS regions are physically isolated, so a regional outage (rare but possible) requires pre-provisioned resources in another region.

### Route 53 Failover Routing

* Define primary and secondary records with failover routing policy
* Associate health checks with the primary record
* When primary health check fails, Route 53 automatically routes to secondary
* DNS propagation depends on TTL — lower TTL means faster failover but more DNS queries

### S3 Cross-Region Replication (CRR)

* Asynchronous replication of objects from source to destination bucket
* Replication is at the object level — existing objects require a one-time batch replication
* Supports replication of delete markers (optional) and encryption
* Replication time control (RTC) guarantees 99.99% of objects replicated within 15 minutes

### RDS Cross-Region Read Replicas

* Asynchronous replication to a read replica in another region
* Read replica can be promoted to standalone primary during failover
* **Promotion breaks the replication link** — it is a one-way operation
* After promotion, you must re-establish replication manually
* Replication lag varies from seconds to minutes depending on write load

### Aurora Global Database

* Dedicated replication infrastructure with **under 1 second** typical lag
* Up to **5 secondary regions**, each with up to 16 read replicas
* Managed cross-region failover with RPO of ~1 second and RTO under 1 minute
* Supports **write forwarding** — secondary regions can forward writes to the primary
* Switchover vs. failover: switchover is planned (zero data loss), failover is unplanned (potential RPO > 0)

---

## Load Balancer Health Checks

Health checks are the automated detection mechanism that determines whether a target is capable of receiving traffic. Misconfigured health checks cause either false positives (unhealthy targets receive traffic) or false negatives (healthy targets are removed from rotation).

### ALB Health Checks

* HTTP/HTTPS health checks against a configurable path (e.g., `/health`)
* Checks evaluate HTTP status codes — default success is **200**
* Configurable matcher for custom success codes (e.g., `200-299`)
* Unhealthy targets are removed from the target group and stop receiving traffic
* Re-added to rotation after passing consecutive healthy checks

### NLB Health Checks

* TCP, HTTP, or HTTPS health checks
* TCP checks only verify connection establishment — no application-level validation
* For production, prefer HTTP health checks that validate application readiness
* NLB preserves client IP — health check source IPs come from the NLB nodes

### Health Check Configuration

| Parameter           | Description                                    | Recommended Value     |
|--------------------|------------------------------------------------|-----------------------|
| Interval           | Time between health checks                     | 10-30 seconds         |
| Healthy Threshold  | Consecutive successes to mark healthy          | 2-3                   |
| Unhealthy Threshold| Consecutive failures to mark unhealthy         | 2-3                   |
| Timeout            | Time to wait for a health check response       | 5-10 seconds          |
| Path (HTTP)        | Endpoint to check                              | `/health` or `/ready` |
| Success Codes      | HTTP status codes indicating health            | `200` or `200-299`    |

**Best Practices:**

* Use a **dedicated health check endpoint** that validates downstream dependencies (database, cache, queues)
* Implement **shallow checks** (`/health`) for load balancer routing and **deep checks** (`/ready`) for deployment readiness
* Set timeout < interval to avoid overlapping health checks
* Use separate health check endpoints for different concerns (liveness vs. readiness)

---

## Route 53 Failover

Route 53 is AWS's DNS service and serves as the global traffic director for HA architectures. Its failover routing policy is the most common mechanism for cross-region failover.

### Failover Routing Policy

* Create two record sets: **primary** and **secondary** with the same domain name
* Associate an active health check with the primary record
* When the primary health check fails, Route 53 responds with the secondary record
* Supports both alias records (to AWS resources) and non-alias records (to IP addresses)

### Health Check Integration

* **Endpoint health checks** — Route 53 sends requests to your endpoint from multiple global locations
* **Calculated health checks** — combine multiple child health checks with AND/OR logic
* **CloudWatch alarm health checks** — integrate with CloudWatch metrics for custom failure detection
* Health checks run from **multiple global locations** — a check is considered failed when a configurable percentage of checkers report failure

### DNS TTL Considerations

* **Lower TTL** (e.g., 60s) enables faster failover but increases DNS query volume and cost
* **Higher TTL** (e.g., 300s) reduces DNS query costs but delays failover
* Clients may cache DNS beyond TTL — Java's default DNS cache is **30 seconds** but some applications cache indefinitely
* During failover events, **some clients will still hit the failed region** until their cached DNS record expires
* Recommended: set TTL to **60 seconds** for failover records as a balance between speed and cost

```text
    ┌─────────────┐     DNS Query     ┌─────────────────┐
    │   Client    ├──────────────────►│   Route 53      │
    └──────┬──────┘                   │                 │
           │                          │  Health Check   │
           │                          │  ┌──────────┐   │
           │                          │  │ Primary  │──►│ Healthy? → Return Primary IP
           │                          │  │  Check   │   │ Unhealthy? → Return Secondary IP
           │                          │  └──────────┘   │
           │                          └─────────────────┘
           │
           ▼
    ┌──────────────┐  (if primary)   ┌──────────────┐
    │  Region A    │                 │  Region B    │
    │  (Primary)   │                 │  (Secondary) │
    └──────────────┘  (if failover)  └──────────────┘
```

---

## Stateless vs Stateful HA

The single greatest enabler of high availability is **statelessness**. A stateless application treats every request independently — no server holds data that cannot be obtained elsewhere. This allows any instance to handle any request, making scaling and failover trivial.

### Challenges of Stateful Applications

* **Server affinity** — users are tied to specific instances, creating single points of failure
* **Failover data loss** — when a stateful instance dies, in-memory sessions are lost
* **Scaling friction** — adding or removing instances disrupts session state
* **Deployment complexity** — rolling deployments must drain sessions before terminating instances

### Sticky Sessions Problems

* ALB sticky sessions use cookies to route a user to the same target
* If that target fails, the session is **lost** — the user is routed to a new target with no context
* Sticky sessions create **uneven load distribution** — some instances accumulate more sessions
* They prevent effective auto-scaling — the ASG cannot freely distribute new connections
* **Rule of thumb:** if you need sticky sessions, you have a design problem

### Externalizing State

Move all session and application state out of the application tier into dedicated, highly available storage:

```text
    ┌──────────────────────────────────────────┐
    │              Stateless App Tier           │
    │                                          │
    │  ┌──────┐   ┌──────┐   ┌──────┐         │
    │  │ EC2  │   │ EC2  │   │ EC2  │         │
    │  │  A   │   │  B   │   │  C   │         │
    │  └──┬───┘   └──┬───┘   └──┬───┘         │
    │     │          │          │              │
    └─────┼──────────┼──────────┼──────────────┘
          │          │          │
          ▼          ▼          ▼
    ┌─────────────────────────────────────┐
    │        External State Stores        │
    │                                     │
    │  ┌────────────┐  ┌───────────────┐  │
    │  │ ElastiCache│  │   DynamoDB    │  │
    │  │  (Redis)   │  │ (Session Tbl) │  │
    │  └────────────┘  └───────────────┘  │
    │                                     │
    │  ┌────────────┐  ┌───────────────┐  │
    │  │    S3      │  │    RDS        │  │
    │  │ (Assets)   │  │ (User Data)   │  │
    │  └────────────┘  └───────────────┘  │
    └─────────────────────────────────────┘
```

---

## Session Management

Externalizing session state requires choosing the right storage backend based on your access patterns, latency requirements, and durability needs.

### ElastiCache (Redis)

* **Sub-millisecond latency** — ideal for session data accessed on every request
* Native TTL support for automatic session expiration
* Multi-AZ with automatic failover via replication groups
* Data structures (hashes, sorted sets) simplify complex session models
* **Risk:** Redis is in-memory — a full cluster failure loses all sessions unless persistence (AOF/RDB) is enabled

### DynamoDB

* **Single-digit millisecond latency** with on-demand or provisioned capacity
* Built-in TTL for automatic session cleanup — no background jobs needed
* Multi-region support via Global Tables for globally distributed sessions
* Fully managed — no patching, scaling, or failover configuration
* **Best for:** applications that need durable sessions with predictable performance

### Cookie-Based Sessions

* Session data is stored **entirely in the client cookie** — no server-side storage
* Signed and encrypted cookies prevent tampering
* **Advantages:** zero server-side state, infinite horizontal scalability
* **Limitations:** cookie size limit (~4KB), sensitive data must never be stored client-side
* **Best for:** small session payloads (user ID, preferences, CSRF tokens)

| Approach     | Latency        | Durability   | Max Size    | Cost         | Use Case                    |
|-------------|----------------|-------------|-------------|-------------|----------------------------|
| ElastiCache | Sub-millisecond| Low (in-mem) | Unlimited*  | Medium       | High-throughput web apps    |
| DynamoDB    | Single-digit ms| High         | 400 KB/item | Pay-per-use  | Durable, distributed apps   |
| Cookies     | Zero (client)  | Client-side  | ~4 KB       | Free         | Small, non-sensitive data    |

---

## HA Comparison Table

| Strategy            | RTO          | Availability Target | Cost    | Complexity | Data Loss Risk |
|--------------------|-------------|--------------------|---------|-----------|--------------------|
| Single AZ          | Hours       | ~99%               | Lowest  | None       | High               |
| Multi-AZ           | 1-2 min     | 99.95%             | 2x base | Low        | None (sync repl.)  |
| Pilot Light        | 15-30 min   | 99.9%              | Low     | Medium     | Minutes of data    |
| Warm Standby       | 5-15 min    | 99.95%             | Medium  | Medium     | Seconds of data    |
| Hot Standby        | 1-5 min     | 99.99%             | High    | High       | Seconds of data    |
| Active-Active      | ~0 (auto)   | 99.99-99.999%      | 2x+     | Very High  | Conflict possible  |

**Cost vs. Availability Trade-off:**

* Every additional nine of availability roughly **doubles or triples** your infrastructure cost
* Multi-AZ is the **minimum acceptable baseline** for any production workload
* Active-active is reserved for workloads where even minutes of downtime have severe business impact
* Most production applications target **99.95% to 99.99%** as the practical sweet spot

---

## HA Architecture Diagram

A complete high availability architecture combining all patterns discussed:

```text
                              ┌──────────────────────┐
                              │      Route 53         │
                              │  (Failover + Latency) │
                              └──────────┬───────────┘
                                         │
                        ┌────────────────┴────────────────┐
                        │                                 │
              ┌─────────▼─────────┐             ┌─────────▼─────────┐
              │   PRIMARY REGION  │             │  SECONDARY REGION │
              │   (us-east-1)     │             │  (eu-west-1)      │
              │                   │             │                   │
              │  ┌─────────────┐  │             │  ┌─────────────┐  │
              │  │  CloudFront │  │             │  │  CloudFront │  │
              │  └──────┬──────┘  │             │  └──────┬──────┘  │
              │         │         │             │         │         │
              │  ┌──────▼──────┐  │             │  ┌──────▼──────┐  │
              │  │     WAF     │  │             │  │     WAF     │  │
              │  └──────┬──────┘  │             │  └──────┬──────┘  │
              │         │         │             │         │         │
              │  ┌──────▼──────┐  │             │  ┌──────▼──────┐  │
              │  │     ALB     │  │             │  │     ALB     │  │
              │  │  (Multi-AZ) │  │             │  │  (Multi-AZ) │  │
              │  └──────┬──────┘  │             │  └──────┬──────┘  │
              │    ┌────┴────┐    │             │    ┌────┴────┐    │
              │    │         │    │             │    │         │    │
              │ ┌──▼──┐  ┌──▼──┐ │             │ ┌──▼──┐  ┌──▼──┐ │
              │ │AZ-1a│  │AZ-1b│ │             │ │AZ-1a│  │AZ-1b│ │
              │ │ ASG │  │ ASG │ │             │ │ ASG │  │ ASG │ │
              │ └──┬──┘  └──┬──┘ │             │ └──┬──┘  └──┬──┘ │
              │    └────┬───┘    │             │    └────┬───┘    │
              │         │        │             │         │        │
              │  ┌──────▼──────┐ │             │  ┌──────▼──────┐ │
              │  │   Aurora    │ │   Async     │  │   Aurora    │ │
              │  │  (Primary)  │─├─────────────├─►│  (Replica)  │ │
              │  │  Multi-AZ   │ │   Repl.     │  │  Multi-AZ   │ │
              │  └──────┬──────┘ │             │  └─────────────┘ │
              │         │        │             │                   │
              │  ┌──────▼──────┐ │             │  ┌─────────────┐ │
              │  │ ElastiCache │ │             │  │ ElastiCache │ │
              │  │   (Redis)   │ │             │  │   (Redis)   │ │
              │  └─────────────┘ │             │  └─────────────┘ │
              │                   │             │                   │
              │  ┌─────────────┐ │   S3 CRR    │  ┌─────────────┐ │
              │  │   S3        │─├─────────────├─►│   S3        │ │
              │  │ (Assets)    │ │             │  │ (Assets)    │ │
              │  └─────────────┘ │             │  └─────────────┘ │
              └───────────────────┘             └───────────────────┘
```

**Architecture Notes:**

* Route 53 uses a **combination of failover and latency-based routing** — primary region for writes, latency-based for reads
* CloudFront provides edge caching to reduce origin load and improve perceived availability
* WAF protects against DDoS and application-layer attacks that could cause downtime
* ALB spans multiple AZs within each region — a single AZ failure is transparent to users
* Aurora Global Database provides cross-region replication with sub-second lag
* ElastiCache handles session state and caching independently in each region
* S3 CRR ensures static assets and backups are available in the secondary region

---

## Key Takeaways

* **Multi-AZ is the baseline** — any production workload without Multi-AZ deployment is accepting unnecessary risk
* **Statelessness is the foundation of HA** — externalize all state to purpose-built stores (ElastiCache, DynamoDB, S3)
* **Automate everything** — manual failover has an RTO measured in hours; automated failover is measured in seconds
* **DNS TTL matters** — set failover record TTLs to 60 seconds; test that your client applications respect TTL
* **Test your failover** — schedule regular chaos engineering exercises (AWS Fault Injection Simulator) to validate your recovery procedures
* **Choose the right tier** — not every application needs 99.999%; over-engineering HA wastes budget that could fund other reliability investments
* **Active-active is not always better** — the data synchronization complexity of active-active can introduce more failures than it prevents if not implemented correctly
* **Health checks are your early warning system** — invest in deep health checks that validate real application readiness, not just TCP connectivity
* **Cost scales with nines** — budget for the availability tier your business actually requires, and document the trade-offs

---

## Interview Questions

### 1. How would you design a multi-region active-passive failover architecture on AWS? What is the expected RTO?

**Answer:** The architecture uses Route 53 failover routing policy with health checks on the primary region. The primary region runs the full application stack (ALB → ASG → Aurora Primary → ElastiCache). The secondary region runs a warm standby with scaled-down ASG instances and an Aurora cross-region read replica.

When Route 53 health checks detect the primary is unhealthy, DNS failover routes traffic to the secondary region. The Aurora read replica is promoted to a standalone primary. ASG scales up to full capacity.

Expected RTO is **5-15 minutes** for warm standby — driven by DNS TTL propagation (60s), Aurora promotion (~30s), and ASG scaling (2-5 minutes). RPO depends on Aurora replication lag, typically under 1 second. To reduce RTO further, use a hot standby (full capacity in both regions) which brings RTO to **1-5 minutes**, limited primarily by DNS TTL.

### 2. What are the trade-offs between active-active and active-passive architectures?

**Answer:** Active-active provides near-zero RTO because both regions are already serving traffic — failover is simply removing one region from the routing pool. However, it introduces **data consistency challenges** — bidirectional replication can lead to write conflicts that require resolution strategies (last-writer-wins, application-level merging). Active-active also costs approximately 2x because both regions run at full capacity.

Active-passive is simpler — unidirectional replication eliminates write conflicts, and the passive region runs at reduced capacity to save cost. The trade-off is higher RTO (5-30 minutes depending on standby strategy) and potential data loss equal to the replication lag at the time of failure.

**Decision criteria:** Choose active-active when your SLA demands 99.99%+ availability and your data model tolerates eventual consistency. Choose active-passive when your SLA allows 99.95% and you need strong consistency guarantees.

### 3. Why are sticky sessions considered an anti-pattern for highly available systems?

**Answer:** Sticky sessions create server affinity — a user's requests are always routed to the same backend instance. This creates several HA problems:

First, if the sticky instance fails, the session is **completely lost** — the user is redirected to a new instance with no session context, typically forcing re-authentication. Second, sticky sessions cause **uneven load distribution** because sessions are not rebalanced when new instances are added via auto-scaling. Third, during **rolling deployments**, instances with active sticky sessions cannot be terminated until sessions drain or expire, slowing deployment velocity.

The solution is to externalize session state to ElastiCache (Redis) or DynamoDB. Every instance reads session data from the shared store on each request, making all instances interchangeable. Any instance can serve any user, and instance failures are transparent to the user.

### 4. How do Route 53 health checks work, and what are the DNS TTL implications for failover speed?

**Answer:** Route 53 health checks send requests to your endpoint from multiple global health checker locations (approximately 15+ worldwide). A health check is considered failed when a configurable threshold of checkers (default: 3 out of the health checking regions) report failure. This prevents false positives from regional network issues.

Health checks run every **10 or 30 seconds** (configurable). With fast health checks (10s interval) and 3 failure threshold, detection takes approximately **30 seconds**.

DNS TTL is the critical factor in failover speed. When Route 53 detects failure and updates the DNS record, existing clients continue using their cached DNS response until the TTL expires. With a 60-second TTL, the worst case is 60 seconds of additional traffic to the failed region after Route 53 has already switched. Some DNS resolvers and applications cache beyond the stated TTL — Java's `InetAddress` caches for 30 seconds by default, but some libraries cache indefinitely, which must be addressed at the application level with `networkaddress.cache.ttl` JVM settings.

### 5. Explain the differences between RDS Multi-AZ, Aurora Multi-AZ, and DynamoDB Global Tables for high availability.

**Answer:** These represent three different approaches to database HA:

**RDS Multi-AZ** uses **synchronous block-level replication** to a standby instance in another AZ. The standby is not readable — it exists only for failover. Failover takes 60-120 seconds and the DNS endpoint remains unchanged. This provides HA within a single region only.

**Aurora Multi-AZ** uses a fundamentally different architecture — a **shared distributed storage layer** replicated 6 ways across 3 AZs. Compute and storage are decoupled, so a compute failure does not risk data. Up to 15 read replicas can serve read traffic and any can be promoted to primary in under 30 seconds. Aurora Global Database extends this cross-region with dedicated replication infrastructure achieving sub-second lag.

**DynamoDB Global Tables** provide **multi-region, multi-active** replication. Every replica is both readable and writable, with automatic conflict resolution using last-writer-wins timestamps. Replication latency is typically under 1 second. This is the only option among the three that provides active-active multi-region capability out of the box, but it requires accepting eventual consistency and its conflict resolution model.

**Summary:** RDS Multi-AZ is the simplest (single-region HA). Aurora offers the best balance of HA, performance, and read scalability. DynamoDB Global Tables provide the highest availability tier with multi-region active-active, at the cost of eventual consistency.
