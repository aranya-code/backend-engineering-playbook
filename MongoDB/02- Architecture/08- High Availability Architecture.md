# 08- High Availability Architecture

## Overview

High availability (HA) in MongoDB is the ability of a database deployment to continue serving application workloads despite failures of individual infrastructure or database components.

MongoDB high availability is primarily built around replica sets, but production HA is broader than simply running multiple MongoDB instances.

A resilient MongoDB architecture must consider:

- Replica-set topology
- Majority voting
- Automatic elections
- Failure-domain placement
- Write concern
- Read concern
- Read preference
- Replication lag
- Application failover behavior
- Connection pooling
- Network failures
- Storage failures
- Backup and disaster recovery
- Monitoring and alerting
- Capacity planning
- Operational procedures

A useful distinction is:

```text
Replication
    ↓
Copies data between MongoDB members

High Availability
    ↓
Keeps the service usable when components fail

Disaster Recovery
    ↓
Restores service/data after larger failures
```

Replication is a fundamental building block of HA, but replication alone does not guarantee application availability or recoverability.

---

## Availability Model

A production MongoDB deployment typically looks like:

```mermaid
flowchart TB
    Client[Backend Application]

    Client --> Router[Application / Driver Topology]

    subgraph Region["AWS Region"]
        subgraph AZ1["Availability Zone A"]
            P[(MongoDB Primary)]
        end

        subgraph AZ2["Availability Zone B"]
            S1[(MongoDB Secondary)]
        end

        subgraph AZ3["Availability Zone C"]
            S2[(MongoDB Secondary)]
        end
    end

    P -->|Replication| S1
    P -->|Replication| S2

    Router --> P
    Router -. Failover .-> S1
    Router -. Failover .-> S2
```

The objective is that failure of one availability zone or one database server does not permanently prevent the replica set from electing a new primary.

---

## High Availability vs High Durability

These concepts are related but different.

| Property | Primary Goal |
|---|---|
| High availability | Keep service operational during failures |
| Durability | Preserve acknowledged data |
| Consistency | Control what data reads can observe |
| Disaster recovery | Recover from major failures or data loss |
| Scalability | Handle increasing workload |

For example, a three-member replica set improves availability because another member can become primary.

A majority write concern improves durability semantics.

Backups improve recovery from logical data loss.

None of these properties should be treated as interchangeable.

---

## MongoDB HA Building Blocks

A production HA design usually combines:

```text
Replica Set
    +
Failure-Domain Distribution
    +
Majority Voting
    +
Appropriate Write Concern
    +
Driver Topology Discovery
    +
Retry / Idempotency
    +
Monitoring
    +
Backups
    +
Disaster Recovery
```

If any of these are poorly designed, the database may remain technically available while the application still experiences downtime or incorrect behavior.

---

## Replica Set as the HA Foundation

A replica set contains multiple MongoDB members that maintain replicated copies of the dataset.

Typical topology:

```text
             Primary
                │
        ┌───────┴───────┐
        │               │
        ▼               ▼
   Secondary 1     Secondary 2
```

The primary normally handles writes.

Secondaries replicate operations through the oplog and can participate in elections.

If the primary fails:

```text
Primary Failure
      ↓
Failure Detection
      ↓
Election
      ↓
New Primary
      ↓
Driver Topology Update
      ↓
Application Resumes
```

---

## Majority and Fault Tolerance

For a three-member voting replica set:

```text
Members = 3
Majority = 2
```

The deployment can generally tolerate loss of one voting member while retaining a majority.

For five voting members:

```text
Members = 5
Majority = 3
```

It can generally tolerate loss of two voting members while retaining a majority.

| Voting Members | Majority | Members That Can Be Lost While Retaining Majority |
|---:|---:|---:|
| 3 | 2 | 1 |
| 5 | 3 | 2 |
| 7 | 4 | 3 |

More voting members are not automatically better.

Additional members increase:

- network traffic
- replication overhead
- operational complexity
- election coordination

Use additional members when they solve a specific availability, geographic, read, or recovery requirement.

---

## Failure-Domain Design

A replica set should not place all members inside the same failure domain.

Bad:

```text
AWS AZ-A
├── Primary
├── Secondary
└── Secondary
```

If AZ-A becomes unavailable, the entire voting topology disappears.

Prefer:

```text
AWS Region
├── AZ-A
│   └── Primary
├── AZ-B
│   └── Secondary
└── AZ-C
    └── Secondary
```

This provides protection against a single availability-zone failure.

For production, failure-domain placement should consider:

- availability zones
- racks
- hosts
- storage systems
- network paths
- regions
- cloud infrastructure dependencies

---

## Region-Level High Availability

Multi-region deployments introduce additional trade-offs.

Example:

```text
Region A
├── Primary
└── Secondary

Region B
└── Secondary
```

Benefits:

- regional redundancy
- geographically separated data
- disaster-recovery options
- potentially lower-latency reads for some workloads

Costs and risks:

- higher network latency
- cross-region replication traffic
- higher infrastructure cost
- more complex election behavior
- more complicated operational procedures

A remote secondary should not automatically be treated as a cross-region disaster-recovery solution.

The topology must be designed so that the desired failure scenarios still have an appropriate voting majority.

---

## Regional Failure and Majority

Consider:

```text
Region A
├── Primary
└── Secondary

Region B
└── Secondary
```

If Region A fails:

```text
Region A
    X

Region B
    Secondary
```

Only one voting member remains.

The surviving member cannot form a majority of the original three-member voting set.

Therefore, automatic failover may not occur.

A topology designed for regional failure must explicitly account for voting majority.

This is one of the most important HA design considerations.

---

## Election Process

When the primary becomes unavailable, eligible members detect the failure and participate in an election.

Simplified flow:

```mermaid
sequenceDiagram
    participant App as Application
    participant P as Primary
    participant S1 as Secondary 1
    participant S2 as Secondary 2

    App->>P: Write
    P-->>App: Acknowledge

    P-xS1: Failure
    P-xS2: Failure

    S1->>S2: Election coordination
    S2->>S1: Election coordination

    S1->>S1: Election
    S1-->>App: New primary discovered

    App->>S1: Write
```

During an election there may be a short period during which writes fail or are retried.

Applications must be designed to tolerate this transient failure window.

---

## Election Is Not Zero-Downtime

Automatic failover reduces downtime but does not mean:

```text
Primary failure
↓
Zero failed requests
```

A primary election introduces a transition period.

During this period:

- existing connections may fail
- writes may receive transient errors
- topology information changes
- clients must discover the new primary
- transactions may be interrupted

A realistic HA objective is therefore:

> Minimize service interruption and recover automatically from expected infrastructure failures.

---

## Application Failover

MongoDB's HA architecture is incomplete if the application cannot discover the new primary.

A replica-set-aware connection string should contain multiple hosts:

```text
mongodb://mongo1:27017,mongo2:27017,mongo3:27017/app?replicaSet=rs0
```

The driver can discover the topology and identify the current primary.

Avoid:

```text
mongodb://mongo1:27017/app
```

for a production replica set when the application needs automatic failover.

A single-host connection configuration can become an application-level availability bottleneck.

---

## Driver Topology Discovery

The MongoDB driver maintains topology information.

Conceptually:

```text
MongoClient
    │
    ├── mongo1 → PRIMARY
    ├── mongo2 → SECONDARY
    └── mongo3 → SECONDARY
```

After failover:

```text
MongoClient
    │
    ├── mongo1 → DOWN
    ├── mongo2 → PRIMARY
    └── mongo3 → SECONDARY
```

The application does not need to manually change its connection string when the driver is configured correctly.

---

## PyMongo HA Configuration

A production Python application can use:

```python
from pymongo import MongoClient

client = MongoClient(
    "mongodb://mongo1:27017,mongo2:27017,mongo3:27017/app",
    replicaSet="rs0",
    serverSelectionTimeoutMS=5000,
    connectTimeoutMS=5000,
    socketTimeoutMS=10000,
)
```

The `MongoClient` should normally be long-lived and shared within the application process.

Do not create a new client for every HTTP request.

---

## Connection Pooling During Failover

A typical backend process contains:

```text
FastAPI / Django Process
        │
        ▼
    MongoClient
        │
   Connection Pool
   ├── Connection
   ├── Connection
   ├── Connection
   └── Connection
```

During failover, the driver updates its topology and manages connections accordingly.

Application behavior should account for:

- stale connections
- transient selection failures
- temporary unavailable primary
- pool exhaustion
- connection establishment delays

Connection-pool settings should be sized according to application concurrency rather than copied from another environment.

---

## Retryable Operations

Transient failures can occur during:

- elections
- network interruptions
- connection resets
- temporary server unavailability

Supported retryable operations can be retried by MongoDB drivers when retryable behavior is enabled and the deployment supports it.

However:

```text
Driver retry
≠
Business operation retry
```

For example:

```text
Create payment
```

may trigger:

```text
MongoDB write
+
Payment gateway call
+
Kafka event
```

Retrying the entire workflow blindly can duplicate external side effects.

Business-level idempotency remains an application responsibility.

---

## Idempotency

HA systems require careful retry design.

An idempotent operation can safely be repeated.

Example:

```javascript
db.orders.updateOne(
  {
    order_id: "order_1001"
  },
  {
    $set: {
      status: "confirmed"
    }
  }
)
```

Repeating the operation produces the same desired state.

Compare this with:

```text
charge_card()
```

which may not be safe to repeat without an idempotency key.

A production backend should separate:

- database retry semantics
- application retry semantics
- external side-effect semantics

---

## Write Concern and HA

Write concern determines how much acknowledgment the application requires.

For example:

```javascript
{
  w: "majority"
}
```

requires acknowledgment from a majority according to MongoDB's write concern semantics.

This is generally stronger for important business data than relying only on:

```javascript
{
  w: 1
}
```

However, stronger write concern can increase latency or reduce write availability when a majority cannot be reached.

The correct setting depends on the business durability requirement.

---

## Majority Availability

Suppose a three-member replica set has:

```text
Primary
Secondary
Secondary
```

If one secondary fails:

```text
Primary
Secondary
X
```

a majority remains.

Majority writes can continue.

If two members become unavailable:

```text
Primary
X
X
```

the remaining member does not represent a majority of the original voting configuration.

Majority-dependent operations may no longer succeed as before.

This is an intentional safety mechanism.

---

## Read Preference and HA

Read preference determines where reads are routed.

| Mode | HA/Availability Characteristic | Common Use |
|---|---|---|
| `primary` | Consistent primary routing | Transactional APIs |
| `primaryPreferred` | Primary preferred, fallback possible | Some availability-oriented reads |
| `secondary` | Secondary only | Reporting workloads |
| `secondaryPreferred` | Secondary preferred | Read scaling |
| `nearest` | Lowest-latency suitable member | Distributed deployments |

Do not select `secondaryPreferred` simply because "more replicas means faster."

Secondary reads introduce stale-read considerations.

---

## Read After Write

Consider:

```text
POST /orders
     ↓
Primary
     ↓
Success

GET /orders/1001
     ↓
Secondary
     ↓
Order not visible yet
```

The application may incorrectly interpret this as:

```text
Order creation failed
```

when the actual issue is replication lag.

For workflows requiring immediate read-after-write consistency, primary reads or an appropriate session/consistency strategy may be required.

---

## Read Concern and HA

Read concern determines the consistency properties of reads.

The choice should reflect the business requirement.

Examples:

```text
Product catalog
    → weaker consistency may be acceptable

Financial state
    → stronger consistency may be required

Authorization decision
    → stale data may be unacceptable

Analytics dashboard
    → secondary / eventually consistent reads may be acceptable
```

HA and consistency are often a trade-off rather than independent goals.

---

## Network Partitions

Network partitions are among the most important HA failure scenarios.

Consider:

```text
          Network Partition
                 X
                 │
        ┌────────┴────────┐
        │                 │
   Primary             Secondary
   Secondary            Secondary
```

The side with sufficient voting majority can continue election-related operations.

The side without a majority should not independently create a competing primary.

This protects against split-brain behavior.

---

## Split-Brain Protection

A distributed database must prevent two independent nodes from simultaneously acting as authoritative primaries.

MongoDB's replica-set election model uses voting and topology state to control primary eligibility.

Conceptually:

```text
Partition A
2 voting members
    ↓
Majority
    ↓
Can elect primary

Partition B
1 voting member
    ↓
No majority
    ↓
Cannot elect primary
```

This safety mechanism can reduce availability during certain partitions, but it prevents conflicting writable histories.

---

## Failure-Domain Trade-Offs

A three-member deployment can be distributed in several ways.

| Topology | AZ Failure Protection | Regional Failure Protection | Complexity |
|---|---|---|---|
| All members in one AZ | Poor | None | Low |
| One member per AZ | Strong for single-AZ failure | None | Moderate |
| Multi-region majority in primary region | Strong AZ protection | Limited | High |
| Majority distributed across regions | Higher regional resilience | Stronger | Higher latency/complexity |

The topology should be selected from explicit failure requirements.

---

## Hidden and Priority-Zero Members

Specialized members can improve operational resilience.

Examples:

- hidden backup member
- delayed member
- disaster-recovery member
- analytics-oriented member

A priority-zero member cannot become primary.

A hidden member is not normally advertised for ordinary application reads.

These configurations can be useful but reduce the number of eligible failover targets.

Do not configure every secondary as specialized infrastructure without considering election capacity.

---

## Delayed Members

A delayed member intentionally trails the primary.

Example:

```text
Primary
   │
   ├── Secondary 1
   ├── Secondary 2
   └── Delayed Member
           │
           └── Delayed by configured interval
```

This can provide protection against certain logical mistakes.

For example:

```text
Accidental destructive update
        ↓
Primary
        ↓
Normal secondaries replicate it
        ↓
Delayed member still contains earlier state
```

A delayed member does not replace:

- backups
- point-in-time recovery
- restore testing

---

## Backup Is Part of HA Architecture

Replication protects against infrastructure failure.

It does not protect against logical corruption replicated to every member.

Example:

```javascript
db.orders.deleteMany({})
```

can replicate the destructive operation.

Therefore:

```text
Replica Set
    +
Backups
    +
Restore Testing
    +
Disaster Recovery
```

should be treated as one resilience architecture.

---

## Disaster Recovery

High availability usually addresses localized failures.

Disaster recovery addresses larger failures such as:

- region loss
- major infrastructure failure
- destructive operator action
- logical corruption
- ransomware or credential compromise
- catastrophic deployment mistakes

A production DR plan should define:

```text
RPO = acceptable data loss
RTO = acceptable recovery time
```

Example:

```text
RPO: 5 minutes
RTO: 30 minutes
```

The actual values must come from business requirements.

---

## Regional Disaster Recovery

A possible architecture is:

```mermaid
flowchart LR
    subgraph RegionA["Primary Region"]
        P[(Primary)]
        S1[(Secondary)]
    end

    subgraph RegionB["DR Region"]
        S2[(Secondary / DR)]
    end

    P -->|Replication| S1
    P -->|Cross-Region Replication| S2
```

The exact voting configuration must ensure that a regional failure behaves as intended.

If the remote member cannot participate in a majority after the primary region fails, automatic regional failover may not be possible.

For that reason, multi-region topology design must be evaluated mathematically rather than assumed to provide automatic regional failover.

---

## Application Architecture

A typical backend HA architecture is:

```mermaid
flowchart TB
    Client[Client]
    LB[Load Balancer]
    API1[FastAPI / Django Instance]
    API2[FastAPI / Django Instance]

    Client --> LB
    LB --> API1
    LB --> API2

    API1 --> Mongo[(MongoDB Replica Set)]
    API2 --> Mongo

    Mongo --> P[(Primary)]
    Mongo --> S1[(Secondary)]
    Mongo --> S2[(Secondary)]
```

High availability must exist across multiple layers:

```text
Client
  ↓
Load Balancer
  ↓
Application Instances
  ↓
MongoDB Replica Set
  ↓
Storage
```

If only MongoDB is redundant but the API runs on one server, the overall system is still not highly available.

---

## HA Across the Backend Stack

A complete production architecture may look like:

```text
                    Internet
                       │
                       ▼
              Load Balancer / Nginx
                       │
              ┌────────┴────────┐
              ▼                 ▼
         API Instance 1    API Instance 2
              │                 │
              └────────┬────────┘
                       │
                       ▼
                MongoDB Replica Set
                 ┌─────┼─────┐
                 ▼     ▼     ▼
               P      S1     S2

Other HA components:
Redis Cluster / Managed Redis
Kafka Cluster
Multi-AZ Kubernetes
Managed Load Balancer
Centralized Monitoring
Backup / DR
```

This is a system-level HA architecture rather than merely a MongoDB configuration.

---

## Kubernetes and MongoDB HA

When MongoDB is deployed on Kubernetes, the orchestration layer must preserve database assumptions.

Important requirements include:

- persistent storage
- stable member identity
- topology-aware scheduling
- pod anti-affinity or topology spread
- persistent volume availability
- controlled disruption
- backup integration
- monitoring
- upgrade procedures

A conceptual topology is:

```text
Kubernetes Cluster
│
├── AZ-A
│   └── MongoDB Pod 0
│
├── AZ-B
│   └── MongoDB Pod 1
│
└── AZ-C
    └── MongoDB Pod 2
```

Simply running three pods does not guarantee HA if Kubernetes schedules all of them onto the same failure domain.

---

## MongoDB Atlas and Managed HA

MongoDB Atlas can manage much of the infrastructure required for highly available deployments.

The application team still needs to understand:

- replica-set topology
- region selection
- read preference
- write concern
- connection strings
- failover behavior
- backup configuration
- monitoring
- security
- capacity

Managed infrastructure reduces operational work; it does not eliminate architecture decisions.

---

## Storage and HA

Replica-set members depend on reliable persistent storage.

Storage failures can manifest as:

- increased latency
- replication lag
- member failure
- recovery delays
- degraded write performance

Monitor:

- disk utilization
- IOPS
- latency
- throughput
- filesystem capacity
- storage errors

A database server with plenty of CPU but saturated storage is not a healthy HA member.

---

## Capacity Planning

HA requires spare capacity.

Suppose:

```text
Normal workload:
3 servers × 40% utilization
```

If one member fails and workload shifts:

```text
2 servers
```

the remaining servers must still have enough capacity.

Do not design every member to run at:

```text
90–95% utilization
```

under normal load.

The system needs headroom for:

- failover
- traffic spikes
- backups
- initial sync
- index builds
- maintenance
- replication bursts

---

## Read Scaling

Secondaries can serve suitable reads.

For example:

```text
Primary
  └── Writes

Secondary 1
  └── Reporting

Secondary 2
  └── Reporting
```

This can reduce primary read load.

However, read scaling should not compromise transactional correctness.

Good candidates include:

- analytics
- dashboards
- non-critical search
- reporting
- background processing

Poor candidates include workflows that require immediate read-after-write consistency unless the application explicitly handles it.

---

## Write Scaling

Replica sets do not horizontally scale writes across all members.

The primary remains the normal write authority.

Therefore:

```text
Replica Set
    ↓
Read redundancy / HA
```

is different from:

```text
Sharding
    ↓
Horizontal write/data scaling
```

If write throughput exceeds the primary's capacity, adding more secondaries does not solve the write bottleneck.

Sharding may become relevant.

---

## High Availability vs Sharding

| Capability | Replica Set | Sharding |
|---|---|---|
| Data redundancy | Yes | Yes, through shard replica sets |
| Automatic failover | Yes | Yes within shard replica sets |
| Horizontal write scaling | No | Yes |
| Horizontal data scaling | Limited | Yes |
| Primary per dataset | One | One per shard |
| Main purpose | HA/redundancy | Scale data/workload |
| Operational complexity | Lower | Higher |

A sharded MongoDB deployment normally uses replica sets for each shard.

Therefore, sharding and HA are complementary rather than mutually exclusive.

---

## HA and Transactions

MongoDB transactions interact with replica-set availability.

A transaction may fail during:

- primary election
- transient network failure
- member failure
- transaction timeout

Applications should:

- keep transactions short
- minimize unnecessary transaction scope
- use appropriate retry mechanisms
- make transaction workflows idempotent where possible
- avoid external irreversible side effects inside retryable database workflows

A transaction can provide atomicity, but it cannot eliminate infrastructure failure.

---

## HA and Change Streams

Change streams rely on MongoDB replication infrastructure.

A production change-stream consumer should handle:

- temporary connection failure
- primary elections
- resume tokens
- duplicate processing
- consumer restarts
- lag
- backpressure

Conceptually:

```mermaid
flowchart LR
    Mongo[(MongoDB Replica Set)]
    Stream[Change Stream Consumer]
    Kafka[Kafka]
    Worker[Workers]

    Mongo --> Stream
    Stream --> Kafka
    Kafka --> Worker
```

The consumer should resume from a safe position after transient failures.

---

## Monitoring and Alerting

HA requires monitoring both database health and application symptoms.

### MongoDB Metrics

Monitor:

- primary/secondary state
- replication lag
- elections
- oplog window
- connections
- CPU
- memory
- disk latency
- disk capacity
- query latency
- write throughput
- read throughput
- operation failures

### Application Metrics

Monitor:

- request latency
- error rate
- timeout rate
- database selection failures
- connection-pool exhaustion
- retry counts
- failed writes
- failed transactions

### Infrastructure Metrics

Monitor:

- availability-zone health
- network errors
- load balancer health
- storage failures
- Kubernetes pod restarts
- node health

---

## Alerting Strategy

Useful alerts include:

```text
Primary unavailable
Replication lag above threshold
Frequent elections
Oplog window approaching risk threshold
Disk capacity low
Connection pool exhausted
Database operation latency elevated
Secondary unhealthy
Backup failure
Restore validation failure
```

Avoid creating alerts for every transient event.

The objective is to detect conditions that require action before they become outages.

---

## Frequent Elections

A replica set experiencing frequent elections may technically remain available while producing significant application instability.

Potential causes include:

- network instability
- overloaded servers
- storage latency
- CPU exhaustion
- memory pressure
- infrastructure interruptions
- misconfigured deployment

A healthy production system should not treat repeated elections as normal.

Investigate the underlying cause.

---

## Replication Lag and HA

Replication lag reduces the practical value of secondaries.

Example:

```text
Primary
   │
   ├── current position: 1,000,000
   │
   └── Secondary
          current position: 900,000
```

If a secondary is significantly behind:

- secondary reads become stale
- failover may have more recovery implications
- oplog exhaustion becomes possible
- operational recovery becomes more difficult

Replication lag should therefore be both a performance and HA metric.

---

## Connection Failures During Election

Applications may observe:

```text
ServerSelectionTimeoutError
Connection reset
Not primary
Transient transaction error
```

during failover.

The correct response is not necessarily:

```text
Restart the application
```

Instead:

```text
Check replica-set state
↓
Check driver topology
↓
Check connection pool
↓
Check election status
↓
Allow topology discovery/retry
```

Application restart should not be the normal failover mechanism.

---

## Security and HA

Security controls must not accidentally destroy availability.

Examples:

- firewall rules must allow replica-set communication
- TLS certificates must remain valid across all members
- DNS must resolve all configured hosts
- authentication configuration must work after failover
- secret rotation must not break all clients simultaneously

A security configuration that works only against the current primary is incomplete.

---

## Secret Management

Production connection strings should not be committed to Git.

Avoid:

```python
MONGODB_URI = "mongodb://admin:password@mongo1:27017/app"
```

Prefer:

```python
import os

mongodb_uri = os.environ["MONGODB_URI"]
```

Then inject the secret through the deployment platform.

Examples include:

- AWS Secrets Manager
- Kubernetes Secrets
- CI/CD secret stores
- MongoDB Atlas secret integrations

Secret rotation should be tested against failover scenarios.

---

## Operational Changes

Replica-set configuration changes can affect availability.

Examples include:

- changing member priority
- adding a member
- removing a member
- changing votes
- changing hidden status
- changing delayed-member configuration
- moving infrastructure
- upgrading MongoDB

Treat these as production changes.

Use:

```text
Change plan
    ↓
Expected topology
    ↓
Failure analysis
    ↓
Execution
    ↓
Health verification
    ↓
Rollback plan
```

---

## Rolling Maintenance

One advantage of a replica set is that maintenance can often be performed without taking the entire database offline.

Conceptually:

```text
Secondary 1
    ↓
Maintenance

Secondary 2
    ↓
Healthy

Primary
    ↓
Healthy
```

Then another member can be maintained.

For primary maintenance:

```text
Primary
    ↓
Controlled stepdown
    ↓
Election
    ↓
Secondary becomes primary
    ↓
Maintenance
```

Maintenance procedures should be tested before production execution.

---

## Controlled Primary Stepdown

For planned maintenance, an operator can use:

```javascript
rs.stepDown()
```

This is useful for validating:

- application failover
- driver topology discovery
- retry behavior
- election behavior

It should not be used casually during peak traffic.

A controlled failover test is a valuable production-readiness exercise when performed safely.

---

## High Availability Testing

Do not assume HA works because three MongoDB processes are running.

Test:

### Primary Failure

```text
Kill primary
↓
Election
↓
New primary
↓
Application reconnects
```

### Secondary Failure

```text
Stop secondary
↓
Verify primary remains available
↓
Verify replication health after recovery
```

### Network Partition

```text
Simulate connectivity loss
↓
Observe election behavior
↓
Verify no split-brain
```

### Application Failure

```text
Restart API instance
↓
Verify connection recovery
```

### AZ Failure

Where the infrastructure supports it:

```text
Remove one AZ
↓
Verify majority
↓
Verify application availability
```

---

## Chaos Testing

For mature production environments, controlled failure testing can validate assumptions.

Potential experiments:

- terminate a secondary
- step down primary
- introduce network latency
- temporarily block member communication
- restart an application instance
- exhaust connection pools
- simulate storage pressure
- test backup restoration

Chaos testing should be:

- controlled
- observable
- reversible
- approved
- performed against appropriate environments

The purpose is to verify the architecture rather than simply create failures.

---

## Backup and Restore Testing

A backup strategy is incomplete without restore validation.

A production runbook should answer:

```text
Where is the backup?
How recent is it?
Can it be restored?
How long does restore take?
What data is recovered?
How is application consistency verified?
```

A restore test should validate both:

```text
Database recoverability
+
Application correctness
```

---

## Disaster Recovery Runbook

A high-level DR workflow may look like:

```text
Detect Regional Failure
        ↓
Confirm Scope
        ↓
Declare Incident
        ↓
Evaluate Replica / Backup State
        ↓
Promote or Restore DR Environment
        ↓
Validate MongoDB Health
        ↓
Validate Application Connectivity
        ↓
Validate Critical Data
        ↓
Route Traffic
        ↓
Monitor Recovery
        ↓
Reconcile / Resynchronize
```

The exact workflow depends on the deployment architecture.

---

## Cost Considerations

HA increases infrastructure cost.

A production three-member replica set requires additional:

- compute
- storage
- replication network traffic
- monitoring
- backup storage
- operational effort

Multi-region HA increases costs further.

Cost optimization should not simply remove redundancy.

Instead consider:

- appropriate instance sizing
- storage optimization
- managed services
- workload-specific secondary sizing
- backup retention
- archival policies
- read routing
- capacity planning

The target is the required availability level at an acceptable operational cost.

---

## Common Mistakes

### Treating Three Servers as Automatically Highly Available

If all three servers share the same failure domain, one infrastructure failure can remove the entire deployment.

### Hard-Coding the Primary

This makes application availability dependent on one server address.

Use replica-set-aware topology discovery.

### Assuming Elections Are Invisible

Applications can experience transient failures during elections.

Design retries and idempotency accordingly.

### Reading Everything from Secondaries

This can create stale-read bugs.

Route reads based on consistency requirements.

### Using Majority Writes Without Capacity Planning

Majority writes depend on sufficient voting-member availability.

A topology that loses majority may experience write availability degradation.

### Ignoring Replication Lag

A secondary that is technically healthy but severely behind may be unsuitable for reads or failover.

### Treating Replicas as Backups

Logical corruption can replicate to all members.

Maintain independent backups.

### Placing All Members in One AZ

This defeats the purpose of failure-domain redundancy.

### Overloading Secondaries

A secondary used for reporting can become so busy that replication falls behind.

### Ignoring Driver Configuration

A perfect MongoDB topology cannot compensate for an application that connects only to one member.

### Testing HA Only During an Incident

Failover behavior should be tested before it is needed.

---

## Interview Traps

### "Replica sets provide zero downtime."

Not exactly.

They provide automatic failover, but elections and network transitions can cause transient application errors.

### "Three nodes guarantee availability."

Only if the topology, network, storage, and application are correctly designed and a voting majority remains available.

### "More replicas always mean better HA."

Additional members can improve redundancy, but they also add cost and operational complexity.

### "Secondary reads improve availability."

They can improve read distribution, but they introduce stale-read and routing considerations.

### "Replication protects against data corruption."

Replication protects against some infrastructure failures. Logical corruption can replicate to all members.

### "Multi-region replica sets automatically provide regional failover."

Not necessarily.

Voting configuration, majority placement, network latency, and failure-domain design determine whether automatic failover is possible.

### "MongoDB HA means the database is the only redundant component."

No.

Application servers, load balancers, storage, networking, caches, queues, and monitoring infrastructure can all become availability bottlenecks.

---

## Troubleshooting Methodology

### Primary Is Unavailable

```text
Symptom
↓
Possible causes
    ├── Primary process failure
    ├── Network failure
    ├── Storage failure
    ├── Resource exhaustion
    └── Election in progress
↓
Isolation strategy
    ├── Check rs.status()
    ├── Check server logs
    ├── Check infrastructure health
    └── Check application topology
↓
Diagnostic commands
    ├── rs.status()
    ├── rs.conf()
    └── db.serverStatus()
↓
Root cause
↓
Corrective action
    ├── Restore failed member
    ├── Resolve network/storage issue
    └── Allow or initiate controlled failover
↓
Prevention
    ├── Multi-AZ topology
    ├── Monitoring
    └── Failover testing
```

### Application Cannot Reconnect After Failover

```text
Symptom
↓
Possible causes
    ├── Single-host connection string
    ├── Incorrect replicaSet option
    ├── DNS failure
    ├── Connection pool issue
    ├── Election still in progress
    └── Network restriction
↓
Isolation strategy
    ├── Inspect replica-set topology
    ├── Inspect driver logs
    └── Verify network connectivity
↓
Diagnostic commands
    ├── rs.status()
    └── MongoDB connectivity checks
↓
Root cause
↓
Corrective action
    ├── Configure replica-set URI
    ├── Fix DNS/network
    └── Handle transient errors
↓
Prevention
    ├── Automated failover tests
    └── Production connection configuration review
```

### Secondary Is Too Far Behind

```text
Symptom
↓
Possible causes
    ├── High write throughput
    ├── Slow storage
    ├── CPU saturation
    ├── Network latency
    └── Reporting workload
↓
Isolation strategy
    ├── Measure replication lag
    ├── Inspect resource utilization
    └── Identify competing workloads
↓
Diagnostic commands
    ├── rs.status()
    ├── db.serverStatus()
    └── Oplog inspection
↓
Root cause
↓
Corrective action
    ├── Reduce secondary workload
    ├── Increase capacity
    └── Improve storage/network
↓
Prevention
    ├── Lag alerts
    ├── Capacity planning
    └── Appropriate oplog sizing
```

### Region Failure Removes Majority

```text
Symptom
↓
Possible causes
    ├── Majority concentrated in failed region
    ├── Network isolation
    └── Incorrect multi-region topology
↓
Isolation strategy
    ├── Determine surviving voting members
    ├── Check replica-set configuration
    └── Confirm regional connectivity
↓
Diagnostic commands
    ├── rs.status()
    └── rs.conf()
↓
Root cause
↓
Corrective action
    ├── Activate DR procedure
    ├── Restore/promote appropriate infrastructure
    └── Route application traffic
↓
Prevention
    ├── Failure-domain-aware topology
    ├── Tested DR
    └── Explicit RPO/RTO
```

---

## Production Readiness Checklist

### Replica Topology

- [ ] Multiple data-bearing members
- [ ] Members distributed across independent failure domains
- [ ] Voting majority survives expected failures
- [ ] Election priorities reviewed
- [ ] Specialized members have documented purposes

### Application Connectivity

- [ ] Replica-set-aware connection string
- [ ] Multiple hosts configured
- [ ] Long-lived MongoClient
- [ ] Connection pools sized appropriately
- [ ] Server-selection timeout configured
- [ ] Failover behavior tested

### Consistency

- [ ] Write concern explicitly selected
- [ ] Read concern explicitly selected
- [ ] Read preference explicitly selected
- [ ] Read-after-write requirements documented
- [ ] Secondary-read behavior understood

### Reliability

- [ ] Retry behavior tested
- [ ] Idempotency implemented for retryable workflows
- [ ] Transaction failure behavior tested
- [ ] Connection failures handled
- [ ] Primary stepdown tested

### Monitoring

- [ ] Primary health monitored
- [ ] Secondary health monitored
- [ ] Replication lag monitored
- [ ] Election frequency monitored
- [ ] Oplog window monitored
- [ ] Connection usage monitored
- [ ] Storage capacity monitored
- [ ] Database latency monitored

### Disaster Recovery

- [ ] Backups configured
- [ ] Restore tested
- [ ] RPO documented
- [ ] RTO documented
- [ ] DR environment documented
- [ ] Regional failure scenario tested

### Security

- [ ] Authentication enabled
- [ ] Least-privilege users configured
- [ ] TLS configured
- [ ] Network access restricted
- [ ] Secrets managed securely
- [ ] Certificate rotation tested

---

## Key Takeaways

- **MongoDB high availability is a system-level property built on replica sets, failure-domain-aware placement, majority voting, correct driver configuration, monitoring, and tested recovery procedures.**
- **A replica set can automatically fail over, but elections introduce a transient interruption; application clients must support topology discovery, connection recovery, retries, and idempotent operations.**
- **Availability and consistency must be designed together using topology, write concern, read concern, and read preference rather than treating replicas as generic read copies.**
- **Multi-AZ and multi-region architectures must be evaluated against actual majority requirements; simply placing replicas in different regions does not guarantee automatic regional failover.**
- **Replication protects availability and redundancy, while backups and disaster recovery protect against logical corruption, destructive operations, and larger infrastructure failures.**