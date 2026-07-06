# Reliability Patterns

Reliability in cloud architecture is the ability of a system to recover from failures, dynamically scale to meet demand, and continue operating correctly even when individual components break. AWS defines reliability as one of the six pillars of the Well-Architected Framework — and for good reason. In distributed systems, failure is not a possibility; it is an inevitability. Hardware degrades, networks partition, deployments introduce bugs, and dependencies go offline.

Reliability patterns are proven architectural strategies that help you design systems that **withstand**, **detect**, and **recover** from failures automatically. The goal is not to prevent every failure, but to ensure that no single failure cascades into a system-wide outage. A reliable system on AWS combines redundancy across Availability Zones, self-healing infrastructure, stateless compute, idempotent operations, and graceful degradation — all orchestrated through services designed for fault tolerance from the ground up.

This document covers the foundational reliability patterns every backend engineer should understand when building production systems on AWS.

---

## Multi-AZ Deployments

An **Availability Zone (AZ)** is one or more discrete data centers within an AWS Region, each with redundant power, networking, and connectivity. AZs within a region are connected through low-latency links but are physically separated enough to isolate failures like power outages, floods, or network disruptions.

Multi-AZ deployment is the **baseline reliability pattern** on AWS. By distributing resources across multiple AZs, you eliminate single points of failure at the data center level.

### How AZs Work

```text
                         AWS Region (us-east-1)
  ┌──────────────────────────────────────────────────────────┐
  │                                                          │
  │   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
  │   │    AZ-1a      │  │    AZ-1b      │  │    AZ-1c      │  │
  │   │              │  │              │  │              │  │
  │   │  ┌────────┐  │  │  ┌────────┐  │  │  ┌────────┐  │  │
  │   │  │ EC2    │  │  │  │ EC2    │  │  │  │ EC2    │  │  │
  │   │  │Instance│  │  │  │Instance│  │  │  │Instance│  │  │
  │   │  └────────┘  │  │  └────────┘  │  │  └────────┘  │  │
  │   │  ┌────────┐  │  │  ┌────────┐  │  │              │  │
  │   │  │RDS     │  │  │  │RDS     │  │  │              │  │
  │   │  │Primary │──│──│─▶│Standby │  │  │              │  │
  │   │  └────────┘  │  │  └────────┘  │  │              │  │
  │   └──────────────┘  └──────────────┘  └──────────────┘  │
  │                                                          │
  │            ┌──────────────────────┐                      │
  │            │   ALB (Cross-AZ)    │                      │
  │            └──────────────────────┘                      │
  └──────────────────────────────────────────────────────────┘
```

### Services with Multi-AZ Support

| Service | Multi-AZ Behavior | Failover Mechanism |
|---|---|---|
| **RDS** | Synchronous replication to standby in another AZ | Automatic DNS failover (~60-120s) |
| **ElastiCache (Redis)** | Replica nodes in different AZs | Automatic failover with Redis cluster mode |
| **ELB (ALB/NLB)** | Distributes traffic across registered AZs | Automatic; unhealthy AZ targets drained |
| **EFS** | Data stored redundantly across multiple AZs | Transparent to application |
| **Aurora** | Storage layer spans 3 AZs with 6 copies of data | Failover to read replica in ~30s |
| **DynamoDB** | Data replicated across 3 AZs automatically | Fully managed, transparent |

### Key Considerations

* Always deploy across **at least 2 AZs**, preferably 3, for production workloads
* Enable **cross-zone load balancing** on your ALB to distribute traffic evenly
* RDS Multi-AZ is for **high availability**, not read scaling — use Read Replicas for that
* Multi-AZ does **not protect** against region-level failures; that requires Multi-Region

---

## Multi-Region Deployments

Multi-Region architecture distributes your application across two or more AWS Regions to protect against region-level failures and to reduce latency for geographically dispersed users. This is the highest level of redundancy AWS offers but comes with significant complexity and cost.

### When to Go Multi-Region

* Regulatory requirements mandate data residency in specific geographies
* Business requires **RPO near zero** and **RTO under minutes**
* Users are distributed globally and need low-latency access
* The cost of downtime exceeds the cost of running in multiple regions

### Active-Active vs Active-Passive

```text
  Active-Active                          Active-Passive
  ──────────────                         ───────────────

  ┌────────────┐    ┌────────────┐       ┌────────────┐    ┌────────────┐
  │ Region A   │    │ Region B   │       │ Region A   │    │ Region B   │
  │            │    │            │       │ (Primary)  │    │ (Standby)  │
  │ ┌────────┐ │    │ ┌────────┐ │       │            │    │            │
  │ │  App   │◀├────├▶│  App   │ │       │ ┌────────┐ │    │ ┌────────┐ │
  │ └────────┘ │    │ └────────┘ │       │ │  App   │ │    │ │  App   │ │
  │ ┌────────┐ │    │ ┌────────┐ │       │ │ Active │ │    │ │  Idle  │ │
  │ │  DB    │◀├────├▶│  DB    │ │       │ └────────┘ │    │ └────────┘ │
  │ │ (R/W)  │ │    │ │ (R/W)  │ │       │ ┌────────┐ │    │ ┌────────┐ │
  │ └────────┘ │    │ └────────┘ │       │ │  DB    │─├────├▶│  DB    │ │
  └────────────┘    └────────────┘       │ │Primary │ │    │ │Replica │ │
                                         │ └────────┘ │    │ └────────┘ │
  Route 53: Latency/Weighted             └────────────┘    └────────────┘
  Data: Bi-directional replication
                                         Route 53: Failover routing
                                         Data: Async replication
```

### Data Replication Strategies

| Strategy | Service | Consistency | Lag |
|---|---|---|---|
| **DynamoDB Global Tables** | DynamoDB | Eventually consistent across regions | Typically < 1s |
| **Aurora Global Database** | Aurora | Async replication | Typically < 1s |
| **S3 Cross-Region Replication** | S3 | Eventually consistent | Minutes |
| **ElastiCache Global Datastore** | ElastiCache Redis | Async replication | Sub-second |

* Active-active requires careful handling of **write conflicts** — use last-writer-wins, CRDTs, or application-level conflict resolution
* Active-passive is simpler but wastes standby resources and has higher RTO
* Use **Route 53 health checks** with failover routing to automate region switchover

---

## Auto-Healing with Auto Scaling

Auto Scaling Groups (ASGs) are not just for scaling — they are a **core reliability mechanism**. When an instance becomes unhealthy, the ASG automatically terminates it and launches a replacement, maintaining your desired capacity without human intervention.

### How ASG Auto-Healing Works

```text
  ┌─────────────────────────────────────────────────┐
  │              Auto Scaling Group                  │
  │         Desired: 3  |  Min: 2  |  Max: 6        │
  │                                                 │
  │  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
  │  │Instance A│  │Instance B│  │Instance C│      │
  │  │ Healthy  │  │ Healthy  │  │Unhealthy │      │
  │  └──────────┘  └──────────┘  └─────┬────┘      │
  │                                     │           │
  │                              ┌──────▼────┐      │
  │                              │ Terminated│      │
  │                              └──────┬────┘      │
  │                                     │           │
  │                              ┌──────▼────┐      │
  │                              │Instance D │      │
  │                              │  Healthy  │      │
  │                              └───────────┘      │
  └─────────────────────────────────────────────────┘
```

### Health Check Types

| Health Check | Source | What It Checks | Default |
|---|---|---|---|
| **EC2** | EC2 status checks | Hardware/hypervisor-level failures | Enabled by default |
| **ELB** | ALB/NLB target health | Application-level health endpoint | Must be explicitly enabled |
| **Custom** | External monitoring | Any application-specific condition | Via API calls |

### Best Practices

* Always configure **ELB health checks** on your ASG — EC2 checks alone miss application-level failures
* Set an appropriate **health check grace period** (e.g., 300s) so new instances have time to bootstrap before being evaluated
* Configure **cooldown periods** to prevent rapid scaling oscillation (default: 300s for simple scaling)
* Use **launch templates** over launch configurations for versioning and flexibility
* Combine with **lifecycle hooks** to run initialization scripts before an instance enters service

---

## Health Checks and Self-Recovery

Health checks are the **nervous system** of a reliable architecture. Without them, failures go undetected and cascading outages become inevitable.

### ELB Health Checks

* ALB performs HTTP/HTTPS health checks against a configurable path (e.g., `/health`)
* Configurable parameters: **interval** (default 30s), **timeout** (5s), **unhealthy threshold** (2), **healthy threshold** (5)
* Unhealthy targets are automatically removed from the target group — no traffic is sent to them
* Design health endpoints to check **real dependencies** (database connectivity, cache availability), not just return `200 OK`

### Route 53 Health Checks

* Monitor endpoint availability from multiple global locations
* Support HTTP, HTTPS, and TCP checks
* Can be configured with **calculated health checks** that aggregate multiple child checks
* Integrate with **failover routing** to redirect DNS to a healthy region or backup endpoint
* CloudWatch alarms can be triggered by health check status changes

### Self-Healing Pattern

```text
  ┌──────────┐     Health Check Fails     ┌───────────────┐
  │          │ ─────────────────────────▶  │  CloudWatch   │
  │  Target  │                            │    Alarm      │
  │          │                            └───────┬───────┘
  └──────────┘                                    │
                                                  ▼
                                          ┌───────────────┐
                                          │   SNS Topic   │
                                          └───────┬───────┘
                                                  │
                                    ┌─────────────┼─────────────┐
                                    ▼             ▼             ▼
                             ┌───────────┐ ┌───────────┐ ┌───────────┐
                             │  Lambda   │ │  SSM      │ │  Notify   │
                             │ Remediate │ │ RunCommand│ │  On-call  │
                             └───────────┘ └───────────┘ └───────────┘
```

* Use **SSM Automation** runbooks to restart services, reboot instances, or rotate credentials automatically
* Implement **cascading health checks**: unhealthy dependencies should propagate to the parent service's health status
* Avoid health check endpoints that are computationally expensive — they should be lightweight and fast

---

## Circuit Breaker Pattern

The Circuit Breaker pattern prevents a service from repeatedly calling a failing dependency, which would waste resources and potentially cascade the failure. It is modeled after electrical circuit breakers that trip to prevent overload.

### States

```text
                    Success
                  ┌─────────┐
                  │         │
                  ▼         │
            ┌───────────┐   │
    ───────▶│  CLOSED   │───┘
            │(Normal Op)│
            └─────┬─────┘
                  │
                  │ Failure threshold exceeded
                  ▼
            ┌───────────┐
            │   OPEN    │
            │(Fail Fast)│──── All requests immediately fail
            └─────┬─────┘     (return fallback / error)
                  │
                  │ Timeout expires
                  ▼
            ┌───────────┐
            │ HALF-OPEN │
            │(Test Req) │──── Allow limited test requests
            └─────┬─────┘
                  │
           ┌──────┴──────┐
           │             │
       Success        Failure
           │             │
           ▼             ▼
      ┌─────────┐  ┌─────────┐
      │ CLOSED  │  │  OPEN   │
      └─────────┘  └─────────┘
```

### AWS Implementation

* **AWS App Mesh** with Envoy proxy supports circuit breaking at the service mesh level — configure outlier detection to eject unhealthy endpoints
* **API Gateway** can be combined with Lambda to implement circuit breaker logic using DynamoDB to store circuit state
* **Step Functions** can model circuit breaker workflows with Wait states and choice states
* Use **DynamoDB** or **ElastiCache** to persist circuit state (failure counts, timestamps, current state) across distributed instances

### Configuration Parameters

| Parameter | Description | Typical Value |
|---|---|---|
| **Failure Threshold** | Number of failures before opening | 5 |
| **Success Threshold** | Successes in half-open before closing | 3 |
| **Timeout** | Time before transitioning open → half-open | 30-60 seconds |
| **Monitoring Window** | Time window for counting failures | 60 seconds |

---

## Bulkhead Pattern

The Bulkhead pattern isolates components so that a failure in one does not sink the entire system — just like watertight compartments in a ship prevent a single hull breach from flooding the whole vessel.

### Isolation Strategies

```text
  Without Bulkheads                With Bulkheads
  ──────────────────               ─────────────────

  ┌────────────────────┐           ┌────────────────────┐
  │   Shared Thread    │           │  ┌──────────────┐  │
  │       Pool         │           │  │ Pool: Svc A  │  │
  │                    │           │  │ (10 threads)  │  │
  │  Svc A ████████    │           │  └──────────────┘  │
  │  Svc B ████████    │           │  ┌──────────────┐  │
  │  Svc C ████████    │           │  │ Pool: Svc B  │  │
  │                    │           │  │ (10 threads)  │  │
  │  Svc A overwhelms  │           │  └──────────────┘  │
  │  pool → B & C fail │           │  ┌──────────────┐  │
  └────────────────────┘           │  │ Pool: Svc C  │  │
                                   │  │ (10 threads)  │  │
                                   │  └──────────────┘  │
                                   │                    │
                                   │  Svc A failure     │
                                   │  isolated → B & C  │
                                   │  unaffected        │
                                   └────────────────────┘
```

### AWS Bulkhead Implementations

* **Separate AWS accounts** per environment (dev/staging/prod) and per team using AWS Organizations
* **VPC isolation** — place different services in separate VPCs with controlled peering
* **Separate SQS queues** per consumer type so a slow consumer doesn't block others
* **Per-service DynamoDB tables** rather than a shared table, preventing hot partition impacts from crossing service boundaries
* **ALB target groups** — route different traffic types to isolated target groups
* **Lambda concurrency reservations** — set reserved concurrency per function to prevent one function from consuming all account-level concurrency

### Levels of Bulkhead Isolation

| Level | Mechanism | Blast Radius |
|---|---|---|
| **Thread-level** | Separate thread/connection pools | Within a process |
| **Process-level** | Separate containers/tasks per service | Within a host |
| **Infrastructure-level** | Separate VPCs, accounts, or regions | Within AWS |

---

## Stateless Design

A stateless service stores **no client session data** on the compute instance itself. Every request contains all the information needed to process it, or the service fetches state from an external store. This is critical for reliability because any instance can handle any request — if one instance dies, another picks up seamlessly.

### Why Stateless Matters for Reliability

* Instances can be **terminated and replaced** without losing user sessions
* Auto Scaling can add or remove instances freely without session pinning
* Load balancers can distribute requests to **any healthy target**
* Deployments become trivial — roll out new instances and drain old ones

### Externalizing State

```text
  ┌──────────┐       ┌──────────┐       ┌──────────┐
  │ EC2 / ECS│       │ EC2 / ECS│       │ EC2 / ECS│
  │ Instance │       │ Instance │       │ Instance │
  │ (No local│       │ (No local│       │ (No local│
  │  state)  │       │  state)  │       │  state)  │
  └────┬─────┘       └────┬─────┘       └────┬─────┘
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
       ┌───────────┐ ┌──────────┐ ┌─────────┐
       │ElastiCache│ │ DynamoDB │ │   S3    │
       │ (Sessions)│ │ (State)  │ │ (Files) │
       └───────────┘ └──────────┘ └─────────┘
```

### Where to Externalize What

| State Type | Recommended Store | Reason |
|---|---|---|
| **User sessions** | ElastiCache Redis | Sub-millisecond reads, TTL support |
| **Shopping carts / temp data** | DynamoDB | Durable, auto-scaling, single-digit ms latency |
| **File uploads** | S3 | Virtually unlimited storage, 11 9s durability |
| **Distributed locks** | DynamoDB / ElastiCache | Conditional writes or Redis SETNX |
| **Configuration** | SSM Parameter Store / AppConfig | Centralized, versioned, encrypted |

---

## Idempotency

An operation is **idempotent** if performing it multiple times produces the same result as performing it once. This is critical in distributed systems where network failures, retries, and duplicate message delivery are common.

### Why Idempotency Matters

* SQS delivers messages **at least once** — your processor may receive duplicates
* API clients may retry on timeout, sending the same request multiple times
* Lambda may execute the same event more than once in failure scenarios
* Step Functions may retry failed states, re-executing the same operation

### Idempotency Keys

The standard pattern is for the client to include a unique **idempotency key** (e.g., UUID) with each request. The server checks if this key has been seen before:

* **First time**: Process the request, store the key and result
* **Subsequent times**: Return the stored result without reprocessing

### DynamoDB Conditional Writes

```text
  Client ──▶ PUT /orders
              {
                "idempotencyKey": "abc-123",
                "amount": 99.99
              }

  Server ──▶ DynamoDB PutItem
              ConditionExpression:
                "attribute_not_exists(idempotencyKey)"

              ┌─────────────────────┐
              │ Key exists?         │
              │                     │
              │ NO  → Write item,   │
              │       process order │
              │                     │
              │ YES → Return cached │
              │       response      │
              └─────────────────────┘
```

### Implementation Patterns

| Approach | Service | Use Case |
|---|---|---|
| **Conditional PutItem** | DynamoDB | Prevent duplicate writes |
| **Powertools Idempotency** | Lambda Powertools | Decorator-based idempotency for Lambda |
| **Deduplication ID** | SQS FIFO | Message-level deduplication (5-min window) |
| **Event ID tracking** | DynamoDB + Lambda | Track processed event IDs with TTL cleanup |

* Set a **TTL** on idempotency records to prevent unbounded storage growth (e.g., 24 hours)
* Store the **response** alongside the idempotency key so retried requests return identical results

---

## Graceful Degradation

Graceful degradation ensures that when parts of a system fail, the user experience degrades smoothly rather than collapsing entirely. Instead of a complete outage, users get a reduced but functional experience.

### Fallback Strategies

* **Cached responses**: Serve stale data from ElastiCache when the primary database is unavailable
* **Default values**: Return sensible defaults when a personalization service is down
* **Feature disabling**: Turn off non-critical features (recommendations, analytics) to preserve core functionality
* **Static fallback pages**: Serve a pre-rendered static page from S3/CloudFront when the application is completely unavailable

### Feature Flags

Use **AWS AppConfig** or **LaunchDarkly** to control feature availability at runtime without deployments:

* Instantly disable a feature that is causing errors
* Gradually roll out a feature to a percentage of users
* Kill-switch non-essential features during peak load

### Queue-Based Load Leveling

```text
  High Traffic Burst              Queue Absorbs Burst
  ──────────────────              ────────────────────

  Clients ═══════╗               Clients ═══════╗
                 ║                                ║
                 ▼                                ▼
          ┌─────────────┐                 ┌─────────────┐
          │ Application │                 │  SQS Queue  │
          │   Server    │ ← overwhelmed   │  (Buffer)   │
          │   (OOM)     │                 └──────┬──────┘
          └─────────────┘                        │
                                          Steady drain
                                                 │
                                          ┌──────▼──────┐
                                          │   Workers   │
                                          │ (At their   │
                                          │  own pace)  │
                                          └─────────────┘
```

* Use **SQS** to decouple producers from consumers — the queue absorbs traffic spikes
* Configure **dead-letter queues** for messages that fail repeatedly
* Set appropriate **visibility timeouts** and **maxReceiveCount** before messages land in the DLQ

---

## Chaos Engineering on AWS

Chaos engineering is the practice of **deliberately injecting failures** into production systems to verify that they can withstand real-world disruptions. It shifts reliability from hope to evidence.

### AWS Fault Injection Simulator (FIS)

AWS FIS is a managed chaos engineering service that lets you run controlled experiments against your AWS workloads:

* **Stop/terminate EC2 instances** to test auto-healing
* **Throttle API calls** to simulate AWS service degradation
* **Inject latency** into network traffic
* **Fail over RDS** instances to test Multi-AZ recovery
* **Drain ECS tasks** to test container rescheduling
* **Disrupt AZ connectivity** to test Multi-AZ resilience

### Principles of Chaos Engineering

* **Start small**: Begin with non-production environments, then graduate to production
* **Define steady state**: Know what "normal" looks like before injecting failures
* **Hypothesize**: Predict what should happen before running the experiment
* **Minimize blast radius**: Use guardrails (stop conditions) to halt experiments if impact exceeds expectations
* **Automate**: Run chaos experiments as part of CI/CD pipelines

### Example Experiments

| Experiment | What It Tests | Expected Outcome |
|---|---|---|
| Terminate 1 of 3 EC2 instances | ASG auto-healing | New instance launches, traffic redistributes |
| Fail over RDS primary | Multi-AZ database resilience | Standby promoted, app reconnects in < 120s |
| Inject 500ms latency to a dependency | Circuit breaker / timeout config | Circuit opens, fallback response served |
| Kill an entire AZ | Cross-AZ redundancy | Traffic shifts to remaining AZs, no user impact |
| Throttle DynamoDB reads | Retry and backoff logic | Exponential backoff kicks in, no data loss |

---

## Reliability Patterns Comparison Table

| Pattern | Problem Solved | AWS Services | Complexity |
|---|---|---|---|
| **Multi-AZ** | Data center failure | RDS, ElastiCache, ALB, Aurora, EFS | Low |
| **Multi-Region** | Region-level failure, global latency | Route 53, DynamoDB Global Tables, Aurora Global | High |
| **Auto-Healing** | Instance failure, capacity maintenance | ASG, EC2, ECS, EKS | Low |
| **Health Checks** | Detecting failures automatically | ELB, Route 53, CloudWatch | Low |
| **Circuit Breaker** | Cascading failures from bad dependencies | App Mesh, API Gateway, Lambda, DynamoDB | Medium |
| **Bulkhead** | Failure isolation, blast radius reduction | VPCs, Accounts, SQS, Lambda concurrency | Medium |
| **Stateless Design** | Instance replacement, scaling flexibility | ElastiCache, DynamoDB, S3 | Low |
| **Idempotency** | Duplicate processing from retries | DynamoDB, SQS FIFO, Lambda Powertools | Medium |
| **Graceful Degradation** | Partial outages, overload situations | SQS, AppConfig, CloudFront, ElastiCache | Medium |
| **Chaos Engineering** | Unverified reliability assumptions | AWS FIS, CloudWatch | Medium |

---

## Key Takeaways

* **Multi-AZ is non-negotiable** for production workloads — it is low-cost, low-complexity, and eliminates the most common failure mode (single data center outage)
* **Stateless compute is a prerequisite** for effective auto-healing and scaling — externalize all state to purpose-built stores like ElastiCache, DynamoDB, and S3
* **Health checks must be application-aware** — an EC2 status check passing while your application is deadlocked is a false positive that delays recovery
* **Idempotency is not optional** in distributed systems — every write operation should be safe to retry without side effects
* **Circuit breakers and bulkheads protect against cascading failures** — without them, a single dependency outage can take down your entire platform
* **Graceful degradation preserves user trust** — serving partial functionality is always better than a complete outage
* **Chaos engineering proves your reliability patterns work** — AWS FIS lets you validate your architecture under controlled failure conditions
* **Multi-Region adds tremendous complexity** — only adopt it when your RPO/RTO requirements or regulatory constraints demand it
* **Design for failure at every layer**: compute should be replaceable, data should be replicated, and dependencies should be dispensable

---

## Interview Questions

### 1. How does an Auto Scaling Group detect and replace unhealthy instances? What health check types are available?

An ASG can use three types of health checks. **EC2 health checks** (default) monitor hardware and hypervisor-level issues via EC2 status checks — if the underlying host or network is impaired, the instance is marked unhealthy. **ELB health checks** perform application-level HTTP checks against a specified endpoint; this catches scenarios where the OS is running but the application has crashed or is deadlocked. **Custom health checks** allow external systems to call the `SetInstanceHealth` API to programmatically flag instances. When an instance is marked unhealthy, the ASG terminates it and launches a replacement to maintain the desired capacity. The **health check grace period** is crucial — it prevents the ASG from terminating instances that are still bootstrapping. Best practice is to always enable ELB health checks in addition to EC2 checks, because EC2 checks alone cannot detect application-layer failures.

### 2. Explain the Circuit Breaker pattern. How would you implement it for a microservice on AWS?

The Circuit Breaker pattern has three states. In the **Closed** state, requests flow normally and failures are counted. When failures exceed a threshold within a time window, the circuit transitions to **Open**, where all requests immediately fail fast without calling the downstream service — this prevents resource exhaustion and gives the failing service time to recover. After a configured timeout, the circuit moves to **Half-Open**, allowing a limited number of test requests through. If these succeed, the circuit closes; if they fail, it reopens. On AWS, you can implement this using **AWS App Mesh** with Envoy sidecar proxies that support outlier detection and circuit breaking natively. Alternatively, for Lambda-based architectures, you can store circuit state (failure counts, current state, last state change timestamp) in **DynamoDB** with conditional updates, and use **Lambda Powertools** middleware to check circuit state before making downstream calls. The key configuration parameters are failure threshold, recovery timeout, and the monitoring window for counting failures.

### 3. What is the difference between active-active and active-passive Multi-Region architectures? When would you choose each?

**Active-active** runs full application stacks in multiple regions simultaneously, with both regions serving production traffic. Route 53 uses latency-based or weighted routing to direct users to the nearest region. The challenge is data consistency — you need bidirectional replication (e.g., DynamoDB Global Tables) and a strategy for handling write conflicts. **Active-passive** designates one region as primary (handling all traffic) and another as standby (receiving replicated data but not serving traffic). On failure, Route 53 failover routing switches DNS to the standby region. Active-passive is simpler and cheaper but has higher RTO because the standby needs to warm up. Choose active-active when you need near-zero RTO, serve a global user base, or need to minimize latency for all users. Choose active-passive when your users are concentrated in one geography, your RTO requirements allow for minutes of switchover time, or when the complexity of conflict resolution outweighs the reliability benefit.

### 4. Why is idempotency critical in distributed systems, and how do you implement it with DynamoDB?

In distributed systems, exactly-once delivery is practically impossible. Network timeouts cause clients to retry, SQS provides at-least-once delivery, and Lambda may process events more than once. Without idempotency, these retries can cause duplicate charges, double-booked orders, or inconsistent state. The implementation pattern uses an **idempotency key** — a unique identifier (UUID) sent by the client with each request. The server uses a **DynamoDB conditional write** (`attribute_not_exists(idempotencyKey)`) when processing the request. If the key doesn't exist, the item is written and the operation proceeds. If the key already exists, the condition fails, and the server returns the previously stored result. The idempotency records should have a **TTL** (e.g., 24 hours) to prevent unbounded table growth. For Lambda functions, **Lambda Powertools** provides a built-in idempotency decorator that handles key generation, state storage, and expiry automatically using DynamoDB as the persistence layer.

### 5. How would you design a system that gracefully degrades under partial failure rather than going completely offline?

Graceful degradation requires identifying which features are **essential** vs **non-essential** and building fallback paths for each dependency. First, classify services into tiers: Tier 1 (checkout, authentication) must always work; Tier 2 (recommendations, analytics) can be disabled. Implement **feature flags** using AWS AppConfig to instantly toggle non-critical features without deploying code. For data dependencies, serve **cached responses from ElastiCache** when the primary database is slow or unavailable — stale data is better than no data. Use **SQS for load leveling** — instead of processing requests synchronously under high load, enqueue them and process at a sustainable rate. Configure **circuit breakers** on all external dependencies so that a failing service doesn't block the critical path. Set up **static fallback pages in S3/CloudFront** as the last resort — if the entire application is down, users see a maintenance page rather than a connection error. Finally, practice these failure modes with **AWS FIS** so you know the system behaves as designed when real incidents occur.
