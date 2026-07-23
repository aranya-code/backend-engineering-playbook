# Redis Architecture

## Overview

Redis follows a simple yet highly efficient architecture that allows it to process millions of operations per second with very low latency. Unlike traditional databases that rely on disk-based storage engines, Redis keeps its working dataset in memory and processes commands using a single-threaded event loop.

The architecture is designed to minimize overhead, reduce locking, and maximize throughput, making Redis one of the fastest data stores available.

At its core, Redis consists of:

- Redis Client
- Redis Server
- In-Memory Data Store
- Persistence Layer
- Replication Layer
- High Availability Components (Sentinel/Cluster)

---

# High-Level Architecture

```
                  Client Applications
        (Django, FastAPI, Node.js, Java)

                     │
                     │ TCP Connection
                     ▼

              +-------------------+
              |   Redis Server    |
              +-------------------+
                      │
      ┌───────────────┼────────────────┐
      │               │                │
      ▼               ▼                ▼
 Command Parser   Memory Engine   Persistence
                                      │
                         ┌────────────┴────────────┐
                         ▼                         ▼
                    RDB Snapshot               AOF Log

```

The Redis server receives requests from clients, executes commands in memory, and optionally persists data to disk.

---

# Components of Redis Architecture

## 1. Redis Client

A Redis client is any application that communicates with the Redis server.

Examples:

- Django
- FastAPI
- Flask
- Spring Boot
- Node.js
- Go Applications

Example using Python:

```python
import redis

r = redis.Redis(host="localhost", port=6379)

r.set("name", "Aranya")

print(r.get("name"))
```

The client sends commands such as:

```redis
SET
GET
DEL
HSET
LPUSH
```

over a TCP connection.

---

## 2. Redis Server

The Redis Server is responsible for:

- Receiving requests
- Parsing commands
- Executing commands
- Returning responses

Example:

```
Client
   │
GET user:100
   │
   ▼
Redis Server
   │
Search Memory
   │
Return Value
```

Since everything happens in memory, execution is extremely fast.

---

## 3. In-Memory Data Store

This is the heart of Redis.

Instead of writing every request to disk:

```
Disk
```

Redis stores objects directly in RAM.

```
RAM

user:1
user:2
user:3
product:1
cart:101
session:xyz
```

Accessing RAM is significantly faster than accessing disk.

Approximate latency comparison:

| Storage | Latency |
|----------|---------|
| RAM | ~100 ns |
| SSD | ~100 µs |
| HDD | ~10 ms |

This difference explains why Redis is so fast.

---

# Request Flow

Suppose a Django application requests a user profile.

```
Client
   │
GET user:101
   ▼

Redis Server

   │
Find key in memory

   ▼

Return value
```

No SQL query is executed.

No disk access is required.

Everything occurs in RAM.

---

# Client-Server Communication

Redis communicates over TCP using the Redis Serialization Protocol (RESP).

Flow:

```
Client

SET user:1 "Alice"

        │

        ▼

TCP Socket

        │

        ▼

Redis Server

        │

OK
```

RESP is lightweight and optimized for high-speed communication.

---

# Command Execution Flow

When Redis receives a command, it follows several steps.

```
Receive Request

       │

Parse Command

       │

Validate Command

       │

Locate Key

       │

Execute Operation

       │

Return Result
```

Example:

```
GET user:100
```

Execution:

```
Receive GET

↓

Locate user:100

↓

Read Value

↓

Return JSON
```

This process typically completes in microseconds.

---

# Why Redis is Single-Threaded

One of the most commonly asked interview questions is:

> Why is Redis single-threaded?

Redis executes commands using a single main thread.

Advantages:

- No thread synchronization
- No locking overhead
- No deadlocks
- Simpler architecture
- Predictable performance

Instead of multiple worker threads competing for shared memory, Redis processes requests sequentially at extremely high speed.

```
Request 1

↓

Execute

↓

Request 2

↓

Execute

↓

Request 3

↓

Execute
```

This design works because memory access is already extremely fast.

> **Note:** Modern Redis versions use additional threads for background tasks (such as networking and persistence), but command execution remains single-threaded.

---

# Event Loop

Redis uses an event-driven architecture.

```
           Event Loop

        Wait for Request

               │

               ▼

Receive Command

               │

               ▼

Execute

               │

               ▼

Return Response

               │

               ▼

Wait Again
```

The server continuously listens for new client requests without creating a new thread for each connection.

This makes Redis highly efficient under heavy workloads.

---

# Persistence Layer

Although Redis primarily stores data in memory, it supports optional persistence to disk.

Two mechanisms are available:

## RDB

Creates snapshots periodically.

```
Memory

↓

Snapshot

↓

dump.rdb
```

Advantages:

- Smaller files
- Faster recovery
- Lower runtime overhead

---

## AOF

Logs every write command.

```
SET

↓

Append

↓

appendonly.aof
```

Advantages:

- Better durability
- Minimal data loss

---

# Replication Layer

Redis supports Master-Replica replication.

```
             Master

          /     |     \

 Replica   Replica   Replica
```

The master handles write operations.

Replicas receive updates automatically and typically serve read requests, improving scalability and availability.

---

# High Availability

Production deployments often include Sentinel or Redis Cluster.

### Sentinel

```
Master

│

├── Replica

├── Replica

└── Sentinel
```

Responsibilities:

- Monitor nodes
- Detect failures
- Promote replicas
- Automatic failover

---

### Redis Cluster

```
Shard 1

Shard 2

Shard 3

Shard 4
```

Each shard stores only a portion of the data, enabling horizontal scaling and distributing load across multiple servers.

---

# Memory Management

Redis allocates memory dynamically.

```
Memory

│

├── Strings

├── Lists

├── Sets

├── Hashes

├── Streams

└── Metadata
```

When memory limits are reached, Redis uses configured eviction policies such as:

- LRU
- LFU
- TTL
- Random

We will study these in detail later.

---

# Typical Production Architecture

```
                  Users
                     │
                     ▼
             Load Balancer
                     │
        ┌────────────┴────────────┐
        ▼                         ▼
    Django API              FastAPI API
        │                         │
        └────────────┬────────────┘
                     ▼
                Redis Cluster
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
     PostgreSQL            Celery Workers
```

Redis acts as the high-speed data access layer between applications and the primary database.

---

# Advantages of Redis Architecture

- Extremely low latency
- High throughput
- Simple architecture
- Minimal locking
- Excellent scalability
- Supports replication
- Supports clustering
- High availability
- Efficient memory utilization

---

# Limitations

Despite its strengths, Redis architecture has some trade-offs:

- Entire working dataset should fit in memory.
- Large RAM requirements can increase infrastructure costs.
- Single-threaded command execution can become a bottleneck for CPU-intensive workloads.
- Improper persistence configuration may lead to data loss after failures.

---

# Summary

Redis achieves exceptional performance through a simple yet powerful architecture centered around in-memory storage, a single-threaded execution model, and an event-driven design. By eliminating disk I/O from the critical execution path and providing optional persistence, replication, and clustering, Redis serves as an ideal caching and data access layer for modern applications.

---

# Key Takeaways

- Redis follows a client-server architecture.
- Data is primarily stored in RAM for ultra-fast access.
- Clients communicate with Redis over TCP using RESP.
- Commands are executed by a single-threaded event loop.
- Persistence is provided through RDB snapshots and AOF logs.
- Replication enables read scaling and fault tolerance.
- Sentinel provides automatic failover.
- Redis Cluster enables horizontal scaling through sharding.
- Redis architecture is optimized for low latency, high throughput, and production scalability.