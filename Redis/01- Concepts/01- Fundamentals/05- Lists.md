# Lists

## Overview

Redis Lists are ordered collections of elements that preserve insertion order. Unlike Strings, which store a single value, Lists can hold multiple values under a single key, making them ideal for sequential data.

Internally, Redis optimizes Lists for fast insertion and removal at both ends, making them well-suited for implementing queues, stacks, task processing systems, messaging workflows, and activity feeds.

Lists are one of the most commonly used Redis data structures in backend applications because many real-world problems naturally involve ordered sequences of items.

---

# What is a Redis List?

A Redis List is an ordered collection of elements associated with a single key.

```
tasks

↓

┌────────┬────────┬────────┬────────┐
│ Task 1 │ Task 2 │ Task 3 │ Task 4 │
└────────┴────────┴────────┴────────┘
```

Each element maintains its position within the list.

Unlike Sets, Lists allow:

- Duplicate values
- Ordered elements
- Fast insertion at both ends

---

# Characteristics of Redis Lists

Redis Lists provide several important features.

- Ordered collection
- Duplicate values allowed
- Dynamic size
- Fast insertion
- Fast removal
- Suitable for queue-based systems

Lists automatically grow and shrink as elements are added or removed.

---

# Internal Representation

Conceptually, a Redis List looks like:

```
orders

↓

Head

↓

┌──────┬──────┬──────┬──────┐
│1001 │1002 │1003 │1004 │
└──────┴──────┴──────┴──────┘

↓

Tail
```

Elements remain ordered from the head to the tail.

---

# Time Complexity

| Operation | Complexity |
|------------|------------|
| Insert at Head | O(1) |
| Insert at Tail | O(1) |
| Remove from Head | O(1) |
| Remove from Tail | O(1) |
| Access by Index | O(n) |

Because Redis is optimized for operations at the beginning and end of the list, Lists are excellent for queue-like workloads.

---

# Queue Implementation

One of the most common Redis List use cases is implementing a queue.

```
Incoming Jobs

↓

┌──────────────┐
│ Redis Queue  │
└──────────────┘

↓

Worker
```

Example jobs:

```
Email

↓

Invoice

↓

Notification

↓

Report
```

Workers continuously consume tasks from the queue.

---

# Background Task Processing

Many backend systems use Redis Lists as task queues.

Example:

```
User Uploads Image

↓

Task Added

↓

Redis List

↓

Background Worker

↓

Resize Image

↓

Upload to Storage
```

This prevents long-running operations from blocking user requests.

---

# Message Queue

Lists can also function as simple message queues.

```
Producer

↓

Redis List

↓

Consumer
```

Messages are processed in the order they are received.

This pattern is commonly used in:

- Email systems
- Notification services
- Logging pipelines
- Job schedulers

---

# Activity Feed

Applications frequently maintain recent user activities.

```
Recent Orders

↓

Order A

Order B

Order C

Order D
```

New activities are added while older activities are removed as needed.

---

# Undo History

Editors often maintain recent operations.

```
Undo History

↓

Edit 1

↓

Edit 2

↓

Edit 3
```

Since Lists preserve order, they naturally support undo and redo functionality.

---

# Playlist Management

Streaming applications frequently store playlists.

```
Playlist

↓

Song 1

↓

Song 2

↓

Song 3

↓

Song 4
```

Order is preserved exactly as intended.

---

# Shopping Cart

A shopping cart can be modeled as a List.

```
Cart

↓

Laptop

↓

Mouse

↓

Keyboard
```

Although Redis Hashes are often better for storing product details, Lists can represent the sequence of selected items.

---

# Lists vs Strings

| Feature | String | List |
|----------|---------|------|
| Single Value | Yes | No |
| Multiple Values | No | Yes |
| Ordered | N/A | Yes |
| Duplicate Values | N/A | Yes |
| Queue Support | No | Yes |

Strings store one value, whereas Lists store multiple ordered values.

---

# Lists vs Sets

| Feature | List | Set |
|----------|------|-----|
| Ordered | Yes | No |
| Duplicate Values | Yes | No |
| Position Matters | Yes | No |
| Queue Support | Excellent | Poor |

Choose Lists when element order is important.

---

# Common Production Use Cases

Redis Lists are widely used for:

- Background job queues
- Task scheduling
- Message queues
- Notification systems
- Recent search history
- Activity feeds
- Playlist management
- Order processing
- Undo history
- Event buffering

---

# When Should You Use Lists?

Choose Lists when:

- Order matters.
- Items should be processed sequentially.
- Duplicate values are acceptable.
- Queue or stack behavior is required.
- Items are frequently added or removed from either end.

---

# When Should You Use Other Data Types?

| Requirement | Better Choice |
|-------------|---------------|
| Unique Values | Sets |
| Rankings | Sorted Sets |
| User Profiles | Hashes |
| Event Streaming | Streams |
| Simple Cache | Strings |

Selecting the appropriate Redis data structure simplifies application design and improves performance.

---

# Production Considerations

When using Lists in production:

- Avoid extremely large lists.
- Periodically remove stale entries.
- Use Lists for queue-like workloads.
- Monitor memory usage.
- Consider Streams for more advanced messaging requirements.
- Design consumers to handle failures gracefully.

---

# Best Practices

- Use Lists for ordered collections.
- Keep individual list sizes manageable.
- Use descriptive key names.
- Remove processed items promptly.
- Choose Streams instead of Lists when message acknowledgments or consumer groups are required.

---

# Summary

Redis Lists are ordered collections optimized for high-performance insertion and removal operations at both ends. They are commonly used to implement queues, stacks, task processing systems, activity feeds, and messaging workflows. Their simplicity and efficiency make them one of the most practical Redis data structures for backend applications.

---

# Key Takeaways

- Redis Lists store ordered collections of elements.
- Lists preserve insertion order and allow duplicate values.
- Insertions and removals at the head or tail execute in **O(1)** time.
- Lists are ideal for queues, stacks, task processing, and activity feeds.
- Order is maintained, making Lists suitable for sequential workflows.
- Use Lists when processing items in order; choose other data structures when uniqueness, ranking, or field-based access is required.