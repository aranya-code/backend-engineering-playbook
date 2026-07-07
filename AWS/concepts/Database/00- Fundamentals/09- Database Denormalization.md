# Database Denormalization

# Introduction

Denormalization intentionally introduces redundancy to improve read performance.

---

# Why Denormalize?

- Reduce JOIN operations
- Improve reporting
- Speed up read-heavy workloads

---

# Use Cases

- Dashboards
- Analytics
- Product catalogs
- Recommendation systems

---

# Advantages

- Faster reads
- Simpler queries

---

# Disadvantages

- Duplicate data
- More complex updates
- Increased storage

---

# Normalization vs Denormalization

| Feature | Normalization | Denormalization |
|---------|---------------|-----------------|
| Redundancy | Low | Higher |
| Reads | Slower | Faster |
| Writes | Easier consistency | More update effort |

---

# Best Practices

- Normalize first.
- Denormalize only after identifying performance bottlenecks.
- Document duplicated fields.

---

# Interview Questions

1. Why denormalize?
2. When is denormalization appropriate?
3. Can normalized and denormalized tables coexist?

---

# Quick Revision

Denormalization improves read performance by trading storage and update complexity.
