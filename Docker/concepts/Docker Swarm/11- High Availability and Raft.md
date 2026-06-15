# High Availability and Raft

## Overview

One of Docker Swarm's biggest strengths is its ability to remain operational even when nodes fail.

This capability is achieved through:

- High Availability (HA)
- Manager Redundancy
- Raft Consensus
- Leader Election
- Quorum Management

Without these mechanisms, a failure of the primary manager could bring the entire cluster offline.

---

# What is High Availability (HA)?

## Definition

High Availability is the ability of a system to continue functioning even when components fail.

Goal:

```text
Node Failure

      │

      ▼

Application Continues Running
```

Users should experience little or no disruption.

---

# Why High Availability Matters

Imagine a swarm cluster with a single manager.

```text
Manager

Worker1
Worker2
Worker3
```

If the manager fails:

```text
Manager ❌
```

The cluster loses its control plane.

Although existing containers may continue running, cluster management operations stop.

Examples:

```text
Cannot Scale

Cannot Deploy

Cannot Update

Cannot Schedule Tasks
```

---

# High Availability Solution

Use multiple managers.

```text
Manager1

Manager2

Manager3
```

Now the cluster can tolerate failures.

---

# Swarm High Availability Architecture

```text
                Manager1 (Leader)

                      │

          ┌───────────┼───────────┐

          ▼                       ▼

   Manager2                 Manager3

     Follower                Follower


          │

          ▼

      Worker Nodes
```

All managers maintain synchronized cluster state.

---

# Manager Nodes and HA

Managers form the:

```text
Control Plane
```

Responsibilities:

- Scheduling
- Service creation
- Scaling
- Updates
- State management
- Cluster decisions

Because managers are critical, redundancy is required.

---

# What is Raft?

## Definition

Raft is a distributed consensus algorithm used by Docker Swarm manager nodes.

Purpose:

- Maintain consistent cluster state
- Elect leaders
- Prevent split-brain scenarios
- Provide fault tolerance

---

# Why Raft Exists

Suppose multiple managers exist:

```text
Manager1

Manager2

Manager3
```

Question:

```text
Who Makes Decisions?
```

Raft ensures:

```text
Exactly One Leader
```

at any point in time.

---

# Raft Architecture

```text
Manager1 → Leader

Manager2 → Follower

Manager3 → Follower
```

---

# Leader Node

The leader performs:

```text
Scheduling

Service Updates

Node Management

State Changes
```

Only one leader exists.

---

# Follower Nodes

Followers:

```text
Replicate State

Participate in Voting

Monitor Leader Health
```

They remain synchronized with the leader.

---

# Raft State Replication

When a change occurs:

Example:

```bash
docker service create nginx
```

Leader receives request.

---

# Replication Workflow

```text
Leader

   │

Write Change

   │

   ▼

Follower 1

Follower 2

   │

   ▼

Acknowledgement
```

Only after majority approval is the change committed.

---

# What is Quorum?

## Definition

Quorum is the minimum number of managers required to agree before a cluster decision becomes valid.

Formula:

```text
(N / 2) + 1
```

where:

```text
N = Number of Managers
```

---

# Quorum Examples

| Managers | Quorum Required |
|-----------|----------------|
| 1 | 1 |
| 3 | 2 |
| 5 | 3 |
| 7 | 4 |

---

# Why Quorum Matters

Without quorum:

```text
Cluster Cannot Make Decisions
```

Because state consistency cannot be guaranteed.

---

# Example: Three Managers

```text
Manager1

Manager2

Manager3
```

Quorum:

```text
2
```

---

# Failure Scenario

```text
Manager3 ❌
```

Remaining:

```text
Manager1

Manager2
```

Quorum still exists:

```text
2 / 3
```

Cluster continues operating.

---

# Failure Scenario 2

```text
Manager2 ❌

Manager3 ❌
```

Remaining:

```text
Manager1
```

Quorum:

```text
1 / 3
```

Not enough.

Cluster becomes read-only.

---

# Leader Election

One of Raft's most important responsibilities.

---

# Initial State

```text
Manager1 → Leader

Manager2 → Follower

Manager3 → Follower
```

---

# Leader Failure

```text
Manager1 ❌
```

Followers detect missing heartbeats.

---

# Election Begins

```text
Manager2

Manager3
```

vote.

---

# New Leader

```text
Manager2 → Leader
```

Cluster continues operating.

---

# Leader Election Workflow

```text
Leader Failure

      │

      ▼

Election Triggered

      │

      ▼

Managers Vote

      │

      ▼

New Leader Selected
```

---

# Heartbeats

Leaders periodically send:

```text
Heartbeat Messages
```

to followers.

Purpose:

```text
Confirm Leader Alive
```

---

# Heartbeat Example

```text
Leader

  │

Heartbeat

  │

  ▼

Followers
```

---

# Missing Heartbeats

Followers assume:

```text
Leader Failed
```

and start a new election.

---

# Split-Brain Problem

## What is Split-Brain?

A distributed system issue where multiple nodes believe they are the leader simultaneously.

Example:

```text
Manager1 → Leader

Manager2 → Leader
```

Conflicting decisions occur.

---

# Why Split-Brain is Dangerous

Possible outcomes:

```text
Data Corruption

Conflicting State

Unpredictable Behavior
```

---

# How Raft Prevents Split-Brain

Through:

```text
Leader Election

Quorum

Majority Voting
```

Only one manager can obtain majority approval.

---

# Odd Number of Managers

Docker recommends:

```text
1

3

5

7
```

Managers.

---

# Why Not Even Numbers?

Example:

```text
4 Managers
```

Quorum:

```text
3
```

Failure tolerance remains:

```text
1 Failure
```

similar to 3 managers.

More resources, no major benefit.

---

# Recommended Manager Counts

## Development

```text
1 Manager
```

---

## Small Production

```text
3 Managers
```

---

## Medium Production

```text
5 Managers
```

---

## Large Production

```text
7 Managers
```

Rarely needed.

---

# Manager Availability Zones

Production managers should be distributed.

Example:

```text
AZ1 → Manager1

AZ2 → Manager2

AZ3 → Manager3
```

Protects against:

```text
Rack Failure

Server Failure

Zone Failure
```

---

# Worker Failure vs Manager Failure

## Worker Failure

```text
Worker1 ❌
```

Result:

```text
Tasks Rescheduled
```

Cluster remains healthy.

---

## Manager Failure

```text
Leader ❌
```

Result:

```text
Leader Election
```

Cluster remains healthy if quorum exists.

---

# Raft Database

Managers store cluster state in:

```text
Raft Database
```

Contains:

```text
Services

Secrets

Configs

Networks

Node Information
```

---

# Raft Replication

Every manager stores a copy.

```text
Manager1

Manager2

Manager3
```

All contain cluster metadata.

---

# What Happens Without Quorum?

Example:

```text
3 Managers
```

Quorum:

```text
2
```

Failures:

```text
Manager2 ❌

Manager3 ❌
```

Only:

```text
Manager1
```

remains.

---

# Result

Existing workloads:

```text
Continue Running
```

But:

```text
Cannot Create Services

Cannot Scale

Cannot Update
```

Control plane becomes unavailable.

---

# Viewing Managers

```bash
docker node ls
```

Example:

```text
HOSTNAME     STATUS

manager1     Leader

manager2     Reachable

manager3     Reachable
```

---

# Promoting a Worker

```bash
docker node promote worker1
```

Worker becomes manager.

---

# Demoting a Manager

```bash
docker node demote manager2
```

Manager becomes worker.

---

# High Availability Best Practices

## Use Three Managers

Most common production deployment.

```text
Manager1

Manager2

Manager3
```

---

## Use Odd Numbers

Always:

```text
1

3

5

7
```

---

## Distribute Managers

Avoid placing all managers on one server.

---

## Monitor Quorum

Regularly verify:

```bash
docker node ls
```

---

## Backup Swarm State

Protect:

```text
Raft Database
```

especially manager nodes.

---

# Real-World Example

Production Cluster:

```text
Manager1 (Leader)

Manager2 (Follower)

Manager3 (Follower)

Worker1

Worker2

Worker3
```

Failure:

```text
Manager1 ❌
```

Result:

```text
Manager2 → Leader
```

No downtime.

---

# Common Interview Questions

## What is Raft?

Raft is the distributed consensus algorithm used by Docker Swarm managers to maintain cluster state and perform leader elections.

---

## What is Quorum?

Quorum is the minimum number of manager nodes required to agree on a cluster decision.

---

## Why Use Three Managers?

Three managers provide fault tolerance while maintaining quorum with minimal resource usage.

---

## What Happens When the Leader Fails?

Follower managers hold an election and select a new leader automatically.

---

## What Happens If Quorum Is Lost?

Existing workloads continue running, but cluster management operations become unavailable.

---

## Why Does Docker Recommend Odd Numbers of Managers?

Odd numbers maximize fault tolerance while minimizing resource consumption and avoiding voting deadlocks.

---

## What Problem Does Raft Solve?

Raft solves distributed consensus, leader election, state replication, and split-brain prevention.

---

# Interview One-Liner

Docker Swarm achieves High Availability through multiple manager nodes coordinated by the Raft consensus algorithm, which provides leader election, quorum-based decision making, state replication, and fault tolerance for the cluster control plane.
