# High Availability — Multi-AZ vs. Multi-Region

## Availability Zones (AZs) — The Baseline

An AWS Region consists of multiple physically separate data centers (AZs), connected by low-latency links but isolated enough that a failure in one (power, cooling, a physical incident) doesn't take down the others.

## Multi-AZ Architecture

Running resources across two or more AZs within the same Region.

```text
Region: us-east-1
 ├── AZ-a: EC2 instances, RDS primary
 ├── AZ-b: EC2 instances, RDS standby
 └── AZ-c: EC2 instances
```

**What it protects against:** a single data center-level failure. **What it doesn't protect against:** an entire Region-level event (rare, but not zero — a Region can have broad service disruptions affecting all its AZs simultaneously, even if individual AZ failures are isolated from each other).

Multi-AZ is the baseline expectation for any production workload on AWS — many managed services (RDS Multi-AZ, ALB, Auto Scaling Groups) make this close to a checkbox rather than a from-scratch design exercise.

## Multi-Region Architecture

Running resources across two or more entirely separate Regions.

```text
us-east-1 (Primary)          eu-west-1 (Secondary)
 ├── Full application stack   ├── Full application stack
 └── Database                 └── Database (replicated)
```

**What it protects against:** a full Region-level event, and can also reduce latency for geographically distributed users (see Route 53 latency-based routing).

## Why Multi-Region Is a Much Bigger Step Than Multi-AZ

- **Data replication becomes cross-region**, with real latency (tens to hundreds of milliseconds) between writes and their replication to the other Region — this directly affects consistency guarantees
- **Cost roughly doubles** (or more) for active-active designs, since you're running full infrastructure in more than one place
- **Operational complexity increases substantially** — deployments, monitoring, and incident response all now need to account for multiple Regions, and testing failover for real (not just in theory) becomes its own significant undertaking

## The Honest Trade-off

Multi-AZ is close to "do this by default." Multi-Region is a deliberate, expensive decision that should be justified by an actual business requirement (regulatory data residency, genuinely global low-latency requirements, or an availability target that Multi-AZ alone can't meet) — not adopted reflexively because it sounds more resilient.

## Senior-Level Considerations

- "We're multi-region" means very different things depending on whether it's active-active, active-passive (warm standby), or just backups in another region — these have wildly different costs and actual recovery characteristics (see Disaster Recovery Strategies)
- Global services (Route 53, CloudFront, IAM, S3 with cross-region replication) already operate above the single-Region layer — understanding which AWS services are inherently multi-region vs. region-scoped is a prerequisite for designing this correctly
