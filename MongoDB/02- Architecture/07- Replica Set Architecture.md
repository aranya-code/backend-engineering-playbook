# 07- Replica Set Architecture

## Overview

A MongoDB replica set is a group of MongoDB instances that maintain the same dataset through replication and provide high availability through automatic elections and failover.

A typical replica set contains:

- One primary
- One or more secondaries
- Replication metadata and an oplog
- Election and heartbeat mechanisms

The primary normally accepts writes. Secondaries replicate the primary's operations and can serve reads when an appropriate read preference is configured.

A production replica set provides:

- High availability
- Automatic failover
- Data redundancy
- Read scaling for suitable workloads
- Operational flexibility
- The foundation for transactions and change streams

The important engineering point is that replication is not simply "copying data to another server." It is a distributed coordination mechanism involving the oplog, heartbeats, elections, write concern, read concern, replication lag, and failure handling.

---

## Replica Set Architecture

A basic three-member replica set looks like:

```mermaid
flowchart LR
    App[Backend Application]

    P[(Primary)]
    S1[(Secondary 1)]
    S2[(Secondary 2)]

    App -->|Writes| P
    App -->|Reads| P

    P -->|Oplog Replication| S1
    P -->|Oplog Replication| S2

    S1 -. Optional Reads .-> App
    S2 -. Optional Reads .-> App
```

The primary is responsible for accepting writes and publishing operations through the replication log.

Secondaries replicate those operations and maintain their own copies of the dataset.

If the primary becomes unavailable, eligible members participate in an election and one secondary can become the new primary.

---

## Replica Set Members

### Primary

The primary is the current writable member.

Typical application traffic:

```text
Application
    ↓
Primary
    ↓
Write
```

The primary:

- accepts writes
- records operations in the oplog
- replicates operations to secondaries
- participates in elections
- serves reads according to read preference

Only one member is normally primary at a time.

---

## Secondary

A secondary maintains a replicated copy of the primary's data.

Typical flow:

```text
Primary
   ↓
Oplog
   ↓
Secondary
   ↓
Apply Operations
```

Secondaries can:

- provide redundancy
- participate in elections
- serve eligible reads
- support backups or reporting workloads depending on configuration
- maintain additional copies for disaster recovery

A secondary should not automatically be treated as a generic read replica. Read preference, consistency requirements, workload characteristics, and replication lag must be considered.

---

## Replica Set Topology

A common production topology is:

```text
             ┌──────────────┐
             │   Primary    │
             │   MongoDB    │
             └──────┬───────┘
                    │
          ┌─────────┴─────────┐
          │                   │
          ▼                   ▼
 ┌────────────────┐   ┌────────────────┐
 │   Secondary 1  │   │   Secondary 2  │
 │   MongoDB      │   │   MongoDB      │
 └────────────────┘   └────────────────┘
```

For production systems, the members should generally be distributed across independent failure domains such as:

```text
Availability Zone A
    Primary

Availability Zone B
    Secondary

Availability Zone C
    Secondary
```

This reduces the risk that a single infrastructure failure removes a majority of voting members.

---

## Why a Three-Member Replica Set Is Common

A three-member replica set provides:

- one primary
- two secondaries
- three voting members
- the ability to lose one voting member while retaining a majority

For example:

```text
3 voting members
Majority = 2
```

If one member fails:

```text
2 remaining
    ↓
Majority retained
```

An election can still occur if the primary is the failed member.

This is a major reason production systems commonly use an odd number of voting members.

---

## Voting Members

Replica-set members can participate in elections through voting.

The voting majority is important for:

- elections
- majority write acknowledgment
- maintaining cluster availability

For a replica set with:

```text
3 voting members
```

the majority is:

```text
2
```

For:

```text
5 voting members
```

the majority is:

```text
3
```

Adding more voting members does not automatically improve application performance. It increases coordination and operational complexity.

---

## Election and Failover

MongoDB uses an election mechanism to select a new primary when the existing primary becomes unavailable.

Simplified flow:

```mermaid
sequenceDiagram
    participant P as Primary
    participant S1 as Secondary 1
    participant S2 as Secondary 2
    participant A as Application

    A->>P: Write request
    P-->>A: Acknowledgment

    P-xS1: Failure / unreachable
    P-xS2: Failure / unreachable

    S1->>S2: Election coordination
    S2->>S1: Election coordination

    S1->>S1: Become eligible candidate
    S1-->>A: New primary discovered

    A->>S1: New write
```

The actual election protocol is more sophisticated than this simplified sequence, but the operational model is:

```text
Primary failure
      ↓
Failure detection
      ↓
Election
      ↓
New primary
      ↓
Clients rediscover primary
      ↓
Application resumes writes
```

---

## Heartbeats

Replica-set members continuously communicate with each other.

Heartbeats allow members to determine:

- whether another member is reachable
- whether it is primary or secondary
- member health
- replica-set topology information
- election-related state

A network partition can therefore affect the replica set even when MongoDB processes themselves are healthy.

For example:

```text
MongoDB Process
      │
      ├── Healthy
      │
      └── Network unreachable
```

From the perspective of other members, the server may be unavailable.

---

## Failure Detection

A primary does not immediately become "failed" because one application request times out.

Replica-set health is based on communication between members and the replica-set protocol.

Application-level failures and replica-set failures are different:

```text
Application
    ↓
Connection timeout
```

does not necessarily mean:

```text
MongoDB primary failed
```

Possible causes include:

- application network failure
- DNS problems
- connection-pool exhaustion
- firewall rules
- overloaded server
- primary election
- actual process failure

Troubleshooting should isolate these possibilities.

---

## Oplog

The oplog is the replication log used by secondaries to reproduce operations performed on the primary.

Conceptually:

```text
Primary
   │
   ├── Write
   │
   └── Oplog entry
          │
          ├── Secondary 1
          └── Secondary 2
```

The oplog is stored in the `local` database.

Secondaries use it to determine which operations they need to apply.

The oplog is a critical component of:

- replication
- secondary catch-up
- change streams
- rollback behavior
- initial synchronization workflows

---

## Oplog Replication Flow

A simplified replication flow is:

```mermaid
flowchart LR
    Write[Client Write]
    Primary[Primary]
    Oplog[Primary Oplog]
    Secondary[Secondary]
    Apply[Apply Operation]

    Write --> Primary
    Primary --> Oplog
    Oplog --> Secondary
    Secondary --> Apply
```

The secondary tracks its replication position and continuously attempts to stay close to the primary.

---

## Replication Lag

Replication lag is the delay between an operation being committed on the primary and that operation becoming available on a secondary.

Example:

```text
Primary:
10:00:00 write

Secondary:
10:00:00.500 apply

Lag:
500 ms
```

Large lag can be caused by:

- high write throughput
- slow disks
- CPU saturation
- memory pressure
- network latency
- long-running operations
- secondary workload
- insufficient hardware

Replication lag matters when applications read from secondaries.

---

## Why Replication Lag Matters

Suppose:

```text
POST /orders
    ↓
Primary
    ↓
Order created
```

Immediately afterward:

```text
GET /orders/1001
    ↓
Secondary
```

If the secondary has not applied the write yet, the read may not observe the newly created order.

This creates a common production behavior:

```text
Write succeeds
     ↓
Secondary read
     ↓
Data appears missing
```

This is not necessarily data loss.

It can be a consistency/read-routing issue.

---

## Read Preference

MongoDB supports different read preferences that determine where reads may be routed.

Common modes include:

| Read Preference | Behavior | Typical Use |
|---|---|---|
| `primary` | Read only from primary | Strongest default application consistency |
| `primaryPreferred` | Primary when available | Prefer primary but tolerate fallback |
| `secondary` | Read from secondary | Reporting/read scaling |
| `secondaryPreferred` | Prefer secondary | Read-heavy workloads |
| `nearest` | Lowest network latency suitable member | Geo/distributed deployments |

For many transactional backend applications, `primary` is the safest default unless the application explicitly understands secondary-read consistency.

---

## Primary Reads

Default-style application behavior:

```text
Application
     │
     ├── Write ──→ Primary
     │
     └── Read ───→ Primary
```

Advantages:

- straightforward consistency model
- avoids stale secondary reads
- simpler application behavior

Limitations:

- primary handles most traffic
- read scaling is limited

This is often appropriate for transactional workloads.

---

## Secondary Reads

A read-heavy system may intentionally use:

```text
Application
    │
    └── Read
          ↓
      Secondary
```

Advantages:

- distributes read workload
- protects primary from some read traffic
- useful for reporting or analytics

Risks:

- stale data
- replication lag
- inconsistent read observations
- more complicated failure behavior

Secondary reads should be an explicit architectural decision.

---

## Read Preference Is Not a Consistency Guarantee

Choosing:

```text
secondaryPreferred
```

does not mean:

```text
eventually consistent everywhere
```

in a simple application-level sense.

Actual visibility depends on:

- replication state
- read concern
- write concern
- session behavior
- topology
- selected member
- workload

Consistency should therefore be designed using read concern, write concern, read preference, and application semantics together.

---

## Write Concern

Write concern controls how much acknowledgment the client requires before considering a write successful.

Examples include:

```javascript
{
  w: 1
}
```

and:

```javascript
{
  w: "majority"
}
```

Conceptually:

```text
w: 1
    ↓
Primary acknowledges

w: "majority"
    ↓
Majority acknowledgment requirement
```

The exact durability semantics depend on the deployment and configuration.

---

## Majority Write Concern

For a three-member replica set:

```text
Primary
Secondary 1
Secondary 2
```

a majority means:

```text
2 voting members
```

A majority write provides stronger protection against losing the acknowledged operation during a primary failure than a primary-only acknowledgment.

For business-critical writes, majority write concern is commonly preferred.

---

## Write Concern Trade-offs

| Configuration | Benefit | Trade-off |
|---|---|---|
| `w: 1` | Lower write latency | Weaker replication acknowledgment |
| `w: "majority"` | Stronger durability semantics | Potentially higher latency |
| Higher explicit `w` | More acknowledgments | More latency and failure sensitivity |
| `w: 0` | Minimal client wait | No write acknowledgment |

Do not select write concern purely for performance.

Base it on the business consequences of an acknowledged write being lost or rolled back.

---

## Read Concern

Read concern determines the consistency characteristics of data returned by reads.

Common levels include:

- `local`
- `available`
- `majority`
- `linearizable`
- `snapshot`

The correct choice depends on the operation.

For example:

```text
Ordinary read
    → local / default-style behavior may be sufficient

Critical consistency boundary
    → stronger read concern may be appropriate

Transaction
    → snapshot semantics may be relevant
```

Read concern should be evaluated together with read preference and write concern.

---

## Read and Write Consistency

A production request can involve several independent decisions:

```text
                MongoDB
                   │
        ┌──────────┼──────────┐
        │          │          │
   Read Concern Write Concern Read Preference
        │          │          │
        └──────────┼──────────┘
                   │
             Application
```

For example:

```text
Write to primary
    ↓
majority acknowledgment
    ↓
Read from primary
```

has very different semantics from:

```text
Write to primary
    ↓
w: 1
    ↓
Read from secondary
```

The latter can observe a lagging view.

---

## Rollback

A rollback can occur when a primary accepts operations that do not become part of the surviving majority history before that primary is replaced.

Conceptually:

```text
Old Primary
    │
    ├── Write A
    ├── Write B
    └── Network partition
           │
           ▼
New Primary elected
           │
           ▼
Old Primary rejoins
           │
           ▼
Conflicting operations reconciled
```

Operations that were not preserved in the surviving history may be rolled back.

This is one reason write concern matters.

For important business writes, application design should avoid assuming that every acknowledged operation has identical durability semantics.

---

## Initial Sync

A new secondary must obtain the dataset and replication history required to become a functioning member.

Conceptually:

```text
New Secondary
      ↓
Initial Sync
      ↓
Copy Data
      ↓
Catch Up from Oplog
      ↓
Secondary State
```

Initial synchronization can generate significant:

- disk I/O
- network traffic
- CPU usage
- storage activity

Do not casually add or rebuild replica-set members on heavily loaded production systems without capacity planning.

---

## Secondary Lag and Initial Sync

A secondary may fall behind temporarily:

```text
Primary
  │
  ├── 1000 writes/sec
  │
  ▼
Secondary
  └── applies 800 writes/sec
```

The lag grows over time.

If the secondary cannot catch up before the relevant oplog history is no longer available, it may require a new initial sync.

This makes oplog sizing an important operational consideration.

---

## Hidden Members

A hidden member is not advertised for ordinary application reads but can still maintain replicated data.

Possible uses include:

- dedicated backup workloads
- operational reporting
- disaster-recovery support
- specialized maintenance operations

A hidden member should not automatically be treated as a free backup server.

Its configuration and workload must be designed carefully.

---

## Priority

Replica-set members can have different election priorities.

Conceptually:

```text
Primary Candidate
      │
      ├── High priority
      └── Low priority
```

Priority can influence which members are preferred during elections.

This is useful when:

- some servers have better capacity
- some availability zones are preferred
- certain nodes should not become primary
- hidden or specialized members should remain secondary

Priority should be designed alongside failure-domain placement.

---

## Priority 0 Members

A priority-zero member cannot become primary.

This can be useful for:

- delayed members
- specialized backup nodes
- disaster-recovery members
- geographically remote members

However, removing election eligibility also changes the topology's failover capacity.

Do not use priority zero without understanding the resulting voting and availability characteristics.

---

## Delayed Members

A delayed member intentionally remains behind the primary.

This can provide a recovery mechanism for certain operational failures, such as an accidental destructive write.

Conceptually:

```text
Primary
   │
   ├── Secondary 1
   ├── Secondary 2
   └── Delayed Member
          │
          └── Intentionally behind
```

A delayed member is not a replacement for backups or point-in-time recovery.

It is a specialized recovery control.

---

## Arbiter Considerations

An arbiter participates in elections but does not store a copy of the dataset.

This can reduce storage requirements, but it also provides no data redundancy.

For modern production designs, adding an arbiter merely to achieve a voting majority should be evaluated carefully.

A data-bearing secondary generally provides more operational value because it contributes both:

- voting capacity
- data redundancy

---

## Replica Set States

Members transition through different operational states.

Common concepts include:

- PRIMARY
- SECONDARY
- STARTUP
- STARTUP2
- RECOVERING
- ROLLBACK
- ARBITER
- UNKNOWN
- DOWN
- REMOVED

The exact state is important during troubleshooting.

For example:

```text
PRIMARY
   ↓
Failure
   ↓
SECONDARY
   ↓
Election
   ↓
PRIMARY
```

An unexpected state such as `RECOVERING` or `ROLLBACK` requires investigation before treating the member as healthy.

---

## Replica Set Status

Use `mongosh` to inspect replica-set status:

```javascript
rs.status()
```

This provides information about:

- member state
- health
- election state
- replication status
- operation times
- heartbeat information
- member identity

A concise topology check can begin with:

```javascript
rs.status().members.map(member => ({
  name: member.name,
  stateStr: member.stateStr,
  health: member.health
}))
```

---

## Replica Configuration

Inspect the replica-set configuration with:

```javascript
rs.conf()
```

This is useful for reviewing:

- member names
- member IDs
- priority
- votes
- hidden settings
- delayed configuration
- replica-set identity

Configuration changes should be treated as production changes rather than casual shell operations.

---

## Replica Set Initiation

A development replica set can be initiated with:

```javascript
rs.initiate({
  _id: "rs0",
  members: [
    { _id: 0, host: "mongo1:27017" },
    { _id: 1, host: "mongo2:27017" },
    { _id: 2, host: "mongo3:27017" }
  ]
})
```

The hostname used in the replica-set configuration must be reachable by all replica-set members and by clients as required by the deployment.

Do not use container-local hostnames that clients cannot resolve in a production Kubernetes or external-client topology.

---

## Connection Strings

Applications should generally use a replica-set-aware connection string.

Example:

```text
mongodb://mongo1:27017,mongo2:27017,mongo3:27017/app?replicaSet=rs0
```

For authentication:

```text
mongodb://app_user:password@mongo1:27017,mongo2:27017,mongo3:27017/app?replicaSet=rs0&authSource=admin
```

In production:

- do not hard-code credentials
- use TLS
- use secret management
- configure appropriate timeouts
- use the correct replica-set name
- validate server discovery and failover behavior

---

## Python and PyMongo

PyMongo's `MongoClient` handles replica-set topology discovery.

Example:

```python
from pymongo import MongoClient

client = MongoClient(
    "mongodb://mongo1:27017,mongo2:27017,mongo3:27017/app",
    replicaSet="rs0",
    serverSelectionTimeoutMS=5000,
    connectTimeoutMS=5000,
    socketTimeoutMS=10000,
)

db = client["app"]
```

The client discovers the current primary rather than permanently binding application writes to one server.

This is essential for automatic failover.

---

## Connection Pooling

`MongoClient` manages connection pooling internally.

In a web application:

```text
Application Process
       │
       └── MongoClient
              │
              ├── Connection
              ├── Connection
              ├── Connection
              └── Connection
```

Create a client per application process rather than constructing a new client for every request.

For example:

```python
from pymongo import MongoClient

mongo_client = MongoClient(
    settings.mongodb_uri,
    serverSelectionTimeoutMS=5000,
)
```

Then reuse:

```python
mongo_client["app"]["orders"]
```

throughout the process.

---

## FastAPI Lifecycle

A FastAPI application can initialize a shared MongoDB client during application startup.

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pymongo import MongoClient


mongo_client: MongoClient | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global mongo_client

    mongo_client = MongoClient(
        "mongodb://mongo1:27017,mongo2:27017,mongo3:27017/app",
        replicaSet="rs0",
        serverSelectionTimeoutMS=5000,
    )

    mongo_client.admin.command("ping")

    yield

    mongo_client.close()


app = FastAPI(lifespan=lifespan)
```

With synchronous PyMongo, database operations are blocking. For high-concurrency async FastAPI workloads, use a supported async MongoDB driver strategy appropriate to the application's current MongoDB/PyMongo ecosystem rather than assuming synchronous calls are non-blocking.

---

## Django Integration

Django applications using MongoDB through PyMongo should similarly maintain a long-lived client.

Do not create a new MongoClient for every request:

```python
def view(request):
    client = MongoClient(...)
```

Prefer a shared application-level client managed through configuration and lifecycle.

The replica set should be part of the connection configuration so the driver can discover topology changes.

---

## Failover from an Application Perspective

Suppose:

```text
Application
    ↓
Primary A
```

Primary A fails:

```text
Application
    ↓
Primary A
    X
```

Replica set elects:

```text
Secondary B
     ↓
New Primary
```

The driver detects the topology change:

```text
MongoClient
    ↓
Topology Discovery
    ↓
New Primary
```

The application should be designed to tolerate transient errors during the election window.

---

## Retryable Writes

MongoDB drivers support retryable write behavior for supported operations and deployments.

Applications should still distinguish:

```text
Transient infrastructure failure
```

from:

```text
Business-level failure
```

Retries should be carefully designed around idempotency.

For example:

```text
Create payment
```

requires more careful retry semantics than:

```text
Update document to status = "processed"
```

because an application-level retry may duplicate an external side effect even if MongoDB itself handles a retry safely.

---

## Transaction Behavior During Elections

Transactions are tied to server sessions and replica-set topology.

An election can interrupt an in-progress transaction.

Applications should therefore:

- use appropriate retry patterns
- keep transactions short
- avoid unnecessary transaction scopes
- handle transient transaction errors
- avoid external side effects inside a transaction unless the side-effect workflow is explicitly designed for retries

A transaction should not be treated as an automatic solution to distributed workflow consistency.

---

## Change Streams and Replica Sets

Change streams depend on MongoDB replication infrastructure.

A typical architecture is:

```mermaid
flowchart LR
    App[Application]
    Primary[(Primary)]
    Secondary[(Secondary)]
    Stream[Change Stream Consumer]
    Kafka[Kafka]

    App --> Primary
    Primary --> Secondary
    Primary --> Stream
    Stream --> Kafka
```

Change streams can be used for:

- cache invalidation
- asynchronous processing
- integration events
- search synchronization
- analytics pipelines

Consumers should persist or otherwise safely manage resume information and process events idempotently.

---

## High Availability

High availability depends on more than having three MongoDB processes.

A production design should consider:

- independent availability zones
- network isolation
- storage reliability
- sufficient voting members
- appropriate election priority
- replication lag
- monitoring
- backup and restore
- connection-string topology discovery
- application retry behavior
- operational runbooks

Example:

```text
AWS Region
│
├── AZ-A
│    └── Primary
│
├── AZ-B
│    └── Secondary
│
└── AZ-C
     └── Secondary
```

This protects against a single-AZ failure more effectively than:

```text
One AZ
├── Primary
├── Secondary
└── Secondary
```

---

## Network Partitions

A network partition can create asymmetric visibility:

```text
Partition A
    Primary

        X

Partition B
    Secondary
    Secondary
```

If the primary cannot communicate with a majority, it may step down.

The secondary side can elect a new primary if it has the required voting majority.

This prevents both sides from independently accepting writes as primary, reducing split-brain risk.

---

## Split-Brain Prevention

MongoDB's replica-set election protocol is designed around majority voting.

The goal is to ensure:

```text
Only a member with sufficient election support
can become primary
```

This is why majority availability matters.

A topology where a network partition leaves two isolated groups without a clear majority is intentionally conservative.

The system may sacrifice write availability rather than allow conflicting primaries.

---

## Failure Scenarios

| Failure | Expected Behavior |
|---|---|
| Secondary failure | Primary continues if majority remains |
| Primary failure | Eligible secondary can be elected |
| One AZ failure | Healthy if voting majority remains |
| Network partition | Election may occur |
| Secondary lag | Reads may become stale |
| Oplog window exhausted | Secondary may require resync |
| Storage failure | Member becomes unhealthy |
| Application connection failure | Driver reconnects/topology updates |
| Majority unavailable | Majority writes may stop succeeding |

Actual behavior depends on topology, configuration, write concern, and failure conditions.

---

## Monitoring Replica Sets

Important metrics include:

### Replication Lag

Monitor the difference between primary and secondary operation progress.

Large lag can indicate:

- CPU pressure
- disk pressure
- network problems
- excessive workload
- slow queries
- insufficient capacity

### Member Health

Track:

```text
PRIMARY
SECONDARY
DOWN
RECOVERING
ROLLBACK
```

### Elections

Unexpected frequent elections are an operational signal.

Possible causes include:

- unstable network
- overloaded servers
- resource exhaustion
- infrastructure failures
- aggressive operational changes

### Connections

Monitor:

- connection count
- connection utilization
- rejected connections
- pool saturation

### Storage

Track:

- disk utilization
- disk latency
- data growth
- oplog growth
- free space

---

## Oplog Monitoring

The oplog window is particularly important.

Conceptually:

```text
Oplog Window
<---------------------------->

Secondary lag
        <---->
```

If:

```text
secondary lag > oplog window
```

the secondary may no longer be able to catch up incrementally.

It may require initial synchronization.

For high-write systems, oplog sizing should account for expected write bursts and operational recovery time.

---

## Production Health Checks

A basic operational check can begin with:

```javascript
rs.status()
```

Then inspect:

```javascript
rs.conf()
```

and server statistics:

```javascript
db.serverStatus()
```

For replication-related information:

```javascript
db.getSiblingDB("local").oplog.rs.stats()
```

Operational diagnostics should be interpreted in the context of:

- workload
- member state
- lag
- disk performance
- elections
- application traffic

---

## Backup Strategy

Replication is not backup.

A replica set protects against:

- server failure
- some infrastructure failures
- primary failure

It does not inherently protect against:

- accidental deletion
- malicious modification
- application bugs
- destructive migrations
- logical corruption

If an application executes:

```javascript
db.orders.deleteMany({})
```

the deletion can replicate to every member.

Therefore:

```text
Replication ≠ Backup
```

A production system still needs tested backups and recovery procedures.

---

## Disaster Recovery

A disaster-recovery design should define:

```text
RPO
RTO
```

### RPO

How much data loss is acceptable?

### RTO

How long can recovery take?

Replica-set redundancy can reduce local failure recovery time, but disaster recovery may require:

- managed backups
- point-in-time recovery
- geographically separate infrastructure
- tested restore procedures
- documented operational runbooks

For critical systems, recovery testing should be performed regularly.

---

## Security

Replica-set traffic should be secured in production.

Important controls include:

- TLS for client connections
- TLS for member-to-member communication where required
- authentication
- authorization
- least-privilege users
- network restrictions
- secret management
- audit logging where required

A production connection string should not expose credentials in source control.

Use mechanisms such as:

```text
AWS Secrets Manager
Kubernetes Secrets
Environment-injected secrets
Managed MongoDB secret configuration
```

The exact mechanism should match the deployment environment and security architecture.

---

## Deployment with Docker

A development replica set can be run with multiple MongoDB containers.

Conceptually:

```text
Docker Network
│
├── mongo1
├── mongo2
└── mongo3
```

All containers must be able to resolve and communicate using the hostnames configured in:

```javascript
rs.initiate({
  _id: "rs0",
  members: [
    { _id: 0, host: "mongo1:27017" },
    { _id: 1, host: "mongo2:27017" },
    { _id: 2, host: "mongo3:27017" }
  ]
})
```

For production, prefer a managed MongoDB service or a carefully engineered deployment platform rather than treating a development Docker Compose replica set as production infrastructure.

---

## Kubernetes Considerations

Running MongoDB on Kubernetes introduces additional operational requirements:

- persistent volumes
- stable network identities
- pod disruption handling
- storage performance
- topology spread
- anti-affinity
- backup integration
- monitoring
- upgrade procedures

Replica-set members should not all be scheduled onto the same failure domain.

For example:

```text
MongoDB StatefulSet
        │
        ├── Pod 0 → AZ-A
        ├── Pod 1 → AZ-B
        └── Pod 2 → AZ-C
```

The orchestration layer must preserve stable identity and storage semantics.

---

## MongoDB Atlas

MongoDB Atlas manages many replica-set infrastructure concerns for production deployments.

A backend engineer still needs to understand:

- replica-set topology
- regions
- read preferences
- write concerns
- replication lag
- failover
- connection strings
- backups
- monitoring
- security

Managed infrastructure reduces operational burden but does not eliminate architectural responsibility.

---

## Cost Considerations

A replica set increases infrastructure requirements because data is replicated.

Three members generally imply:

```text
More compute
+
More storage
+
More network replication
+
More monitoring
```

However, the cost should be evaluated against the cost of:

- downtime
- data loss
- recovery
- operational incidents
- unavailable APIs

For production workloads, redundancy is generally an availability requirement rather than an optional optimization.

---

## Common Mistakes

### Running a Single MongoDB Instance in Production

A single instance provides no automatic failover.

### Putting All Members in One Availability Zone

An AZ failure can remove the majority of the voting topology.

### Assuming Replication Is Backup

Replicated deletes and corruption can affect every member.

### Reading from Secondaries Without Understanding Lag

This can create stale-read behavior that appears as application inconsistency.

### Using `w: 1` Everywhere

Write concern should reflect business durability requirements.

### Ignoring Oplog Window

A secondary can fall so far behind that incremental catch-up becomes impossible.

### Creating MongoClient Per Request

This creates unnecessary connection-management overhead.

### Hard-Coding the Primary Host

Applications should use replica-set-aware connection strings and driver topology discovery.

### Ignoring Elections

Frequent elections are not normal background noise. They are an operational signal that should be investigated.

### Using an Arbiter as a General Replacement for a Secondary

An arbiter provides voting capacity but no data redundancy.

### Treating Replicas as Read Scaling by Default

Secondaries can serve reads, but doing so introduces consistency and workload-management considerations.

---

## Interview Traps

### "A replica set is just a primary with read replicas."

Incomplete.

Replica sets provide replication, elections, failover, voting, oplog-based synchronization, and topology management.

### "Three nodes means you can always lose two nodes."

No.

A three-member voting replica set normally requires a majority for election and majority-based operations.

Losing two members leaves only one voting member, so a new primary generally cannot be elected.

### "Replication means zero data loss."

No.

Durability depends on write concern, failure timing, topology, and recovery behavior.

### "Secondary reads are always eventually consistent."

The behavior depends on read preference, read concern, sessions, topology, and replication state.

### "MongoDB automatically handles every application retry."

No.

Drivers provide retry mechanisms for supported operations, but business-level idempotency and external side effects remain application responsibilities.

### "Replication replaces backups."

It does not.

Replication protects availability and provides redundancy; backups protect against logical and operational data-loss scenarios.

### "Adding more replicas always improves performance."

Additional members increase replication and coordination overhead and may provide little benefit if the workload is not designed to use them.

---

## Troubleshooting Methodology

### Primary Keeps Changing

```text
Symptom
↓
Possible causes
    ├── Network instability
    ├── Server overload
    ├── Disk latency
    ├── Process crashes
    └── Infrastructure failure
↓
Isolation strategy
    ├── Inspect rs.status()
    ├── Review server metrics
    ├── Check logs
    └── Inspect network health
↓
Diagnostic commands
    ├── rs.status()
    ├── rs.conf()
    └── db.serverStatus()
↓
Root cause
↓
Corrective action
    ├── Stabilize infrastructure
    ├── Resolve resource pressure
    └── Fix network configuration
↓
Prevention
    ├── Election monitoring
    ├── Capacity planning
    └── Multi-AZ deployment
```

### Secondary Is Lagging

```text
Symptom
↓
Possible causes
    ├── High write volume
    ├── Slow disk
    ├── CPU saturation
    ├── Network latency
    └── Secondary workload
↓
Isolation strategy
    ├── Compare replication progress
    ├── Check resource metrics
    └── Check slow operations
↓
Diagnostic commands
    ├── rs.status()
    ├── db.serverStatus()
    └── oplog inspection
↓
Root cause
↓
Corrective action
    ├── Remove competing workload
    ├── Increase capacity
    └── Improve storage/network
↓
Prevention
    ├── Lag alerts
    ├── Capacity planning
    └── Appropriate oplog sizing
```

### Application Cannot Write After Failover

```text
Symptom
↓
Possible causes
    ├── Driver topology not configured correctly
    ├── Connection pool state
    ├── Election still in progress
    ├── DNS/network failure
    └── Retry configuration
↓
Isolation strategy
    ├── Check rs.status()
    ├── Check application logs
    └── Verify replica-set connection string
↓
Diagnostic commands
    ├── rs.status()
    └── connection/topology diagnostics
↓
Root cause
↓
Corrective action
    ├── Use replica-set-aware URI
    ├── Reuse MongoClient
    └── Handle transient errors
↓
Prevention
    ├── Failover testing
    ├── Driver configuration tests
    └── Application retry strategy
```

---

## Production Readiness Checklist

### Topology

- [ ] Multiple data-bearing members
- [ ] Members distributed across failure domains
- [ ] Appropriate voting configuration
- [ ] Election priorities reviewed
- [ ] No unnecessary arbiter dependency

### Application

- [ ] Replica-set-aware connection string
- [ ] Long-lived MongoClient
- [ ] Appropriate server selection timeout
- [ ] Appropriate socket/connect timeouts
- [ ] Retry strategy reviewed
- [ ] Idempotency considered

### Consistency

- [ ] Write concern selected intentionally
- [ ] Read concern selected intentionally
- [ ] Read preference selected intentionally
- [ ] Secondary-read behavior understood
- [ ] Replication lag monitored

### Operations

- [ ] Replica-set health monitored
- [ ] Election alerts configured
- [ ] Replication lag alerts configured
- [ ] Oplog window monitored
- [ ] Disk capacity monitored
- [ ] Connection usage monitored

### Recovery

- [ ] Backups configured
- [ ] Restore procedures documented
- [ ] Recovery tested
- [ ] RPO defined
- [ ] RTO defined
- [ ] Disaster-recovery architecture reviewed

### Security

- [ ] Authentication enabled
- [ ] Least-privilege users configured
- [ ] TLS configured
- [ ] Network access restricted
- [ ] Secrets stored securely
- [ ] Audit requirements addressed

---

## Key Takeaways

- **A MongoDB replica set provides replication, automatic elections, failover, and data redundancy; production availability depends on topology, majority voting, and failure-domain placement.**
- **The oplog is central to replication, and replication lag plus oplog-window capacity must be monitored because an excessively lagging secondary may require resynchronization.**
- **Read preference, read concern, and write concern jointly determine important consistency and durability behavior; secondary reads should never be introduced without understanding stale-read implications.**
- **Applications should use replica-set-aware connection strings and long-lived MongoDB clients, while explicitly handling transient failures, elections, retries, and idempotency.**
- **Replication is not backup: production systems still require tested backups, recovery procedures, monitoring, security controls, and disaster-recovery planning.**