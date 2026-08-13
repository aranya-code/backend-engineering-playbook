# Database Interview Questions

A comprehensive collection of senior-level database interview questions and detailed model answers. Designed for Backend Engineers, DevOps Engineers, Cloud Engineers, and Solution Architects preparing for technical interviews at senior and staff levels.

These questions go beyond textbook definitions — they test production experience, architectural reasoning, and the ability to diagnose and resolve real-world database incidents.

---

# Topics Covered

| # | Topic | Questions | Focus Area |
|---|-------|-----------|------------|
| 01 | [Relational and NoSQL](./01-%20Relational%20and%20NoSQL.md) | 5 | SQL vs NoSQL trade-offs, CAP theorem alignment, Multi-AZ vs Replicas, Aurora vs RDS, encryption migration |
| 02 | [Caching and Performance](./02-%20Caching%20and%20Performance.md) | 5 | Cache-Aside vs Write-Through, Stampede mitigation, EngineCPUUtilization trap, OOM prevention |
| 03 | [System Design Scenarios](./03-%20System%20Design%20Scenarios.md) | 3 | Flash sale architecture, zero-downtime DMS migration, connection exhaustion diagnosis |
| 04 | [Amazon RDS and Aurora](./04-%20Amazon%20RDS%20and%20Aurora.md) | 12 | Storage auto-scaling, failover mechanics, RDS Proxy pinning, Aurora storage, Global Database, Backtrack, Blue-Green upgrades |
| 05 | [Database Architecture and Scaling](./05-%20Database%20Architecture%20and%20Scaling.md) | 10 | Split-brain, sync vs async replication, sharding, DynamoDB hot partitions, CQRS, Saga pattern, optimistic vs pessimistic locking |
| 06 | [Production Troubleshooting Scenarios](./06-%20Production%20Troubleshooting%20Scenarios.md) | 7 | CPU 100%, connection leaks, stale reads, storage full, Redis CPU trap, accidental DELETE recovery, DynamoDB throttling |

---

# Interview Preparation Roadmap

```text
Phase 1: Theory (Warm-Up)
  Relational and NoSQL → Caching and Performance

Phase 2: AWS Services (Core Knowledge)
  Amazon RDS and Aurora

Phase 3: Architecture (Design Thinking)
  System Design Scenarios → Database Architecture and Scaling

Phase 4: Production (Real-World Readiness)
  Production Troubleshooting Scenarios
```

---

# Question Categories by Role

| Target Role | Essential Files | Focus |
|-------------|----------------|-------|
| Backend Developer | 01, 02, 03 | Data modeling, caching, system design |
| Senior Backend Developer | 01, 02, 03, 05 | + Architecture patterns, scaling, locking |
| DevOps Engineer | 04, 06 | RDS operations, monitoring, incident response |
| Senior DevOps Engineer | 04, 05, 06 | + Sharding, replication, HA/DR strategies |
| Solution Architect | All (01–06) | Full-spectrum database architecture |

---

# Question Format

Every question includes:

- Clear problem statement or scenario
- Step-by-step model answer with production context
- ASCII architecture diagrams where applicable
- SQL examples and AWS CLI commands
- Comparison tables for decision-making questions
- Key gotchas and common mistakes

---

# Total Coverage

```text
42 Questions across 6 files

Breakdown:
  Theory & Concepts:      10 questions
  AWS Service Operations: 12 questions
  System Design:          13 questions
  Incident Scenarios:      7 questions
```

---

# Navigation

| Direction | Link |
|-----------|------|
| ⬆️ Parent | [Database Module](../README.md) |
| ⬅️ Previous | [Comparison Guide](../03-%20Comparison%20Guide/) |

---
