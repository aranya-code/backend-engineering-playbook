# 🗄️ AWS Database Notes

This folder contains structured notes on AWS database and caching services.

The notes are written for:
- Interview preparation
- Real-world architecture understanding
- Quick revision
- Backend & DevOps learning
- AWS certification preparation

---

# 📂 Folder Structure

```text
Databases/
│
├── RDS/
│   ├── RDS Overview.md
│   ├── RDS Read Replicas.md
│   ├── RDS Multi AZ.md
│   ├── RDS Proxy.md
│   ├── RDS Security.md
│   ├── RDS Storage Auto Scaling.md
│   ├── Single AZ to Multi AZ.md
│   └── Quick Revision Notes.md
│
├── Aurora/
│   ├── Aurora Overview.md
│   ├── Aurora Security.md
│   └── Aurora vs RDS.md
│
├── ElastiCache/
│   ├── ElastiCache Overview.md
│   ├── Caching Strategies.md
│   ├── DB Cache Architecture.md
│   ├── Cache Aside.md
│   ├── Write Through.md
│   ├── TTL.md
│   └── Quick Revision Notes.md
│
├── MemoryDB/
│   ├── MemoryDB for Redis.md
│   └── MemoryDB vs ElastiCache.md
│
└── README.md
```

---

# 🛢️ Amazon RDS

## Topics Covered
- RDS basics
- Managed database concepts
- Read replicas
- Multi-AZ deployments
- RDS Proxy
- Storage auto scaling
- Security & encryption
- High availability

---

## Important Concepts

### Multi-AZ
Used for:
- High availability
- Disaster recovery

Uses:
- Synchronous replication

---

### Read Replicas
Used for:
- Read scaling
- Reporting workloads
- Analytics

Uses:
- Asynchronous replication

---

### RDS Proxy
Helps:
- Connection pooling
- Lambda scalability
- Reducing DB stress

---

# ⚡ Amazon Aurora

Aurora is AWS’s cloud-optimized relational database.

## Benefits
- Higher performance
- Better scalability
- Faster failover
- Better replication

---

## Common Interview Topic

### Aurora vs Standard RDS

Aurora provides:
- Better performance
- Distributed storage
- Faster replication
- Better failover handling

---

# 🚀 Amazon ElastiCache

Fully managed in-memory caching service.

Supports:
- Redis
- Memcached

---

## Main Benefits

- Ultra-low latency
- Reduced database load
- Faster applications
- Better scalability

---

# 🧠 Caching Strategies

## Cache Aside (Lazy Loading)

Application:
1. Checks cache
2. Cache miss → DB
3. Stores result in cache

Most common strategy.

---

## Write Through

Writes happen to:
- Cache
- Database

at the same time.

---

## TTL (Time To Live)

Defines:
- How long cache data remains valid

---

# 💾 Amazon MemoryDB for Redis

Durable Redis-compatible in-memory database.

Unlike ElastiCache:
- Strong durability is a primary focus

Useful for:
- Real-time applications
- Gaming
- Financial systems

---

# 🎯 Interview Focus Areas

## Very Important Topics

### Multi-AZ vs Read Replica
Most commonly asked RDS interview topic.

---

### Redis vs Memcached

| Redis | Memcached |
|---|---|
| Persistent | Non-persistent |
| Rich data structures | Simple key-value |
| Replication support | Limited features |

---

### RDS vs DB on EC2

RDS advantages:
- Managed backups
- Monitoring
- Automatic patching
- High availability
- Easier scaling

---

# 🧠 Real-World Architecture Thinking

Typical production setup:

```text
Application
     ↓
ElastiCache (Redis)
     ↓
Amazon RDS Multi-AZ
     ↓
Read Replicas
```

This architecture provides:
- Faster reads
- Lower DB load
- High availability
- Better scalability

---

# 📝 Notes Philosophy

These notes focus on:
- Small definitions
- Interview-ready explanations
- Real-world examples
- Architecture thinking
- Practical AWS usage

---

# 📌 Best Practices

- Use Multi-AZ for production databases
- Use Read Replicas for scaling reads
- Cache expensive queries
- Use Redis for modern workloads
- Use encryption at rest and in transit
- Monitor database metrics with CloudWatch

---

# 🔥 Final Goal

This folder is designed to become:
- A production-ready database knowledge base
- An AWS interview preparation system
- A backend engineering reference handbook

---