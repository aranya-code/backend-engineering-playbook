# 11 - Mock Senior Backend Interview

---

# Interview Format

| Round | Topic |
|---------|---------|
| Round 1 | Fundamentals |
| Round 2 | Data Modeling |
| Round 3 | Performance |
| Round 4 | Production Problems |
| Round 5 | System Design |
| Round 6 | Coding Discussion |
| Round 7 | Architecture Discussion |

---

# Round 1 — Fundamentals

## Interviewer

Tell me about DynamoDB.

### Good Answer

> DynamoDB is AWS's fully managed NoSQL database designed for predictable single-digit millisecond latency at virtually any scale. It automatically handles partitioning, replication, scaling, and high availability. Unlike relational databases, schema design starts with access patterns instead of normalized entities.

---

## Interviewer

When would you NOT use DynamoDB?

### Good Answer

I would avoid DynamoDB if the application requires:

- Complex joins
- Heavy ad-hoc reporting
- Relational integrity across many tables
- SQL analytics
- Frequent schema exploration

In those cases PostgreSQL or another relational database would likely be a better choice.

---

## Interviewer

Explain horizontal scaling.

### Good Answer

DynamoDB hashes the partition key and distributes data across physical partitions.

As traffic grows:

```text
Traffic

↓

More Partitions

↓

Higher Throughput
```

Applications don't manage these partitions directly.

---

# Round 2 — Data Modeling

## Interviewer

How do you design a DynamoDB table?

### Good Answer

I follow this order:

```text
Business Requirements

↓

Access Patterns

↓

Partition Key

↓

Sort Key

↓

Indexes

↓

Validation

↓

Performance Testing
```

I never begin with entities like Customer or Order.

I begin with the queries the application must support.

---

## Interviewer

What is your opinion on Single Table Design?

### Good Answer

Single-table design is extremely powerful for high-scale workloads because it minimizes joins and network round trips.

However, I don't consider it mandatory.

For smaller systems or independently owned microservices, multiple tables may provide better maintainability.

The decision depends on:

- Team size
- Ownership
- Complexity
- Access patterns
- Operational overhead

---

## Interviewer

How do you avoid hot partitions?

### Good Answer

I focus primarily on partition-key design.

Strategies include:

- High-cardinality keys
- Write sharding
- Random suffixes where appropriate
- Caching hot data
- Reviewing CloudWatch metrics
- Avoiding sequential partition keys

---

# Round 3 — Performance

## Interviewer

Your API latency suddenly increased.

Walk me through your investigation.

### Good Answer

I follow a structured process:

```text
CloudWatch

↓

Latency

↓

Throttle Events

↓

Capacity

↓

Hot Partitions

↓

Query vs Scan

↓

Recent Deployments

↓

Application Logs
```

Only after identifying the bottleneck would I consider increasing capacity.

---

## Interviewer

Why is Query preferred over Scan?

### Good Answer

Query reads only the items matching a partition key.

Scan reads the entire table.

Large scans:

- Consume unnecessary RCUs
- Increase latency
- Don't scale well

Production APIs should almost always use Query.

---

## Interviewer

How would you reduce DynamoDB costs?

### Good Answer

I would review:

- Access patterns
- Unused GSIs
- Scan operations
- Item size
- TTL usage
- Backup strategy
- Auto Scaling configuration
- Cache hit ratio

Adding capacity isn't the first optimization step.

---

# Round 4 — Production Problems

## Interviewer

A customer reports seeing stale data after an update.

### Good Answer

First, I'd determine whether the application is reading from:

- Base table
- GSI

If it's a GSI, eventual consistency is expected.

Possible solutions:

- Read from the base table when freshness is critical
- Use strongly consistent reads where supported
- Implement retry logic for read-after-write scenarios
- Review cache invalidation behavior

---

## Interviewer

Your DynamoDB bill doubled overnight.

### Good Answer

I'd investigate:

```text
CloudWatch

↓

Consumed Capacity

↓

Traffic Changes

↓

New GSIs

↓

Large Writes

↓

Scans

↓

Storage Growth
```

The goal is to identify whether the increase came from workload changes or design inefficiencies before making architectural changes.

---

## Interviewer

How would you recover from accidental deletion?

### Good Answer

If Point-in-Time Recovery is enabled:

```text
Restore

↓

New Table

↓

Validate

↓

Application Cutover
```

I wouldn't overwrite production directly without validating the restored data.

---

# Round 5 — System Design

## Interviewer

Design a shopping cart.

### Good Answer

Schema:

```text
PK

USER#123
```

```text
SK

ITEM#100

ITEM#200

ITEM#300
```

Architecture:

```text
Client

↓

API

↓

DynamoDB

↓

Streams

↓

Inventory Update

↓

Lambda
```

Advantages:

- One query retrieves the cart
- Horizontal scaling
- Event-driven updates

---

## Interviewer

Would you use DynamoDB for banking?

### Good Answer

It depends.

I'd happily use DynamoDB for:

- User profiles
- Sessions
- Notifications
- Fraud events
- Account metadata

For core ledger transactions requiring complex consistency guarantees and reporting, a relational database may be a better fit.

---

## Interviewer

How would you build a global application?

### Good Answer

Architecture:

```text
Users

↓

Nearest Region

↓

Global Tables

↓

Replication

↓

Other Regions
```

I'd also discuss:

- Conflict resolution
- Data residency
- Disaster recovery
- Latency
- Monitoring

---

# Round 6 — Coding Discussion

## Interviewer

How do you organize Boto3 code?

### Good Answer

I avoid SDK calls inside controllers.

Instead:

```text
Controller

↓

Service

↓

Repository

↓

Boto3
```

Benefits:

- Testability
- Separation of concerns
- Easier mocking
- Cleaner architecture

---

## Interviewer

How do you handle throttling?

### Good Answer

I implement:

- Exponential backoff
- Jitter
- Retry limits
- Logging
- Metrics
- Alerting

Blind retries can worsen contention.

---

## Interviewer

How do you prevent duplicate orders?

### Good Answer

I'd use:

- Conditional writes
- Idempotency keys
- Transactions only when multiple related writes must succeed together

---

# Round 7 — Architecture Discussion

## Interviewer

Describe a production architecture using DynamoDB.

### Good Answer

```text
Clients

↓

Load Balancer

↓

API

↓

Redis

↓

DynamoDB

↓

Streams

↓

Lambda

↓

SNS

↓

SQS

↓

Microservices

↓

CloudWatch
```

---

## Interviewer

Where does Redis fit?

### Good Answer

Redis handles:

- Hot reads
- Sessions
- Rate limiting
- Frequently accessed data
- Temporary caching

DynamoDB remains the durable source of truth.

---

## Interviewer

How do you monitor DynamoDB?

### Good Answer

CloudWatch metrics:

- ReadThrottleEvents
- WriteThrottleEvents
- SuccessfulRequestLatency
- Consumed RCUs
- Consumed WCUs
- SystemErrors
- UserErrors

I also configure alarms and dashboards for operational visibility.

---

# Bonus Round — Rapid Fire

| Question | Expected Answer |
|-----------|----------------|
| Fastest lookup? | GetItem |
| Preferred query operation? | Query |
| Avoid? | Scan |
| GSI consistency? | Eventual |
| LSI consistency? | Strong or Eventual |
| Stream retention? | 24 Hours |
| Max item size? | 400 KB |
| TTL immediate? | No |
| Multi-region? | Global Tables |
| Automatic backup? | PITR |

---

# What Interviewers Look For

Excellent candidates consistently:

- Explain trade-offs instead of absolute rules.
- Design around access patterns.
- Discuss operational monitoring.
- Mention cost optimization.
- Consider scalability and failure scenarios.
- Think in terms of production systems rather than isolated APIs.

---

# Common Mistakes

## Saying "DynamoDB scales automatically, so I don't need to think about schema."

Automatic scaling cannot compensate for:

- Poor partition-key selection
- Hot partitions
- Inefficient access patterns

---

## Using Scan as the Default Query Method

Production systems should almost always use Query or GetItem.

---

## Creating GSIs for Every New Requirement

Every GSI increases:

- Storage
- Write costs
- Operational complexity

Indexes should support well-defined access patterns.

---

## Forgetting Monitoring

A production DynamoDB deployment should include:

- CloudWatch dashboards
- Alarms
- CloudTrail
- Backup validation
- Capacity monitoring

---

# Final Interview Advice

When answering senior DynamoDB interview questions:

1. Clarify requirements before proposing a solution.
2. Explain your reasoning, not just the final answer.
3. Discuss trade-offs between consistency, latency, scalability, and cost.
4. Consider operational concerns such as monitoring, recovery, and observability.
5. Mention complementary AWS services (Lambda, SQS, SNS, EventBridge, ElastiCache, CloudWatch) where they strengthen the architecture.

A candidate who demonstrates structured thinking, production awareness, and the ability to justify architectural decisions will stand out far more than one who simply recites DynamoDB features.

---

# Mock Interview Scorecard

| Skill Area | Excellent Candidate Demonstrates |
|------------|----------------------------------|
| Fundamentals | Understands DynamoDB architecture and trade-offs |
| Data Modeling | Designs around access patterns, not entities |
| Performance | Optimizes queries, avoids scans, handles hot partitions |
| Transactions | Chooses between conditional writes and transactions appropriately |
| Security | Applies IAM, KMS, least privilege, and monitoring |
| Production Operations | Uses CloudWatch, PITR, backups, and incident response practices |
| System Design | Integrates DynamoDB effectively with other AWS services |
| Coding | Writes clean, testable Boto3 code with retries and error handling |
| Communication | Explains decisions clearly and justifies trade-offs |

---

# Key Takeaways

- Senior DynamoDB interviews focus on **decision-making**, not memorization.
- Your ability to explain **why** you chose a design is more important than recalling API names.
- Strong candidates balance **performance, scalability, consistency, reliability, and cost** in every answer.
- Treat DynamoDB as one component of a larger distributed system, integrating it thoughtfully with caching, messaging, monitoring, and recovery mechanisms.
- If you can confidently work through the scenarios in this mock interview, you'll be well prepared for most senior backend interviews involving DynamoDB.