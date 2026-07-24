# Set Commands

## Overview

Redis Sets are **unordered collections of unique elements**. Unlike Lists, Sets automatically prevent duplicate values, making them an excellent choice for operations involving uniqueness, membership testing, and mathematical set operations.

Sets are implemented using hash tables or integer sets internally, depending on the stored values and the size of the collection. This allows Redis to perform membership checks, insertions, and deletions in constant time for most workloads.

Redis Sets are widely used in backend systems for:

- User permissions
- Role-based access control (RBAC)
- Tags and categories
- Friend and follower relationships
- Shopping cart uniqueness
- Unique visitors
- Feature flags
- Recommendation engines
- Mutual connections
- Interest matching

Unlike Lists, Sets do **not preserve insertion order**.

---

# Understanding Redis Sets

A Set stores only unique values.

```
Tags

+---------+
| Python  |
| Redis   |
| Docker  |
| AWS     |
+---------+
```

Adding an existing value has no effect.

```
SADD tags Redis

↓

Already Exists

↓

No Duplicate Added
```

---

# Common Set Commands

| Command | Description |
|----------|-------------|
| SADD | Add members |
| SMEMBERS | Retrieve all members |
| SISMEMBER | Check membership |
| SCARD | Count members |
| SREM | Remove members |
| SPOP | Remove random member |
| SRANDMEMBER | Retrieve random member |
| SMOVE | Move member between sets |
| SUNION | Union of sets |
| SINTER | Intersection of sets |
| SDIFF | Difference of sets |
| SUNIONSTORE | Store union |
| SINTERSTORE | Store intersection |
| SDIFFSTORE | Store difference |
| SSCAN | Incrementally iterate members |

---

# SADD

Adds one or more members.

Syntax

```redis
SADD key member
```

Example

```redis
SADD languages Python
```

Output

```
(integer) 1
```

Adding multiple members:

```redis
SADD languages Python Redis Docker AWS
```

Duplicate values are ignored.

Complexity

```
O(1)
```

Per element.

---

# SMEMBERS

Returns every member.

Example

```redis
SMEMBERS languages
```

Output

```
1) Python

2) Redis

3) Docker

4) AWS
```

Order is not guaranteed.

Complexity

```
O(N)
```

---

# SISMEMBER

Checks whether a member exists.

Example

```redis
SISMEMBER languages Redis
```

Output

```
(integer) 1
```

If absent:

```
(integer) 0
```

Complexity

```
O(1)
```

Production Uses

- Permission validation
- User roles
- Feature access
- Membership checks

---

# SCARD

Returns the number of members.

Example

```redis
SCARD languages
```

Output

```
(integer) 4
```

Complexity

```
O(1)
```

Useful for:

- Counting users
- Active sessions
- Followers
- Online members

---

# SREM

Removes members.

Example

```redis
SREM languages Docker
```

Output

```
(integer) 1
```

---

# SPOP

Removes and returns a random member.

Example

```redis
SPOP languages
```

Output

```
Python
```

Useful for:

- Lottery systems
- Random task assignment
- Sampling

---

# SRANDMEMBER

Returns a random member without removing it.

Example

```redis
SRANDMEMBER languages
```

Useful for:

- Recommendations
- Random suggestions
- Sampling datasets

---

# SMOVE

Moves a member from one set to another.

Example

```redis
SMOVE

pending

completed

task1
```

Architecture

```
Pending

↓

task1

↓

Completed
```

Useful for workflow management.

---

# SUNION

Returns all unique members from multiple sets.

Example

```redis
SUNION frontend backend
```

Example

```
Frontend

React

Angular

Vue

Backend

Python

Java

Redis
```

Result

```
React

Angular

Vue

Python

Java

Redis
```

Duplicates appear only once.

---

# SINTER

Returns common members.

Example

```redis
SINTER teamA teamB
```

Example

```
Team A

Alice

Bob

Charlie

Team B

Bob

Charlie

David
```

Result

```
Bob

Charlie
```

Useful for:

- Mutual friends
- Shared interests
- Common permissions

---

# SDIFF

Returns members in one set but not another.

Example

```redis
SDIFF active inactive
```

Useful for:

- Permission comparison
- User segmentation
- Data analysis

---

# SUNIONSTORE

Stores the union into another set.

Example

```redis
SUNIONSTORE

all_users

premium_users

free_users
```

---

# SINTERSTORE

Stores the intersection.

Example

```redis
SINTERSTORE

common_users

group1

group2
```

---

# SDIFFSTORE

Stores the difference.

Example

```redis
SDIFFSTORE

eligible_users

registered

blocked
```

---

# SSCAN

Incrementally scans members.

Syntax

```redis
SSCAN key cursor
```

Example

```redis
SSCAN users 0
```

Useful for:

- Large datasets
- Production systems
- Incremental processing

Prefer SSCAN over loading extremely large sets into memory.

---

# Permission System Example

```
User

↓

Roles

↓

Redis Set

↓

Permissions
```

Example

```
admin:permissions

↓

READ

WRITE

DELETE

EXPORT
```

Permission validation

```
SISMEMBER

↓

Has Permission?

↓

Allow / Deny
```

---

# Friend System Example

```
user:100:friends

↓

Alice

Bob

Charlie
```

Mutual friends

```
SINTER

↓

user:100:friends

↓

user:200:friends
```

---

# Tag System Example

```
Article

↓

Redis Set

↓

Python

Redis

Docker
```

Unique tags are automatically maintained.

---

# Recommendation Engine

```
User A Interests

↓

Python

Redis

AWS

User B Interests

↓

Redis

Docker

AWS

↓

SINTER

↓

Redis

AWS
```

---

# Common Production Use Cases

Redis Sets are commonly used for:

- User roles
- RBAC
- API permissions
- Feature flags
- Friend lists
- Followers
- Product categories
- Search filters
- Recommendation engines
- Unique visitor tracking

---

# Common Mistakes

## Assuming Order

Sets are unordered.

Never rely on insertion order.

---

## Using Lists for Unique Data

Bad

```
User

↓

List

↓

Duplicate Entries
```

Better

```
User

↓

Set

↓

Unique Values
```

---

## Loading Huge Sets

Avoid

```redis
SMEMBERS
```

on massive sets.

Use

```redis
SSCAN
```

instead.

---

## Forgetting Set Operations

Many applications manually compare collections.

Redis already provides:

- UNION
- INTERSECTION
- DIFFERENCE

These operations are highly optimized.

---

# Best Practices

- Use Sets whenever uniqueness is required.
- Prefer SSCAN for very large collections.
- Use SINTER for relationship analysis.
- Store identifiers instead of large objects.
- Monitor very large sets.
- Use prefixes for logical grouping.
- Document set naming conventions.

---

# Performance Considerations

| Command | Complexity |
|----------|------------|
| SADD | O(1) |
| SISMEMBER | O(1) |
| SCARD | O(1) |
| SREM | O(1) |
| SPOP | O(1) |
| SRANDMEMBER | O(1) |
| SMOVE | O(1) |
| SMEMBERS | O(N) |
| SSCAN | O(1) per iteration |
| SUNION | O(N) |
| SINTER | O(N) |
| SDIFF | O(N) |

---

# Production Considerations

For enterprise Redis deployments:

- Prefer SSCAN over SMEMBERS for extremely large sets.
- Keep member values reasonably small.
- Store IDs instead of complete objects.
- Use set operations to reduce application-side processing.
- Monitor memory consumption of high-cardinality sets.
- Consider Sorted Sets if ordering or ranking is required.

---

# Summary

Redis Sets provide a highly efficient mechanism for storing unique collections of data. Their support for constant-time membership checks and built-in mathematical operations makes them ideal for implementing permissions, relationships, recommendation systems, and unique collections. By leveraging operations such as `SINTER`, `SUNION`, and `SDIFF`, developers can offload complex set computations to Redis, resulting in faster and more scalable applications.

---

# Key Takeaways

- Redis Sets store **unique, unordered** values.
- `SADD`, `SREM`, and `SISMEMBER` are the core commands for managing set members.
- `SUNION`, `SINTER`, and `SDIFF` enable powerful server-side set operations.
- `SSCAN` is the preferred method for iterating over large sets in production.
- Sets are ideal for permissions, tags, friend lists, recommendation engines, and unique collections.
- Do not rely on element order when using Sets.
- Store lightweight identifiers rather than large objects to optimize memory usage.
```