# Redis CLI

Master the Redis Command Line Interface for development, debugging, administration, and production operations. This section covers everything from basic CLI usage to advanced server administration commands, providing a practical, command-oriented reference for backend engineers.

---

# Objectives

After completing this section, you will be able to:

- Connect securely to Redis instances
- Navigate and use the Redis CLI efficiently
- Work with every Redis data structure from the command line
- Execute transactions and Pub/Sub operations
- Manage key expiration and TTL
- Monitor Redis servers in production
- Configure Redis at runtime
- Troubleshoot common Redis issues
- Use Redis CLI effectively during interviews and production incidents

---

# Learning Path

```text
Redis CLI Basics
        │
        ▼
Key Management
        │
        ▼
Core Data Structures
(Strings → Lists → Sets → Sorted Sets → Hashes)
        │
        ▼
Streams
        │
        ▼
Transactions
        │
        ▼
Pub/Sub
        │
        ▼
Expiration & TTL
        │
        ▼
Server Administration
        │
        ▼
Runtime Configuration
        │
        ▼
CLI Cheat Sheet
```

---

# Quick Navigation

| Chapter | Topic |
|----------|-------|
| [01 - Redis CLI Basics](./01-%20Redis%20CLI%20Basics.md) | Learn how to connect to Redis, use `redis-cli`, authentication, TLS, interactive mode, scripting, and essential CLI workflows. |
| [02 - Keys Commands](./02-%20Keys%20Commands.md) | Manage Redis keys using commands like `DEL`, `UNLINK`, `SCAN`, `TYPE`, `RENAME`, `COPY`, and memory inspection. |
| [03 - String Commands](./03-%20String%20Commands.md) | Work with Redis Strings including counters, caching, atomic operations, and string manipulation commands. |
| [04 - List Commands](./04-%20List%20Commands.md) | Learn List operations for queues, stacks, task processing, and blocking operations. |
| [05 - Set Commands](./05-%20Set%20Commands.md) | Store unique collections and perform membership checks, unions, intersections, and differences. |
| [06 - Sorted Set Commands](./06-%20Sorted%20Set%20Commands.md) | Build leaderboards, ranking systems, priority queues, and scheduling systems using Sorted Sets. |
| [07 - Hash Commands](./07-%20Hash%20Commands.md) | Store structured objects efficiently using Redis Hashes for users, products, sessions, and configurations. |
| [08 - Stream Commands](./08-%20Stream%20Commands.md) | Learn Redis Streams for event-driven architectures, message processing, and Consumer Groups. |
| [09 - Transaction Commands](./09-%20Transaction%20Commands.md) | Execute atomic operations using `MULTI`, `EXEC`, `WATCH`, and optimistic locking. |
| [10 - Pub-Sub Commands](./10-%20Pub-Sub%20Commands.md) | Implement real-time messaging, notifications, and event broadcasting with Redis Pub/Sub. |
| [11 - Expiration & TTL Commands](./11-%20Expiration%20%26%20TTL%20Commands.md) | Manage key lifecycles using TTLs, expiration policies, and automatic cleanup strategies. |
| [12 - Server Commands](./12-%20Server%20Commands.md) | Monitor server health, inspect clients, analyze memory, investigate latency, and manage persistence. |
| [13 - Configuration Commands](./13-%20Configuration%20Commands.md) | Configure Redis runtime settings, memory limits, security, persistence, ACLs, and operational tuning. |
| [14 - Redis CLI Cheat Sheet](./14-%20Redis%20CLI%20Cheat%20Sheet.md) | A concise command reference for development, production support, and interview preparation. |

---

# Module Breakdown

## 01. Redis CLI Basics

Learn how to:

- Install and use `redis-cli`
- Connect to local and remote servers
- Authenticate securely
- Work with TLS
- Execute commands interactively and non-interactively
- Pipe commands from files
- Use Redis CLI for automation

---

## 02. Key Management

Master commands for:

- Creating and deleting keys
- Renaming keys
- Copying keys
- Scanning large datasets
- Memory inspection
- Safe production practices

---

## 03. Redis Data Structures

This module covers the five most commonly used Redis data structures:

### Strings

- Caching
- Counters
- Session storage
- Atomic operations

### Lists

- Queues
- Stacks
- Job processing
- Messaging

### Sets

- Permissions
- Tags
- Unique collections
- Friend relationships

### Sorted Sets

- Leaderboards
- Rankings
- Scheduling
- Rate limiting

### Hashes

- User profiles
- Products
- Configuration
- Sessions

---

## 04. Streams

Learn modern event processing using:

- Stream creation
- Consumer Groups
- Acknowledgements
- Pending messages
- Event replay
- Reliable messaging

---

## 05. Transactions

Understand:

- MULTI
- EXEC
- WATCH
- Optimistic locking
- Atomic execution
- Production transaction patterns

---

## 06. Publish / Subscribe

Build real-time applications using:

- Notifications
- Live chat
- WebSocket broadcasting
- Cache invalidation
- Service communication

---

## 07. Key Expiration

Implement:

- Session expiration
- OTP management
- API rate limiting
- Distributed locks
- Temporary caches
- Sliding expiration

---

## 08. Server Administration

Monitor Redis using:

- INFO
- MEMORY
- SLOWLOG
- CLIENT
- LATENCY
- Persistence commands
- Health checks

---

## 09. Runtime Configuration

Learn to:

- Tune memory
- Configure persistence
- Manage ACLs
- Change runtime settings
- Optimize production environments

---

## 10. CLI Cheat Sheet

A practical quick reference containing:

- Frequently used commands
- Complexity reference
- Production best practices
- Dangerous commands
- Interview revision notes

---

# Skills You'll Gain

After completing this module, you'll be able to:

- Confidently use Redis CLI for daily development
- Debug production Redis issues
- Monitor Redis performance
- Inspect and optimize memory usage
- Configure Redis servers securely
- Work with every Redis data structure
- Build messaging and event-driven systems
- Troubleshoot Redis during incidents
- Perform operational maintenance
- Answer Redis CLI interview questions confidently

---

# Best Practices Covered

Throughout this section, you'll learn industry-standard practices such as:

- Prefer `SCAN` over `KEYS`
- Use `UNLINK` instead of `DEL` for large objects
- Configure `maxmemory` appropriately
- Monitor `SLOWLOG` regularly
- Use `SET EX` for temporary data
- Protect Redis using ACLs and TLS
- Prefer `BGSAVE` over `SAVE`
- Keep Redis values lightweight
- Use Consumer Groups for reliable message processing
- Automate configuration management

---

# Prerequisites

Before starting this module, you should be familiar with:

- Basic Redis concepts
- Redis installation
- Common Redis data structures
- Command-line basics

---


