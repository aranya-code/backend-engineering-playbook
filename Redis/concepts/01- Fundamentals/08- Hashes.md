# Hashes

## Overview

Redis Hashes are one of the most efficient and commonly used data structures for storing objects. A Hash stores data as a collection of **field-value pairs**, making it similar to a row in a relational database or an object in a programming language.

Instead of storing an entire object as a single String, Redis Hashes allow individual attributes to be stored and updated independently. This improves memory efficiency and avoids rewriting the entire object when only a single field changes.

Hashes are widely used in backend applications for storing user profiles, product information, configurations, shopping carts, and metadata.

---

# What is a Redis Hash?

A Redis Hash is a collection of field-value pairs stored under a single key.

```
Key

↓

user:1001

↓

+----------------------+
| name     → Alice     |
| age      → 28        |
| city     → Kolkata   |
| role     → Admin     |
+----------------------+
```

Each field can be accessed or modified independently.

---

# Characteristics of Redis Hashes

Redis Hashes provide several important features.

- Store multiple fields under one key
- Efficient memory usage
- Fast field lookup
- Individual field updates
- Schema-less
- Dynamic structure

Unlike relational databases, Redis does not require predefined columns.

---

# Internal Representation

Conceptually, a Hash looks like this:

```
user:1001

↓

+---------------------------+
| name      Alice           |
| email     alice@test.com  |
| city      Kolkata         |
| age       28              |
+---------------------------+
```

The key identifies the object, while the fields represent its attributes.

---

# Time Complexity

| Operation | Complexity |
|------------|------------|
| Add Field | O(1) |
| Read Field | O(1) |
| Update Field | O(1) |
| Delete Field | O(1) |

Redis Hashes provide constant-time access to individual fields.

---

# Why Use Hashes?

Suppose a user profile is stored as a String.

```
user:1001

↓

{
  "name":"Alice",
  "age":28,
  "city":"Kolkata"
}
```

If only the age changes:

```
28 → 29
```

The entire JSON object must be rewritten.

With a Hash:

```
user:1001

↓

age

↓

29
```

Only the required field changes.

This is both faster and more memory efficient.

---

# User Profiles

One of the most common Redis Hash use cases.

```
user:1001

↓

Name

Email

Phone

City

Role
```

Each field can be updated independently without affecting the others.

---

# Product Information

E-commerce systems frequently store product details.

```
product:500

↓

Name

Price

Stock

Category

Brand
```

Updating the stock does not require rewriting the entire product object.

---

# Shopping Cart Metadata

Hashes are useful for storing cart information.

```
cart:200

↓

User ID

Total Price

Discount

Coupon

Status
```

---

# Configuration Management

Applications often cache configuration values.

```
config

↓

Theme

Language

Timezone

Currency
```

Applications can retrieve only the required configuration field.

---

# Employee Records

Example:

```
employee:15

↓

Name

Department

Salary

Designation
```

Each attribute remains independently accessible.

---

# Session Data

Instead of storing a serialized object, applications can store session fields separately.

```
session:xyz

↓

User ID

Login Time

IP Address

Device
```

---

# Hashes vs Strings

| Feature | String | Hash |
|----------|---------|------|
| Single Value | Yes | No |
| Multiple Fields | No | Yes |
| Partial Update | No | Yes |
| Memory Efficient | Less | More |
| Object Storage | Limited | Excellent |

Hashes are generally a better choice for structured objects.

---

# Hashes vs Relational Database

| Feature | Redis Hash | SQL Table Row |
|----------|------------|---------------|
| Schema | No | Yes |
| Field Update | O(1) | SQL UPDATE |
| Query Language | Redis Commands | SQL |
| Relationships | No | Yes |

Redis Hashes are designed for fast object storage rather than relational querying.

---

# Common Production Use Cases

Redis Hashes are commonly used for:

- User profiles
- Product catalogs
- Shopping carts
- Employee records
- Configuration settings
- Session data
- Customer information
- Metadata storage
- Inventory management
- Cached database rows

---

# When Should You Use Hashes?

Choose Hashes when:

- Data naturally represents an object.
- Individual fields are updated frequently.
- Memory efficiency is important.
- Field-level access is required.

---

# When Should You Use Other Data Types?

| Requirement | Better Choice |
|-------------|---------------|
| Single Cached Value | Strings |
| Ordered Queue | Lists |
| Unique Collection | Sets |
| Rankings | Sorted Sets |
| Event Streaming | Streams |

Selecting the appropriate data structure improves performance and simplifies application design.

---

# Production Considerations

When using Hashes in production:

- Use descriptive field names.
- Group related fields within a single Hash.
- Avoid creating excessively large Hashes.
- Cache frequently accessed objects.
- Monitor memory usage for large datasets.

---

# Best Practices

- Use Hashes to model application objects.
- Store related attributes together.
- Update individual fields instead of replacing entire objects.
- Use consistent key naming conventions.
- Avoid storing deeply nested data structures inside a single Hash.

---

# Summary

Redis Hashes provide an efficient way to store structured objects as field-value pairs. They allow individual fields to be accessed and updated independently, making them ideal for user profiles, product catalogs, configuration settings, session data, and many other backend use cases. Compared to storing serialized objects as Strings, Hashes offer better memory utilization and more efficient updates.

---

# Key Takeaways

- Redis Hashes store multiple field-value pairs under a single key.
- They are ideal for representing structured objects.
- Individual fields can be read or updated independently.
- Most Hash operations execute in **O(1)** time.
- Hashes are more memory efficient than storing serialized objects as Strings.
- Common use cases include user profiles, product information, session data, and configuration storage.
- Hashes are one of the most widely used Redis data structures in modern backend applications.