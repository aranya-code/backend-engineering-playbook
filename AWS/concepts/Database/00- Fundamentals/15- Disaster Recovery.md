# Disaster Recovery

# Introduction

Disaster Recovery (DR) focuses on restoring systems after major failures such as regional outages, natural disasters, or data corruption.

---

# DR Objectives

- Restore business operations
- Minimize data loss
- Reduce recovery time

---

# Common DR Strategies

## Backup & Restore

Lowest cost, longest recovery.

## Pilot Light

Critical infrastructure always running.

## Warm Standby

Scaled-down production environment.

## Multi-Site Active/Active

Highest availability and lowest recovery time.

---

# AWS Services

- Amazon RDS Cross-Region Read Replicas
- Aurora Global Database
- AWS Backup
- Amazon S3 Cross-Region Replication

---

# Choosing a Strategy

| Strategy | Cost | Recovery Speed |
|----------|------|----------------|
| Backup & Restore | Low | Slow |
| Pilot Light | Medium | Moderate |
| Warm Standby | High | Fast |
| Active/Active | Highest | Fastest |

---

# Best Practices

- Define RPO and RTO.
- Replicate critical workloads.
- Regularly perform DR drills.
- Document recovery procedures.

---

# Interview Questions

1. What is Disaster Recovery?
2. Pilot Light vs Warm Standby?
3. Which DR strategy provides the lowest RTO?

---

# Quick Revision

DR prepares systems for large-scale failures using predefined recovery strategies.
