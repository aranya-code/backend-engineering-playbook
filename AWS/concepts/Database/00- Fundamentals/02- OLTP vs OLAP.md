# OLTP vs OLAP

# Introduction

Backend systems usually process transactional workloads (OLTP) while analytics platforms process reporting workloads (OLAP).

---

# OLTP

Online Transaction Processing

Characteristics

- Small transactions
- Frequent reads/writes
- Low latency
- Highly normalized

Examples

- Banking
- Shopping cart
- Payments

AWS Services

- Amazon RDS
- Amazon Aurora

---

# OLAP

Online Analytical Processing

Characteristics

- Large scans
- Aggregations
- Historical analysis
- Read intensive

Examples

- Dashboards
- BI
- Reporting

AWS Services

- Amazon Redshift
- Athena

---

# Comparison

| Feature | OLTP | OLAP |
|---------|------|------|
| Purpose | Transactions | Analytics |
| Queries | Short | Complex |
| Updates | Frequent | Rare |
| Latency | Milliseconds | Seconds |

---

# Best Practices

Never run heavy reporting queries on your production OLTP database.

Use replicas, warehouses, or ETL pipelines.

---

# Interview Questions

- Why separate OLTP and OLAP?
- Why is Redshift unsuitable for OLTP?
