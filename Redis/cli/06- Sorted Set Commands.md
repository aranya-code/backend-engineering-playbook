# Sorted Set Commands

## Overview

Redis **Sorted Sets (ZSETs)** are one of the most powerful data structures available in Redis. Like Sets, Sorted Sets store **unique members**, but unlike Sets, every member is associated with a **score**. Redis automatically maintains the collection in ascending order based on these scores.

Internally, Redis implements Sorted Sets using a combination of:

- **Hash Table** (fast member lookup)
- **Skip List** (efficient sorted ordering)

This hybrid implementation enables both fast lookups and efficient range queries, making Sorted Sets ideal for ranking and ordered data.

Sorted Sets are commonly used in backend systems for:

- Leaderboards
- Ranking systems
- Priority queues
- Recommendation engines
- Scheduling systems
- Time-based ordering
- Rate limiting
- Search result ranking
- Gaming applications
- Analytics dashboards

Unlike Lists, elements are automatically sorted. Unlike Sets, each element has an associated numeric score.

---

# Understanding Sorted Sets

Every member has a score.

```
+--------+-------+
| Member | Score |
+--------+-------+
| Alice  |  100  |
| Bob    |  250  |
| John   |  300  |
| David  |  450  |
+--------+-------+
```

Redis automatically maintains this order.

---

# Common Sorted Set Commands

| Command | Description |
|----------|-------------|
| ZADD | Add members |
| ZRANGE | Retrieve members |
| ZREVRANGE | Retrieve in descending order |
| ZRANK | Member rank |
| ZREVRANK | Reverse rank |
| ZSCORE | Retrieve score |
| ZREM | Remove members |
| ZCARD | Count members |
| ZCOUNT | Count by score |
| ZINCRBY | Increment score |
| ZRANGEBYSCORE | Retrieve by score |
| ZREMRANGEBYSCORE | Remove by score |
| ZPOPMIN | Remove lowest score |
| ZPOPMAX | Remove highest score |
| ZSCAN | Incremental iteration |

---

# ZADD

Adds one or more members.

Syntax

```redis
ZADD leaderboard score member
```

Example

```redis
ZADD leaderboard

100 Alice

250 Bob

400 David
```

Output

```
(integer) 3
```

Complexity

```
O(log N)
```

Redis automatically places each member in the correct position.

---

# ZRANGE

Returns members in ascending order.

Example

```redis
ZRANGE leaderboard 0 -1
```

Output

```
1) Alice

2) Bob

3) David
```

Useful for:

- Ordered reports
- Rankings
- Scheduling

---

# ZREVRANGE

Returns members in descending order.

Example

```redis
ZREVRANGE leaderboard 0 2
```

Output

```
David

Bob

Alice
```

Very common for:

- Top players
- Highest scores
- Trending items

---

# ZRANK

Returns a member's rank.

Example

```redis
ZRANK leaderboard Bob
```

Output

```
(integer) 1
```

Ranks start at zero.

---

# ZREVRANK

Returns reverse ranking.

Example

```redis
ZREVRANK leaderboard Bob
```

Useful for:

- Leaderboards
- Competition rankings

---

# ZSCORE

Returns the score of a member.

Example

```redis
ZSCORE leaderboard Bob
```

Output

```
250
```

Useful when displaying rankings.

---

# ZREM

Removes members.

Example

```redis
ZREM leaderboard Alice
```

Output

```
(integer) 1
```

---

# ZCARD

Returns the number of members.

Example

```redis
ZCARD leaderboard
```

Output

```
(integer) 15000
```

Complexity

```
O(1)
```

---

# ZCOUNT

Counts members within a score range.

Example

```redis
ZCOUNT leaderboard 100 500
```

Useful for:

- Analytics
- Statistics
- Reporting

---

# ZINCRBY

Updates a score.

Example

```redis
ZINCRBY leaderboard 50 Bob
```

Current

```
Bob

250
```

After update

```
Bob

300
```

Redis automatically reorders the member.

---

# ZRANGEBYSCORE

Returns members within a score range.

Example

```redis
ZRANGEBYSCORE leaderboard 200 400
```

Output

```
Bob

John
```

Useful for:

- Price ranges
- Date ranges
- Score filtering
- Time windows

---

# ZREMRANGEBYSCORE

Deletes members within a score range.

Example

```redis
ZREMRANGEBYSCORE sessions 0 1650000000
```

Useful for removing expired entries.

---

# ZPOPMIN

Removes the member with the lowest score.

Example

```redis
ZPOPMIN jobs
```

Architecture

```
Priority Queue

↓

Lowest Priority

↓

Removed
```

---

# ZPOPMAX

Removes the highest score.

Example

```redis
ZPOPMAX leaderboard
```

Useful for retrieving top-ranked entries.

---

# ZSCAN

Incrementally scans a Sorted Set.

Example

```redis
ZSCAN leaderboard 0
```

Recommended for:

- Large datasets
- Production systems

---

# Leaderboard Example

```
Players

↓

ZADD

↓

Leaderboard

↓

ZREVRANGE

↓

Top Players
```

Example

```
Alice

1500

Bob

1800

David

2400
```

Top 3

```redis
ZREVRANGE leaderboard 0 2
```

---

# Priority Queue Example

```
Tasks

↓

Priority Score

↓

Redis Sorted Set

↓

Worker

↓

ZPOPMIN
```

The smallest score represents the highest priority.

---

# Scheduler Example

```
Task

↓

Execution Timestamp

↓

Sorted Set

↓

Worker

↓

ZRANGEBYSCORE
```

Tasks are executed based on timestamps.

---

# Delayed Job Queue

```
Application

↓

Schedule Job

↓

ZADD timestamp

↓

Worker

↓

ZRANGEBYSCORE

↓

Execute
```

Very common in distributed systems.

---

# Rate Limiter Example

```
API Request

↓

Timestamp

↓

Sorted Set

↓

Old Entries Removed

↓

Count Requests
```

Sliding window rate limiting often uses Sorted Sets.

---

# Recommendation Engine

```
Products

↓

Popularity Score

↓

Sorted Set

↓

Top Products
```

Scores may represent:

- Sales
- Views
- Ratings
- Clicks

---

# Analytics Dashboard

```
User Scores

↓

Sorted Set

↓

Top 10 Users

↓

Dashboard
```

---

# Common Production Use Cases

Sorted Sets are commonly used for:

- Gaming leaderboards
- Trending products
- Search ranking
- Priority scheduling
- Delayed task execution
- Time-series indexing
- Sliding window rate limiting
- Analytics
- Recommendation systems
- Top-N reports

---

# Common Mistakes

## Using Lists for Rankings

Lists require manual sorting.

Sorted Sets maintain order automatically.

---

## Storing Large Objects

Instead of

```
Entire User Object
```

Store

```
User ID
```

Retrieve details separately.

---

## Ignoring Scores

Scores should have clear meaning:

Examples:

- Timestamp
- Price
- Rating
- Priority
- Score

Avoid arbitrary values.

---

## Loading Massive Sorted Sets

Avoid

```redis
ZRANGE 0 -1
```

for millions of entries.

Instead:

- Paginate
- Use score ranges
- Use ZSCAN

---

# Best Practices

- Store lightweight identifiers.
- Use timestamps as scores for scheduling.
- Use numeric rankings for leaderboards.
- Paginate large result sets.
- Monitor memory usage.
- Remove obsolete members regularly.
- Use ZINCRBY instead of deleting and reinserting members.

---

# Performance Considerations

| Command | Complexity |
|----------|------------|
| ZADD | O(log N) |
| ZREM | O(log N) |
| ZRANK | O(log N) |
| ZREVRANK | O(log N) |
| ZSCORE | O(1) |
| ZCARD | O(1) |
| ZCOUNT | O(log N) |
| ZINCRBY | O(log N) |
| ZRANGE | O(log N + M) |
| ZREVRANGE | O(log N + M) |
| ZRANGEBYSCORE | O(log N + M) |
| ZSCAN | O(1) per iteration |

*M = number of returned elements.*

---

# Production Considerations

For production deployments:

- Store IDs rather than large payloads.
- Periodically remove stale entries.
- Use timestamps for delayed processing.
- Paginate large leaderboards.
- Monitor high-cardinality Sorted Sets.
- Use Sorted Sets for sliding window rate limiting instead of Lists.
- Combine with Hashes when additional metadata is required.

---

# Comparison with Other Data Structures

| Feature | List | Set | Sorted Set |
|---------|------|-----|------------|
| Ordered | ✅ | ❌ | ✅ |
| Unique Values | ❌ | ✅ | ✅ |
| Scores | ❌ | ❌ | ✅ |
| Fast Membership | ❌ | ✅ | ✅ |
| Ranking | ❌ | ❌ | ✅ |
| Range Queries | Limited | ❌ | ✅ |

---

# Summary

Redis Sorted Sets combine the uniqueness of Sets with automatic ordering based on numeric scores, making them one of the most versatile data structures in Redis. They are the preferred choice for leaderboards, scheduling systems, priority queues, recommendation engines, and any application that requires efficient ranking or ordered retrieval. By leveraging score-based operations such as `ZRANGEBYSCORE`, `ZINCRBY`, and `ZREVRANGE`, backend engineers can build scalable and high-performance systems with minimal application-side processing.

---

# Key Takeaways

- Sorted Sets store **unique members associated with numeric scores**.
- Redis automatically maintains members in sorted order.
- `ZADD`, `ZRANGE`, `ZREVRANGE`, and `ZSCORE` are the fundamental commands.
- `ZINCRBY` efficiently updates rankings without manual sorting.
- `ZRANGEBYSCORE` enables powerful score-based queries.
- Sorted Sets are ideal for leaderboards, scheduling, priority queues, analytics, and sliding window rate limiting.
- Store lightweight identifiers and retrieve detailed data separately for optimal memory efficiency.
```