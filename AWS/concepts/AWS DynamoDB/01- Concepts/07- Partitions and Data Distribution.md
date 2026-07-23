# 07 - Partitions and Data Distribution

## Overview

One of DynamoDB's defining characteristics is its ability to scale from a handful of requests per second to millions without requiring developers to redesign their infrastructure. This capability is possible because DynamoDB is **partitioned**.

A partition is the fundamental storage unit inside DynamoDB. Every item written to a table is stored in a physical partition, and every read or write operation is ultimately served by one of these partitions.

Unlike traditional databases, where developers often manage sharding manually, DynamoDB automatically creates, manages, balances, and splits partitions as your workload grows.

Understanding partitions is essential because concepts such as throughput, hot partitions, adaptive capacity, and partition keys all build upon this architecture.

---

# What is a Partition?

A partition is a physical storage unit managed by DynamoDB.

Instead of storing every item on one server, DynamoDB spreads data across multiple partitions.

```text
                 DynamoDB Table

        +-----------------------------+
        |                             |
        |   Customer Data             |
        |   Order Data                |
        |   Product Data              |
        |                             |
        +-------------+---------------+
                      |
        ---------------------------------------
        |             |             |          |
        ▼             ▼             ▼          ▼

   Partition A   Partition B   Partition C   Partition D
```

Each partition stores only a portion of the table's data.

To the application, however, the table appears as a single logical database.

---

# Why Does DynamoDB Partition Data?

Imagine a table containing one billion customer records.

If every record were stored on a single machine:

```text
Application

      │

      ▼

Database Server

1 Billion Records
```

Eventually that server would reach its limits.

Problems include:

- CPU exhaustion
- Memory constraints
- Storage limitations
- Network bottlenecks
- Increased latency

Instead of making one server larger, DynamoDB distributes data across many storage nodes.

```text
Application

        │

        ▼

+----------------------------------+
|         DynamoDB Table           |
+----------------------------------+

      │      │      │      │

      ▼      ▼      ▼      ▼

 Partition A
 Partition B
 Partition C
 Partition D
```

Each partition handles only a fraction of the workload.

As demand increases, DynamoDB simply adds more partitions.

---

# How Does DynamoDB Choose a Partition?

Developers never specify which partition stores an item.

Instead, DynamoDB performs a hashing operation on the **Partition Key**.

```text
Partition Key

      │

      ▼

Hash Function

      │

      ▼

Hash Value

      │

      ▼

Physical Partition
```

This process is completely automatic.

For example:

```text
UserId = USER#1001

↓

Hash

↓

Partition B
```

Another user:

```text
UserId = USER#8273

↓

Hash

↓

Partition D
```

As long as the partition key remains the same, DynamoDB can always determine exactly where the item is stored.

---

# Why Hashing?

Suppose DynamoDB stored records alphabetically.

```text
A - D

↓

Partition 1

E - H

↓

Partition 2

I - Z

↓

Partition 3
```

If 90% of users happened to have names beginning with **A**, Partition 1 would become overloaded.

Hashing avoids this problem.

Instead of using alphabetical ordering, the partition key is transformed into a seemingly random value.

The result is a much more even distribution of data.

---

# Partition Capacity

Each partition has a finite amount of resources.

These resources include:

- CPU
- Memory
- Storage
- Network bandwidth
- Read throughput
- Write throughput

Although AWS abstracts these limits away from developers, they still exist internally.

As a table grows, DynamoDB creates additional partitions to distribute both data and traffic.

This automatic scaling is one of DynamoDB's greatest advantages over manually sharded databases.

---

# Automatic Partition Splitting

Initially, a table may consist of a single partition.

```text
Users Table

↓

Partition A
```

As storage or throughput requirements increase:

```text
Users Table

↓

Partition A

Partition B
```

Eventually:

```text
Users Table

↓

Partition A

Partition B

Partition C

Partition D
```

This process occurs automatically.

Developers never manually create partitions.

---

# Storage-Based Partitioning

Partitions are created not only because of traffic but also because of storage growth.

As data volume increases, DynamoDB automatically redistributes items across new partitions.

From the application's perspective:

- No downtime occurs.
- No configuration changes are required.
- Queries continue functioning normally.

This ability to expand transparently is one reason DynamoDB is considered serverless.

---

# Throughput-Based Partitioning

Traffic growth can also trigger partition creation.

Imagine an application suddenly receiving ten times its normal traffic.

Instead of overwhelming existing partitions, DynamoDB increases partition capacity by distributing requests across additional partitions whenever possible.

This allows applications to scale with demand while maintaining predictable latency.

---

# Logical vs Physical View

Developers see a single table.

```text
Users Table
```

Internally, AWS may store that table across dozens or even hundreds of partitions.

```text
Users Table

↓

Partition A

Partition B

Partition C

Partition D

Partition E

Partition F
```

The physical architecture is completely hidden from applications.

This abstraction greatly simplifies application development.

---

# Data Locality

Items with the same partition key are stored together.

Example:

```text
PK = CUSTOMER#1001

SK = ORDER#001

----------------------

PK = CUSTOMER#1001

SK = ORDER#002

----------------------

PK = CUSTOMER#1001

SK = ORDER#003
```

Because these items share the same partition key, DynamoDB stores them in the same logical partition.

This enables highly efficient queries that retrieve all related records without scanning the rest of the table.

Data locality is one of the reasons composite primary keys are so powerful.

---

# Even Distribution is Critical

Suppose we choose:

```text
Partition Key

Country
```

Most users come from:

```text
USA
```

Result:

```text
USA

↓

Partition A

Millions of Requests
```

Meanwhile:

```text
Canada

↓

Partition B

Very Few Requests
```

One partition becomes overloaded while others remain mostly idle.

This is known as a **Hot Partition**.

The problem is not the partition itself—it is the choice of partition key.

---

# Adaptive Capacity

Traffic in real applications is rarely perfectly balanced.

Some partitions naturally receive more requests than others.

To improve performance, DynamoDB includes a feature called **Adaptive Capacity**.

Adaptive Capacity dynamically reallocates internal resources to partitions experiencing higher demand.

Benefits include:

- Reduced throttling
- Improved throughput
- Better utilization of available capacity
- Automatic optimization

Although Adaptive Capacity helps absorb temporary traffic imbalances, it is **not** a substitute for good partition key design.

A poorly designed partition key can still become a bottleneck.

---

# Why Developers Rarely Think About Partitions

Traditional distributed databases often require engineers to manage:

- Sharding
- Rebalancing
- Node failures
- Cluster expansion
- Replica placement

With DynamoDB, AWS handles all of these responsibilities.

Developers focus on:

- Primary Keys
- Data Modeling
- Access Patterns

Everything else is managed by the service.

This abstraction is one of DynamoDB's biggest operational advantages.

---

# Common Mistakes

## Assuming More Partitions Always Improve Performance

Additional partitions increase scalability only when data and traffic are distributed evenly.

Poor partition key design can overload a single partition regardless of how many partitions exist.

---

## Ignoring Access Patterns

A partition key should distribute traffic—not merely provide uniqueness.

Many beginners choose keys based only on uniqueness without considering request distribution.

---

## Expecting to Control Partitions

Unlike traditional sharded databases, DynamoDB does not expose partitions to developers.

There are no APIs for creating, deleting, or assigning partitions.

AWS manages the partition lifecycle automatically.

---

# Interview Notes

A common interview question is:

> **If DynamoDB manages partitions automatically, why should developers care about them?**

Because developers choose the **partition key**.

The partition key determines how evenly data and traffic are distributed across physical partitions.

A good partition key enables DynamoDB to scale efficiently.

A poor partition key can create hot partitions, increased latency, and request throttling—even though the infrastructure itself is fully managed.

Understanding partitions is therefore essential for designing scalable DynamoDB applications.

---

# Key Takeaways

- A partition is the fundamental physical storage unit in DynamoDB.
- DynamoDB automatically distributes items across partitions using a hash of the partition key.
- Developers never manually manage partitions.
- Partitions grow automatically based on storage and throughput requirements.
- Items sharing the same partition key are stored together, enabling efficient queries.
- Even traffic distribution is essential for achieving predictable performance.
- Adaptive Capacity helps optimize uneven workloads but does not replace good schema design.
- The quality of your partition key ultimately determines how well DynamoDB can scale.