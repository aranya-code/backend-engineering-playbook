# Database Indexing

# Introduction

Indexes are specialized data structures that improve query performance by allowing the database engine to locate rows without scanning the entire table.

---

# Why Indexes Matter

Without an index:
- Full table scan
- Higher CPU usage
- Increased I/O
- Slower queries

With an index:
- Faster lookups
- Reduced disk reads
- Better query performance

---

# Common Index Types

- Primary Index
- Secondary Index
- Composite Index
- Unique Index
- Full-Text Index

---

# Trade-offs

Advantages:
- Faster SELECT queries
- Efficient sorting and filtering

Disadvantages:
- Additional storage
- Slower INSERT, UPDATE, DELETE operations

---

# Best Practices

- Index columns used in WHERE, JOIN, and ORDER BY clauses.
- Avoid excessive indexing.
- Periodically review unused indexes.

---

# Interview Questions

1. What is an index?
2. Why do indexes slow writes?
3. What is a composite index?

---

# Quick Revision

- Index = Faster reads
- Too many indexes = Slower writes
- Index only frequently queried columns
