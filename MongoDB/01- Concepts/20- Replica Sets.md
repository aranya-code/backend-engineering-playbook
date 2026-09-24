# 20- Replica Sets

## Overview

A MongoDB replica set is a group of MongoDB servers that maintain multiple copies of the same dataset and coordinate to provide high availability, automatic failover, and replicated data.

A typical replica set contains:

```text
                    Application
                         |
                         v
                    MongoDB Driver
                         |
                         v
                      Primary
                     /       \
                    v         v
               Secondary   Secondary
```

The primary normally accepts writes. Secondary members continuously replicate the primary's operations and can optionally serve reads according to the configured read preference.

Replica sets are foundational to production MongoDB deployments because they provide:

- High availability.
- Automatic primary elections.
- Data redundancy.
- Replication.
- Failover.
- Read scaling through secondary reads.
- Majority-based durability semantics.
- Support for transactions and change streams.

A replica set is not a backup system. Replication can reproduce accidental updates or deletes across all members, so production systems still require independent backups and recovery procedures.

## Replica Set Architecture

A replica set consists of MongoDB processes that share a common replica-set name and coordinate their state.

A production topology commonly looks like:

```mermaid
flowchart LR
    A[Application] --> D[MongoDB Driver]
    D --> P[Primary]

    P -->|Replication| S1[Secondary 1]
    P -->|Replication| S2[Secondary 2]

    S1 -->|Heartbeat / Election State| P
    S2 -->|Heartbeat / Election State| P

    D -. Read Preference .-> S1
    D -. Read Preference .-> S2
```

The MongoDB driver discovers the topology and maintains awareness of which member is primary, which members are secondary, and which members are eligible for specific operations.

## Primary

The primary is the replica-set member responsible for accepting normal write operations.

Conceptually:

```text
Application
    |
    | write
    v
Primary
    |
    +---- Oplog
    |
    +---- Secondary 1
    |
    +---- Secondary 2
```

The primary records operations in the replica-set oplog. Secondary members replicate those operations.

A replica set has at most one primary under normal operating conditions.

### Primary Responsibilities

The primary:

- Accepts writes.
- Participates in replication.
- Maintains the oplog.
- Serves reads when read preference permits.
- Participates in elections.
- Reports topology state to the replica-set members.

Applications should normally connect using a replica-set-aware MongoDB connection string rather than hard-coding a single primary address.

## Secondary

A secondary maintains a replicated copy of the primary's data.

```text
Primary
   |
   | oplog
   v
Secondary
   |
   v
Apply operations
```

Secondaries continuously process replicated operations.

They can:

- Provide redundancy.
- Participate in elections.
- Serve reads when configured.
- Support backup strategies.
- Provide specialized workload isolation in appropriate architectures.

Secondaries should not be treated as independent databases containing intentionally different application data.

## Oplog

The oplog is a capped collection that records operations that need to be replicated to other members.

Conceptually:

```text
Primary
   |
   v
Oplog
   |
   +---- Secondary 1
   |
   +---- Secondary 2
```

A secondary reads the primary's oplog entries and applies the corresponding operations.

The oplog is therefore central to replication.

### Why the Oplog Matters

The oplog allows secondaries to catch up from the point represented by the retained history.

If a secondary falls too far behind and the required oplog entries are no longer available, it may require an initial synchronization instead of simply continuing from its current position.

## Replication Flow

A simplified replication flow is:

```mermaid
sequenceDiagram
    participant A as Application
    participant P as Primary
    participant O as Oplog
    participant S1 as Secondary 1
    participant S2 as Secondary 2

    A->>P: Write
    P->>O: Record replication operation
    P-->>A: Acknowledge according to write concern
    O->>S1: Replicate operation
    O->>S2: Replicate operation
    S1->>S1: Apply operation
    S2->>S2: Apply operation
```

The exact timing of acknowledgment depends on the configured write concern.

For example:

```text
w: 1
```

can acknowledge after the primary satisfies the requested condition, while:

```text
w: "majority"
```

requires the majority acknowledgment condition.

## Heartbeats

Replica-set members periodically communicate with one another to monitor topology health.

These communications allow members to determine:

- Whether other members are reachable.
- Which members are healthy.
- Which member is primary.
- Whether an election may be required.
- Whether a member is recovering or unavailable.

Conceptually:

```text
Primary
  ↕ heartbeat
Secondary A
  ↕ heartbeat
Secondary B
```

A member becoming unreachable does not immediately mean the entire cluster is unavailable.

The remaining members evaluate the topology and may elect a new primary if the election requirements are satisfied.

## Elections

An election occurs when the replica set needs to select a new primary.

A common trigger is primary failure:

```text
Primary
   |
   X
Failure
   |
   v
Election
   |
   v
Secondary
   |
   v
New Primary
```

Elections can also be triggered by other topology or configuration events.

The purpose of an election is to maintain a single authoritative primary rather than allowing multiple members to independently accept writes.

## Election Flow

A simplified election process is:

```text
Primary becomes unavailable
        |
        v
Members detect failure
        |
        v
Eligible members evaluate topology
        |
        v
Election
        |
        v
Candidate selected
        |
        v
New primary established
        |
        v
Drivers discover new primary
        |
        v
Application resumes writes
```

During an election there can be a temporary period where writes fail or are retried.

Applications should therefore be designed to tolerate transient topology errors.

## Automatic Failover

Automatic failover is one of the main reasons to deploy a replica set.

Without a replica set:

```text
Application
    |
    v
Single MongoDB Server
    |
    X
Failure
    |
    v
Application unavailable
```

With a replica set:

```text
Application
    |
    v
Primary
    |
    X
Failure
    |
    v
Election
    |
    v
New Primary
    |
    v
Application reconnects
```

The MongoDB driver is responsible for topology discovery and reconnecting to the appropriate member.

## MongoDB Driver Topology Discovery

A production application should use a replica-set-aware connection string.

Example:

```text
mongodb://mongo-1:27017,mongo-2:27017,mongo-3:27017/?replicaSet=rs0
```

The driver can discover:

```text
mongo-1 → Primary
mongo-2 → Secondary
mongo-3 → Secondary
```

After an election:

```text
mongo-1 → Secondary
mongo-2 → Primary
mongo-3 → Secondary
```

The application does not need to manually update its connection string.

This is an important distinction between:

```text
Connecting to one MongoDB server
```

and:

```text
Connecting to a replica-set topology
```

## Replica Set Members

Replica-set members can have different configuration properties.

Important member attributes include:

- Priority.
- Votes.
- Hidden status.
- Delay.
- Tags.
- Build indexes behavior where applicable.

These properties allow operators to design specialized topologies.

## Voting Members

Voting members participate in replica-set elections and majority calculations.

A voting member contributes to the quorum used to determine whether a primary can be elected and whether majority write conditions can be satisfied.

For production architecture, voting-member placement should consider failure domains.

Avoid placing all voting members in the same:

- Availability Zone.
- Host.
- Rack.
- Failure domain.

## Priority

Priority influences which members are preferred candidates for becoming primary.

Conceptually:

```text
Member A
priority = higher
      |
      v
Preferred candidate

Member B
priority = lower
      |
      v
Backup candidate
```

Priority is useful when certain members have:

- Better hardware.
- Lower network latency.
- Better availability.
- Preferred geographic placement.

A member with priority `0` cannot become primary.

This can be useful for dedicated secondary or disaster-recovery members.

## Hidden Members

A hidden member participates in replication but is not normally exposed through standard client read routing.

Typical uses include:

- Dedicated backup infrastructure.
- Reporting workloads through controlled access.
- Operational isolation.
- Specialized maintenance workloads.

Hidden members still require appropriate resource capacity and monitoring.

A hidden member is not automatically a backup.

## Delayed Members

A delayed replica-set member intentionally maintains data behind the current primary by a configured delay.

Conceptually:

```text
Primary
   |
   | current state
   v
Normal Secondary

Primary
   |
   | intentional delay
   v
Delayed Secondary
```

A delayed member can provide a recovery point against certain logical mistakes.

For example:

```text
10:00  Correct data
10:05  Accidental delete
10:10  Delete replicated
```

A deliberately delayed member may still contain the pre-delete state at 10:05 depending on its configured delay.

This is a specialized recovery mechanism, not a replacement for proper backups.

## Arbiter

An arbiter participates in elections but does not store a copy of the application data.

Conceptually:

```text
Primary
   |
   +---- Secondary
   |
   +---- Arbiter
```

The arbiter can contribute a vote without contributing data redundancy.

This can help with specific election configurations, but it does not increase the number of stored copies of the data.

For production systems, full data-bearing members are generally preferable when infrastructure capacity permits because they provide both voting and data redundancy.

## Three-Member Replica Set

A common production topology is:

```text
             Primary
             /     \
            v       v
       Secondary  Secondary
```

This provides:

- Three data-bearing copies.
- Majority quorum of two.
- Election capability after one member fails.

Failure example:

```text
Primary
   X
Failure

Secondary A
     +
Secondary B
     |
     v
Election
     |
     v
New Primary
```

The exact behavior depends on member configuration and network connectivity.

## Majority

For a three-voting-member replica set:

```text
Total voting members = 3
Majority = 2
```

For example:

```text
Primary + Secondary A
        |
        v
Majority
```

This concept is used for:

- Elections.
- Majority write concern.
- Replica-set durability semantics.

Majority should not be confused with:

```text
all members
```

A majority means more than half of the voting members.

## Write Concern and Replica Sets

Replica sets make write concern meaningful beyond a single server.

Consider:

```javascript
{
  w: "majority"
}
```

The application requests acknowledgment after the majority requirement has been satisfied.

Conceptually:

```text
Application
    |
    v
Primary
    |
    +---- Secondary A
    |
    +---- Secondary B
    |
    v
Majority acknowledged
    |
    v
Application
```

This generally provides stronger protection against losing an acknowledged write during a primary failure than a primary-only acknowledgment.

## Read Preference and Replica Sets

Read preference determines which members can serve reads.

Examples:

```text
primary
```

```text
secondary
```

```text
secondaryPreferred
```

```text
nearest
```

This enables architectures such as:

```text
Transactional reads
        |
        v
     Primary

Analytics reads
        |
        v
    Secondary
```

The application must explicitly tolerate secondary staleness when using secondary-oriented read preferences.

## Read Preference During Failover

Suppose:

```text
Primary
   |
   X
Failure
```

With:

```text
readPreference = primary
```

reads requiring the primary may temporarily fail or wait for a new primary.

With:

```text
readPreference = primaryPreferred
```

eligible secondary reads may be possible during primary unavailability.

With:

```text
readPreference = secondaryPreferred
```

secondary members are preferred under normal conditions and the primary can be used as fallback.

The availability/consistency trade-off must be intentional.

## Secondary Lag

Secondary lag measures how far a secondary is behind the primary's replication state.

```text
Primary
   |
   | current
   v
Oplog position: 100000

Secondary
   |
   | behind
   v
Oplog position: 99800
```

Lag can increase due to:

- High write volume.
- Slow disk.
- CPU pressure.
- Network problems.
- Large operations.
- Secondary workload.
- Insufficient resources.

Secondary lag matters because it affects:

- Read freshness.
- Failover readiness.
- Backup quality.
- Recovery behavior.

## Monitoring Replication Lag

In `mongosh`, operational inspection can include:

```javascript
rs.status()
```

and:

```javascript
rs.printSecondaryReplicationInfo()
```

Depending on the MongoDB version and deployment, additional monitoring tools and metrics should be used for production observability.

Monitor:

- Replication lag.
- Oplog window.
- Member health.
- Elections.
- Connection counts.
- CPU.
- Memory.
- Disk I/O.
- Network throughput.

## Oplog Window

The oplog has finite capacity.

The important operational concept is the **oplog window**:

```text
Oldest retained operation
        |
        +----------------------+
                               |
                               v
                         Current operation
```

If a secondary is offline longer than the available oplog history, it may not be able to catch up incrementally.

For example:

```text
Oplog window = 12 hours
Secondary offline = 20 hours
```

The secondary may require an initial synchronization.

Production systems should monitor whether the oplog window is sufficient for expected outages and replication delays.

## Initial Sync

Initial synchronization establishes a member's dataset when it cannot catch up from the available replication history.

Conceptually:

```text
New / stale secondary
        |
        v
Initial synchronization
        |
        +---- Copy data
        |
        +---- Build required state
        |
        +---- Catch up replication
        |
        v
Secondary becomes operational
```

Initial sync can consume significant:

- Network bandwidth.
- Disk I/O.
- CPU.
- Source-member resources.

Avoid adding replica members without considering their impact on the existing cluster.

## Rollback

Rollback can occur when a former primary contains operations that were not sufficiently replicated before it lost leadership.

Conceptually:

```text
Old Primary
    |
    +---- Write A
    |
    +---- Write B
    |
    v
Primary failure
    |
    v
New primary elected
    |
    v
Uncommitted operations may be rolled back
```

This is one reason majority write concern is important for durability-sensitive workloads.

Applications should not assume:

```text
primary accepted write
=
write is permanently safe
```

without considering write concern and replica-set state.

## Split-Brain Prevention

A replica set is designed to maintain a single primary under normal election rules.

The election protocol uses voting and topology information to prevent multiple members from independently becoming authoritative primaries.

Network partitions are especially important:

```text
       Partition
          |
    +-----+-----+
    |           |
    v           v
Majority     Minority
```

The side with a majority can maintain the primary role under appropriate conditions.

The minority side cannot simply continue operating as an independent writable primary.

This protects consistency at the cost of availability in some partition scenarios.

## Network Partitions

A network partition can produce:

```text
Region A
Primary + Secondary
       X
Network
       X
Region B
Secondary
```

The isolated member cannot safely assume that it should become primary merely because it cannot contact the existing primary.

Quorum and election rules are designed to avoid multiple writable primaries.

Production topology should therefore place voting members across independent failure domains.

## High Availability

Replica sets provide high availability through:

```text
Replication
    +
Failure detection
    +
Election
    +
Driver topology discovery
    =
Automatic failover
```

A typical application flow is:

```mermaid
sequenceDiagram
    participant App
    participant Driver
    participant P as Primary
    participant S as Secondary

    App->>Driver: Write request
    Driver->>P: Write
    P-->>Driver: Acknowledge
    Driver-->>App: Success

    P-x P: Failure
    S->>S: Election
    S->>Driver: New topology
    App->>Driver: New write
    Driver->>S: Write
    S-->>Driver: Acknowledge
    Driver-->>App: Success
```

There is still a failover interval during which operations may fail or be retried.

High availability does not mean zero downtime.

## Driver Retry Behavior

Modern MongoDB drivers support retry mechanisms for certain transient failures.

Applications should still implement correct error handling.

Important categories include:

- Retryable writes.
- Transient transaction errors.
- Server selection failures.
- Network errors.
- Primary step-down events.

Do not implement application retries as:

```python
while True:
    try:
        write()
        break
    except Exception:
        continue
```

This can create retry storms and duplicate business effects.

Retries should be bounded, observable, and designed around idempotent operations.

## Retryable Writes

Retryable writes can help applications recover from certain transient topology or network failures.

Example connection configuration:

```python
from pymongo import MongoClient

client = MongoClient(
    MONGODB_URI,
    retryWrites=True,
)
```

The exact operations eligible for retry and their semantics depend on the MongoDB deployment and driver version.

Applications should still use:

- Unique business identifiers.
- Idempotency keys where appropriate.
- Bounded retries.
- Error classification.
- Proper logging.

## Transactions and Replica Sets

Replica sets provide the topology required for many MongoDB transaction use cases.

A transaction can span multiple documents and collections while the replica set handles replication and failover semantics.

Conceptually:

```text
Transaction
    |
    +---- Document A
    +---- Document B
    +---- Document C
    |
    v
Commit
    |
    v
Replica-set durability
```

Transactions still need appropriate:

- Read concern.
- Write concern.
- Session management.
- Retry behavior.

Transactions do not remove the need for good data modeling.

## Change Streams and Replica Sets

Change streams depend on MongoDB deployment capabilities that include replica-set infrastructure.

A common event-driven architecture is:

```text
MongoDB Replica Set
        |
        v
Change Stream
        |
        v
Consumer
        |
        +---- Kafka
        +---- Celery
        +---- Search index
        +---- Cache invalidation
```

Change stream consumers should support:

- Resume tokens.
- Retry.
- Idempotency.
- Backpressure.
- Monitoring.
- Consumer restart.

## Production Topology

A production deployment should avoid placing all members on the same failure domain.

Poor topology:

```text
Availability Zone A
    |
    +---- Primary
    +---- Secondary
    +---- Secondary
```

A failure of the zone can remove the entire replica set.

Better:

```text
AZ A              AZ B              AZ C
 |                 |                 |
Primary          Secondary         Secondary
```

This improves resilience against a single-zone failure.

The exact topology depends on:

- Cloud provider.
- Region architecture.
- Latency.
- Cost.
- Election requirements.
- Disaster recovery objectives.

## AWS Deployment Considerations

On AWS, a common topology is:

```text
Region
 |
 +---- AZ-a
 |      |
 |    Primary
 |
 +---- AZ-b
 |      |
 |    Secondary
 |
 +---- AZ-c
        |
      Secondary
```

This protects against failure of a single Availability Zone.

For managed deployments such as MongoDB Atlas, topology configuration should still be evaluated against:

- Region placement.
- Availability zones.
- Election behavior.
- Network latency.
- Backup configuration.
- Cost.

Do not assume that managed infrastructure automatically produces the topology required by the application's RPO and RTO.

## Docker Development Topology

A local replica set is useful for development and testing transaction, change-stream, and failover behavior.

A conceptual Docker topology is:

```text
Docker Network
    |
    +---- mongo-1
    +---- mongo-2
    +---- mongo-3
```

Each MongoDB process must be configured consistently with the same replica-set name.

A production deployment should not blindly copy a development Docker topology.

Development environments typically lack:

- Failure-domain separation.
- Production storage.
- Appropriate security controls.
- Backup architecture.
- Production monitoring.

## Connection String

A replica-set-aware connection string typically contains multiple hosts and the replica-set name:

```text
mongodb://mongo-1:27017,mongo-2:27017,mongo-3:27017/?replicaSet=rs0
```

Production connection strings may additionally include settings related to:

- Authentication.
- TLS.
- Retryable writes.
- Timeouts.
- Read preference.
- Application name.

Example:

```text
mongodb://app_user:REDACTED@mongo-1,mongo-2,mongo-3/orders?replicaSet=rs0&authSource=admin&retryWrites=true
```

Never hard-code credentials in source code or commit them to Git.

## Python Connection Management

Create a long-lived `MongoClient`.

```python
from pymongo import MongoClient

client = MongoClient(
    settings.mongodb_uri,
    serverSelectionTimeoutMS=5_000,
    connectTimeoutMS=5_000,
    retryWrites=True,
)

db = client["orders"]
```

Do not create a new client for every HTTP request.

The client maintains:

- Connection pools.
- Topology information.
- Server monitoring.
- Connection lifecycle.

## FastAPI Integration

A production FastAPI application can create the client during application startup and close it during shutdown.

Conceptually:

```text
FastAPI Startup
      |
      v
MongoClient
      |
      v
Connection pool
      |
      v
Request handlers
      |
      v
MongoDB replica set
      |
      v
FastAPI Shutdown
      |
      v
Close client
```

The client should be shared across requests within the application process.

## Kubernetes Considerations

Kubernetes can manage application workloads around MongoDB, but running a production MongoDB replica set inside Kubernetes requires careful stateful-storage and failure-domain design.

Important concerns include:

- Stateful identities.
- Persistent volumes.
- Storage performance.
- Pod anti-affinity.
- Availability zones.
- Network identity.
- Pod disruption budgets.
- Backup strategy.
- Recovery procedures.
- Upgrade sequencing.

A MongoDB replica set should not be treated like a stateless deployment.

## Security

Every replica-set member should be secured.

Important controls include:

- Authentication.
- Authorization.
- TLS.
- Network restrictions.
- Secret management.
- Encryption at rest.
- Encryption in transit.
- Auditing where required.
- Least-privilege application accounts.

A common mistake is securing the primary while treating secondaries as internal and therefore trusted.

All members contain replicated data and must be protected accordingly.

## Authentication

Applications should use dedicated database users.

For example:

```text
Application User
    |
    +---- Read orders
    +---- Write orders
    +---- No administrative privileges
```

Avoid using an administrative account for application traffic.

Credentials should be stored using:

- Kubernetes Secrets.
- AWS Secrets Manager.
- Environment-specific secret management.
- MongoDB deployment secret mechanisms.

Do not commit credentials to:

- Git.
- Dockerfiles.
- CI logs.
- Application source code.

## Monitoring

Replica-set monitoring should cover both database health and application impact.

Important metrics include:

| Metric | Why it matters |
|---|---|
| Primary availability | Determines write availability |
| Election count | Indicates topology instability |
| Replication lag | Indicates secondary freshness |
| Oplog window | Determines catch-up capacity |
| Connection count | Indicates resource pressure |
| CPU | Detects resource saturation |
| Memory | Detects working-set pressure |
| Disk latency | Can slow replication |
| Disk usage | Prevents capacity failures |
| Network throughput | Detects replication bottlenecks |
| Write latency | Indicates application impact |

## Election Monitoring

Frequent elections are usually a production concern.

Possible causes include:

- Network instability.
- Resource exhaustion.
- Process crashes.
- Host failures.
- Storage problems.
- Configuration issues.

A pattern such as:

```text
Primary elected
    ↓
Primary steps down
    ↓
New primary
    ↓
Another election
    ↓
New primary
```

can cause:

- Write failures.
- Increased latency.
- Retry storms.
- Application errors.
- Transaction interruptions.

Election frequency should therefore be monitored.

## Replication Monitoring

Monitor replication lag continuously.

A simplified relationship is:

```text
Write rate
   +
Secondary processing capacity
   +
Network performance
   |
   v
Replication lag
```

If lag continually grows:

```text
Primary writes > Secondary apply capacity
```

The system is approaching an operational limit.

Possible corrective actions include:

- Query optimization.
- Secondary resource scaling.
- Reporting workload isolation.
- Storage optimization.
- Network improvements.
- Reducing unnecessary write volume.

## Capacity Planning

Replica sets consume resources for both application traffic and replication.

Plan for:

- Data size.
- Index size.
- Oplog size.
- Working set.
- Write throughput.
- Read throughput.
- Replication traffic.
- Connection count.
- Backup workload.
- Recovery workload.

A secondary that is expected to become primary during failover must have sufficient capacity to serve production traffic.

This is a critical planning principle:

> Do not size secondaries only for normal replication; size the failover topology for the workload it must carry after a failure.

## Backups and Replica Sets

Replication is not backup.

Consider:

```text
Application bug
      |
      v
Delete many documents
      |
      v
Primary
      |
      v
Replicated to secondaries
```

All members may now contain the incorrect state.

Backups provide a separate recovery path.

Production systems should define:

- RPO.
- RTO.
- Backup frequency.
- Retention.
- Restore procedures.
- Restore validation.
- Point-in-time recovery where required.

## Disaster Recovery

A replica set primarily provides high availability within its configured topology.

Disaster recovery may require additional infrastructure such as:

- Cross-region deployment.
- Managed backups.
- Point-in-time recovery.
- Independent backup storage.
- Documented recovery procedures.
- Regular restore testing.

Architecture should distinguish:

```text
High Availability
    |
    v
Recover quickly from member failure

Disaster Recovery
    |
    v
Recover from larger infrastructure or logical failures
```

## Operational Commands

Inspect replica-set status:

```javascript
rs.status()
```

Inspect replica-set configuration:

```javascript
rs.conf()
```

Inspect replication information:

```javascript
rs.printSecondaryReplicationInfo()
```

Inspect server status:

```javascript
db.serverStatus()
```

Inspect current operations where appropriate:

```javascript
db.currentOp()
```

These commands provide useful operational information, but production monitoring should not depend solely on manually running shell commands.

## Replica-Set Initialization

A development replica set can be initialized using:

```javascript
rs.initiate({
  _id: "rs0",
  members: [
    { _id: 0, host: "mongo-1:27017" },
    { _id: 1, host: "mongo-2:27017" },
    { _id: 2, host: "mongo-3:27017" }
  ]
})
```

After initialization:

```javascript
rs.status()
```

can be used to inspect the topology.

The exact configuration should match the deployment environment and MongoDB version.

## Production Deployment Principles

A production replica set should generally have:

- Multiple data-bearing members.
- Members distributed across failure domains.
- Replica-set-aware application connections.
- Appropriate write concern.
- Explicit read preference.
- Authentication and authorization.
- TLS.
- Monitoring.
- Backup and restore capability.
- Capacity headroom.
- Tested failover behavior.

Avoid designing a production cluster around the assumption that:

```text
Primary failure
=
zero application impact
```

There can be a failover interval during which requests fail, retry, or experience elevated latency.

## Rolling Maintenance

Replica sets support maintenance without necessarily taking the entire database offline.

A typical operational pattern is:

```text
Secondary
   |
   v
Maintenance
   |
   v
Healthy secondary

Next secondary
   |
   v
Maintenance

Primary
   |
   v
Planned step-down
   |
   v
Another member becomes primary
```

Maintenance should be planned so that sufficient voting and data-bearing capacity remains available.

Before maintenance:

- Verify replica health.
- Verify replication lag.
- Verify backups.
- Confirm capacity.
- Understand election behavior.
- Confirm application retry behavior.

## Version Upgrades

Replica-set upgrades should be performed using a controlled rollout strategy.

A simplified approach is:

```text
Upgrade secondary
      |
      v
Verify health
      |
      v
Upgrade next secondary
      |
      v
Verify health
      |
      v
Controlled primary transition
      |
      v
Upgrade former primary
```

Exact upgrade procedures depend on MongoDB version, deployment architecture, and supported upgrade paths.

Never treat a database version upgrade as an ordinary stateless application deployment.

## Common Mistakes

### Running Only One MongoDB Instance in Production

A single server provides no replica-set failover.

Use multiple members across appropriate failure domains.

### Putting All Members in One Availability Zone

A zone-level failure can remove the entire replica set.

Distribute members across independent failure domains where practical.

### Treating Replicas as Backups

Replication copies logical changes.

It does not protect against accidental or malicious changes.

Use independent backups.

### Hard-Coding the Primary Host

The primary can change after an election.

Use a replica-set-aware connection string and driver topology discovery.

### Ignoring Replication Lag

A lagging secondary can affect:

- Read freshness.
- Failover readiness.
- Backup recovery.
- Application behavior.

### Using Secondary Reads for Critical Decisions

Stale reads can cause incorrect business decisions.

Use primary-oriented or appropriately consistent reads for critical workflows.

### Under-Sizing Secondaries

If a secondary cannot handle the production workload after becoming primary, failover may preserve availability but still result in severe performance degradation.

### Ignoring Oplog Window

A secondary that remains offline beyond the available oplog history may require initial synchronization.

### Assuming Elections Are Free

Elections can cause temporary write unavailability and increased latency.

Applications must handle them.

### Using Arbitrarily Large Retry Loops

Retries without limits can amplify a database outage.

Use bounded retries and exponential backoff where appropriate.

## Troubleshooting Methodology

### Primary Unavailable

```text
Symptom
↓
Application cannot write
↓
Possible causes
- Primary failure
- Election in progress
- Network partition
- Authentication/connectivity issue
- Replica-set health problem
↓
Isolation strategy
- Inspect replica-set state
- Check application topology discovery
- Check network connectivity
- Check server health
↓
Diagnostic commands
```

```javascript
rs.status()
```

```javascript
rs.conf()
```

```text
Root cause
↓
Determine whether an election is required or already occurring
↓
Corrective action
- Restore failed member
- Resolve network problem
- Allow election to complete
- Fix application connection configuration
↓
Prevention
- Multi-member topology
- Failure-domain distribution
- Monitoring
- Failover testing
```

### Secondary Lagging

```text
Symptom
↓
Secondary replication lag increases
↓
Possible causes
- High write rate
- Slow disk
- CPU saturation
- Network latency
- Heavy secondary reads
↓
Isolation strategy
- Check replication metrics
- Check host resources
- Inspect workload
- Check oplog window
↓
Diagnostic commands
```

```javascript
rs.printSecondaryReplicationInfo()
```

```javascript
db.serverStatus()
```

```text
Root cause
↓
Secondary cannot apply operations quickly enough
↓
Corrective action
- Increase resources
- Optimize workload
- Isolate reporting queries
- Improve storage/network
↓
Prevention
- Capacity planning
- Lag alerts
- Workload monitoring
```

### Secondary Requires Initial Sync

```text
Symptom
↓
Secondary cannot catch up from oplog
↓
Possible causes
- Member offline too long
- Oplog window too small
- Replication history unavailable
↓
Isolation strategy
- Check secondary state
- Check oplog window
- Check member uptime
↓
Diagnostic commands
```

```javascript
rs.status()
```

```text
Root cause
↓
Required oplog history is no longer available
↓
Corrective action
- Perform initial sync according to deployment procedure
- Ensure sufficient storage and network capacity
↓
Prevention
- Size oplog appropriately
- Monitor oplog window
- Alert on replication lag
```

### Frequent Elections

```text
Symptom
↓
Primary changes repeatedly
↓
Possible causes
- Network instability
- Host instability
- Resource exhaustion
- Storage problems
- Process crashes
↓
Isolation strategy
- Correlate election timestamps
- Inspect host metrics
- Inspect MongoDB logs
- Check network health
↓
Diagnostic commands
```

```javascript
rs.status()
```

```text
Root cause
↓
Identify member or infrastructure instability
↓
Corrective action
- Resolve network/resource issue
- Replace unstable host
- Review topology
↓
Prevention
- Infrastructure monitoring
- Capacity headroom
- Election alerts
- Failure testing
```

## Production Checklist

- [ ] Use multiple data-bearing members.
- [ ] Distribute members across independent failure domains.
- [ ] Configure a replica-set-aware connection string.
- [ ] Use appropriate write concern.
- [ ] Define read preference intentionally.
- [ ] Monitor replication lag.
- [ ] Monitor oplog window.
- [ ] Monitor elections.
- [ ] Monitor primary availability.
- [ ] Protect every member with authentication and network security.
- [ ] Enable TLS where required.
- [ ] Use least-privilege database users.
- [ ] Maintain independent backups.
- [ ] Test restores.
- [ ] Test primary failover.
- [ ] Test secondary failure.
- [ ] Test application retry behavior.
- [ ] Verify secondaries can handle failover traffic.
- [ ] Plan rolling maintenance.
- [ ] Document RPO and RTO.
- [ ] Maintain operational runbooks.

## Architecture Decision Guide

| Requirement | Replica-set design consideration |
|---|---|
| Basic high availability | Multiple data-bearing members |
| Automatic failover | Multiple voting members with suitable topology |
| Zone-level resilience | Distribute members across zones |
| Stronger write durability | Majority write concern |
| Read scaling | Secondary read preference where staleness is acceptable |
| Geographic reads | Topology-aware or latency-aware read preference |
| Dedicated reporting | Specialized secondary/topology configuration |
| Backup | Independent backup system |
| Disaster recovery | Cross-region/managed backup architecture |
| Event-driven processing | Change streams + idempotent consumers |
| Financial transactions | Replica set + appropriate transaction/read/write concerns |
| High write throughput | Capacity planning for primary and replication |
| Large datasets | Evaluate sharding separately from replica-set HA |

## Senior-Level Design Principles

### Design for Failure, Not Just Normal Operation

A replica set is valuable because failure is expected.

Evaluate:

```text
What happens when:
- Primary fails?
- Secondary fails?
- Network partitions?
- A zone fails?
- Replication falls behind?
- Oplog window becomes insufficient?
- Election takes longer than expected?
- The application retries a write?
```

### Size for Failover

If three members normally distribute workloads:

```text
Primary:    60% capacity
Secondary:  20% capacity
Secondary:  20% capacity
```

do not assume the system is safe merely because normal traffic fits.

After primary failure, one secondary may need to carry most or all production workload.

Failover capacity must be part of capacity planning.

### Keep Consistency Policies Explicit

Replica-set topology, read preference, read concern, and write concern together define important application behavior.

Do not hide them in arbitrary repository defaults.

### Treat Elections as Application Events

Applications should be designed to tolerate:

- Temporary write failures.
- Connection changes.
- Increased latency.
- Transaction interruption.
- Retryable errors.

### Separate HA From DR

Replica sets address high availability and replication.

Backups and disaster recovery address broader failure scenarios.

Both are required for production systems.

## Interview Traps

### What is a MongoDB replica set?

A group of MongoDB instances that maintain replicated copies of the same dataset and coordinate to provide high availability and automatic failover.

### What is the role of the primary?

The primary normally accepts writes and serves as the authoritative writable member of the replica set.

### What is the role of a secondary?

A secondary replicates the primary's operations and can provide redundancy, participate in elections, and serve reads when configured.

### What happens when the primary fails?

Eligible members detect the failure, an election can occur, and a new primary can be selected if the replica set has sufficient quorum.

### What is the oplog?

The oplog is the replication log used by secondary members to reproduce operations performed on the primary.

### Does replication equal backup?

No.

Replication can replicate accidental or malicious changes. Independent backups are still required.

### What is majority?

A majority is more than half of the voting members.

For three voting members:

```text
Majority = 2
```

### Why are elections necessary?

They establish a new authoritative primary after the existing primary becomes unavailable or steps down.

### What is replication lag?

The delay between the replication state of the primary and a secondary.

### What happens when a secondary falls too far behind?

If the required oplog history is no longer available, the member may require an initial synchronization.

### Why distribute replica-set members across Availability Zones?

To avoid a single zone failure taking down all members.

### Can a secondary become primary?

Yes, if it is eligible and wins an election.

### Can an arbiter store data?

No.

An arbiter participates in voting but does not maintain a data-bearing copy.

### Why might a hidden member be useful?

It can provide a specialized member for controlled workloads such as backups or operational tasks without being a normal client read target.

### Why is majority write concern important?

It provides stronger durability semantics by requiring the write to satisfy the replica-set majority acknowledgment condition rather than relying only on primary acknowledgment.

### Can a replica set scale writes horizontally?

No.

A replica set primarily provides redundancy and read scaling. MongoDB sharding is the architecture used for horizontal partitioning of data and write workload across shards.

## Key Takeaways

- A MongoDB replica set provides **replication, redundancy, automatic elections, and high availability** through a coordinated group of MongoDB members with a primary and one or more secondaries.
- The **oplog, heartbeats, elections, and majority quorum** form the core mechanisms that allow replica sets to detect failures, replicate data, and establish a new primary.
- Production applications should use **replica-set-aware connection strings and MongoDB drivers**, design for transient election failures, and ensure secondaries have enough capacity to handle production traffic after failover.
- **Replication is not backup**; accidental deletes, corrupted writes, and application errors can propagate to every replica, so independent backups, restore testing, and disaster recovery procedures remain necessary.
- Senior-level replica-set design requires thinking beyond member count: distribute failure domains, monitor replication lag and oplog windows, define consistency policies, test elections and failures, and size the topology for both normal operation and failover.