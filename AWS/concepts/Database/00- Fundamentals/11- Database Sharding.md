# Database Sharding

# Introduction

Sharding horizontally distributes data across multiple independent database servers.

---

# Why Shard?

- Scale beyond a single server
- Increase write throughput
- Reduce storage bottlenecks

---

# Sharding Strategies

## Range-Based
Shard by ID range.

## Hash-Based
Hash the key to determine the shard.

## Geographic
Shard by region or country.

---

# Advantages

- Horizontal scalability
- Higher write capacity
- Fault isolation

---

# Challenges

- Cross-shard joins
- Resharding complexity
- Distributed transactions
- Operational overhead

---

# Partitioning vs Sharding

| Feature | Partitioning | Sharding |
|---------|--------------|----------|
| Database | One | Multiple |
| Scaling | Limited | Horizontal |
| Server | Single | Multiple |

---

# Best Practices

- Choose stable shard keys.
- Avoid hot shards.
- Monitor shard imbalance.

---

# Interview Questions

1. What is sharding?
2. Sharding vs partitioning?
3. What is a hot shard?

---

# Quick Revision

Sharding = Split data across multiple database servers.
