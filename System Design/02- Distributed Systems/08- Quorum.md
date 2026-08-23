# 08- Quorum

## Overview

Quorum is a distributed-systems mechanism that requires a defined subset of nodes or replicas to participate successfully in an operation before that operation is considered complete.

The core idea is simple:

> Do not require every replica to respond, but require enough replicas to provide the desired fault-tolerance and consistency properties.

Quorums are commonly used in:

- Leaderless replication
- Distributed databases
- Replicated storage
- Consensus-related systems
- Distributed locking
- Cluster membership
- Service coordination

A typical replicated system may have:

```text
N = 3 replicas

        +---------+
        | Replica |
        |    A    |
        +---------+
             |
             |
+---------+  |  +---------+
| Replica |--+--| Replica |
|    B    |     |    C    |
+---------+     +---------+
```

Instead of waiting for all three replicas, a system may require only two:

```text
Required acknowledgements = 2

Replica A → ACK
Replica B → ACK
Replica C → unavailable

Operation → SUCCESS
```

This provides a balance between:

- Availability
- Latency
- Fault tolerance
- Consistency

Quorum is not a single consistency model. It is a mechanism whose actual guarantees depend on how it is implemented and combined with replication, ordering, versioning, failure detection, and conflict resolution.

---

## Why Quorum Exists

Distributed systems frequently replicate data because a single machine is a failure point.

Without replication:

```text
Application
     |
     v
Database
     |
     X
   Failure
```

Replication improves resilience:

```text
             Database
          /      |      \
         v       v       v
        N1      N2      N3
```

However, requiring every replica to respond creates another problem.

If:

```text
N1 → healthy
N2 → healthy
N3 → failed
```

and every operation requires all three nodes, the system becomes unavailable.

A quorum allows the system to tolerate some failures:

```text
N1 → ACK
N2 → ACK
N3 → FAILED

Required = 2

Result → SUCCESS
```

The system therefore avoids making every replica a mandatory dependency.

---

## Quorum Terminology

Several variables are commonly used when discussing quorum replication.

| Symbol | Meaning |
|---|---|
| `N` | Number of replicas for the data |
| `W` | Number of replicas required to acknowledge a write |
| `R` | Number of replicas consulted for a read |
| `Q` | Generic quorum size |
| `RF` | Replication factor |

For a replicated dataset:

```text
N = 3
```

there may be:

```text
N1
N2
N3
```

A write quorum might be:

```text
W = 2
```

and a read quorum:

```text
R = 2
```

These parameters define how much coordination an operation requires.

---

## Quorum Size

For a cluster with `N` members, a simple majority quorum is commonly represented as:

```text
Q = floor(N / 2) + 1
```

Examples:

| Nodes | Majority Quorum |
|---:|---:|
| 1 | 1 |
| 3 | 2 |
| 5 | 3 |
| 7 | 4 |
| 9 | 5 |

The purpose of majority quorum is to ensure that two independent majorities cannot both exist simultaneously.

For:

```text
N = 5
Q = 3
```

two groups cannot both contain three distinct nodes because:

```text
3 + 3 > 5
```

Therefore, any two majorities must overlap by at least one node.

This intersection property is fundamental to many distributed coordination algorithms.

---

## Read and Write Quorums

In leaderless replication, read and write quorums are commonly represented as:

```text
N = Total replicas

W = Write quorum

R = Read quorum
```

For example:

```text
N = 3
W = 2
R = 2
```

The write requires two replica acknowledgements.

The read consults two replicas.

Conceptually:

```text
Write Quorum

N1  N2
 |   |
 +---+
   |
  ACK


Read Quorum

N2  N3
 |   |
 +---+
   |
  READ
```

The two quorum sets overlap.

---

## Quorum Intersection

A commonly discussed condition for read/write quorum overlap is:

```text
R + W > N
```

For:

```text
N = 3
R = 2
W = 2
```

we have:

```text
2 + 2 > 3
```

Therefore, a read quorum and write quorum must share at least one replica when selected from the same replica set.

Example:

```text
Write quorum:
N1 N2

Read quorum:
   N2 N3
   ^^
   overlap
```

The shared replica provides an opportunity for the read to observe information associated with the write.

However, this equation should not be interpreted as:

> `R + W > N` guarantees strong consistency.

That conclusion is too simplistic.

Actual consistency depends on:

- Version semantics
- Read semantics
- Write semantics
- Concurrent writes
- Failure behavior
- Repair
- Ordering
- Conflict resolution
- Clock assumptions
- Database implementation

---

## Majority Quorum vs Read/Write Quorum

These concepts are related but should not be treated as identical.

### Majority Quorum

A majority generally means:

```text
Q > N / 2
```

For:

```text
N = 5
```

a majority is:

```text
3
```

### Read/Write Quorum

Read/write quorum allows separate values:

```text
R = 1
W = 3
```

or:

```text
R = 3
W = 1
```

or:

```text
R = 2
W = 2
```

The appropriate configuration depends on the system's consistency and availability requirements.

---

## Write Quorum

Consider:

```text
N = 5
W = 3
```

A client writes:

```text
user_id = 123
plan = premium
```

The coordinator sends the write to all relevant replicas:

```text
             Coordinator
             /    |    \
            v     v     v
           N1    N2    N3
```

Suppose:

```text
N1 → ACK
N2 → ACK
N3 → ACK
N4 → timeout
N5 → timeout
```

Because:

```text
3 ACKs >= W
```

the operation can be considered successful according to that quorum configuration.

The remaining replicas may catch up later.

---

## Write Quorum and Failure Tolerance

For:

```text
N = 5
W = 3
```

the system can potentially tolerate two unavailable replicas while still completing a write:

```text
N1 → ACK
N2 → ACK
N3 → ACK
N4 → DOWN
N5 → DOWN
```

But if three replicas are unavailable:

```text
N1 → ACK
N2 → ACK
N3 → DOWN
N4 → DOWN
N5 → DOWN
```

then:

```text
ACKs = 2
W = 3
```

and the write cannot satisfy the quorum.

This demonstrates a fundamental trade-off:

> A larger quorum can provide stronger overlap properties but requires more healthy replicas to remain available.

---

## Read Quorum

Consider:

```text
N = 5
R = 3
```

The coordinator queries replicas:

```text
N1
N2
N3
N4
N5
```

It only needs enough valid responses to satisfy:

```text
R = 3
```

For example:

```text
N1 → version 20
N2 → version 20
N3 → version 21
N4 → timeout
N5 → timeout
```

The system has received three responses.

If version metadata indicates that version 21 is authoritative, the coordinator can return version 21 and potentially repair stale replicas.

---

## Quorum Does Not Mean Every Replica Is Current

Suppose:

```text
N = 3
W = 2
```

A successful write might produce:

```text
N1 → v42
N2 → v42
N3 → v41
```

The client receives success because:

```text
2 replicas acknowledged v42
```

But N3 is still stale.

Therefore:

```text
Successful quorum write
        ≠
All replicas immediately synchronized
```

The system may rely on:

- Read repair
- Background repair
- Hinted handoff
- Anti-entropy
- Log replay
- Replica synchronization

to eventually converge N3.

---

## Read-After-Write Behavior

Quorums can influence read-after-write visibility.

Consider:

```text
N = 3
W = 2
R = 2
```

A write reaches:

```text
N1
N2
```

A subsequent read reaches:

```text
N2
N3
```

The intersection is:

```text
N2
```

Therefore, the read has an opportunity to observe the new value.

However, this does not mean every system automatically provides linearizable read-after-write semantics.

The implementation must correctly handle:

- Version selection
- Concurrent writes
- Clock skew
- Replica failures
- Read repair
- Network partitions
- Request ordering

---

## Quorum and Stale Reads

Suppose:

```text
N1 → v10
N2 → v10
N3 → v11
```

A read with:

```text
R = 1
```

might contact N1 and return:

```text
v10
```

even though v11 exists elsewhere.

A read with:

```text
R = 2
```

might contact:

```text
N1 → v10
N3 → v11
```

and identify v11 as the newer version.

This demonstrates why increasing the read quorum can reduce the probability of stale reads.

The exact behavior remains implementation-dependent.

---

## Quorum Trade-offs

Increasing quorum size generally increases coordination.

For example:

```text
N = 5
```

Compare:

```text
W = 1
```

with:

```text
W = 4
```

`W = 1`:

- Lower write latency
- Higher write availability
- More replicas can temporarily lag
- Weaker overlap guarantees

`W = 4`:

- Higher write coordination
- Lower write availability during failures
- More replicas acknowledge before success
- Stronger overlap characteristics

The correct value depends on workload requirements.

---

## Latency

Quorum operations are usually constrained by the responses required to satisfy the quorum.

Suppose:

```text
N = 5
W = 3
```

and response times are:

```text
N1 → 15 ms
N2 → 20 ms
N3 → 30 ms
N4 → 100 ms
N5 → 150 ms
```

If the coordinator needs three acknowledgements, approximate completion may be:

```text
max(15, 20, 30)
≈ 30 ms
```

assuming the system can accept the fastest three successful responses.

This can be better than waiting for all five.

However, quorum size should not be chosen solely from average latency.

Tail latency matters:

```text
p50
p95
p99
p99.9
```

A slow replica can become disproportionately important if the quorum requires it.

---

## Geographic Quorums

Consider three regions:

```text
India
Europe
US
```

with one replica in each.

A quorum might require:

```text
2 of 3 regions
```

A write could therefore require:

```text
India ✓
Europe ✓
US ✗
```

This provides regional fault tolerance but introduces cross-region latency.

If the system instead uses:

```text
India ✓
India ✓
India ✓
```

the quorum may be faster but does not provide the same regional failure tolerance.

Therefore, quorum placement matters.

---

## Quorum Placement

A sophisticated system should consider **where** replicas are located, not only how many exist.

Suppose:

```text
Region A:
N1
N2

Region B:
N3

W = 2
```

A write could succeed entirely inside Region A.

If Region A fails:

```text
N1 ✗
N2 ✗
N3 ✓
```

the system cannot satisfy:

```text
W = 2
```

even though one replica remains healthy.

A better topology might distribute replicas across failure domains:

```text
AZ-1 → N1
AZ-2 → N2
AZ-3 → N3
```

Now an availability-zone failure may still leave enough replicas to satisfy quorum.

---

## Failure Domains

Quorums should be designed around actual failure domains.

Possible failure domains include:

- Process
- Container
- Host
- Rack
- Availability Zone
- Region
- Cloud provider
- Network segment

If all quorum members reside on the same host:

```text
Host A
  |
  +--> N1
  +--> N2
  +--> N3
```

then a host failure destroys the entire quorum.

Replication should therefore be distributed across independent failure domains where the availability requirement justifies it.

---

## Quorum in Availability Zones

A typical AWS architecture might use:

```text
                    Application
                        |
                        v
                 Distributed DB
                 /      |      \
                v       v       v
              AZ-a    AZ-b    AZ-c
               N1      N2      N3
```

For:

```text
N = 3
W = 2
```

the system can potentially continue writing after one AZ becomes unavailable.

The actual behavior depends on the database technology and deployment model.

The important architectural principle is:

> Replicas should be placed so that the required quorum survives the failure domain you are designing against.

---

## Quorum and Network Partitions

Consider:

```text
N1 ---- N2

         X

        N3
```

A network partition separates the cluster.

Suppose:

```text
N = 3
Q = 2
```

The partition containing N1 and N2 has a majority:

```text
N1 + N2 = 2
```

The isolated N3 does not:

```text
N3 = 1
```

A majority-based coordination system can allow the majority partition to continue making progress while the minority partition is prevented from making conflicting decisions.

This is a fundamental reason majority quorums are important in distributed coordination.

---

## Quorum and CAP

During a network partition, a distributed system may have to choose whether to:

```text
Require quorum
```

or:

```text
Continue operating without quorum
```

If quorum is required:

```text
No quorum
   |
   v
Reject operation
```

Availability may decrease, but conflicting operations are less likely.

If the system continues operating without sufficient quorum:

```text
No quorum
   |
   v
Accept operation
```

availability improves, but consistency guarantees may weaken.

The correct behavior depends on the system's consistency model.

---

## Quorum vs Consensus

Quorum and consensus are related but not equivalent.

### Quorum

A quorum means:

> Enough nodes participated in an operation.

Example:

```text
5 nodes
Quorum = 3
```

### Consensus

Consensus is a protocol through which distributed nodes agree on a value or ordered sequence despite failures.

Examples include:

- Raft
- Paxos
- Multi-Paxos
- Viewstamped Replication

Consensus protocols use quorum-like majority participation, but quorum itself is not a consensus algorithm.

This distinction is critical in system design.

---

## Quorum in Raft

Raft commonly uses a majority quorum for decisions.

For:

```text
5-node cluster
```

the majority is:

```text
3 nodes
```

A leader can generally commit replicated log entries once they have been replicated to a majority, subject to Raft's specific commitment rules.

Conceptually:

```text
Leader
  |
  +--> Follower 1 ✓
  +--> Follower 2 ✓
  +--> Follower 3 ✗
  +--> Follower 4 ✗

Majority = 3
```

The leader plus two followers provide the required majority.

Raft's safety comes from the complete consensus protocol, not from the number three alone.

---

## Quorum in Leaderless Databases

Leaderless databases commonly use quorum parameters for data reads and writes:

```text
N = replicas
W = write acknowledgements
R = read responses
```

For example:

```text
N = 3
W = 2
R = 2
```

This is conceptually different from Raft:

```text
Leaderless database
→ Quorum-based replication

Raft
→ Consensus protocol using majority quorums
```

The term "quorum" appears in both architectures, but the semantics are different.

---

## Quorum in Distributed Locks

Quorums can also be used to coordinate distributed locks.

Conceptually:

```text
Lock Request
     |
     v
N1 ✓
N2 ✓
N3 ✗
     |
     v
Quorum reached
```

However, distributed locking is significantly more complicated than counting acknowledgements.

A production lock system must consider:

- Expiration
- Clock behavior
- Client crashes
- Network partitions
- Lock ownership
- Fencing
- Stale clients

A simple quorum acknowledgement is not automatically a safe distributed lock.

---

## Fencing Tokens

Consider a distributed lock:

```text
Client A acquires lock
```

Then Client A becomes disconnected but continues operating.

A new client acquires the lock:

```text
Client B → newer lock
```

If Client A can still perform writes, both clients may operate concurrently.

A fencing token can help:

```text
Client A → token 41
Client B → token 42
```

The storage layer rejects operations using an older token:

```text
token 41 < token 42
```

This is an example of why quorum alone is insufficient for robust distributed coordination.

---

## Quorum and Distributed Transactions

Quorums can help replicate transactional state, but they do not automatically provide distributed ACID transactions.

For example:

```text
Transaction
   |
   +--> Database A
   |
   +--> Database B
```

requires coordination across independent resources.

A quorum only answers:

```text
Did enough replicas acknowledge?
```

It does not automatically answer:

```text
Did every participant atomically commit?
```

Protocols such as:

- Two-Phase Commit
- Three-Phase Commit
- Consensus-based transaction systems

solve different problems.

---

## Quorum and Eventual Consistency

A quorum-based system can still be eventually consistent.

Consider:

```text
N1 → v10
N2 → v11
N3 → v11
```

A successful write may have reached:

```text
N2
N3
```

while N1 remains stale.

Eventually:

```text
N1 → v11
```

through repair.

Therefore:

```text
Quorum
    ≠
Immediate global synchronization
```

Quorum is a mechanism for defining how much participation is required, not a guarantee that all replicas are synchronized immediately.

---

## Quorum and Strong Consistency

Some distributed databases use quorum protocols as part of stronger consistency guarantees.

However, strong consistency typically requires additional mechanisms around:

- Serialization
- Ordering
- Leader election
- Consensus
- Linearizable operations
- Version validation
- Failure handling

Therefore, when evaluating a database, ask:

> What consistency guarantee does this quorum configuration actually provide?

Do not infer the answer from the word "quorum."

---

## Quorum Configuration Examples

For:

```text
N = 3
```

possible configurations include:

| R | W | Typical Behavior |
|---:|---:|---|
| 1 | 1 | Lowest coordination |
| 1 | 2 | Stronger write participation |
| 2 | 1 | More read participation |
| 2 | 2 | Quorum overlap |
| 3 | 3 | Maximum replica participation |

For:

```text
N = 5
```

a majority configuration is commonly:

```text
R = 3
W = 3
```

while a system prioritizing low read latency might use a smaller read quorum.

The correct configuration should be derived from:

```text
Consistency requirement
        +
Availability requirement
        +
Latency requirement
        +
Failure-domain requirement
```

---

## Quorum Availability Calculation

A useful way to reason about availability is:

```text
Available replicas >= Required quorum
```

For:

```text
N = 5
W = 3
```

the system needs at least:

```text
3 available replicas
```

Therefore it can tolerate up to:

```text
5 - 3 = 2
```

replica failures while satisfying that quorum.

This is a simplified availability calculation. Real systems must also account for:

- Network partitions
- Slow replicas
- Correlated failures
- Replica placement
- Failure detection
- Operational constraints

---

## Quorum and Tail Latency

Quorum selection affects tail latency.

Suppose:

```text
Replica latency:

N1 = 10 ms
N2 = 12 ms
N3 = 15 ms
N4 = 80 ms
N5 = 150 ms
```

For:

```text
W = 2
```

the system may complete around:

```text
12 ms
```

if N1 and N2 acknowledge.

For:

```text
W = 4
```

it may need to wait for:

```text
80 ms
```

assuming N4 is required among the four fastest successful responses.

Thus:

```text
Higher quorum
    |
    v
More coordination
    |
    v
Potentially higher tail latency
```

This matters in high-throughput backend systems.

---

## Quorum and Load

Larger quorums also increase load.

If every write is sent to:

```text
N = 5
```

replicas, a single logical write can generate multiple physical operations.

This is known as write amplification.

For example:

```text
100,000 logical writes/sec
```

with:

```text
RF = 5
```

can produce approximately:

```text
500,000 replica write operations/sec
```

before accounting for retries, repair, indexes, and internal database work.

Capacity planning must therefore consider physical replication traffic rather than only application-level request volume.

---

## Quorum and Cost

Higher replication and quorum requirements can increase:

- Compute
- Storage
- Network traffic
- Cross-region transfer
- Database I/O
- Repair workload
- Monitoring requirements

For example:

```text
Application
    |
    v
1 logical write
    |
    +--> Replica A
    +--> Replica B
    +--> Replica C
```

The database infrastructure handles multiple physical operations for one application-level write.

This is one reason quorum configuration should be treated as an architectural decision rather than a minor database setting.

---

## Monitoring

Production quorum systems should expose metrics such as:

| Metric | Purpose |
|---|---|
| Quorum success rate | Detect availability degradation |
| Quorum failure rate | Detect insufficient healthy replicas |
| Read latency | Detect slow reads |
| Write latency | Detect slow writes |
| Replica latency | Identify problematic nodes |
| Replica availability | Detect failures |
| Replication lag | Detect divergence |
| Repair backlog | Detect convergence problems |
| Conflict rate | Detect concurrent-write issues |
| Cross-region latency | Detect network problems |

Alerting should focus on quorum failures and increasing tail latency because these often reveal problems before total system failure.

---

## Operational Best Practices

### Design Quorums Around Failure Domains

Do not simply count replicas.

Ask:

```text
Can the quorum survive an AZ failure?
```

or:

```text
Can the quorum survive a regional failure?
```

### Monitor the Slowest Replicas

A replica that is technically healthy but consistently slow can increase quorum latency.

### Test Quorum Loss

Simulate:

- Node failure
- AZ failure
- Network partition
- High latency
- Packet loss
- Replica overload

### Keep Backups Independent

Quorum replication does not replace backups.

### Document Consistency Guarantees

For every critical operation, document:

```text
Read consistency:
Write consistency:
Failure behavior:
Staleness tolerance:
```

### Avoid Arbitrary Quorum Settings

Do not choose:

```text
R = 2
W = 2
```

because it is common.

Choose it because it satisfies explicit system requirements.

---

## Security Considerations

Quorum communication often involves communication between multiple trusted database nodes.

Production deployments should:

- Encrypt node-to-node traffic.
- Authenticate cluster members.
- Restrict database network access.
- Use least-privilege credentials.
- Encrypt data at rest.
- Encrypt backups.
- Rotate credentials.
- Audit administrative operations.
- Restrict cross-region connectivity.
- Protect quorum metadata from unauthorized modification.

A compromised replica can be particularly dangerous if the system trusts responses from multiple nodes.

Authentication and integrity protection are therefore essential.

---

## Disaster Recovery

Quorum replication protects against certain infrastructure failures, but it is not a complete disaster recovery strategy.

Consider:

```text
All replicas
    |
    v
Corrupted application write
```

The corruption can replicate successfully:

```text
N1 → corrupted
N2 → corrupted
N3 → corrupted
```

A quorum system has correctly replicated the wrong data.

Therefore, production systems should combine quorum replication with:

- Point-in-time backups
- Immutable backups
- Cross-region backups where required
- Restore testing
- Data-integrity validation
- Defined RPO
- Defined RTO

---

## Quorum vs Replication Factor

Replication factor and quorum are different concepts.

### Replication Factor

Defines:

```text
How many copies exist?
```

### Quorum

Defines:

```text
How many participants are required?
```

For example:

```text
Replication Factor = 5

N1
N2
N3
N4
N5
```

A write quorum might be:

```text
W = 3
```

Therefore:

```text
5 copies exist
3 acknowledgements required
```

Increasing replication factor does not automatically increase quorum.

---

## Quorum vs Majority

A majority quorum is:

```text
Q > N / 2
```

But quorum systems can be configured with different read and write sizes.

For example:

```text
N = 5
R = 1
W = 5
```

is not a majority read quorum, but it is a valid read/write quorum configuration in systems that support such semantics.

Therefore:

```text
Majority
```

is a particular quorum size, while:

```text
Quorum
```

is the broader concept.

---

## Common Mistakes

### Assuming Quorum Means Strong Consistency

A quorum only defines participation requirements.

**Avoidance:** Verify the database's actual consistency semantics.

### Ignoring Failure Domains

Five replicas in one availability zone do not provide five independent failure domains.

**Avoidance:** Distribute replicas across the failure domains that matter.

### Choosing Quorum Based Only on Node Count

The formula:

```text
R + W > N
```

does not answer every architectural question.

**Avoidance:** Consider latency, consistency, partitions, placement, and application semantics.

### Ignoring Tail Latency

A high quorum may wait for slow replicas.

**Avoidance:** Monitor p95, p99, and higher-percentile latency.

### Assuming Successful Quorum Means All Replicas Are Current

Some replicas may still be stale.

**Avoidance:** Design repair and convergence mechanisms.

### Confusing Quorum With Consensus

A quorum is not a complete consensus protocol.

**Avoidance:** Understand how Raft or Paxos uses quorums as part of a larger protocol.

### Ignoring Correlated Failures

Three replicas on the same host can fail together.

**Avoidance:** Place replicas across independent failure domains.

### Treating Quorum as a Distributed Lock

A quorum acknowledgement alone does not prevent stale clients from acting.

**Avoidance:** Use proper locking protocols and fencing where required.

---

## Real-World Backend Example

Consider a globally distributed user-profile system:

```text
                   Global API
                       |
             +---------+---------+
             |         |         |
             v         v         v
           Region A  Region B  Region C
             |         |         |
             v         v         v
            N1        N2        N3
```

Suppose:

```text
N = 3
R = 2
W = 2
```

A user updates their profile:

```text
PATCH /users/123
```

The coordinator sends the write to:

```text
N1
N2
N3
```

If:

```text
N1 → ACK
N2 → ACK
N3 → timeout
```

the operation succeeds.

A later read can query two replicas:

```text
N2 → updated
N3 → stale
```

The system can return the newer version and potentially repair N3.

This architecture can work well for profile attributes where temporary eventual consistency is acceptable.

It would be much less appropriate for something like:

```text
Bank account balance
```

where incorrect concurrent state can have direct financial consequences.

---

## Design Decision Framework

When deciding on a quorum configuration, reason through the following:

```text
                    Start
                      |
                      v
             What must be consistent?
                      |
             +--------+--------+
             |                 |
           Strong           Eventual
             |                 |
             v                 v
        More coordination   Lower coordination
             |                 |
             +--------+--------+
                      |
                      v
             What failures matter?
                      |
             +--------+--------+
             |                 |
             AZ failure      Region failure
             |                 |
             v                 v
       Distribute replicas across
       appropriate failure domains
                      |
                      v
             What latency is acceptable?
                      |
                      v
             Choose R / W / Q
                      |
                      v
             Test failure scenarios
```

The configuration should emerge from requirements rather than from a generic rule.

---

## Interview Perspective

A common interview question is:

> "What is quorum?"

A strong answer is:

> Quorum is the minimum number of replicas or nodes that must participate successfully in an operation for the system to consider that operation complete. In replicated systems, quorum allows the system to tolerate some node failures without waiting for every replica.

If asked:

> "What are N, R, and W?"

Answer:

```text
N = Number of replicas

R = Number of replicas consulted for a read

W = Number of replicas required to acknowledge a write
```

If asked:

> "Why is R + W > N important?"

Answer:

> It guarantees that a read quorum and write quorum overlap when they are selected from the same replica set. That overlap can help a read observe a write, depending on the database's versioning and consistency semantics. It should not be interpreted as a universal guarantee of linearizability.

If asked:

> "What happens if one node fails?"

For:

```text
N = 3
W = 2
```

two healthy replicas can still satisfy the write quorum.

If asked:

> "Does quorum equal consensus?"

Answer:

> No. A quorum is a participation threshold. Consensus is a distributed protocol that allows nodes to agree on a value or ordered log despite failures. Protocols such as Raft use majority quorums as part of their safety and progress mechanisms.

Senior-level discussions should connect quorum to:

```text
Quorum
  |
  +--> Replication
  |
  +--> Read / Write Consistency
  |
  +--> Failure Domains
  |
  +--> Network Partitions
  |
  +--> CAP
  |
  +--> Consensus
  |
  +--> Tail Latency
  |
  +--> Availability
  |
  +--> Repair
  |
  +--> Disaster Recovery
```

---

## Key Takeaways

- Quorum defines how many replicas or nodes must participate successfully in an operation, allowing distributed systems to balance consistency, availability, latency, and fault tolerance.
- In leaderless replication, `N`, `R`, and `W` describe replica count, read participation, and write acknowledgement requirements; `R + W > N` provides quorum overlap but does not universally guarantee strong consistency.
- Quorum design must consider failure domains, replica placement, network partitions, tail latency, replication lag, and repair behavior rather than only the number of nodes.
- Quorum is a mechanism, not a consensus algorithm; protocols such as Raft use majority quorums as part of a broader protocol for distributed agreement.
- Production quorum systems require explicit consistency guarantees, independent backups, failure testing, monitoring, secure node communication, and carefully chosen read/write policies.