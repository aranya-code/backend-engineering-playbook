# Scalability Patterns

Scalability is the ability of a system to handle increased load by adding resources — without degrading performance or requiring architectural redesign. On AWS, scalability is not a single toggle; it is a combination of architectural patterns, managed services, and automation policies that work together to absorb traffic spikes, sustain steady growth, and optimize cost during low-demand periods.

A well-scaled system maintains consistent latency, throughput, and availability as demand fluctuates from 10 users to 10 million. AWS provides scaling primitives at every layer — compute, storage, database, networking — and the engineering challenge is choosing the right pattern for each component.

---

## Horizontal vs Vertical Scaling

**Vertical Scaling (Scale Up)** means increasing the capacity of a single instance — more CPU, more RAM, larger disk. You move from a `t3.medium` to an `r6i.4xlarge`. It is simple but has a hard ceiling: there is a largest instance type, and scaling requires downtime for non-live-migratable workloads.

**Horizontal Scaling (Scale Out)** means adding more instances of the same size behind a load balancer. It has no theoretical ceiling and provides fault tolerance — losing one instance does not take down the service.

```text
Vertical Scaling                    Horizontal Scaling

┌─────────────┐                    ┌──────────┐
│             │                    │ Instance │
│  BIGGER     │                    │    A     │
│  INSTANCE   │                    └────┬─────┘
│             │                         │
│  CPU: 64    │              ┌──────────┼──────────┐
│  RAM: 256GB │              │          │          │
│             │         ┌────┴───┐ ┌────┴───┐ ┌────┴───┐
│             │         │ Inst B │ │ Inst C │ │ Inst D │
└─────────────┘         └────────┘ └────────┘ └────────┘
                        Each: CPU 4, RAM 16GB
  Single point            Distributed across
  of failure              multiple nodes
```

### Comparison Table

| Aspect               | Vertical Scaling            | Horizontal Scaling              |
|-----------------------|-----------------------------|---------------------------------|
| **Mechanism**         | Bigger instance             | More instances                  |
| **Downtime**          | Usually required            | Zero downtime                   |
| **Cost curve**        | Exponential (larger = $$)   | Linear (add more = $)           |
| **Fault tolerance**   | None (single node)          | Built-in (N-1 survival)         |
| **Complexity**        | Low                         | Higher (state, sessions, LB)    |
| **Ceiling**           | Largest instance type       | Virtually unlimited             |
| **State management**  | Easy (local state)          | Requires externalized state     |
| **Best for**          | Databases, legacy apps      | Stateless services, web tiers   |

**Production guidance:** Default to horizontal scaling for application tiers. Use vertical scaling only for workloads that cannot be distributed (e.g., single-leader databases, license-locked software). Always externalize session state to ElastiCache or DynamoDB before scaling out.

---

## Auto Scaling Groups (ASG)

Auto Scaling Groups are the core mechanism for horizontal scaling of EC2 instances. An ASG maintains a fleet of instances, replaces unhealthy ones, and adjusts capacity based on scaling policies. Every ASG has three critical parameters:

* **Minimum capacity** — the floor; the ASG never scales below this
* **Desired capacity** — the current target; ASG launches or terminates to match
* **Maximum capacity** — the ceiling; the ASG never scales above this

```text
ASG Lifecycle:

  Launch Template ──► ASG ──► Instances across AZs
                       │
            ┌──────────┼──────────┐
            │          │          │
         AZ-a (2)   AZ-b (2)   AZ-c (2)
            │          │          │
            └──────────┼──────────┘
                       │
                 ALB Target Group
                       │
                   Health Checks
                  (EC2 + ELB)
```

### Target Tracking Scaling

Target tracking is the simplest and most commonly used policy. You define a target metric value, and ASG automatically adjusts capacity to keep the metric near that target — similar to a thermostat.

**Common target metrics:**

* `ASGAverageCPUUtilization` — target 50-70% for general workloads
* `ALBRequestCountPerTarget` — target based on per-instance throughput benchmarks
* `ASGAverageNetworkIn` / `ASGAverageNetworkOut` — for network-bound workloads
* Custom CloudWatch metrics — e.g., queue depth per instance

**Example configuration:**

```text
Policy: TargetTrackingScaling
  TargetValue:          60.0
  PredefinedMetricType: ASGAverageCPUUtilization
  DisableScaleIn:       false
  Cooldown:             300 seconds
```

**Production tips:**
* Set `DisableScaleIn: false` unless you have a separate scale-in policy
* Use a warm-up period (`EstimatedInstanceWarmup`) that matches your application boot time
* Combine with instance warm pools to reduce launch latency

### Step Scaling

Step scaling provides fine-grained control by defining multiple adjustment steps based on CloudWatch alarm breach severity. Unlike target tracking, you must create the CloudWatch alarms yourself.

**Step adjustment example:**

| Alarm Breach Range        | Adjustment         | Resulting Action        |
|---------------------------|--------------------|-------------------------|
| CPU 60-70%                | +1 instance        | Gentle scale-out        |
| CPU 70-85%                | +3 instances       | Moderate scale-out      |
| CPU 85-100%               | +5 instances       | Aggressive scale-out    |
| CPU < 30%                 | -1 instance        | Gentle scale-in         |
| CPU < 15%                 | -2 instances       | Moderate scale-in       |

**When to use step scaling over target tracking:**
* You need asymmetric scale-out vs scale-in behavior
* You want different aggressiveness at different thresholds
* You are scaling on a metric that target tracking does not support natively

### Scheduled Scaling

Scheduled scaling adjusts capacity based on known traffic patterns — predictable peaks and valleys tied to time of day, day of week, or business events.

**Use cases:**
* E-commerce: scale up before daily peak hours (9 AM - 9 PM)
* Batch processing: scale up overnight for ETL jobs
* Marketing events: pre-scale before a product launch or flash sale

```text
Scheduled Action Examples:

  ┌─────────────────────────────────────────┐
  │ Action: morning-scale-up                │
  │ Cron:   0 8 * * MON-FRI                │
  │ Min: 6  Desired: 10  Max: 20           │
  ├─────────────────────────────────────────┤
  │ Action: evening-scale-down              │
  │ Cron:   0 22 * * *                      │
  │ Min: 2  Desired: 2   Max: 10           │
  ├─────────────────────────────────────────┤
  │ Action: flash-sale-prep                 │
  │ OneTime: 2025-11-29T00:00:00Z           │
  │ Min: 20 Desired: 30  Max: 50           │
  └─────────────────────────────────────────┘
```

### Predictive Scaling

Predictive scaling uses machine learning to analyze historical traffic patterns and proactively scale capacity **before** demand arrives. It generates a forecast and schedules capacity changes in advance.

* Requires at least 24 hours of historical data; works best with 14+ days
* Forecasts are regenerated every 24 hours
* Can be used in **forecast-only** mode to validate predictions before enabling
* Combine with target tracking as a reactive fallback

```text
Predictive Scaling Timeline:

  Forecast Generated         Capacity Pre-provisioned
        │                           │
  ──────┼───────────────────────────┼──────────────────►
        │     ML analyzes past      │   Instances ready
        │     14 days of traffic    │   BEFORE spike
        │                           │
                                    └── Traffic spike arrives
                                        (zero cold-start delay)
```

### Scaling Policy Comparison

| Policy              | Trigger            | Latency      | Complexity | Best For                           |
|---------------------|--------------------|--------------|------------|------------------------------------|
| **Target Tracking** | Metric target      | Reactive     | Low        | Steady workloads, general use      |
| **Step Scaling**    | CloudWatch alarms  | Reactive     | Medium     | Multi-threshold, custom metrics    |
| **Scheduled**       | Cron / one-time    | Proactive    | Low        | Predictable traffic patterns       |
| **Predictive**      | ML forecast        | Proactive    | Low        | Recurring patterns, daily cycles   |

**Production recommendation:** Start with target tracking. Layer scheduled scaling for known events. Add predictive scaling after accumulating 2+ weeks of traffic data. Reserve step scaling for advanced custom-metric scenarios.

---

## Scaling Lambda and Containers

### Lambda Concurrency

Lambda scales automatically by running more concurrent executions. Each invocation gets its own execution environment. Scaling is near-instant but subject to concurrency limits.

* **Account-level default:** 1,000 concurrent executions (soft limit, can be raised)
* **Reserved concurrency:** Guarantees a fixed pool of concurrency for a specific function; prevents noisy-neighbor starvation
* **Provisioned concurrency:** Pre-initializes execution environments to eliminate cold starts; billed whether invoked or not

```text
Lambda Concurrency Model:

  Incoming Requests ──► Lambda Service
                            │
              ┌─────────────┼─────────────┐
              │             │             │
         ┌────┴───┐   ┌────┴───┐   ┌────┴───┐
         │ Env 1  │   │ Env 2  │   │ Env 3  │   ... up to
         │(warm)  │   │(warm)  │   │(cold)  │   concurrency
         └────────┘   └────────┘   └────────┘   limit

  Reserved:     Function gets dedicated slice (e.g., 100)
  Provisioned:  Environments pre-warmed, zero cold start
  Unreserved:   Shared pool, first-come-first-served
```

**Production tips:**
* Set reserved concurrency on critical functions to isolate them from account-wide throttling
* Use provisioned concurrency for latency-sensitive APIs (< 100ms P99 requirement)
* Monitor `Throttles` metric — if non-zero, increase reserved concurrency or request a limit increase

### ECS Service Auto Scaling

ECS services scale tasks using Application Auto Scaling, which supports the same policy types as EC2 ASG:

* **Target tracking** — scale on `ECSServiceAverageCPUUtilization` or `ECSServiceAverageMemoryUtilization`
* **Step scaling** — scale on custom CloudWatch metrics (e.g., SQS queue depth)
* **Scheduled scaling** — time-based task count adjustments

For ECS on EC2, you must also scale the underlying EC2 instances (capacity provider strategy handles this). For ECS on Fargate, infrastructure scaling is fully managed.

### EKS and Karpenter

Kubernetes workloads on EKS use:

* **Horizontal Pod Autoscaler (HPA)** — scales pod replicas based on CPU, memory, or custom metrics
* **Karpenter** — an open-source node provisioner that replaces Cluster Autoscaler; provisions right-sized EC2 instances in seconds based on pending pod requirements

```text
EKS Scaling Stack:

  Metric (CPU/Custom) ──► HPA ──► Increase Pod Replicas
                                        │
                                  Pods Pending?
                                        │
                                   Karpenter ──► Launch right-sized
                                                  EC2 node in ~30s
```

**Karpenter advantages over Cluster Autoscaler:**
* Provisions nodes in ~30 seconds vs 2-5 minutes
* Selects optimal instance type from a broad set (no pre-defined node groups)
* Consolidates underutilized nodes automatically

### Fargate Scaling

Fargate abstracts infrastructure entirely. You scale at the task level:

* ECS Fargate: Application Auto Scaling on service tasks
* EKS Fargate: Each pod runs on its own Fargate node — no node-level scaling needed

---

## Database Scaling

### Read Replicas (RDS and Aurora)

Read replicas offload read traffic from the primary database. The primary handles all writes; replicas serve reads with asynchronous replication lag (typically < 1 second for Aurora).

* **RDS:** Up to 5 read replicas per instance; cross-region replicas available
* **Aurora:** Up to 15 read replicas in the same cluster; share the same storage volume (zero storage replication lag)

```text
Write/Read Splitting:

  Application
      │
      ├── Writes ──► Primary DB (writer endpoint)
      │                   │
      │              Replication (async)
      │                   │
      └── Reads ───► Reader Endpoint (load-balanced)
                      │         │         │
                   Replica 1  Replica 2  Replica 3
```

**Production guidance:**
* Use the Aurora reader endpoint for automatic load balancing across replicas
* Monitor `ReplicaLag` — alert if it exceeds your application's staleness tolerance
* For strict read-after-write consistency, route reads to the writer endpoint after writes

### Sharding (DynamoDB Partition Keys)

DynamoDB scales horizontally by distributing data across partitions based on the partition key. A well-designed partition key distributes traffic evenly; a hot partition key creates bottlenecks.

**Good partition keys:** `user_id`, `order_id`, `device_id` — high cardinality, even distribution
**Bad partition keys:** `status`, `date`, `country` — low cardinality, hot partitions

| Key Design            | Cardinality | Distribution | Risk             |
|-----------------------|-------------|--------------|------------------|
| `user_id`             | High        | Even         | Low              |
| `date`                | Low         | Hot spots    | Throttling       |
| `status` (ACTIVE/DONE)| Very low   | 2 partitions | Severe hotspot   |
| `user_id#date`        | High        | Even         | Low (composite)  |

### Aurora Auto Scaling

Aurora can automatically add or remove read replicas based on CloudWatch metrics:

* Scale on `CPUUtilization` or `DatabaseConnections`
* Define min (1) and max (15) replica count
* Replicas register with the reader endpoint automatically
* New replicas become available in ~5-10 minutes (shared storage = fast provisioning)

### DynamoDB On-Demand vs Provisioned

| Aspect                | On-Demand                        | Provisioned                       |
|-----------------------|----------------------------------|-----------------------------------|
| **Capacity planning** | None required                    | Set RCU/WCU per table             |
| **Scaling**           | Instant, per-request             | Auto Scaling with target tracking |
| **Cost**              | ~6x per request vs provisioned   | Lower at steady-state             |
| **Burst handling**    | Doubles previous peak in 30 min  | Uses burst credits, then throttle |
| **Best for**          | Unpredictable, spiky traffic     | Predictable, steady workloads     |
| **Throttling risk**   | Low (but has per-partition cap)  | Higher if under-provisioned       |

**Production recommendation:** Start with on-demand for new tables. After 2-4 weeks of stable traffic, switch to provisioned with auto scaling for cost savings. Use on-demand for tables with unpredictable burst patterns.

---

## Scaling Patterns for Different Workloads

Different workload types demand different scaling strategies. Applying the wrong pattern leads to either over-provisioning (wasted cost) or under-provisioning (degraded performance).

| Workload Type     | Scaling Strategy                       | Primary Services                          | Key Metric                    |
|-------------------|----------------------------------------|-------------------------------------------|-------------------------------|
| **Web application** | Horizontal ASG + ALB                 | EC2 ASG, ALB, ElastiCache                | Request count per target      |
| **REST API**      | Lambda or Fargate auto scaling         | API Gateway, Lambda, Fargate              | Concurrent executions         |
| **Batch / ETL**   | Scheduled scaling + Spot instances     | EC2 ASG, AWS Batch, Step Functions        | Queue depth, job backlog      |
| **Stream processing** | Shard-based parallel consumers    | Kinesis, Lambda ESM, KCL on EC2          | Iterator age, records behind  |
| **Event-driven**  | Lambda concurrency + SQS buffering     | SQS, Lambda, EventBridge                  | Queue depth, throttle count   |
| **ML inference**  | Endpoint auto scaling                  | SageMaker, ECS GPU, Inferentia            | Invocations per instance      |
| **Static content**| CDN scaling (infinite)                 | CloudFront, S3                            | Cache hit ratio               |
| **Database**      | Read replicas + connection pooling     | Aurora, RDS Proxy, DynamoDB               | CPU utilization, connections  |

---

## Capacity Planning

Scaling policies react to demand, but capacity planning ensures your system **can** scale when it needs to. Without planning, you hit limits, quotas, or architectural bottlenecks under real load.

### Load Testing

* Use tools like **Locust**, **k6**, or **AWS Distributed Load Testing** (based on JMeter)
* Test against production-like infrastructure, not downsized replicas
* Gradually increase load to find the breaking point, then set ASG max at 2x that point
* Test scaling behavior: verify instances launch, register with ALB, and serve traffic within expected time

### Baseline Metrics

Establish baselines before scaling policies can be tuned:

* **P50/P95/P99 latency** at normal load
* **CPU/memory utilization** at normal and peak load
* **Requests per second** per instance at acceptable latency
* **Database connections** per instance and total pool size

### Buffer Capacity

* Set ASG min to handle **baseline traffic + 20% buffer**
* Set ASG max to handle **peak traffic + 50% headroom**
* Maintain at least 2 instances across 2 AZs for high availability at minimum
* Account for AZ failure: if running 6 instances across 3 AZs, losing 1 AZ means 4 instances must handle full load

### Service Quotas

AWS enforces account-level quotas that can block scaling if not pre-adjusted:

* EC2 instance limits (per instance type, per region)
* Lambda concurrent execution limit (default 1,000)
* ELB target group limits
* VPC ENI limits per subnet
* DynamoDB per-partition throughput (3,000 RCU / 1,000 WCU)

**Action:** Audit and request quota increases via AWS Service Quotas console **before** peak events, not during an outage.

---

## Scaling Architecture Diagram

The following diagram illustrates a fully scaled AWS architecture with scaling mechanisms at every tier:

```text
                        ┌──────────────┐
                        │  CloudFront  │ ◄── Infinite edge scaling
                        │     CDN      │
                        └──────┬───────┘
                               │
                        ┌──────┴───────┐
                        │     ALB      │ ◄── Auto scales transparently
                        │ (Application │
                        │  Load Bal.)  │
                        └──────┬───────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
        ┌─────┴─────┐   ┌─────┴─────┐   ┌─────┴─────┐
        │  EC2 ASG  │   │  EC2 ASG  │   │  EC2 ASG  │
        │  (AZ-a)   │   │  (AZ-b)   │   │  (AZ-c)   │
        └─────┬─────┘   └─────┬─────┘   └─────┬─────┘
              │                │                │
              │     Target Tracking Policy      │
              │     + Predictive Scaling         │
              │                │                │
              └────────┬───────┴────────┬───────┘
                       │                │
                ┌──────┴──────┐  ┌──────┴──────┐
                │ ElastiCache │  │  SQS Queue  │
                │  (Redis)    │  │  (buffer)   │
                │  Clustered  │  └──────┬──────┘
                └─────────────┘         │
                                 ┌──────┴──────┐
                                 │   Lambda    │
                                 │  Consumers  │
                                 │ (reserved   │
                                 │ concurrency)│
                                 └──────┬──────┘
                                        │
              ┌─────────────────────────┼─────────────────┐
              │                         │                 │
       ┌──────┴──────┐          ┌───────┴──────┐   ┌─────┴──────┐
       │   Aurora     │          │  DynamoDB    │   │    S3      │
       │  Cluster     │          │  (on-demand) │   │  (infinite │
       │  Writer +    │          │              │   │   storage) │
       │  3 Readers   │          └──────────────┘   └────────────┘
       │ (Auto Scale) │
       └──────────────┘
```

**Scaling at each layer:**

* **CloudFront:** Scales to millions of requests per second at edge locations worldwide
* **ALB:** Scales transparently; pre-warm via AWS support for anticipated large events
* **EC2 ASG:** Target tracking + predictive scaling; warm pools for fast launch
* **ElastiCache:** Cluster mode with sharding; add shards for write scaling, replicas for read scaling
* **SQS + Lambda:** SQS absorbs bursts; Lambda scales consumers independently
* **Aurora:** Writer handles writes; auto-scaled readers handle reads
* **DynamoDB:** On-demand mode or provisioned with auto scaling per table
* **S3:** Infinite storage scaling; 5,500 GET / 3,500 PUT per prefix per second (partition automatically)

---

## Key Takeaways

* **Horizontal scaling is the default** — design stateless services, externalize state, and scale out behind load balancers
* **Layer your scaling policies** — combine target tracking (reactive) with predictive or scheduled scaling (proactive) for optimal responsiveness
* **Scale every tier independently** — compute, cache, queue, and database layers have different scaling mechanisms; bottlenecks migrate when only one layer scales
* **Partition key design determines DynamoDB scalability** — a bad key makes auto scaling irrelevant because one partition takes all the heat
* **Service quotas are silent scaling killers** — audit and pre-increase quotas before peak events
* **Load test your scaling behavior** — test not just your application under load, but that ASG policies fire correctly, instances register with ALBs, and database replicas handle redirected reads
* **Cold start matters** — use warm pools (EC2), provisioned concurrency (Lambda), and pre-scaled clusters (Aurora) to eliminate launch latency during scale-out events
* **Cost follows scale** — use Spot instances in ASGs (with mixed instance policies), reserved instances for baseline, and on-demand for burst to optimize the cost curve

---

## Interview Questions

### Q1: How would you design an auto scaling strategy for a web application with predictable daily traffic patterns and occasional unpredictable spikes?

**Answer:** Use a layered approach. Start with **scheduled scaling** to pre-provision capacity for known daily peaks (e.g., scale up at 8 AM, scale down at 10 PM). Layer **predictive scaling** on top — after 2 weeks of data, it will learn the daily pattern and fine-tune capacity ahead of time. For unpredictable spikes, add a **target tracking policy** (e.g., CPU at 60%) as a reactive safety net. Set the ASG maximum high enough to absorb unexpected bursts. Use **warm pools** to keep pre-initialized instances ready, reducing scale-out time from minutes to seconds. Finally, front the application with **CloudFront** and **ElastiCache** to absorb read-heavy traffic before it reaches the ASG.

### Q2: What are the trade-offs between DynamoDB on-demand and provisioned capacity modes, and when would you switch between them?

**Answer:** On-demand mode requires zero capacity planning and handles spiky traffic instantly, but costs approximately 6x more per request than provisioned capacity. Provisioned mode with auto scaling is cheaper for steady-state workloads but can throttle if traffic spikes faster than auto scaling can react (scaling takes 5-15 minutes). The recommended approach is: start with **on-demand** for new tables or tables with unpredictable traffic. After 2-4 weeks of stable, predictable traffic patterns, switch to **provisioned with auto scaling** to reduce costs. Keep on-demand for tables with seasonal or event-driven spikes where the cost of throttling outweighs the premium of on-demand pricing.

### Q3: Explain how Karpenter differs from Cluster Autoscaler for EKS node scaling, and why it matters in production.

**Answer:** Cluster Autoscaler works with pre-defined **node groups** — you must specify which instance types to use in advance. When pods are pending, it scales existing node groups, which limits instance type diversity and can take 2-5 minutes. **Karpenter** takes a fundamentally different approach: it evaluates pending pod requirements (CPU, memory, GPU, topology constraints) and provisions the **optimal instance type** from a broad set in ~30 seconds. It also performs **node consolidation** — automatically replacing underutilized nodes with smaller ones to reduce cost. In production, this means faster scaling, better bin-packing (less wasted capacity), and lower cost because Karpenter selects the cheapest instance that fits the workload rather than scaling a fixed node group.

### Q4: How do you prevent a scaling bottleneck from migrating between tiers?

**Answer:** When you scale one tier, the bottleneck moves to the next constrained layer. For example, scaling EC2 instances pushes more connections to the database, which then becomes the bottleneck. To prevent this: (1) **Scale every tier independently** — set auto scaling policies on compute, cache, and database layers. (2) **Use connection pooling** — place RDS Proxy between application and database to manage connection limits. (3) **Buffer with queues** — use SQS between tiers to absorb bursts and decouple producer/consumer scaling. (4) **Monitor all tiers simultaneously** — create a CloudWatch dashboard showing metrics across ALB, ASG, ElastiCache, and database so you can see bottleneck migration in real time. (5) **Load test end-to-end** — never test a single tier in isolation; always test the full stack to reveal where the bottleneck migrates under load.

### Q5: A Lambda function is being throttled during peak hours. Walk through your debugging and resolution steps.

**Answer:** First, check the **Throttles** CloudWatch metric to confirm throttling is occurring. Then check the **ConcurrentExecutions** metric against the account-level limit (default 1,000). If the function is consuming most of the account concurrency, it is starving other functions. Resolution steps: (1) **Set reserved concurrency** on the critical function to guarantee it a dedicated pool (e.g., 200). (2) **Set reserved concurrency on non-critical functions** to cap their usage and prevent them from consuming the shared pool. (3) **Request a concurrency limit increase** via Service Quotas if the account-level limit is the constraint. (4) If cold starts are adding latency during scale-up, enable **provisioned concurrency** for the peak hours using scheduled auto scaling on provisioned concurrency. (5) If the Lambda is processing from SQS, reduce the **batch size** or increase **MaximumConcurrency** on the event source mapping to control parallelism. (6) Long-term, evaluate if the function can be optimized to reduce execution duration — shorter execution = lower concurrent executions for the same throughput.
