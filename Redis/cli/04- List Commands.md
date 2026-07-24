# List Commands

## Overview

Redis Lists are one of the core data structures provided by Redis. A List is an **ordered collection of elements** where items can be inserted or removed from both the beginning (head) and the end (tail). Internally, Redis implements Lists using **QuickLists** (a combination of linked lists and listpacks), making them highly efficient for queue-like workloads.

Lists are widely used in backend systems for:

- Job queues
- Task scheduling
- Message buffering
- Activity feeds
- Notification systems
- Event processing
- Chat message history
- Recently viewed items
- Undo/Redo functionality

Unlike Sets, Lists preserve insertion order and allow duplicate values.

---

# Understanding Redis Lists

A Redis List is an ordered sequence of elements.

```
Head                                    Tail

+------+------+------+------+------+
| Job1 | Job2 | Job3 | Job4 | Job5 |
+------+------+------+------+------+
```

Elements can be added or removed from either end.

```
LPUSH  ← Head

RPUSH  → Tail
```

---

# Common List Commands

| Command | Description |
|----------|-------------|
| LPUSH | Insert at beginning |
| RPUSH | Insert at end |
| LPOP | Remove first element |
| RPOP | Remove last element |
| LLEN | Get list length |
| LRANGE | Retrieve elements |
| LINDEX | Get element by index |
| LSET | Replace element |
| LINSERT | Insert before/after element |
| LREM | Remove matching elements |
| LTRIM | Trim list |
| LMOVE | Move element between lists |
| BLPOP | Blocking pop from left |
| BRPOP | Blocking pop from right |
| BLMOVE | Blocking move between lists |

---

# LPUSH

Adds one or more elements to the beginning of a list.

Syntax

```redis
LPUSH key value
```

Example

```redis
LPUSH jobs job1
```

Result

```
(integer) 1
```

Adding multiple elements:

```redis
LPUSH jobs job3 job2 job1
```

Result:

```
job1
job2
job3
```

Complexity

```
O(1)
```

---

# RPUSH

Adds elements to the end of a list.

```redis
RPUSH jobs job4
```

Result

```
job1

↓

job2

↓

job3

↓

job4
```

Useful for:

- FIFO queues
- Message processing
- Event logging

Complexity

```
O(1)
```

---

# LPOP

Removes and returns the first element.

```redis
LPOP jobs
```

Output

```
job1
```

Queue becomes

```
job2

↓

job3

↓

job4
```

---

# RPOP

Removes the last element.

```redis
RPOP jobs
```

Output

```
job4
```

Useful for implementing stacks.

---

# LLEN

Returns the number of elements.

```redis
LLEN jobs
```

Output

```
(integer) 3
```

Complexity

```
O(1)
```

---

# LRANGE

Returns elements within a range.

Syntax

```redis
LRANGE key start stop
```

Example

```redis
LRANGE jobs 0 -1
```

Output

```
1) job1

2) job2

3) job3

4) job4
```

Useful ranges

```
0 -1

Entire list
```

```
0 9

First ten items
```

```
-5 -1

Last five items
```

Complexity

```
O(S)
```

Where **S** is the number of returned elements.

---

# LINDEX

Returns an element by index.

```redis
LINDEX jobs 2
```

Output

```
job3
```

Useful for reading without modifying the list.

---

# LSET

Replaces an element at a specific index.

```redis
LSET jobs 1 job_new
```

Result

```
job1

↓

job_new

↓

job3
```

---

# LINSERT

Insert relative to another element.

Example

```redis
LINSERT jobs BEFORE job3 job2.5
```

Result

```
job1

↓

job2

↓

job2.5

↓

job3
```

---

# LREM

Removes matching elements.

Syntax

```redis
LREM key count value
```

Example

```redis
LREM jobs 1 job2
```

Removes the first occurrence.

Useful for

- Removing cancelled jobs
- Deleting duplicate entries
- Queue cleanup

---

# LTRIM

Keeps only a specified range.

Example

```redis
LTRIM logs 0 99
```

Only the newest 100 entries remain.

Common use case:

```
Activity Feed

↓

Keep Last 100 Items
```

---

# LMOVE

Moves an element between two lists.

Example

```redis
LMOVE

pending

processing

LEFT

RIGHT
```

Architecture

```
Pending Queue

↓

Worker

↓

Processing Queue
```

Useful for reliable job processing.

---

# BLPOP

Blocking version of LPOP.

Example

```redis
BLPOP jobs 30
```

Behavior

```
Worker

↓

Wait

↓

Job Arrives

↓

Return Job
```

Timeout

```
30 seconds
```

Very common in worker systems.

---

# BRPOP

Blocking version of RPOP.

Useful for stack-based processing.

---

# BLMOVE

Blocking version of LMOVE.

Ideal for reliable message queues.

```
Producer

↓

Queue

↓

Worker Waits

↓

Process Job
```

---

# Queue Architecture

Redis Lists are widely used as queues.

```
Producer

↓

LPUSH

↓

Redis List

↓

BRPOP

↓

Consumer
```

This architecture is lightweight and highly performant.

---

# Stack Architecture

Lists can also behave as stacks.

```
LPUSH

↓

Stack

↓

LPOP
```

Last In

↓

First Out

(LIFO)

---

# Activity Feed Example

```
User Posts

↓

RPUSH

↓

Timeline

↓

LRANGE

↓

Display Feed
```

Lists preserve insertion order, making them ideal for timelines.

---

# Chat History

```
User Sends Message

↓

RPUSH chat:room:1

↓

Message Stored

↓

LRANGE

↓

Load Conversation
```

---

# Task Queue Example

```
Application

↓

LPUSH task

↓

Redis Queue

↓

Worker

↓

BLPOP

↓

Execute Task
```

A common architecture before introducing dedicated message brokers.

---

# Common Production Use Cases

Redis Lists are commonly used for:

- Background job queues
- Notification systems
- Activity feeds
- Chat history
- Recently viewed products
- Undo history
- Event buffering
- Batch processing
- Logging pipelines

---

# Common Mistakes

## Using LRANGE on Very Large Lists

```
LRANGE 0 -1
```

On a list containing millions of elements can return enormous amounts of data.

Prefer pagination.

---

## Not Trimming Activity Feeds

Without trimming:

```
Timeline

↓

Millions of Entries
```

Memory usage grows indefinitely.

Use

```redis
LTRIM
```

---

## Polling Instead of Blocking

Avoid

```
Loop

↓

LPOP

↓

Sleep

↓

Repeat
```

Instead use

```
BLPOP
```

Workers remain idle until work arrives.

---

## Using Lists for Random Access

Lists excel at sequential operations.

For random lookups, consider:

- Hashes
- Sorted Sets
- RedisJSON

---

# Best Practices

- Use Lists for ordered data.
- Prefer blocking commands for worker queues.
- Regularly trim large lists.
- Keep queue items reasonably small.
- Monitor queue length.
- Avoid extremely large LRANGE operations.
- Use LMOVE for reliable queue processing.
- Consider Redis Streams for advanced messaging requirements.

---

# Performance Considerations

| Command | Complexity |
|----------|------------|
| LPUSH | O(1) |
| RPUSH | O(1) |
| LPOP | O(1) |
| RPOP | O(1) |
| LLEN | O(1) |
| LRANGE | O(S) |
| LINDEX | O(N) |
| LSET | O(N) |
| LREM | O(N) |
| LTRIM | O(N) |
| LMOVE | O(1) |
| BLPOP | O(1) (until blocking) |

---

# Production Considerations

For production Redis deployments:

- Monitor queue growth to prevent memory exhaustion.
- Use blocking operations (`BLPOP`, `BRPOP`) instead of polling.
- Implement dead-letter queues for failed jobs.
- Trim activity feeds periodically.
- Avoid storing very large payloads directly in Lists; instead, store identifiers and retrieve associated data separately.
- For high-throughput messaging with acknowledgements and consumer groups, consider Redis Streams instead of Lists.

---

# Summary

Redis Lists provide a simple yet powerful mechanism for managing ordered collections of data. Their ability to efficiently insert and remove elements from both ends makes them ideal for implementing queues, stacks, timelines, and message buffers. Combined with blocking operations like `BLPOP` and reliable movement commands such as `LMOVE`, Lists form the foundation of many production-grade backend workflows.

---

# Key Takeaways

- Redis Lists are ordered collections that preserve insertion order.
- `LPUSH` and `RPUSH` add elements to the head and tail respectively.
- `LPOP` and `RPOP` remove elements efficiently from either end.
- `BLPOP` and `BRPOP` enable efficient worker queues without polling.
- `LTRIM` is essential for controlling memory usage in feeds and logs.
- `LMOVE` supports reliable queue processing between multiple lists.
- Lists are ideal for queues, stacks, timelines, and chat histories.
- For advanced messaging patterns, Redis Streams are often a better choice.