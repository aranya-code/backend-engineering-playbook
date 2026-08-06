# Scenario Based Questions

## Overview

Scenario-based questions are commonly asked in senior backend, system design, and architect interviews because they evaluate practical problem-solving rather than theoretical knowledge.

Instead of asking for definitions, interviewers present real production situations and expect candidates to:

- Analyze the problem
- Identify the root cause
- Explain trade-offs
- Recommend solutions
- Justify architectural decisions

This chapter covers common Kafka production scenarios along with concise, interview-ready answers.

---

# Scenario 1: Consumer Lag Keeps Increasing

**Question**

> Your Consumer Lag keeps increasing every hour. How would you investigate?

**Answer**

Start with a structured approach.

Check:

- Consumer health
- Consumer processing time
- Database performance
- External API latency
- Network
- Broker health
- Partition count
- Consumer count

Workflow:

```text
Consumer Lag

↓

Consumer Healthy?

↓

Database Healthy?

↓

Broker Healthy?

↓

Network Healthy?

↓

Scale or Optimize
```

Do not immediately add consumers before identifying the bottleneck.

---

# Scenario 2: Duplicate Messages

**Question**

> Users report duplicate order processing. What could be the reason?

**Answer**

Possible causes:

- Producer retries without idempotence
- Consumer restarted before committing offsets
- Manual offset reset
- Business logic not idempotent

Recommended solution:

- Enable idempotent producers
- Commit offsets after processing
- Design idempotent consumers

---

# Scenario 3: Messages Are Missing

**Question**

> Some events are never processed. How would you investigate?

**Answer**

Check:

- Offset commit strategy
- Auto Commit configuration
- Consumer logs
- Topic retention
- Dead Letter Topic
- Producer errors

Determine whether messages were:

- Never produced
- Produced but expired
- Produced but skipped
- Produced and committed before processing

---

# Scenario 4: Producer Timeout

**Question**

> Producers suddenly start throwing `TimeoutException`. What would you check?

**Answer**

Investigate:

- Broker availability
- Network latency
- Disk usage
- Broker CPU
- Leader election
- Request latency

Do not simply increase timeout values without identifying the root cause.

---

# Scenario 5: Broker Failure

**Question**

> One broker crashes. What happens?

**Answer**

Workflow:

```text
Broker Failure

↓

Leader Election

↓

New Leader

↓

Producer Retry

↓

Consumer Continues
```

If replication is configured correctly, applications continue with minimal interruption.

---

# Scenario 6: Entire Broker Is Lost Permanently

**Question**

> A broker's disk is destroyed. What should you do?

**Answer**

Steps:

- Replace server
- Install Kafka
- Restore configuration
- Rejoin cluster
- Allow replicas to synchronize
- Monitor ISR

If Replication Factor = 1:

Data may be permanently lost.

---

# Scenario 7: Consumer Crash During Processing

**Question**

> A consumer crashes after processing a message but before committing the offset. What happens?

**Answer**

After restart:

```text
Message

↓

Read Again

↓

Processed Again
```

Duplicates occur.

Consumers should be idempotent.

---

# Scenario 8: Consumer Commits Before Processing

**Question**

> What happens if offsets are committed before processing?

**Answer**

Workflow:

```text
Receive Message

↓

Commit Offset

↓

Crash
```

Kafka assumes the message was processed.

Result:

```text
Message Lost
```

Offsets should be committed after successful processing.

---

# Scenario 9: One Partition Receives Most Traffic

**Question**

> One partition receives 90% of the traffic. Why?

**Answer**

Likely cause:

Poor partition key.

Example:

```text
Country

↓

Only Few Values
```

Better:

```text
Order ID

↓

High Cardinality
```

Choose keys that distribute traffic evenly.

---

# Scenario 10: Consumers Are Idle

**Question**

> You have ten consumers but only four are working.

**Answer**

Possible reason:

```text
4 Partitions

↓

10 Consumers
```

Only four consumers receive work.

Consumer parallelism is limited by partition count.

---

# Scenario 11: Under Replicated Partitions

**Question**

> Production monitoring shows Under Replicated Partitions. What do you do?

**Answer**

Investigate:

- Broker health
- Disk I/O
- Network latency
- CPU usage
- Replica synchronization

URP is a high-priority production issue.

---

# Scenario 12: Frequent Rebalancing

**Question**

> Consumer Groups rebalance every few minutes.

**Answer**

Possible causes:

- Consumer crashes
- Long processing
- Heartbeat failures
- Rolling deployments
- Incorrect timeout settings

Investigate logs before changing configurations.

---

# Scenario 13: High Producer Latency

**Question**

> Producer latency suddenly doubles.

**Answer**

Check:

- Network
- Broker CPU
- Disk latency
- Request queue
- Compression
- Batch configuration

Measure first.

Tune later.

---

# Scenario 14: Kafka Disk Is Almost Full

**Question**

> Broker disk usage reaches 95%.

**Answer**

Actions:

- Add storage
- Add brokers
- Review retention
- Archive old data
- Reduce unnecessary topics

Never allow production disks to reach 100%.

---

# Scenario 15: Kafka Cluster Needs to Handle Double the Traffic

**Question**

> Traffic is expected to double next month. What would you do?

**Answer**

Review:

- Broker capacity
- Partition count
- Consumer scaling
- Producer throughput
- Network
- Storage

Scale horizontally by:

- Adding brokers
- Increasing partitions
- Adding consumers

---

# Scenario 16: Messages Must Be Processed Exactly Once

**Question**

> How would you guarantee Exactly Once Processing?

**Answer**

Use:

- Idempotent Producers
- Transactions
- Manual Offset Commit
- Transaction-aware consumers

Also ensure business operations are idempotent.

---

# Scenario 17: Strict Ordering Is Required

**Question**

> Customer events must always remain in order.

**Answer**

Use:

```text
Customer ID

↓

Partition Key
```

Kafka guarantees ordering within a partition.

---

# Scenario 18: Cross-Region Disaster Recovery

**Question**

> How would you prepare Kafka for a regional outage?

**Answer**

Recommended approach:

- Replication Factor = 3
- MirrorMaker 2
- Cross-region cluster
- Backups
- Disaster recovery runbook
- Tested failover procedure

---

# Scenario 19: Large File Transfer

**Question**

> Should Kafka be used to transfer large video files?

**Answer**

No.

Instead:

```text
Upload File

↓

Object Storage

↓

Kafka Event

↓

File URL
```

Kafka should carry metadata, not large binary files.

---

# Scenario 20: Designing Kafka for an E-Commerce Platform

**Question**

> Design a Kafka-based architecture for an e-commerce application.

**Answer**

Example:

```text
Customer

↓

Order Service

↓

Kafka

↓

Inventory

↓

Payment

↓

Shipping

↓

Notification

↓

Analytics
```

Each service consumes only the events it requires.

---

# General Interview Approach

When answering scenario questions:

1. Clarify assumptions.
2. Explain the symptoms.
3. Identify possible causes.
4. Describe your investigation process.
5. Recommend a solution.
6. Mention monitoring and prevention.

Interviewers value structured thinking more than memorized answers.

---

# Common Follow-Up Questions

- How would you monitor this?
- How would you prevent it?
- How would you scale the solution?
- What are the trade-offs?
- What happens during broker failure?
- What metrics would you monitor?
- How would you test this?
- How would you troubleshoot in production?

---

# Interview Tips

- Start with the most likely root cause.
- Explain your troubleshooting sequence.
- Mention relevant Kafka metrics.
- Discuss trade-offs instead of absolute answers.
- Relate solutions to real production environments.
- Avoid proposing configuration changes before identifying the underlying problem.
- Use diagrams when explaining architectures.
- Demonstrate an operational mindset, not just theoretical knowledge.

---

# Summary

Scenario-based Kafka interview questions assess how candidates think under real production conditions. Rather than testing definitions, they evaluate troubleshooting ability, architectural reasoning, operational experience, and decision-making. A structured approach—understanding the problem, identifying root causes, proposing practical solutions, and discussing trade-offs—demonstrates the skills expected of senior backend engineers and software architects.

---

# Key Takeaways

- Scenario questions evaluate practical experience rather than memorized definitions.
- Always investigate the root cause before applying fixes.
- Use metrics, logs, and monitoring to guide troubleshooting.
- Understand the trade-offs between scalability, reliability, and performance.
- Design consumers and producers for failure and recovery.
- Be prepared to discuss monitoring, prevention, and scaling strategies.
- Structured, logical reasoning is often more important than the final answer.
- Production-oriented thinking is a key differentiator in senior Kafka interviews.