# Data Structures Interview Questions

## Overview

One of the most common mistakes candidates make is thinking Redis is simply a **key-value cache**.

In reality, Redis supports multiple optimized data structures, each designed for specific workloads.

Senior interviewers frequently ask:

- Which Redis data structure would you use?
- Why did you choose it?
- What is its time complexity?
- What are the trade-offs?
- What happens at scale?

This chapter covers the most frequently asked interview questions related to Redis data structures.

---

# Q1. What data structures does Redis support?

### Answer

Redis supports multiple native data structures.

| Data Structure | Primary Use Case |
|----------------|------------------|
| String | Cache, Counters |
| Hash | Objects |
| List | Queues |
| Set | Unique Collections |
| Sorted Set | Leaderboards |
| Bitmap | User Activity |
| HyperLogLog | Approximate Counting |
| Geospatial | Location Services |
| Streams | Event Streaming |

---

## Interview Tip

Don't just list them.

Explain **when** you would use each one.

---

# Q2. Which Redis data structure is used the most?

### Answer

The most commonly used is the **String**.

Strings are used for

- Cache
- Sessions
- Tokens
- Counters
- JSON
- Feature flags

Example

```bash
SET user:101 "John"
GET user:101
```

---

# Q3. Why are Redis Strings so versatile?

### Answer

Redis Strings can store

- Text
- Numbers
- JSON
- Binary Data
- Serialized Objects

Maximum size

```
512 MB
```

---

# Q4. When should you use a Hash instead of a String?

### Answer

Use Hashes when storing multiple fields belonging to one object.

Instead of

```text
user:101:name

user:101:age

user:101:email
```

Store

```bash
HSET user:101 \
name John \
age 30 \
email john@example.com
```

Advantages

- Less memory
- Easier updates
- Better organization

---

# Q5. What is the time complexity of HGET?

### Answer

```
O(1)
```

Redis uses hash tables internally.

Retrieving a field is extremely fast.

---

# Q6. When should Lists be used?

### Answer

Lists are ideal for

- Queues
- Task processing
- Chat messages
- Activity feeds
- Recent history

Example

```bash
LPUSH jobs job1

RPUSH jobs job2

LPOP jobs
```

---

# Q7. Difference between LPUSH and RPUSH?

### Answer

```
LPUSH

↓

Insert Left
```

```
RPUSH

↓

Insert Right
```

Example

```
LPUSH A

LPUSH B

List

B A
```

---

# Q8. What is the complexity of LPUSH?

### Answer

```
O(1)
```

Insertion happens at one end of the list.

---

# Q9. When should Sets be used?

### Answer

Sets are ideal when

- Values must be unique
- Order doesn't matter

Examples

- Tags
- User permissions
- Friend lists
- Product categories

Example

```bash
SADD admins alice bob alice
```

Result

```
alice

bob
```

Duplicate values are ignored.

---

# Q10. What is the difference between List and Set?

| List | Set |
|------|------|
| Ordered | Unordered |
| Duplicates allowed | Unique values |
| Queue | Membership |
| Index based | Lookup based |

---

# Q11. Why are Sets useful?

### Answer

Fast membership testing.

Example

```bash
SISMEMBER admins alice
```

Complexity

```
O(1)
```

---

# Q12. What are Sorted Sets?

### Answer

Sorted Sets maintain

```
Value

+

Score
```

Example

```bash
ZADD leaderboard 100 Alice

ZADD leaderboard 90 Bob
```

Result

```
Alice

Bob
```

sorted by score.

---

# Q13. What are Sorted Sets used for?

### Answer

Very common interview question.

Production examples

- Leaderboards
- Rankings
- Gaming
- Trending posts
- Stock rankings
- Recommendation engines

---

# Q14. Difference between Set and Sorted Set?

| Set | Sorted Set |
|------|------------|
| No score | Score |
| Unordered | Ordered |
| Faster | Slightly slower |
| Membership | Ranking |

---

# Q15. What is the complexity of ZADD?

### Answer

```
O(log N)
```

Redis maintains ordering internally.

---

# Q16. What are Bitmaps?

### Answer

Bitmaps store

```
0

or

1
```

efficiently.

Example

Track

```
User Logged In Today?
```

```
Bit

↓

0

or

1
```

Millions of users require very little memory.

---

# Q17. When are Bitmaps useful?

### Answer

Examples

- Daily login tracking
- Attendance
- Feature rollout
- Boolean flags

---

# Q18. What is HyperLogLog?

### Answer

HyperLogLog estimates

```
Unique Count
```

using a probabilistic algorithm.

Instead of storing

```
10 Million Users
```

it stores a compact representation.

Memory

Approximately

```
12 KB
```

regardless of dataset size.

---

# Q19. When should HyperLogLog be used?

### Answer

Examples

- Unique visitors
- Unique IPs
- Daily active users
- Analytics

Trade-off

Small error

↓

Huge memory savings.

---

# Q20. What are Geospatial indexes?

### Answer

Redis stores coordinates.

Example

```
Restaurant

↓

Latitude

Longitude
```

Commands

```bash
GEOADD

GEORADIUS

GEOSEARCH
```

Use cases

- Food delivery
- Ride sharing
- Nearby stores
- Maps

---

# Q21. What are Redis Streams?

### Answer

Streams are an append-only data structure designed for event processing.

Architecture

```
Producer

↓

Stream

↓

Consumer Group

↓

Consumers
```

Used for

- Event processing
- Messaging
- Logging
- Background jobs

---

# Q22. Difference between Pub/Sub and Streams?

| Pub/Sub | Streams |
|----------|----------|
| Fire and forget | Persistent |
| No history | Message history |
| No replay | Replay supported |
| No consumer groups | Consumer groups |
| Real-time only | Reliable processing |

---

# Q23. Which Redis data structure would you use for a leaderboard?

### Answer

```
Sorted Set
```

Reason

- Ranking
- Scores
- Top N
- Range queries

---

# Q24. Which structure is best for caching JSON?

### Answer

Usually

```
String
```

Store serialized JSON.

Alternative

```
Hash
```

if individual fields require frequent updates.

---

# Q25. Which structure is best for user profiles?

### Answer

```
Hash
```

Each profile attribute becomes a field.

Advantages

- Partial updates
- Lower memory usage
- Easy retrieval

---

# Q26. Which structure is best for implementing a queue?

### Answer

```
List
```

Commands

```bash
LPUSH

BRPOP
```

or

Modern systems may prefer

```
Streams
```

for reliable processing.

---

# Q27. Which structure is best for unique tags?

### Answer

```
Set
```

Duplicates are automatically removed.

---

# Q28. Which structure is best for real-time analytics?

### Answer

Depends on the requirement.

| Requirement | Structure |
|-------------|-----------|
| Counter | String |
| Unique Users | HyperLogLog |
| Rankings | Sorted Set |
| User Activity | Bitmap |
| Events | Stream |

---

# Rapid Fire Questions

| Question | Answer |
|----------|--------|
| Ordered unique collection? | Sorted Set |
| Queue? | List |
| User Profile? | Hash |
| Counter? | String |
| Unique visitors? | HyperLogLog |
| Login tracking? | Bitmap |
| Nearby restaurants? | Geospatial |
| Messaging? | Streams |

---

# Senior Interview Tips

Interviewers rarely ask only

> "What is a Hash?"

Instead they ask

> "You have a leaderboard with 100 million players. Which data structure would you use and why?"

A strong answer includes

- Sorted Set
- O(log N) insertion
- Efficient ranking
- Range queries
- Top-N retrieval
- Production scalability

---

# Common Mistakes

## Using Strings for Everything

Redis provides specialized data structures.

Choose the correct one.

---

## Ignoring Time Complexity

Senior engineers should know

- O(1)
- O(log N)
- O(N)

for commonly used commands.

---

## Choosing Lists for Unique Data

Lists allow duplicates.

Sets do not.

---

## Using Pub/Sub for Reliable Messaging

Use Streams when message durability and replay are required.

---

# Best Practices

- Select data structures based on access patterns.
- Understand command complexity before using a structure at scale.
- Avoid oversized values within a single key.
- Prefer Hashes for objects with multiple fields.
- Use Sorted Sets for ranking problems.
- Choose Streams over Lists when reliability and consumer groups are required.

---

# Summary

Redis offers a rich set of specialized data structures that solve different classes of problems efficiently. Senior engineers are expected not only to know these structures, but also to understand their performance characteristics, trade-offs, and production use cases. Selecting the appropriate data structure is one of the most important design decisions when building scalable Redis-backed systems.

---

# Key Takeaways

- Strings are the most versatile and widely used Redis data structure.
- Hashes efficiently store objects with multiple fields.
- Lists are ideal for queues and ordered sequences.
- Sets enforce uniqueness and support fast membership checks.
- Sorted Sets combine uniqueness with ranking capabilities.
- Bitmaps and HyperLogLog provide highly memory-efficient solutions for specialized analytics.
- Streams enable reliable event processing with consumer groups.
- Understanding the strengths and complexities of each data structure is essential for senior backend interviews.