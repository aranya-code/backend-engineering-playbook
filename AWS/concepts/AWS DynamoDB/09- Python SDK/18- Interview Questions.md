# 18 - Interview Questions

## Overview

This chapter contains interview questions commonly asked for:

- Senior Backend Developer
- Lead Backend Engineer
- Python Developer
- AWS Developer
- Solutions Architect
- System Design Interviews

The questions focus on **real production knowledge**, not just API memorization.

---

# Beginner Level

## 1. What is Amazon DynamoDB?

**Answer**

Amazon DynamoDB is a fully managed NoSQL database service provided by AWS. It offers:

- Single-digit millisecond latency
- Automatic scaling
- High availability
- Built-in replication
- Managed backups
- Serverless operation

It stores data as key-value and document items.

---

## 2. Is DynamoDB SQL or NoSQL?

**Answer**

DynamoDB is a **NoSQL** database.

Unlike relational databases, it:

- Doesn't use joins
- Doesn't require fixed schemas
- Scales horizontally
- Uses partition keys for data distribution

---

## 3. What are the primary components of a DynamoDB table?

**Answer**

A table consists of:

- Partition Key
- Optional Sort Key
- Items
- Attributes

Example:

```text
Orders

Partition Key

↓

order_id

↓

Item

↓

Attributes
```

---

## 4. What is a Partition Key?

**Answer**

The Partition Key determines:

- Data placement
- Partition selection
- Request routing

A good partition key distributes traffic evenly.

---

## 5. What is a Sort Key?

**Answer**

A Sort Key allows multiple related items to exist under the same partition and enables efficient sorting and range queries.

Example:

```text
customer_id

↓

2025-01

↓

2025-02

↓

2025-03
```

---

# Intermediate Level

## 6. Query vs Scan

**Expected Answer**

Query:

- Uses Partition Key
- Fast
- Efficient
- Low cost

Scan:

- Reads entire table
- Slow
- Expensive
- Avoid for production APIs

---

## 7. Why is Scan discouraged?

Because it:

- Reads every partition
- Consumes large amounts of RCUs
- Doesn't scale well
- Increases latency

Use Query whenever possible.

---

## 8. What is eventual consistency?

Eventual consistency means:

```text
Write

↓

Replication

↓

Read

↓

Eventually Updated
```

The read may temporarily return stale data.

---

## 9. What is strong consistency?

Strong consistency guarantees the latest committed value.

Tradeoff:

- Higher latency
- Higher cost
- Lower throughput

---

## 10. What are GSIs?

Global Secondary Indexes provide alternative access patterns.

They:

- Use different partition keys
- Have independent throughput
- Support new query patterns

---

## 11. What are LSIs?

Local Secondary Indexes:

- Share the same partition key
- Use different sort keys
- Must be created during table creation

---

## 12. Difference between GSI and LSI?

| Feature | GSI | LSI |
|----------|-----|-----|
| Partition Key | Different | Same |
| Sort Key | Optional | Different |
| Create Later | Yes | No |
| Size Limit | Unlimited | 10 GB per partition |

---

# Senior Backend Questions

## 13. How would you design a table for an e-commerce system?

Expected discussion:

- Access patterns
- Customer orders
- Product lookup
- Order history
- GSIs
- Composite sort keys
- Pagination

Interviewers expect design reasoning rather than a single schema.

---

## 14. Explain Single Table Design.

Expected Answer:

Store multiple entity types in one table using:

- Composite keys
- Entity prefixes
- Sort key patterns

Benefits:

- Fewer queries
- Better scalability
- Lower latency

---

## 15. What causes Hot Partitions?

Poor partition keys.

Example:

```text
status

↓

ACTIVE
```

Millions of writes target one partition.

Better:

```text
user_id
```

Traffic distributes evenly.

---

## 16. How do you avoid Hot Partitions?

- High-cardinality keys
- Write sharding (when necessary)
- Even request distribution
- Review access patterns
- Monitor CloudWatch metrics

---

## 17. Why design for access patterns?

Unlike relational databases, DynamoDB is optimized for predefined access patterns.

Schema design begins with:

```text
Questions

↓

Queries

↓

Keys

↓

Indexes
```

---

## 18. Explain DynamoDB Transactions.

Transactions provide:

- ACID guarantees
- Multi-item consistency
- Automatic rollback
- Atomic writes

Used for:

- Banking
- Inventory
- Payments

---

## 19. Difference between BatchWriteItem and Transactions?

Batch:

- Faster
- No rollback
- No atomicity

Transactions:

- ACID
- Rollback
- Higher cost
- Business consistency

---

## 20. Explain Conditional Writes.

Conditional writes prevent race conditions.

Example:

```text
Update

↓

Only If

Version = 5
```

Useful for optimistic locking.

---

# Production Questions

## 21. How would you monitor DynamoDB?

Expected Answer:

- CloudWatch
- CloudTrail
- Structured logging
- Distributed tracing (AWS X-Ray/OpenTelemetry)
- Custom metrics

---

## 22. How do you secure DynamoDB?

Discuss:

- IAM Roles
- Least privilege
- Encryption
- KMS
- VPC Endpoints (where applicable)
- CloudTrail
- Secrets Manager
- Input validation

---

## 23. What happens if DynamoDB throttles requests?

Expected Answer:

- SDK retries
- Exponential backoff
- Jitter
- Auto Scaling (Provisioned mode)
- Review partition key design
- Monitor consumed capacity

---

## 24. How do you optimize performance?

Discuss:

- Query instead of Scan
- Better partition keys
- Smaller items
- ProjectionExpression
- Batch operations
- DAX
- Redis caching
- Auto Scaling

---

## 25. Explain DynamoDB Local.

Expected Answer:

A local version of DynamoDB used for:

- Development
- Integration testing
- CI/CD

without requiring AWS resources.

---

# Python/Boto3 Questions

## 26. Difference between Client and Resource?

Client:

- Low-level API
- Full AWS feature coverage
- Closer to the DynamoDB API

Resource:

- Higher-level abstraction
- More Pythonic interface
- Easier for everyday CRUD operations

---

## 27. Why use the Repository Pattern?

Benefits:

- Better testing
- Separation of concerns
- Easier maintenance
- Cleaner architecture
- Dependency injection

---

## 28. How do you implement retries?

Expected Answer:

```text
Failure

↓

Retry

↓

Exponential Backoff

↓

Jitter
```

Retry only transient failures.

---

## 29. Why shouldn't unit tests call AWS?

Because unit tests should be:

- Fast
- Deterministic
- Offline
- Independent of external systems

Mock dependencies instead.

---

## 30. Why use DynamoDB Local?

Because it enables:

- Offline development
- Faster testing
- Zero AWS cost
- Repeatable integration tests

---

# System Design Questions

## 31. Design a URL Shortener using DynamoDB.

Expected discussion:

- Partition key
- Short code lookup
- Expiration (TTL)
- GSIs (if analytics required)
- Read-heavy optimization
- Caching

---

## 32. Design a Chat Application.

Expected discussion:

- User table
- Conversation table
- Message ordering
- Sort keys
- Pagination
- TTL for temporary messages

---

## 33. Design an Order Management System.

Expected discussion:

- Orders
- Customers
- Inventory
- Transactions
- GSIs
- Event-driven architecture
- Streams

---

## 34. Design an Audit Logging System.

Expected discussion:

- Immutable records
- Time-based sort keys
- TTL (if retention policy allows)
- Export strategy
- Query patterns

---

# Scenario-Based Questions

## 35. Your API suddenly becomes slow. What would you investigate?

A strong answer should include:

- CloudWatch metrics
- Throttling
- Latency
- Hot partitions
- Capacity mode
- Query vs Scan
- Network issues
- Recent deployments
- Application logs

---

## 36. DynamoDB costs doubled overnight. What could be the reasons?

Possible causes:

- Increased traffic
- Full table scans
- New GSI
- Larger items
- Retry storms
- Missing cache
- Provisioned capacity changes

---

## 37. Users report stale data. What could cause this?

Possible causes:

- Eventually consistent reads
- Replication delay
- Application cache
- Incorrect cache invalidation
- Reading from a stale replica (in multi-region architectures)

---

## 38. How would you migrate from PostgreSQL to DynamoDB?

Expected approach:

1. Identify access patterns.
2. Design DynamoDB schema.
3. Create migration scripts.
4. Validate data.
5. Perform staged migration.
6. Dual-write or CDC during transition.
7. Cut over after verification.

---

## 39. A table is experiencing hot partitions. How would you fix it?

Expected discussion:

- Analyze access patterns.
- Redesign partition key.
- Introduce write sharding if appropriate.
- Cache hot data.
- Monitor CloudWatch.
- Rebuild indexes if required.

---

## 40. Your payment API created duplicate orders after retries. How would you solve it?

Expected Answer:

- Idempotency keys
- Conditional writes
- Transactions (where needed)
- Proper retry handling
- Request deduplication

---

# Rapid Fire Questions

| Question | Expected Answer |
|----------|-----------------|
| Maximum item size? | 400 KB |
| Maximum Query/Scan response? | 1 MB |
| Maximum transaction size? | 100 operations, 4 MB |
| Does Query need a partition key? | Yes |
| Does Scan require a partition key? | No |
| Can a GSI be created after table creation? | Yes |
| Can an LSI be created after table creation? | No |
| Is DynamoDB schema-less? | Yes (except key attributes) |
| Does DynamoDB support joins? | No |
| Is DynamoDB serverless? | Yes |
| Does DynamoDB support ACID transactions? | Yes |
| Can DynamoDB automatically expire items? | Yes (TTL) |
| Does DynamoDB support Global Tables? | Yes |
| Does DynamoDB support Point-in-Time Recovery? | Yes |
| Is Boto3 synchronous? | Yes |
| Is aioboto3 asynchronous? | Yes |

---

# Senior Interview Tips

When answering senior-level DynamoDB questions:

- Explain **why**, not just **what**.
- Discuss trade-offs between different approaches.
- Mention operational concerns such as monitoring, observability, and cost.
- Consider failure scenarios and recovery strategies.
- Reference production patterns like Repository Layers, retries, caching, and Infrastructure as Code where appropriate.

Interviewers are generally evaluating architecture and decision-making, not just API familiarity.

---

# Common Mistakes During Interviews

Avoid answers like:

> "I would just use Scan."

Instead explain:

- Why Query is preferred
- Appropriate key design
- Required indexes
- Capacity implications

---

Avoid saying:

> "DynamoDB automatically scales everything."

A stronger answer distinguishes between:

- On-Demand vs Provisioned Capacity
- Auto Scaling behavior
- Adaptive Capacity
- Application-level optimizations

---

# Final Preparation Checklist

Before a DynamoDB interview, make sure you can confidently explain:

- ✅ Table design based on access patterns
- ✅ Partition Keys and Sort Keys
- ✅ GSIs vs LSIs
- ✅ Query vs Scan
- ✅ Conditional Writes
- ✅ Transactions
- ✅ Pagination
- ✅ Boto3 Client vs Resource
- ✅ Repository Pattern
- ✅ Retry strategies with exponential backoff and jitter
- ✅ DynamoDB Local
- ✅ Monitoring with CloudWatch
- ✅ Security with IAM and KMS
- ✅ Performance optimization techniques
- ✅ Disaster recovery (PITR and Global Tables)
- ✅ Common production troubleshooting scenarios

---

# Key Takeaways

- Senior DynamoDB interviews focus on **architecture, scalability, and operational excellence**, not just CRUD APIs.
- Be prepared to justify design decisions, discuss trade-offs, and explain how your solution behaves under production workloads.
- Strong candidates demonstrate knowledge of access-pattern-driven modeling, resilience, observability, security, and cost optimization.
- Practice scenario-based questions, as they closely resemble real-world engineering discussions.