# Redis Data Structures Cheat Sheet

## Overview

Redis provides several specialized data structures optimized for different use cases. Choosing the correct data structure is critical for building efficient, scalable, and maintainable backend applications.

This cheat sheet summarizes the purpose, time complexity, common commands, and production use cases for each Redis data structure.

---

# Quick Comparison

| Data Structure | Stores | Typical Use Cases | Lookup Complexity |
|---------------|--------|-------------------|-------------------|
| String | Single value | Cache, Counters, Sessions | O(1) |
| Hash | Field-value pairs | User Profiles, Objects | O(1) |
| List | Ordered collection | Queues, Activity Feeds | O(1) (Ends) |
| Set | Unique values | Tags, Online Users | O(1) |
| Sorted Set | Ordered unique values | Leaderboards, Rankings | O(log N) |
| Stream | Append-only log | Event Processing, Messaging | O(log N) |
| Bitmap | Bit array | Feature Flags, User Tracking | O(1) |
| HyperLogLog | Approximate set | Unique Visitors | O(1) |
| Geospatial | Coordinates | Ride Sharing, Nearby Search | O(log N) |

---

# 1. Strings

## Best For

- Cache
- Sessions
- Counters
- Tokens
- Feature Flags

---

## Commands

```bash
SET key value

GET key

DEL key

INCR counter

DECR counter

APPEND key text

MGET key1 key2

MSET key1 value1 key2 value2
```

---

## Example

```bash
SET user:101 "Alice"

GET user:101
```

---

## Time Complexity

| Operation | Complexity |
|-----------|------------|
| GET | O(1) |
| SET | O(1) |
| INCR | O(1) |

---

## Production Examples

- Session IDs
- JWT Blacklist
- API Cache
- Counters
- OTP

---

# 2. Hashes

## Best For

Store objects.

```
User

↓

Name

Email

Age

Country
```

---

## Commands

```bash
HSET user:101

name Alice

email alice@example.com

HGET user:101 name

HGETALL user:101

HDEL user:101 age
```

---

## Time Complexity

| Operation | Complexity |
|-----------|------------|
| HSET | O(1) |
| HGET | O(1) |
| HDEL | O(1) |

---

## Production Examples

- User Profiles
- Product Details
- Configuration
- Shopping Cart Items
- Inventory

---

# 3. Lists

## Best For

Ordered data.

```
Newest

↓

Older

↓

Oldest
```

---

## Commands

```bash
LPUSH queue task1

RPUSH queue task2

LPOP queue

RPOP queue

LRANGE queue 0 -1
```

---

## Time Complexity

| Operation | Complexity |
|-----------|------------|
| LPUSH | O(1) |
| RPUSH | O(1) |
| LPOP | O(1) |
| RPOP | O(1) |

---

## Production Examples

- Job Queue
- Activity Feed
- Search History
- Notification Queue

---

# 4. Sets

## Best For

Unique collections.

```
Online Users

↓

Alice

Bob

Charlie
```

---

## Commands

```bash
SADD online Alice

SREM online Alice

SMEMBERS online

SCARD online

SISMEMBER online Alice
```

---

## Time Complexity

| Operation | Complexity |
|-----------|------------|
| SADD | O(1) |
| SREM | O(1) |
| SISMEMBER | O(1) |

---

## Production Examples

- Online Users
- User Roles
- Tags
- Permissions

---

# 5. Sorted Sets

## Best For

Ranked data.

```
Leaderboard

↓

Player

↓

Score
```

---

## Commands

```bash
ZADD leaderboard 100 Alice

ZINCRBY leaderboard 20 Alice

ZRANGE leaderboard 0 -1

ZREVRANGE leaderboard 0 9 WITHSCORES
```

---

## Time Complexity

| Operation | Complexity |
|-----------|------------|
| ZADD | O(log N) |
| ZRANGE | O(log N) |
| ZINCRBY | O(log N) |

---

## Production Examples

- Gaming Leaderboards
- Trending Posts
- Product Rankings
- Priority Queues

---

# 6. Streams

## Best For

Event-driven systems.

```
Producer

↓

Redis Stream

↓

Consumer Group

↓

Workers
```

---

## Commands

```bash
XADD orders *

customer Alice

amount 100

XREAD STREAMS orders 0

XGROUP CREATE orders workers 0

XREADGROUP GROUP workers worker1 STREAMS orders >
```

---

## Production Examples

- Event Processing
- Order Queue
- Email Queue
- Background Jobs

---

# 7. Bitmaps

## Best For

Binary state.

```
User

↓

Visited?

↓

1

0
```

---

## Commands

```bash
SETBIT visits 101 1

GETBIT visits 101

BITCOUNT visits
```

---

## Production Examples

- Daily Active Users
- Feature Flags
- Email Open Tracking
- Login Tracking

---

# 8. HyperLogLog

## Best For

Approximate unique counting.

---

## Commands

```bash
PFADD visitors Alice

PFADD visitors Bob

PFCOUNT visitors

PFMERGE monthly daily
```

---

## Advantages

- Extremely memory efficient
- Suitable for millions of users
- Approximate results

---

## Production Examples

- Unique Visitors
- Unique IP Addresses
- Campaign Reach

---

# 9. Geospatial

## Best For

Location-based applications.

---

## Commands

```bash
GEOADD drivers

77.5946

12.9716

driver101

GEOSEARCH drivers

FROMLONLAT 77.59 12.97

BYRADIUS 5 km
```

---

## Production Examples

- Ride Sharing
- Food Delivery
- Nearby Stores
- Driver Tracking

---

# Choosing the Right Data Structure

| Problem | Recommended Structure |
|----------|-----------------------|
| Cache | String |
| Session | String |
| User Profile | Hash |
| Shopping Cart | Hash |
| Queue | List |
| Online Users | Set |
| Leaderboard | Sorted Set |
| Event Streaming | Stream |
| Feature Flags | Bitmap |
| Unique Visitors | HyperLogLog |
| GPS Tracking | Geospatial |

---

# Complexity Cheat Sheet

| Structure | Read | Write |
|------------|------|-------|
| String | O(1) | O(1) |
| Hash | O(1) | O(1) |
| List | O(N) (middle) | O(1) (ends) |
| Set | O(1) | O(1) |
| Sorted Set | O(log N) | O(log N) |
| Stream | O(log N) | O(log N) |
| Bitmap | O(1) | O(1) |
| HyperLogLog | O(1) | O(1) |
| Geospatial | O(log N) | O(log N) |

---

# Decision Flow

```text
Need to store one value?
        │
        ▼
     String

Need object fields?
        │
        ▼
      Hash

Need ordered queue?
        │
        ▼
      List

Need unique values?
        │
        ▼
       Set

Need ranking?
        │
        ▼
   Sorted Set

Need event log?
        │
        ▼
     Stream

Need binary flags?
        │
        ▼
     Bitmap

Need approximate unique count?
        │
        ▼
   HyperLogLog

Need location search?
        │
        ▼
   Geospatial
```

---

# Common Mistakes

| Mistake | Better Choice |
|----------|---------------|
| Store objects in Strings | Use Hashes |
| Leaderboard with Lists | Use Sorted Sets |
| Queue with Sets | Use Lists or Streams |
| Count uniques with Sets | Use HyperLogLog |
| Nearby search using Hashes | Use Geospatial |
| Event queue using Lists | Prefer Streams for reliable processing |

---

# Interview Tips

Senior interviewers often ask:

- Why Hash instead of String?
- Why Sorted Set instead of List?
- When should Streams replace Pub/Sub?
- Why use HyperLogLog instead of Set?
- Which structure minimizes memory usage?
- What are the time complexities of each operation?

Always explain:

1. Why you selected the data structure.
2. Time complexity.
3. Memory trade-offs.
4. Production scalability.
5. Alternative options and why they were not chosen.