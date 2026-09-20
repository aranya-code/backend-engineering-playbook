# 09- Cost Optimization

## Overview

EC2 cost optimization is the process of matching compute, storage, networking, and operational capacity to actual workload requirements without compromising reliability, performance, security, or recovery objectives.

The goal is not simply to make the EC2 bill smaller.

A production optimization decision should consider:

- Utilization
- Performance
- Availability
- Scaling behavior
- Instance family and size
- Purchasing model
- Storage
- Elastic IP usage
- Load balancers
- Auto Scaling
- Development environment lifecycle
- Backup retention
- Operational overhead

A useful model is:

```text
Business Workload
       |
       v
Required Performance
       |
       v
Required Availability
       |
       v
Capacity Requirement
       |
       v
Instance / Storage Selection
       |
       v
Purchasing Strategy
       |
       v
Continuous Measurement
       |
       v
Cost Optimization
```

The correct question is:

> What is the lowest sustainable cost for the required reliability and performance?

Not:

> What is the cheapest EC2 instance?

## EC2 Cost Model

EC2-related costs can come from several components.

| Component | Typical cost driver |
|---|---|
| EC2 compute | Instance type, runtime, purchasing model |
| EBS | Provisioned storage and performance characteristics |
| Snapshots | Stored snapshot data |
| Public IPv4 | Public IPv4 address usage |
| Elastic IP | Public IPv4 allocation/usage |
| Load Balancer | Load balancer usage and processed traffic |
| Data transfer | Traffic direction and destination |
| NAT Gateway | Hourly usage and processed data |
| CloudWatch | Metrics, logs, alarms, ingestion, retention |
| AMIs | Associated snapshot storage |
| AWS Backup | Backup storage and operations |

The exact price depends on Region, instance type, operating system, purchasing model, storage configuration, and usage.

Cost optimization should therefore begin with **resource-level visibility**, not assumptions.

## Cost Optimization Principles

A practical EC2 optimization strategy follows several principles:

1. **Measure before changing.**
2. **Remove unused resources.**
3. **Right-size active resources.**
4. **Scale capacity with demand.**
5. **Use appropriate purchasing models.**
6. **Optimize storage independently from compute.**
7. **Control non-production environments.**
8. **Automate repetitive optimization.**
9. **Protect reliability while reducing waste.**
10. **Continuously review utilization and architecture.**

The optimization loop is:

```text
Measure
   |
   v
Identify Waste
   |
   v
Validate Workload
   |
   v
Change Capacity / Architecture
   |
   v
Measure Again
   |
   +------> Continue
```

## Cost Visibility

Before optimizing EC2, establish ownership and allocation.

Useful tags include:

| Tag | Example |
|---|---|
| `Environment` | `production` |
| `Application` | `payments-api` |
| `Team` | `backend` |
| `Owner` | `platform` |
| `CostCenter` | `engineering` |
| `ManagedBy` | `terraform` |

A resource without ownership is difficult to optimize safely.

Tagging should be enforced through infrastructure standards where possible rather than relying on engineers to remember tags manually.

## AWS Cost Explorer

AWS Cost Explorer is useful for identifying:

- EC2 spending trends
- Regional costs
- Instance-related spending
- EBS costs
- Data transfer costs
- Changes over time

Analyze costs by dimensions such as:

- Service
- Region
- Usage type
- Linked account
- Tags where configured

A useful workflow is:

```text
Monthly Cost
    |
    v
EC2 Service
    |
    v
Region
    |
    v
Application / Environment
    |
    v
Resource
    |
    v
Optimization Candidate
```

Do not optimize only the largest absolute resource. Consider whether the resource is actually over-provisioned.

## CloudWatch Utilization

CloudWatch provides the operational data needed for right-sizing.

Important metrics can include:

- CPU utilization
- Network traffic
- EBS throughput
- EBS IOPS
- Status checks
- CPU credit metrics for burstable instances

Memory and filesystem utilization are not available from standard EC2 instance metrics in the same way as CPU and network metrics; use the CloudWatch Agent or another monitoring mechanism when these dimensions matter.

A useful analysis window should cover representative workload patterns rather than a few hours.

For production systems, inspect:

- Normal traffic
- Peak traffic
- Batch workloads
- Deployment periods
- Seasonal patterns
- Incident periods

## Right-Sizing

Right-sizing means selecting an instance configuration that provides sufficient resources without persistent over-provisioning.

Example:

```text
Current:
    8 vCPU
    32 GiB RAM

Observed:
    CPU mostly 10-20%
    Memory mostly 30%
    Network moderate
```

This may indicate a right-sizing opportunity.

However, CPU alone is not enough.

A backend service can be CPU-light but:

- Memory-heavy
- Network-heavy
- EBS-intensive
- Connection-limited
- Latency-sensitive

Analyze the actual bottleneck.

## Right-Sizing Workflow

```text
Current Instance
       |
       v
Collect Utilization
       |
       v
Identify Bottleneck
       |
       v
Select Candidate Instance
       |
       v
Validate Application
       |
       v
Load Test / Observe
       |
       v
Resize
       |
       v
Monitor
```

For example:

```text
Django API
   |
   +-- CPU: 20%
   +-- Memory: 80%
   +-- Network: moderate
   +-- DB latency: normal
```

Reducing memory capacity simply because CPU utilization is low would be the wrong optimization.

## Instance Family Selection

Instance families should match workload characteristics.

| Workload characteristic | Relevant consideration |
|---|---|
| CPU-heavy | Compute-optimized |
| Memory-heavy | Memory-optimized |
| Balanced application | General-purpose |
| High network requirements | Network capability |
| High EBS requirements | EBS bandwidth and IOPS capability |
| Bursty low-average workload | Burstable |
| Accelerated workloads | Specialized instance family |

For Python APIs, general-purpose instances are often a reasonable starting point, but actual workload measurements should determine the final choice.

## Burstable Instances

Burstable instances provide baseline CPU performance with the ability to burst above the baseline under the appropriate credit model.

They can be useful for:

- Development environments
- Low-average CPU workloads
- Small APIs
- Intermittent workloads

They can be problematic for:

- Consistently CPU-intensive services
- Predictable high-throughput workloads
- Workloads where sustained CPU performance is required

Monitor CPU credit behavior rather than assuming low average CPU automatically means a burstable instance is appropriate.

## Scale Up vs Scale Out

Cost optimization is also an architectural decision.

### Scale Up

```text
2 vCPU
   |
   v
8 vCPU
```

Fewer larger instances.

### Scale Out

```text
2 vCPU
  |
  +---- EC2
  +---- EC2
  +---- EC2
  +---- EC2
```

More smaller instances.

Scale-out can provide:

- Higher availability
- Better failure isolation
- Independent replacement
- More flexible Auto Scaling

Scale-up can provide:

- Simpler topology
- Fewer instances
- Larger per-instance resource capacity

The lowest compute cost is not necessarily the best architecture.

## Auto Scaling for Cost Control

Auto Scaling allows capacity to follow demand.

Example:

```text
Traffic
  |
  v
CloudWatch Metrics
  |
  v
Scaling Policy
  |
  +---- Scale Out
  |
  +---- Scale In
  |
  v
EC2 Fleet
```

Without Auto Scaling:

```text
Peak Capacity
     |
     v
Running 24/7
```

With appropriate Auto Scaling:

```text
Low Demand -> Small Fleet
High Demand -> Larger Fleet
Low Demand -> Small Fleet
```

This can reduce idle compute capacity.

## Minimum and Maximum Capacity

For an ASG:

```text
Min = 2
Desired = 2
Max = 10
```

During a traffic spike:

```text
2 -> 4 -> 6 -> 8
```

When demand falls:

```text
8 -> 6 -> 4 -> 2
```

Do not set the minimum too low merely to reduce cost.

If the service requires two instances across two Availability Zones for availability, reducing the minimum to one is a reliability tradeoff rather than pure optimization.

## Scaling Policy Selection

Target tracking is often a practical starting point for dynamic scaling.

Example concept:

```text
Target:
Average CPU = 50%

Traffic increases
      |
      v
CPU rises
      |
      v
ASG scales out
      |
      v
CPU falls toward target
```

For production systems, consider metrics closer to actual workload demand when CPU is not a good proxy.

Examples:

- Requests per target
- Queue depth
- Custom application metric
- Concurrent requests
- Worker backlog

For Celery:

```text
Queue Depth
     |
     v
Scaling Policy
     |
     v
More Workers
```

This can be more meaningful than CPU utilization alone.

## Idle Resource Identification

Common EC2 waste includes:

- Stopped instances that are no longer needed
- Running development instances outside working hours
- Unattached EBS volumes
- Old snapshots
- Unused AMIs
- Unused Elastic IP addresses
- Oversized instances
- Idle load balancers
- Over-provisioned Auto Scaling minimums

A resource should not be deleted solely because it appears idle.

First determine:

```text
Resource
   |
   v
Owner?
   |
   v
Purpose?
   |
   v
Required?
   |
   v
Backup?
   |
   v
Safe to remove?
```

## Stopped Instances

Stopping an EC2 instance generally eliminates the instance compute charge while EBS volumes continue to incur storage charges.

This makes stopping useful for temporary development environments.

For example:

```text
Developer Environment
09:00 -> Start
18:00 -> Stop
```

Automating this schedule can reduce non-production compute costs.

Do not automatically stop:

- Production workloads
- Stateful services without lifecycle support
- Systems with strict uptime requirements
- Instances participating in required automation
- Instances whose startup sequence is not reliable

## Development Environment Scheduling

A development environment may run:

```text
24 hours/day
```

even though engineers use it:

```text
10 hours/day
```

Scheduled start/stop can reduce unnecessary runtime.

Example:

```text
Weekday:
08:30 -> Start
20:00 -> Stop

Weekend:
Stopped
```

The exact schedule should follow actual team usage.

Automation should also account for:

- Time zones
- Holidays
- On-call access
- CI/CD jobs
- Integration tests
- Shared environments

## Spot Instances

Spot Instances use spare EC2 capacity and can provide significant savings compared with On-Demand pricing, but they can be interrupted when AWS needs the capacity back.

They are suitable for interruption-tolerant workloads such as:

- Batch processing
- Data processing
- CI workers
- Stateless workers
- Distributed computation
- Certain asynchronous workloads

They are less appropriate as the sole capacity mechanism for workloads that require uninterrupted availability.

A resilient architecture can combine:

```text
ASG
 |
 +-- On-Demand / baseline capacity
 |
 +-- Spot capacity
```

This allows cost optimization without making the entire service dependent on interruptible capacity.

## Savings Plans and Reserved Capacity

Long-running predictable workloads can use commitment-based pricing mechanisms such as Savings Plans.

The decision should be based on:

- Stable baseline demand
- Workload duration
- Organizational commitment
- Forecast accuracy
- Flexibility requirements

Do not commit based on a temporary traffic spike.

A common approach is:

```text
Baseline predictable demand
        |
        v
Commitment
        |
        v
Variable demand
        |
        v
On-Demand / Auto Scaling / Spot
```

This separates predictable capacity from variable capacity.

## On-Demand Capacity

On-Demand is useful when:

- Workloads are unpredictable
- Instances are short-lived
- Flexibility is important
- Capacity requirements are still being learned
- Commitment is undesirable

It may cost more per unit than commitment-based options, but flexibility has operational value.

Cost optimization should account for that value.

## Purchasing Strategy

A production fleet can combine purchasing models.

```text
Required Capacity
       |
       +------------------+
       |                  |
       v                  v
Stable Baseline      Variable Capacity
       |                  |
       v                  +--> On-Demand
Savings Plans            |
                         +--> Spot
```

This is often more flexible than choosing one purchasing model for the entire fleet.

## EBS Cost Optimization

EC2 cost optimization must include EBS.

Review:

- Volume size
- Volume type
- Provisioned IOPS
- Provisioned throughput
- Unattached volumes
- Snapshot retention
- Backup copies

An oversized EBS volume can remain expensive even when the EC2 instance is correctly sized.

## EBS Volume Right-Sizing

Example:

```text
Provisioned:
1 TB gp3

Actual usage:
120 GB
```

The volume may be oversized.

However, reducing EBS capacity requires a migration strategy because shrinking an EBS volume in place is not the normal workflow.

Do not optimize storage size blindly.

Review:

- Actual data usage
- Growth rate
- Backup requirements
- Filesystem behavior
- Application requirements
- Migration effort

## EBS Performance Optimization

EBS cost can also come from unnecessary performance provisioning.

Review:

- IOPS
- Throughput
- Volume type
- EC2 EBS bandwidth
- Application I/O patterns

Example:

```text
Application:
Low I/O workload

Provisioned:
Very high IOPS

Result:
Unused performance capacity
```

Match storage performance to actual requirements.

## Unattached EBS Volumes

Unattached volumes can accumulate after instance termination.

List available volumes:

```bash
aws ec2 describe-volumes \
    --profile production \
    --region ap-south-1 \
    --filters Name=status,Values=available \
    --query 'Volumes[].{
        VolumeId:VolumeId,
        Size:Size,
        Type:VolumeType,
        AZ:AvailabilityZone,
        Created:CreateTime
    }' \
    --output table
```

Do not immediately delete them.

Determine:

- Owner
- Purpose
- Backup status
- Last usage
- Whether recovery depends on them

Then remove confirmed orphaned volumes.

## EBS Snapshot Cost

Snapshots should have lifecycle policies.

Review:

```text
Snapshot
   |
   +-- Owner
   +-- Environment
   +-- Created
   +-- Retention
   +-- Dependency
```

Old snapshots can consume storage over time.

Use automated retention policies where possible.

Do not delete snapshots randomly because later snapshots may depend on the snapshot data chain internally.

Use AWS-supported lifecycle mechanisms and carefully review deletion policies.

## AMI Cleanup

Old AMIs can retain associated EBS snapshots.

Review:

- AMI age
- Application version
- Launch Template references
- ASG usage
- Recovery requirements
- Snapshot dependencies

A common lifecycle is:

```text
New AMI
   |
   v
Deploy
   |
   v
Observe
   |
   v
Retain previous versions
   |
   v
Remove obsolete versions
```

Keep enough historical images to support rollback and recovery requirements.

## Elastic IP Cost

Public IPv4 addresses are a billable resource under current AWS pricing models.

Review:

- Allocated Elastic IPs
- Unused addresses
- Legacy static-IP architectures
- Public IP requirements

List Elastic IPs:

```bash
aws ec2 describe-addresses \
    --profile production \
    --region ap-south-1 \
    --query 'Addresses[].{
        AllocationId:AllocationId,
        PublicIP:PublicIp,
        InstanceId:InstanceId,
        AssociationId:AssociationId
    }' \
    --output table
```

An unassociated Elastic IP should be investigated.

Do not release an address until ownership and dependencies are confirmed.

## Prefer Load Balancers Over Instance Public IPs

A common architecture improvement is:

```text
Before:

Internet
   |
   v
Elastic IP
   |
   v
EC2


After:

Internet
   |
   v
Route 53
   |
   v
ALB
   |
   v
Private EC2
```

The second architecture can improve:

- Availability
- Scaling
- Deployment flexibility
- Instance replacement
- Security isolation

Cost optimization should not be evaluated solely by comparing the price of an Elastic IP with the price of an ALB.

Architecture value matters.

## NAT Gateway Costs

For private EC2 environments, NAT Gateway costs can become significant.

Traffic flow:

```text
Private EC2
    |
    v
NAT Gateway
    |
    v
Internet
```

Costs can be driven by:

- NAT Gateway runtime
- Data processing
- Large package downloads
- Container image pulls
- S3 traffic routed unnecessarily through NAT
- External API traffic

For appropriate AWS service access, consider private connectivity mechanisms such as VPC endpoints where they provide a suitable architecture.

For example:

```text
EC2
 |
 v
VPC Endpoint
 |
 v
S3
```

instead of:

```text
EC2
 |
 v
NAT Gateway
 |
 v
S3
```

The correct design depends on the service and networking requirements.

## Data Transfer Costs

Data transfer can become a larger cost driver than compute for some architectures.

Review:

- Cross-AZ traffic
- Cross-Region traffic
- Internet egress
- NAT Gateway processing
- Large object transfers
- Replication traffic
- Backup copies

A microservices architecture can generate substantial network traffic if services communicate inefficiently across Availability Zones or Regions.

Cost analysis should therefore include the data path:

```text
Client
 |
 v
ALB
 |
 v
EC2
 |
 +--> Redis
 |
 +--> PostgreSQL
 |
 +--> S3
 |
 +--> External API
```

Optimize the expensive traffic paths rather than focusing only on instance pricing.

## Load Balancer Cost Optimization

Review:

- Unused load balancers
- Temporary environments
- Duplicate listeners
- Unused target groups
- Traffic volume
- Environment lifecycle

Do not remove load balancers solely because request volume is low.

An internal or low-traffic load balancer may still provide an important security, routing, or availability boundary.

## Monitoring Cost

Monitoring itself has a cost.

Review:

- CloudWatch Logs ingestion
- Log retention
- Custom metrics
- High-cardinality dimensions
- Detailed monitoring requirements
- Log duplication

For example:

```text
Application
    |
    v
Verbose logs
    |
    v
CloudWatch Logs
    |
    v
High ingestion + storage cost
```

Do not disable observability merely to reduce cost.

Instead:

- Reduce unnecessary log volume
- Set appropriate retention
- Sample noisy telemetry where appropriate
- Keep high-value operational signals
- Archive long-term logs when required

## Non-Production Optimization

Non-production environments are often the easiest place to reduce waste.

Common candidates:

- Development EC2
- Test environments
- QA environments
- Temporary staging environments
- Short-lived CI workers

Useful techniques include:

- Scheduled stop/start
- Smaller instance types
- Auto Scaling
- Spot capacity
- Ephemeral environments
- Automated environment cleanup
- Shorter snapshot retention

Production reliability requirements should not be applied blindly to every development environment.

## Temporary Environments

A temporary environment should have an explicit lifecycle.

Example:

```text
Create
  |
  v
Tag Owner
  |
  v
Tag Expiration
  |
  v
Use
  |
  v
Review
  |
  v
Destroy
```

Example tags:

```text
Environment=temporary
Owner=backend-team
Expires=2026-09-30
Purpose=load-test
```

Automation can identify expired resources for review or cleanup.

## CI/CD Cost Optimization

CI/CD workloads often create short-lived compute demand.

For example:

```text
Git Push
   |
   v
CI Job
   |
   v
Build/Test
   |
   v
Destroy Worker
```

Potential strategies include:

- Ephemeral runners
- Spot capacity where interruption is acceptable
- Right-sized build instances
- Dependency caching
- Container image caching
- Parallelism tuned to actual build time

Do not maximize parallel CI workers blindly. Excess concurrency can increase cost without meaningfully reducing pipeline duration.

## Cost Optimization for Python Applications

Python workloads may be CPU-bound, memory-bound, or concurrency-bound.

For a Django API:

```text
ALB
 |
 v
EC2
 |
 +-- Gunicorn Workers
 |
 +-- DB Connections
 |
 +-- Redis Connections
 |
 +-- Background Tasks
```

Increasing instance size may allow more workers, but can also increase:

- Database connections
- Memory usage
- Redis connections
- Concurrent downstream requests

The optimal instance size therefore depends on the entire request path.

## Gunicorn Worker Capacity

A larger EC2 instance can support more application workers.

However:

```text
More Workers
    |
    +--> More CPU
    +--> More Memory
    +--> More DB Connections
    +--> More Redis Connections
```

If PostgreSQL becomes the bottleneck, adding more EC2 capacity may increase cost without improving throughput.

Cost optimization should therefore identify the actual system bottleneck.

## Celery Worker Cost Optimization

Celery workers should scale based on workload.

A useful signal is:

```text
Queue Depth
     |
     v
Worker Count
```

Instead of:

```text
CPU
 |
 v
Worker Count
```

when CPU is not a good representation of backlog.

For asynchronous workloads, consider:

- Queue depth
- Task execution duration
- Retry rate
- Worker concurrency
- Memory per worker
- Task arrival rate

Workers should scale to the workload while maintaining acceptable queue latency.

## Redis and PostgreSQL Considerations

EC2 cost cannot be optimized independently of dependencies.

Example:

```text
More EC2 Instances
       |
       v
More Application Connections
       |
       v
PostgreSQL Connection Pressure
       |
       v
Database Scaling
       |
       v
Higher Overall Cost
```

Similarly:

```text
More API Instances
       |
       v
More Redis Connections
       |
       v
Higher Cache Load
```

The cheapest EC2 configuration can produce a more expensive overall architecture if it pushes bottlenecks into stateful dependencies.

## Capacity Headroom

Running at extremely high utilization is not automatically cost-efficient.

Example:

```text
Average CPU: 90%
```

This may indicate insufficient headroom.

Traffic spikes can cause:

- Request latency
- Timeouts
- Queue growth
- Autoscaling delays
- Cascading failures

A better target depends on the workload.

The goal is:

```text
Enough headroom
+
Efficient utilization
+
Fast scaling
```

rather than maximum utilization at all times.

## Cost vs Reliability

Cost optimization should not destroy redundancy.

Example:

```text
Cost reduction:
3 instances -> 1 instance
```

This may reduce compute cost but increase:

- Failure impact
- Deployment risk
- Maintenance downtime
- Recovery time

A production architecture should retain the minimum capacity required by its availability objective.

## Cost vs Performance

Reducing instance size can increase:

- CPU contention
- Garbage collection pressure
- Application latency
- Queue depth
- Database connection wait
- Request timeout rate

Always measure after optimization.

A useful evaluation is:

```text
Cost per request
        |
        +
Latency
        |
        +
Error rate
        |
        +
Availability
```

Optimize the overall service rather than one billing line item.

## Cost per Unit of Work

A more useful metric than total monthly spend is often:

```text
Cost per:
- request
- transaction
- job
- customer
- processed GB
- API call
```

For example:

```text
Monthly EC2 Cost
-----------------
Monthly Requests
=
Cost per Request
```

This helps determine whether an architecture is becoming more or less efficient as traffic grows.

## Cost Optimization With Auto Scaling

Suppose:

```text
Minimum: 2
Desired: 2
Maximum: 20
```

If average demand requires only two instances but occasional peaks require ten:

```text
Normal:
2 EC2

Peak:
10 EC2

After peak:
2 EC2
```

This is usually more efficient than running ten instances permanently.

However, scaling must account for:

- Startup time
- Warm-up
- Load balancer registration
- Database capacity
- Cache warm-up
- Application initialization

Fast scaling without dependency capacity can create a new bottleneck.

## Operational Cost Optimization

Engineers should also optimize operational complexity.

A slightly more expensive architecture can be preferable if it significantly reduces:

- Manual operations
- Incident frequency
- Deployment risk
- Recovery time
- Maintenance effort

For example:

```text
Manual EC2 fleet
    |
    +-- SSH
    +-- Manual patching
    +-- Manual scaling
    +-- Manual recovery
```

versus:

```text
IaC
 |
 +-- Golden AMI
 +-- ASG
 +-- ALB
 +-- Automated patching
 +-- Automated recovery
```

The second architecture may have more AWS resources while reducing total operational cost.

## Security and Cost

Cost optimization must not weaken security.

Avoid:

- Removing security controls to save money
- Exposing instances directly to avoid load balancer cost
- Disabling logging without assessing risk
- Sharing production resources unnecessarily
- Removing backups solely to reduce storage cost
- Using weaker instance or network configurations without validation

Security incidents and downtime can cost substantially more than infrastructure savings.

## Cost Optimization Workflow

A production workflow can be:

```text
Inventory
   |
   v
Tag / Ownership
   |
   v
Measure Utilization
   |
   v
Identify Waste
   |
   v
Classify Resource
   |
   +--> Right-size
   +--> Schedule
   +--> Scale
   +--> Delete
   +--> Change Purchasing Model
   +--> Change Architecture
   |
   v
Validate Reliability
   |
   v
Measure Cost Again
```

## Practical CLI Inventory

List running instances:

```bash
aws ec2 describe-instances \
    --profile production \
    --region ap-south-1 \
    --filters Name=instance-state-name,Values=running \
    --query 'Reservations[].Instances[].{
        InstanceId:InstanceId,
        Type:InstanceType,
        AZ:Placement.AvailabilityZone,
        Name:Tags[?Key==`Name`]|[0].Value,
        Environment:Tags[?Key==`Environment`]|[0].Value
    }' \
    --output table
```

List stopped instances:

```bash
aws ec2 describe-instances \
    --profile production \
    --region ap-south-1 \
    --filters Name=instance-state-name,Values=stopped \
    --query 'Reservations[].Instances[].{
        InstanceId:InstanceId,
        Type:InstanceType,
        Name:Tags[?Key==`Name`]|[0].Value,
        Environment:Tags[?Key==`Environment`]|[0].Value
    }' \
    --output table
```

Find unattached EBS volumes:

```bash
aws ec2 describe-volumes \
    --profile production \
    --region ap-south-1 \
    --filters Name=status,Values=available \
    --query 'Volumes[].{
        VolumeId:VolumeId,
        SizeGiB:Size,
        Type:VolumeType,
        AZ:AvailabilityZone
    }' \
    --output table
```

These commands identify candidates. They should not be treated as automatic deletion instructions.

## Cost Optimization Decision Matrix

| Situation | Potential action | Primary risk |
|---|---|---|
| Consistently low utilization | Right-size | Performance degradation |
| Predictable baseline | Savings Plan | Over-commitment |
| Interruptible batch work | Spot | Capacity interruption |
| Development used only during work hours | Scheduled stop/start | Automation dependency |
| Idle EBS volume | Review and delete | Data loss |
| Excessive snapshot retention | Reduce retention | Recovery limitations |
| Large NAT traffic | VPC endpoint / architecture review | Connectivity change |
| Single large instance | Evaluate scale-out | Increased topology complexity |
| High DB pressure | Optimize dependency | Architectural change |
| Idle public IPv4 | Release after validation | Breaking dependency |
| Over-provisioned ASG minimum | Reduce carefully | Availability loss |

## Common Mistakes

### Optimizing CPU Only

Low CPU does not mean an instance is oversized.

The workload may be constrained by:

- Memory
- Network
- EBS
- Database
- Connection limits

**Avoid it:** optimize based on the actual bottleneck.

### Choosing the Cheapest Instance

A cheap instance can create:

- Higher latency
- More instances
- More operational overhead
- More database connections
- Higher total cost

**Avoid it:** optimize total service cost rather than instance price.

### Removing Redundancy

Reducing three instances to one saves compute cost but can create a single point of failure.

**Avoid it:** define minimum availability requirements before reducing capacity.

### Keeping Development Instances Running 24/7

This creates predictable waste.

**Avoid it:** use scheduled lifecycle automation where appropriate.

### Deleting Unattached EBS Volumes Blindly

An unattached volume may contain important recovery data.

**Avoid it:** identify ownership, purpose, backup status, and retention requirements first.

### Keeping Unlimited Snapshots

Old snapshots accumulate storage cost.

**Avoid it:** use explicit retention policies.

### Ignoring Public IPv4 Costs

Unused or unnecessary public IPv4 addresses can create avoidable costs.

**Avoid it:** inventory public addresses and remove confirmed unused resources.

### Ignoring Data Transfer

An optimized EC2 instance can still produce a large bill through network traffic.

**Avoid it:** analyze the complete data path.

### Scaling EC2 Without Scaling Dependencies

Adding API instances can overload PostgreSQL or Redis.

**Avoid it:** model the entire dependency chain.

### Using Spot for Everything

Spot capacity can be interrupted.

**Avoid it:** use it for interruption-tolerant workloads and maintain appropriate baseline capacity.

### Treating Cost Optimization as a One-Time Project

Workloads change.

**Avoid it:** continuously review utilization, architecture, and spend.

## Production Cost Optimization Checklist

### Compute

- [ ] Instance types match workload characteristics
- [ ] CPU utilization reviewed
- [ ] Memory utilization reviewed
- [ ] Network utilization reviewed
- [ ] EBS utilization reviewed
- [ ] Instance startup time measured
- [ ] Right-sizing opportunities evaluated

### Auto Scaling

- [ ] Minimum capacity justified
- [ ] Maximum capacity justified
- [ ] Scaling policies measured
- [ ] Scale-in behavior validated
- [ ] Instance warm-up considered
- [ ] Dependency capacity considered

### Purchasing

- [ ] Baseline demand identified
- [ ] Savings Plans evaluated
- [ ] Spot suitability evaluated
- [ ] On-Demand capacity retained where required
- [ ] Commitments aligned with actual demand

### Storage

- [ ] EBS volumes reviewed
- [ ] Unattached volumes investigated
- [ ] EBS performance right-sized
- [ ] Snapshot retention reviewed
- [ ] Old AMIs reviewed
- [ ] Backup requirements preserved

### Networking

- [ ] Public IPv4 inventory reviewed
- [ ] Elastic IPs reviewed
- [ ] NAT Gateway traffic reviewed
- [ ] VPC endpoints evaluated
- [ ] Cross-AZ traffic reviewed
- [ ] Cross-Region traffic reviewed
- [ ] Internet egress reviewed

### Non-Production

- [ ] Development instances scheduled
- [ ] Test environments cleaned up
- [ ] Temporary resources have owners
- [ ] Temporary resources have expiration
- [ ] CI workers are appropriately sized
- [ ] Non-production retention is controlled

### Reliability and Security

- [ ] Cost changes do not remove required redundancy
- [ ] Backups remain available
- [ ] Monitoring remains enabled
- [ ] Security controls remain intact
- [ ] Recovery requirements remain satisfied
- [ ] Production changes are validated

## Interview Traps

### Is the Cheapest EC2 Instance Always the Most Cost-Effective?

No.

The relevant metric is total workload efficiency, including compute, storage, networking, dependencies, availability, and operational overhead.

### How Do You Identify an Over-Provisioned Instance?

Analyze representative utilization over time across CPU, memory, network, EBS, and application-level metrics, then validate a smaller instance under realistic load.

### Why Is CPU Alone Insufficient for Right-Sizing?

Because an application can be constrained by memory, network, storage I/O, connection limits, or downstream services while CPU remains low.

### How Does Auto Scaling Reduce Cost?

It allows capacity to follow demand instead of permanently maintaining peak capacity.

### Why Not Run One Large Instance?

It may reduce some compute overhead, but it can introduce a single point of failure and make maintenance and scaling less flexible.

### When Are Spot Instances Appropriate?

For workloads that tolerate interruption and can recover or retry work, such as batch processing, distributed workers, and suitable CI workloads.

### What Is the Difference Between Right-Sizing and Auto Scaling?

Right-sizing determines the appropriate capacity of individual instances. Auto Scaling dynamically changes the number of instances based on demand.

### Why Can Adding More EC2 Instances Increase Total Cost Unexpectedly?

More application instances can increase database connections, Redis connections, network traffic, load balancer usage, and other dependency costs.

### Why Should You Investigate Unattached EBS Volumes?

They continue to incur storage costs and may contain important data. They should be identified and safely retired rather than blindly deleted.

### Why Is Cost Optimization a Reliability Concern?

Aggressive cost reduction can remove redundancy, capacity headroom, backup coverage, or monitoring and thereby increase outage risk.

## Key Takeaways

- **Optimize the workload, not just the EC2 line item:** right-size based on CPU, memory, network, EBS, application behavior, dependencies, and availability requirements.
- **Use elasticity for variable demand:** Auto Scaling, scheduled non-production shutdowns, and appropriate Spot usage can reduce idle capacity without permanently sacrificing performance.
- **Treat storage and networking as first-class cost drivers:** EBS, snapshots, public IPv4, NAT Gateway traffic, cross-AZ traffic, and data transfer can materially affect the total architecture cost.
- **Do not trade reliability for small savings:** preserve required redundancy, capacity headroom, backups, monitoring, and security controls when optimizing production systems.
- **Continuously measure cost efficiency:** review utilization, resource ownership, purchasing commitments, and cost per unit of work regularly because workload characteristics and infrastructure requirements change.