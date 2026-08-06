# Message Keys

## Overview

A **Message Key** is an optional value attached to a Kafka message that determines which partition the message will be written to.

While the message value contains the actual business data, the key is primarily used for **partitioning** and **maintaining message ordering**.

Without a message key, Kafka distributes messages across partitions to balance the load. With a message key, Kafka ensures that all messages with the same key are consistently routed to the same partition.

Message keys are fundamental to designing scalable and reliable Kafka applications.

---

# What is a Message Key?

A Kafka message consists of two main parts:

```text
Key

Value
```

Example:

```text
Key

Customer ID = 105

------------------------

Value

Order Created
```

Or in JSON:

```json
Key:
{
    "customer_id": 105
}

Value:
{
    "order_id": 2501,
    "amount": 500,
    "status": "CREATED"
}
```

The key is **not** the business data itself.

Instead, Kafka uses it to determine where the message should be stored.

---

# Message Without a Key

Suppose a producer sends messages without specifying a key.

```text
Producer

↓

Order 1

Order 2

Order 3

Order 4
```

Kafka distributes them across partitions.

```text
Orders Topic

P0 ← Order 1

P1 ← Order 2

P2 ← Order 3

P0 ← Order 4
```

This provides excellent load balancing.

However, message ordering for a particular customer or order is not guaranteed.

---

# Message With a Key

Now suppose every message contains a Customer ID.

```text
Customer ID = 101

↓

Order Created

Customer ID = 101

↓

Payment Completed

Customer ID = 101

↓

Order Shipped
```

Kafka hashes the key.

```text
Hash(Customer ID)

↓

Partition
```

All messages with Customer ID 101 always go to the same partition.

```text
Orders Topic

Partition 2

Order Created

↓

Payment Completed

↓

Order Shipped
```

Ordering is preserved.

---

# How Kafka Chooses a Partition

When a key is provided, Kafka calculates:

```text
Partition = Hash(Key) % Number of Partitions
```

Example:

```text
Customer ID = 105

Hash = 456987

Partitions = 4

456987 % 4 = Partition 3
```

Every future message with Customer ID 105 will also be stored in Partition 3.

---

# Why Are Message Keys Important?

Keys solve several important problems.

They provide:

- Consistent partitioning
- Message ordering
- Predictable routing
- Better scalability

Without keys:

```text
Customer 101

↓

P0

P2

P1

P3
```

Events become scattered across multiple partitions.

With keys:

```text
Customer 101

↓

P2

P2

P2

P2
```

Everything stays together.

---

# Real-World Example

Imagine an online banking system.

Transactions:

```text
Account 5001

Deposit

Withdraw

Transfer

Balance Update
```

Without keys:

```text
Deposit → P0

Withdraw → P3

Transfer → P1

Balance Update → P2
```

Transactions may be processed out of sequence.

With the Account ID as the key:

```text
Account 5001

↓

Partition 1

Deposit

↓

Withdraw

↓

Transfer

↓

Balance Update
```

The transaction history remains ordered.

---

# Ordering Guarantee

Kafka guarantees ordering **within a partition**.

Using keys ensures related messages remain in the same partition.

Example:

```text
Customer 205

↓

Cart Created

↓

Order Created

↓

Payment Completed

↓

Invoice Generated
```

Since every event has the same key, Kafka stores them sequentially.

---

# Common Keys

Typical message keys include:

- Customer ID
- User ID
- Order ID
- Account Number
- Product ID
- Device ID
- Session ID
- Invoice Number

The best key depends on the business entity whose ordering must be preserved.

---

# Choosing a Good Key

A good key should:

- Have high cardinality.
- Evenly distribute messages.
- Represent a logical business entity.
- Preserve required ordering.

Example:

```text
Customer ID
```

Better than:

```text
Country
```

Using Country as a key may send millions of messages to a single partition.

---

# Hot Partitions

A poor key can create a **hot partition**.

Example:

```text
Key

India

↓

Partition 0
```

If millions of users share the same key, one partition becomes overloaded while others remain underutilized.

Example:

```text
P0

95% Traffic

----------------

P1

2%

----------------

P2

2%

----------------

P3

1%
```

This limits throughput.

---

# Key Distribution

A good key distributes messages evenly.

```text
Customer 101 → P0

Customer 102 → P1

Customer 103 → P2

Customer 104 → P3

Customer 105 → P0

Customer 106 → P1
```

Balanced partitions lead to better resource utilization.

---

# Null Keys

A producer may send a message without a key.

```text
Key = null
```

Kafka then distributes messages using its default partitioning strategy.

Example:

```text
Message 1 → P0

Message 2 → P1

Message 3 → P2

Message 4 → P3
```

This is suitable when ordering is not important.

---

# Keys and Consumer Groups

Keys determine the partition.

Consumer groups determine which consumer processes that partition.

```text
Customer 101

↓

Partition 2

↓

Consumer 2
```

Kafka first chooses the partition using the key.

Then it assigns that partition to a consumer.

---

# Keys and Scalability

Message keys allow Kafka to scale while preserving ordering.

Without keys:

```text
Ordering

❌ Not Guaranteed
```

With keys:

```text
Ordering

✅ Guaranteed Per Key
```

This is one of Kafka's biggest advantages over many traditional messaging systems.

---

# Best Practices

- Choose keys based on business entities.
- Ensure keys distribute data evenly.
- Use keys whenever ordering is required.
- Avoid low-cardinality keys.
- Test partition distribution before production.
- Monitor partition utilization regularly.

---

# Common Mistakes

- Using the same key for every message.
- Assuming ordering across all partitions.
- Choosing keys that create hot partitions.
- Using random keys when ordering is required.
- Ignoring key distribution during system design.

---

# Summary

Message keys determine how Kafka distributes messages across partitions. When a key is provided, Kafka consistently routes messages with the same key to the same partition, preserving their order. Well-designed keys improve scalability, maintain ordering for related events, and prevent uneven partition utilization. Choosing the right message key is one of the most important decisions when designing Kafka-based systems.

---

# Key Takeaways

- Message keys determine the destination partition.
- Kafka uses a hash function to map keys to partitions.
- Messages with the same key always go to the same partition.
- Ordering is guaranteed only within a partition.
- Well-designed keys improve scalability and consistency.
- Poor key selection can create hot partitions.
- Null keys allow Kafka to distribute messages automatically.
- Message keys are essential when preserving event order for a business entity.