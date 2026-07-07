# SQL Performance Optimization

# Introduction

Query optimization is often cheaper and more effective than adding more hardware.

---

# Optimization Techniques

- Create appropriate indexes.
- Select only required columns.
- Avoid SELECT *.
- Use WHERE filters.
- Optimize JOINs.
- Batch writes where possible.

---

# Analyze Queries

Use execution plans to identify:

- Full table scans
- Expensive joins
- Missing indexes
- Sort operations

---

# AWS Features

- Amazon RDS Performance Insights
- Enhanced Monitoring
- CloudWatch Metrics

---

# Best Practices

- Review slow query logs.
- Remove unused indexes.
- Keep statistics updated.

---

# Interview Questions

1. Why is SELECT * discouraged?
2. What causes full table scans?
3. How do indexes improve performance?

---

# Quick Revision

Good schema + good indexes + efficient SQL = scalable databases.
