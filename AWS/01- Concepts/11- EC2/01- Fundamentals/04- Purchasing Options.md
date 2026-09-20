# 04- Purchasing Options

## Overview

Amazon EC2 provides multiple purchasing and pricing models for obtaining compute capacity. The correct option depends on workload predictability, interruption tolerance, commitment horizon, capacity requirements, and operational constraints.

The main EC2 purchasing options are:

- On-Demand Instances
- Savings Plans
- Reserved Instances
- Spot Instances
- Dedicated Hosts
- Dedicated Instances
- On-Demand Capacity Reservations

AWS distinguishes **pricing/discount mechanisms** from **capacity assurance**. Savings Plans and Reserved Instances primarily affect how eligible compute usage is priced, while Capacity Reservations address whether EC2 capacity is held for you in a specific Availability Zone. These mechanisms can be combined. :contentReference[oaicite:0]{index=0}

For production backend systems, purchasing strategy should be treated as part of capacity planning and FinOps rather than as a simple "cheapest instance" decision.

---

## Purchasing Options at a Glance

| Option | Commitment | Interruption | Primary Use Case |
|---|---|---|---|
| On-Demand | None | No forced interruption | Variable or short-term workloads |
| Compute Savings Plan | 1 or 3 years | No forced interruption | Predictable compute spend with flexibility |
| EC2 Instance Savings Plan | 1 or 3 years | No forced interruption | Predictable EC2 usage within a Region and instance family |
| Reserved Instance | 1 or 3 years | No forced interruption | Existing workloads with stable instance requirements |
| Spot | None | Can be interrupted | Fault-tolerant and flexible workloads |
| Dedicated Host | Optional commitment | Depends on purchase model | Dedicated physical host, licensing, compliance |
| Dedicated Instance | No long-term commitment required | No forced Spot-style interruption for standard Dedicated Instances | Hardware-level tenant isolation |
| Capacity Reservation | No long-term commitment required | Capacity is reserved | Capacity assurance in a specific Availability Zone |

AWS currently describes Savings Plans as the preferred commitment-based model for many EC2 workloads, while Reserved Instances remain available for compatibility and specific requirements. :contentReference[oaicite:1]{index=1}

---

## On-Demand Instances

On-Demand is the simplest EC2 purchasing model.

You pay for compute capacity without making a long-term commitment. For supported instances, AWS bills On-Demand usage by the second with a 60-second minimum. :contentReference[oaicite:2]{index=2}

### When to Use

On-Demand is appropriate when:

- Workload demand is uncertain.
- Instances are short-lived.
- The workload is difficult to forecast.
- You are evaluating a new application.
- You need flexibility before making a commitment.
- The workload cannot tolerate interruption.
- Capacity requirements change frequently.

Typical backend examples include:

- New production services
- Development environments
- Temporary migration workloads
- Incident-response capacity
- Unpredictable API traffic
- Applications still undergoing capacity testing

### Advantages

- No long-term commitment.
- Simple billing model.
- Maximum flexibility.
- Easy to scale up or down.
- Suitable as baseline capacity while a workload is being characterized.

### Limitations

- Usually more expensive than eligible committed pricing for steady-state usage.
- Requires continuous cost monitoring for long-running workloads.
- Does not by itself guarantee capacity availability in a particular Availability Zone.

### Backend Example

A newly launched FastAPI service might initially run with On-Demand instances:

```text
                    Load Balancer
                    /           \
                   v             v
              On-Demand      On-Demand
                 EC2             EC2
                   \             /
                    \           /
                     Backend
```

After several months of stable usage, the organization can evaluate a commitment such as a Savings Plan.

---

## Savings Plans

Savings Plans provide discounted pricing in exchange for a commitment to a consistent amount of eligible compute usage, measured in USD per hour, for a one- or three-year term. :contentReference[oaicite:3]{index=3}

For EC2, the two relevant Savings Plan types are:

- Compute Savings Plans
- EC2 Instance Savings Plans

---

## Compute Savings Plans

Compute Savings Plans provide the broadest flexibility.

They can apply to eligible compute usage across changes such as:

- EC2 instance family
- Instance size
- Operating system
- Region
- Tenancy

They can also apply to eligible usage outside EC2, including AWS Fargate and Lambda. :contentReference[oaicite:4]{index=4}

### When to Use

Compute Savings Plans are useful when:

- Baseline compute usage is predictable.
- The organization expects architecture changes.
- Instance families may change.
- Workloads may move between EC2 and other supported compute services.
- Long-term commitment is acceptable.
- Flexibility is more valuable than maximizing configuration specificity.

For example:

```text
Year 1

EC2 m-family
    |
    v
Compute Savings Plan


Later

EC2 c-family
    |
    v
Same commitment can continue applying
to eligible usage
```

The key benefit is that the financial commitment is to a level of compute spend rather than a single EC2 instance configuration.

---

## EC2 Instance Savings Plans

EC2 Instance Savings Plans provide a commitment to a specific EC2 instance family in a Region.

They provide less flexibility than Compute Savings Plans but can provide greater savings for workloads with stable EC2 usage. :contentReference[oaicite:5]{index=5}

### When to Use

Consider them when:

- The application is expected to remain on EC2.
- The instance family is stable.
- The Region is stable.
- The organization has predictable baseline usage.
- The workload does not require broad compute-service flexibility.

Example:

```text
Production API
    |
    +-- EC2 m-family
    +-- EC2 m-family
    +-- EC2 m-family
    |
    v
Stable baseline usage
    |
    v
EC2 Instance Savings Plan
```

The important trade-off is:

```text
More specificity
      |
      v
Potentially stronger savings
      |
      +
      |
      v
Less flexibility
```

---

## Savings Plans vs On-Demand

| Characteristic | On-Demand | Savings Plan |
|---|---|---|
| Long-term commitment | No | Yes |
| Usage flexibility | High | Depends on plan |
| Pricing | Standard | Discounted eligible usage |
| Best for | Variable workloads | Predictable baseline |
| Risk | Higher unit cost | Commitment utilization risk |
| Operational management | Simple | Requires commitment planning |

The main mistake is treating a Savings Plan as simply a cheaper On-Demand instance.

It is actually a **financial commitment**. If the organization commits to more usage than it consumes, the unused commitment can reduce the expected savings.

---

## Reserved Instances

Reserved Instances provide discounted pricing in exchange for a one- or three-year commitment to a specified instance configuration. AWS currently recommends evaluating Savings Plans instead for many new commitment decisions, although RIs remain available and can be appropriate for existing processes or specific requirements. :contentReference[oaicite:6]{index=6}

Historically, RIs have been widely used for stable EC2 workloads.

### Standard Reserved Instances

Standard RIs provide significant discounts for defined configurations and can be purchased for one- or three-year terms. Certain attributes can be modified depending on the RI configuration and AWS rules. :contentReference[oaicite:7]{index=7}

### Convertible Reserved Instances

Convertible RIs provide greater flexibility to exchange the reservation for another configuration under AWS's exchange rules, generally in exchange for a lower potential discount than Standard RIs. :contentReference[oaicite:8]{index=8}

### When RIs May Still Matter

RIs can still be relevant when:

- Existing organizations already use RI-based cost management.
- A specific RI capability is required.
- An existing reservation strategy is already optimized.
- Capacity reservation characteristics are required for a particular deployment.

For a new general-purpose commitment decision, evaluate Savings Plans first.

---

## Spot Instances

Spot Instances use spare EC2 capacity and can provide substantial discounts compared with On-Demand pricing. AWS can reclaim Spot capacity when it needs the capacity, with a two-minute interruption notice in the standard interruption process. :contentReference[oaicite:9]{index=9}

The defining characteristic is **interruptibility**.

### Suitable Workloads

Spot is well suited to workloads that can tolerate interruption, such as:

- Batch processing
- Data processing
- CI/CD workers
- Image processing
- Stateless workers
- Distributed computation
- Fault-tolerant background jobs

For example:

```text
                    Queue
                      |
            +---------+---------+
            |                   |
            v                   v
        On-Demand            Spot
        Worker Pool         Worker Pool
            |                   |
            +---------+---------+
                      |
                 Completed Jobs
```

The On-Demand capacity can provide a reliable baseline while Spot capacity provides additional inexpensive capacity.

---

## Spot and Celery

Celery workers are often good candidates for Spot when tasks are designed to tolerate worker interruption.

A resilient design should use:

- Durable task queues
- Idempotent tasks
- Retry policies
- Checkpointing where appropriate
- Externalized task state
- Multiple workers
- Graceful shutdown handling

For example:

```text
                    Redis / SQS
                        |
              +---------+---------+
              |                   |
         On-Demand            Spot Workers
          Workers
              |                   |
              +---------+---------+
                        |
                 External Database
```

If a Spot worker disappears, another worker should be able to continue processing the workload.

Do not use Spot for a stateful workload that assumes an individual instance will remain available.

---

## Spot Interruption Handling

A production Spot workload should treat interruption as an expected event rather than an exceptional event.

The application should be able to:

1. Detect interruption.
2. Stop accepting new work where appropriate.
3. Finish or checkpoint safe work.
4. Persist required state externally.
5. Exit cleanly.
6. Allow the scheduler or Auto Scaling system to replace capacity.

The architecture should assume that a Spot instance can disappear.

---

## Dedicated Hosts

A Dedicated Host is a physical EC2 server dedicated to your use.

Dedicated Hosts provide visibility and control over the physical host and can be useful for:

- Server-bound software licensing
- Per-core or per-socket licensing
- Certain compliance requirements
- Physical host isolation requirements
- Workloads requiring control over instance placement

AWS prices Dedicated Hosts using On-Demand, reservation, or applicable Savings Plan models depending on the host and configuration. :contentReference[oaicite:10]{index=10}

### When to Use

Dedicated Hosts are generally considered when standard virtualized tenancy does not satisfy a licensing, compliance, or physical-placement requirement.

They are usually unnecessary for ordinary Django, FastAPI, Nginx, Celery, or microservice workloads.

---

## Dedicated Instances

Dedicated Instances run on hardware dedicated to a single AWS customer at the host hardware level.

They differ from Dedicated Hosts because Dedicated Hosts provide additional visibility and control over the underlying physical server and instance placement. :contentReference[oaicite:11]{index=11}

Use Dedicated Instances when hardware-level tenant isolation is required but the additional physical-host management capabilities of Dedicated Hosts are not needed.

---

## Dedicated Hosts vs Dedicated Instances

| Characteristic | Dedicated Host | Dedicated Instance |
|---|---|---|
| Dedicated physical hardware | Yes | Yes |
| Physical host visibility | Yes | No |
| Host-level placement control | Yes | No |
| Server-bound licensing use cases | Strong fit | More limited |
| Compliance isolation | Yes | Yes |
| Operational complexity | Higher | Lower |

Neither option should be selected merely because "dedicated" sounds more production-ready.

The additional cost and operational model should be justified by a real requirement.

---

## Capacity Reservations

Capacity Reservations address a different problem from discounting.

They reserve EC2 capacity for your use in a specific Availability Zone for as long as the reservation remains active. :contentReference[oaicite:12]{index=12}

This matters when the problem is not:

> "How can I pay less?"

but:

> "How can I ensure that capacity is available when I need it?"

For example, a business-critical application may require the ability to launch a specific instance type during a disaster recovery event.

```text
Normal Operation
        |
        v
Application running
        |
        v
Capacity Reservation
        |
        v
Known capacity available
during required event
```

Capacity Reservations are billed at the applicable On-Demand rate whether or not the reserved capacity is fully utilized. They can be combined with eligible discount mechanisms such as Savings Plans. :contentReference[oaicite:13]{index=13}

---

## Purchasing vs Capacity Assurance

This distinction is important for interviews and production architecture.

```text
                    EC2 Cost / Capacity Decision
                              |
                +-------------+-------------+
                |                           |
                v                           v
          Pricing Model              Capacity Assurance
                |                           |
        +-------+-------+             +-----+------+
        |       |       |             |            |
    On-Demand Savings  Spot      Capacity       Other
              Plans              Reservation
        |
    Reserved
    Instances
```

Purchasing options primarily determine **how eligible usage is priced**.

Capacity Reservations determine whether specified capacity is held in a particular Availability Zone.

They solve different problems.

---

## Purchasing Strategy for Backend Systems

A production backend often benefits from a mixed purchasing strategy.

For example:

```text
                     Production Compute
                            |
          +-----------------+-----------------+
          |                 |                 |
          v                 v                 v
     Baseline API      Variable Workers    Batch Jobs
          |                 |                 |
     Savings Plan        On-Demand/Spot       Spot
```

A common strategy is:

- Use a commitment such as a Savings Plan for predictable baseline compute.
- Use On-Demand for uncertain or critical additional capacity.
- Use Spot for interruption-tolerant workloads.
- Use Capacity Reservations where guaranteed capacity is required.
- Use dedicated hardware only when licensing or isolation requirements justify it.

AWS's current decision guidance similarly describes hybrid purchasing as a common approach. :contentReference[oaicite:14]{index=14}

---

## Example: Django Production Platform

Consider a production Django platform with:

- Public API
- Celery workers
- Scheduled batch jobs
- Development environments

A possible strategy is:

```text
                    Django API
                        |
                 Auto Scaling Group
                        |
              Savings Plan Baseline
                        |
            +-----------+-----------+
            |                       |
          EC2-A                   EC2-B
            |                       |
        On-Demand                On-Demand


                 Celery Workers
                       |
             +---------+---------+
             |                   |
       On-Demand Workers     Spot Workers


                  Batch Jobs
                       |
                       v
                  Spot Fleet
```

The exact implementation depends on workload characteristics, but the financial principle is to separate:

- Predictable baseline capacity
- Critical variable capacity
- Interruptible workload capacity

---

## Commitment Planning

Before purchasing a commitment, determine the workload's baseline rather than using peak usage.

Suppose monthly EC2 demand looks like:

```text
Peak
 |                 /\        /\
 |       /\       /  \      /  \
 |  /\  /  \  /\ /    \ /\ /    \
 |_/  \/    \/  V      V  V      \__
 |
 +------------------------------------> Time
```

The commitment should generally be based on the level of usage the organization can confidently sustain, not the maximum historical spike.

Peak demand can be handled through flexible capacity.

A common approach is:

```text
Baseline
    -> Commitment

Variable capacity
    -> On-Demand

Interruptible excess
    -> Spot
```

---

## Commitment Risk

A long-term commitment creates financial risk if workload assumptions change.

Potential causes include:

- Migration from EC2 to ECS or EKS
- Serverless migration
- Instance-family changes
- Region migration
- Application shutdown
- Significant workload reduction
- Architecture redesign

For this reason, commitment analysis should consider the expected lifecycle of the application.

Do not commit to three years of capacity simply because the discount appears attractive.

The correct question is:

> How confident are we that this level and type of compute usage will remain valuable throughout the commitment period?

---

## Cost Analysis

The effective cost of an EC2 purchasing strategy is broader than the advertised hourly rate.

Consider:

```text
Total Cost
    =
Compute Cost
+ Storage
+ Data Transfer
+ Load Balancing
+ Monitoring
+ Management
+ Operational Overhead
+ Commitment Risk
```

For Spot workloads, also consider the engineering cost of interruption handling.

For Dedicated Hosts, consider host utilization.

For Savings Plans and RIs, consider the financial impact of underutilized commitments.

For Capacity Reservations, consider the cost of reserved but unused capacity.

---

## Purchasing Strategy and Auto Scaling

Auto Scaling and purchasing strategy are complementary.

Auto Scaling determines:

> How much compute capacity should be running?

Purchasing strategy determines:

> How should that capacity be priced or secured?

For example:

```text
                 Auto Scaling Group
                        |
          +-------------+-------------+
          |                           |
     Baseline Capacity          Burst Capacity
          |                           |
    Savings Plan                 On-Demand
    Coverage                     or Spot
```

This separation allows the application to scale independently of the financial model.

---

## Purchasing Strategy and High Availability

Do not confuse discounted capacity with high availability.

A Savings Plan does not make an application highly available.

A Spot discount does not make an application fault tolerant.

A Capacity Reservation does not automatically provide application redundancy.

High availability still requires architectural mechanisms such as:

- Multiple Availability Zones
- Multiple application instances
- Load balancing
- Health checks
- Automated replacement
- Externalized state
- Appropriate backup and recovery

Purchasing decisions should support the architecture rather than substitute for it.

---

## Security Considerations

Purchasing options have limited direct impact on application security, but cost decisions can influence architecture.

For example:

- Do not move critical workloads to Spot solely for cost savings if the application cannot tolerate interruption.
- Do not compromise isolation requirements to reduce infrastructure cost.
- Ensure dedicated-host requirements are driven by documented compliance or licensing needs.
- Use IAM and network security consistently regardless of purchasing model.
- Apply the same patching, monitoring, and security baselines to On-Demand, Reserved, Savings Plan-covered, and Spot instances.

Security controls should not depend on the pricing model.

---

## Operational Considerations

A mature EC2 purchasing strategy should be reviewed periodically.

Monitor:

- Baseline EC2 utilization
- Savings Plan utilization
- Savings Plan coverage
- RI utilization where applicable
- Spot interruption rates
- On-Demand overflow
- Capacity Reservation utilization
- Instance right-sizing
- Workload migration plans

A commitment that was correct twelve months ago may become inappropriate after an architecture change.

---

## Common Mistakes

### Choosing the Cheapest Option

The lowest hourly price is not necessarily the lowest total cost.

A cheap Spot instance is expensive if interruption causes lost work or unacceptable downtime.

### Using Spot for Stateful Workloads

Spot should not be used for workloads that cannot tolerate interruption unless the application has a robust recovery architecture.

### Committing Based on Peak Usage

Commitments should generally cover predictable baseline demand rather than temporary spikes.

### Treating Savings Plans as Capacity Reservations

A Savings Plan discounts eligible usage. It does not guarantee that a specific EC2 instance will be available in a particular Availability Zone.

### Automatically Buying Reserved Instances

Savings Plans should be evaluated for new commitment decisions, especially when the workload may change instance families or compute services. AWS currently recommends Savings Plans over RIs for many new commitment decisions. :contentReference[oaicite:15]{index=15}

### Ignoring Architecture Changes

Moving from EC2 to ECS, EKS, or Lambda can change how commitments apply.

Review commitments before major migrations.

### Overusing Dedicated Hardware

Dedicated Hosts and Dedicated Instances solve specialized isolation and licensing requirements. They are not inherently better for ordinary web applications.

### Ignoring Unused Capacity Reservations

A Capacity Reservation can incur cost even when the reserved capacity is not being consumed. :contentReference[oaicite:16]{index=16}

---

## Production Decision Framework

Use the following decision process:

```text
                         Workload
                            |
                            v
                Is usage predictable?
                    /             \
                  No               Yes
                  |                 |
                  v                 v
             On-Demand       Can it tolerate
                            interruption?
                              /       \
                            Yes        No
                            |           |
                            v           v
                           Spot      Commitment
                                        |
                              +---------+---------+
                              |                   |
                         Stable EC2        Broad compute
                         family/Region      flexibility
                              |                   |
                              v                   v
                       EC2 Instance SP      Compute SP
```

Then evaluate capacity requirements separately:

```text
Does the workload require guaranteed
capacity in a specific Availability Zone?
                    |
              +-----+-----+
              |           |
             Yes          No
              |           |
              v           v
      Capacity Reservation
```

This separates three decisions:

1. How predictable is the workload?
2. Can the workload tolerate interruption?
3. Does the workload require guaranteed capacity?

---

## Interview Considerations

### What is the difference between On-Demand and Spot?

On-Demand provides flexible compute without a long-term commitment. Spot uses spare EC2 capacity at a lower price but can be interrupted by AWS.

### When would you use a Savings Plan?

Use a Savings Plan when you have predictable baseline compute usage and can make a one- or three-year commitment in exchange for discounted eligible usage.

### Compute Savings Plan vs EC2 Instance Savings Plan?

A Compute Savings Plan provides broader flexibility across eligible EC2 usage and supported compute services. An EC2 Instance Savings Plan is more specific to an EC2 instance family in a Region and can provide stronger savings in exchange for that narrower commitment. :contentReference[oaicite:17]{index=17}

### Are Reserved Instances the same as Savings Plans?

No. Both provide commitment-based pricing benefits, but they differ in how the commitment is defined and how usage flexibility works. AWS currently recommends Savings Plans for many new commitment decisions. :contentReference[oaicite:18]{index=18}

### What is the difference between a Savings Plan and a Capacity Reservation?

A Savings Plan is primarily a pricing commitment. A Capacity Reservation reserves EC2 capacity in a specific Availability Zone. They solve different problems and can be combined. :contentReference[oaicite:19]{index=19}

### When would you use Spot Instances for a backend system?

For fault-tolerant workloads such as asynchronous workers, batch processing, CI/CD jobs, and stateless processing where interruption can be handled safely.

### When would you use a Dedicated Host?

When physical host dedication, host-level visibility, instance placement control, or server-bound licensing requirements justify the additional operational and financial cost.

---

## Key Takeaways

- On-Demand provides maximum flexibility, while Savings Plans and Reserved Instances trade commitment for discounted pricing.
- Use Spot for workloads designed to tolerate interruption, with durable state, retries, and replacement capacity.
- Savings Plans should generally cover predictable baseline usage; avoid committing based solely on peak demand.
- Capacity Reservations solve capacity-assurance problems and are distinct from pricing discounts.
- Production EC2 environments commonly use a hybrid strategy combining committed baseline capacity, flexible On-Demand capacity, and Spot capacity for interruptible workloads.