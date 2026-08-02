# Sets

## Overview

Redis Sets are unordered collections of unique values. Unlike Lists, Sets do not preserve insertion order, and unlike Strings, they can store multiple values under a single key. Their defining characteristic is that duplicate elements are automatically eliminated.

Sets are optimized for operations involving uniqueness, such as membership checks, finding common elements between collections, and performing mathematical set operations like unions, intersections, and differences.

Because of these capabilities, Redis Sets are widely used for access control, tagging systems, recommendation engines, online user tracking, and social network relationships.

---

# What is a Redis Set?

A Redis Set is an unordered collection of unique elements.

```
users:online

↓

{
    Alice,
    Bob,
    Charlie,
    David
}
```

Each element appears only once.

If an application attempts to insert a duplicate value, Redis ignores it automatically.

---

# Characteristics of Redis Sets

Redis Sets provide several important characteristics.

- Unordered collection
- Unique values only
- Automatic duplicate removal
- Fast membership lookup
- Efficient mathematical set operations
- Dynamic size

Sets automatically grow or shrink as elements are added or removed.

---

# Internal Representation

Conceptually, a Redis Set looks like:

```
technologies

↓

+-----------+
| Python    |
| Django    |
| FastAPI   |
| Redis     |
| Docker    |
+-----------+
```

Notice that there is **no concept of position or index**.

---

# Time Complexity

| Operation | Complexity |
|------------|------------|
| Add Element | O(1) |
| Remove Element | O(1) |
| Membership Check | O(1) |
| Union | O(N) |
| Intersection | O(N) |
| Difference | O(N) |

Membership checks are extremely efficient, making Sets suitable for high-performance backend systems.

---

# Why Use Sets?

Suppose an application stores users who have liked a post.

Without a Set:

```
Alice

Bob

Alice

Charlie
```

Duplicates appear.

Using a Set:

```
Alice

Bob

Charlie
```

Redis automatically removes duplicate entries.

---

# Online User Tracking

A common production use case is tracking online users.

```
online_users

↓

Alice

Bob

Charlie

David
```

Checking whether a user is online becomes extremely fast.

---

# User Roles

Applications often store roles assigned to a user.

```
user:101:roles

↓

Admin

Editor

Reviewer
```

Duplicate roles are impossible.

---

# Product Tags

E-commerce systems commonly associate products with tags.

```
product:100

↓

Electronics

Laptop

Gaming

RGB
```

Each tag appears only once.

---

# Permission Management

Backend applications frequently maintain user permissions.

```
permissions

↓

Read

Write

Delete

Export
```

Permission lookup becomes very efficient.

---

# Friend Lists

Social media platforms frequently maintain user relationships.

```
friends:alice

↓

Bob

Charlie

David
```

Since friendships should not contain duplicates, Sets are an excellent choice.

---

# Recommendation Systems

Recommendation engines often compare common interests.

```
User A

↓

Python

Redis

Docker

Kubernetes
```

```
User B

↓

Python

Redis

AWS

FastAPI
```

Redis can efficiently determine the shared interests between users.

---

# Set Operations

Redis supports several mathematical operations.

## Union

Combines all unique elements.

```
Backend Team

↓

Python

Redis

Docker
```

```
DevOps Team

↓

Docker

AWS

Terraform
```

Union:

```
Python

Redis

Docker

AWS

Terraform
```

---

## Intersection

Returns only common elements.

```
Backend

↓

Python

Redis

Docker
```

```
DevOps

↓

Docker

AWS

Redis
```

Intersection:

```
Redis

Docker
```

This is useful for:

- Mutual friends
- Shared permissions
- Common skills
- Shared interests

---

## Difference

Returns elements that exist in one Set but not another.

```
Backend

↓

Python

Redis

Docker
```

```
DevOps

↓

Docker
```

Difference:

```
Python

Redis
```

---

# Sets vs Lists

| Feature | Set | List |
|----------|------|------|
| Ordered | No | Yes |
| Duplicate Values | No | Yes |
| Index Access | No | Yes |
| Membership Lookup | Excellent | Slower |
| Queue Support | No | Yes |

Choose Sets when uniqueness is more important than ordering.

---

# Sets vs Sorted Sets

| Feature | Set | Sorted Set |
|----------|-----|------------|
| Ordering | None | Sorted |
| Score | No | Yes |
| Ranking | No | Yes |
| Leaderboards | No | Yes |

Sorted Sets should be used when ranking or ordering is required.

---

# Common Production Use Cases

Redis Sets are widely used for:

- Online user tracking
- Role management
- Permission systems
- Product tagging
- Social media friendships
- Recommendation engines
- Unique visitors
- API scopes
- Feature flags
- Duplicate detection

---

# When Should You Use Sets?

Use Sets when:

- Duplicate values are not allowed.
- Fast membership checks are required.
- Mathematical set operations are useful.
- Order does not matter.
- Unique relationships must be maintained.

---

# When Should You Use Other Data Types?

| Requirement | Better Choice |
|-------------|---------------|
| Ordered Data | Lists |
| Rankings | Sorted Sets |
| User Profiles | Hashes |
| Event Streams | Streams |
| Single Cached Value | Strings |

Selecting the appropriate data structure improves both performance and maintainability.

---

# Production Considerations

When using Sets in production:

- Use meaningful key names.
- Avoid storing excessively large Sets without monitoring memory usage.
- Take advantage of set operations instead of implementing them in application code.
- Periodically remove obsolete members.
- Monitor memory consumption for high-cardinality Sets.

---

# Best Practices

- Use Sets whenever uniqueness is required.
- Prefer Sets over Lists when duplicate values are not acceptable.
- Use intersections for recommendation systems and mutual relationship calculations.
- Keep Set members concise to reduce memory usage.
- Organize related Sets using consistent key naming conventions.

---

# Summary

Redis Sets are unordered collections of unique values that provide efficient membership checks and powerful mathematical set operations. They are commonly used in backend systems for managing permissions, online users, product tags, recommendations, and social relationships. Their ability to guarantee uniqueness while maintaining high performance makes them one of Redis's most versatile data structures.

---

# Key Takeaways

- Redis Sets store unordered collections of unique elements.
- Duplicate values are automatically eliminated.
- Membership checks execute in **O(1)** time.
- Sets support union, intersection, and difference operations.
- They are ideal for permissions, tagging, online users, recommendations, and social relationships.
- Choose Sets when uniqueness is required and ordering is not important.
- Sets are one of the most powerful Redis data structures for backend application design.