# EC2 Purchasing Options

# Overview

AWS provides multiple purchasing models for EC2 instances, each optimized for different commitment levels, usage patterns, and cost requirements. Selecting the right purchasing option can reduce compute costs by up to 72%.

---

# On-Demand Instances

## How It Works
- Pay per second (Linux/macOS, minimum 60 seconds) or per hour (Windows, RHEL)
- No commitment, no upfront payment
- Launch and terminate at any time

## When to Use
- Short-term, unpredictable workloads
- Applications being developed or tested
- Workloads that cannot be interrupted
- First deployment of a new application (before usage patterns are known)

## Cost
- Most expensive per-hour rate, but no risk of unused commitment

---

# Reserved Instances (RIs)

## How It Works
- Commit to a specific instance type, region (or AZ), and OS for 1 or 3 years
- Receive a significant discount (up to 72% off On-Demand) in exchange for the commitment

## Payment Options

| Payment | Discount | Cash Flow Impact |
|---------|----------|-----------------|
| All Upfront | Highest (~72%) | Large upfront cost, no monthly bill |
| Partial Upfront | Medium (~65%) | Reduced upfront + reduced monthly |
| No Upfront | Lowest (~36%) | No upfront, discounted hourly rate |

## RI Types

| Type | Flexibility | Discount |
|------|-------------|----------|
| Standard RI | Fixed instance type and family | Higher discount |
| Convertible RI | Can change instance family, type, OS, tenancy | Lower discount (~54%) |

## Scope

| Scope | Behavior |
|-------|----------|
| Regional | Discount applies to any AZ in the region, provides capacity reservation benefit automatically |
| Zonal | Discount locked to a specific AZ, provides capacity reservation in that AZ |

---

# Savings Plans

## How It Works
- Commit to a consistent amount of compute spend ($/hour) for 1 or 3 years
- More flexible than RIs — you commit to spend, not to a specific instance type

## Savings Plan Types

| Type | Flexibility | Discount |
|------|-------------|----------|
| Compute Savings Plan | Any instance family, size, OS, region, and even Fargate/Lambda | Up to 66% |
| EC2 Instance Savings Plan | Any size within a specific instance family and region | Up to 72% |

**Key Difference from RIs**: Savings Plans apply automatically to your usage. If you change instance types, the discount follows (for Compute Plans). RIs are locked to a specific configuration.

```text
Example: $10/hour Compute Savings Plan

Your Usage:
  Hour 1:  m5.xlarge in us-east-1  → $10 covered at Savings Plan rate
  Hour 2:  c6g.2xlarge in eu-west-1 → $10 covered at Savings Plan rate (family changed!)
  Hour 3:  Fargate tasks → $10 covered at Savings Plan rate (service changed!)

All covered because Compute Savings Plans are not locked to instance type or region.
```

---

# Spot Instances

## How It Works
- Purchase unused EC2 capacity at up to 90% discount off On-Demand
- AWS can reclaim (interrupt) the instance with a **2-minute warning** when capacity is needed
- Price fluctuates based on supply and demand

## Spot Instance Lifecycle

```text
Request Spot Instance
        │
        ▼
Capacity Available?
   ├── YES → Instance Launches (at current spot price)
   │           │
   │           ▼ (some time later)
   │   AWS needs capacity back?
   │      ├── YES → 2-minute interruption notice
   │      │           │
   │      │           ▼
   │      │   Instance terminated / stopped / hibernated
   │      │   (based on your interruption behavior setting)
   │      │
   │      └── NO → Instance continues running
   │
   └── NO → Request waits (or fails if not persistent)
```

## When to Use Spot
- Batch processing and data analysis
- CI/CD build runners
- Stateless web servers behind a load balancer (with Auto Scaling)
- Big data processing (EMR, Spark)
- Container workloads (ECS, EKS with mixed instance types)

## When NOT to Use Spot
- Databases (data loss on interruption)
- Stateful applications without external state management
- Single-instance production workloads
- Applications that cannot tolerate any interruption

## Spot Strategies
- **Diversify**: Request multiple instance types and AZs to reduce interruption risk
- **Capacity Rebalancing**: ASG detects rebalancing recommendation, launches replacement before interruption
- **Spot Fleet**: Request a collection of Spot (and optionally On-Demand) instances to meet target capacity

---

# Dedicated Hosts

## How It Works
- An entire physical server is dedicated to your account
- You control instance placement on the physical host
- Billed per host (not per instance)

## When to Use
- Software licensing that requires per-socket, per-core, or per-VM licensing (Oracle, SQL Server, Windows Server)
- Compliance requirements mandating dedicated physical hardware
- Hardware affinity (must run on the same physical server after stop/start)

## Dedicated Hosts vs Dedicated Instances

| Feature | Dedicated Host | Dedicated Instance |
|---------|---------------|-------------------|
| Physical Server | You get a specific host | You get dedicated hardware (but no control over which) |
| Instance Placement | You control placement | AWS controls placement |
| Socket/Core Visibility | Yes (for licensing) | No |
| Per-Host Billing | Yes | No (per-instance billing with premium) |
| Use Case | License compliance | Hardware isolation compliance |

---

# Capacity Reservations

## On-Demand Capacity Reservations
- Reserve capacity in a specific AZ for any duration
- No commitment discount — you pay On-Demand rates whether you use it or not
- Guarantees capacity is available when you need it (e.g., disaster recovery failover)

**Combine with Savings Plans**: Use a Capacity Reservation for guaranteed availability + a Savings Plan for the discount. They stack.

---

# Cost Optimization Decision Tree

```text
Is the workload interruptible?
│
├── YES → Can it run on diverse instance types?
│          ├── YES → Spot Instances (up to 90% savings)
│          └── NO  → Spot with specific type (higher interruption risk)
│
└── NO → Is the workload steady-state (predictable)?
          │
          ├── YES → Duration > 1 year?
          │          ├── YES → Savings Plan or Reserved Instance (up to 72%)
          │          └── NO  → On-Demand
          │
          └── NO → Is it variable but always running some baseline?
                    ├── YES → Savings Plan for baseline + On-Demand for peaks
                    └── NO  → On-Demand
```

---

# Full Comparison Table

| Option | Discount | Commitment | Interruption Risk | Best For |
|--------|----------|-----------|-------------------|----------|
| On-Demand | 0% | None | None | Dev/test, unpredictable workloads |
| Reserved Instance | Up to 72% | 1 or 3 years | None | Steady-state production |
| Savings Plan | Up to 72% | $/hour for 1-3 years | None | Flexible steady-state |
| Spot | Up to 90% | None | YES (2-min warning) | Batch, CI/CD, stateless |
| Dedicated Host | Varies | Optional | None | License compliance |
| Dedicated Instance | ~2% premium | None | None | Hardware isolation |
| Capacity Reservation | 0% (On-Demand rate) | None | None | Guaranteed availability |

---

# Common Mistakes

- Buying Reserved Instances before understanding workload patterns. Run On-Demand for 1-3 months first, analyze usage, then commit.
- Not considering Savings Plans — they are more flexible than RIs and usually the better choice for most organizations.
- Running Spot Instances for databases or stateful applications without external state management.
- Forgetting that unused Reserved Instances are charged whether you use them or not — there is no refund.
- Not diversifying Spot requests across multiple instance types and AZs (single type = higher interruption rate).

---

# Key Takeaways

- On-Demand is the default. Use it until you understand your usage patterns.
- Savings Plans are generally preferred over Reserved Instances due to flexibility.
- Spot Instances offer up to 90% savings but require workloads that tolerate interruption.
- Combine purchasing options: Savings Plan for baseline + On-Demand for peaks + Spot for batch.
- Dedicated Hosts are only necessary for per-socket/per-core software licensing.
- Always analyze AWS Cost Explorer and Compute Optimizer before committing to reservations.

---
