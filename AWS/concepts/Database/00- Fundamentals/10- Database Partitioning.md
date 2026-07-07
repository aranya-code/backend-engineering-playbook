# Database Partitioning

# Introduction

Database partitioning divides a large table into smaller logical pieces (partitions) while keeping it as a single database object.

---

# Why Partition?

- Improve query performance
- Reduce maintenance time
- Manage very large datasets
- Archive historical data efficiently

---

# Partition Types

## Range Partitioning
Partition data based on value ranges (dates, IDs).

Example:
- 2024 Orders
- 2025 Orders
- 2026 Orders

## List Partitioning
Partition based on predefined values.

Example:
- Region = India
- Region = USA

## Hash Partitioning
Uses a hash function to distribute rows evenly.

## Composite Partitioning
Combines two or more partitioning strategies.

---

# Benefits

- Faster scans
- Easier maintenance
- Parallel query execution
- Better archival strategy

---

# Limitations

- Poor partition design can hurt performance.
- Cross-partition queries may still be expensive.

---

# Best Practices

- Partition using frequently filtered columns.
- Avoid creating too many tiny partitions.
- Review partition strategy as data grows.

---

# Interview Questions

1. What is partitioning?
2. Difference between partitioning and sharding?
3. When should range partitioning be used?

---

# Quick Revision

Partitioning = Split one large table into smaller logical partitions inside the same database.
