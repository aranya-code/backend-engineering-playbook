# RDS Best Practices and Cost Optimization

Production databases are typically the most expensive and critical components of an application architecture. Optimizing database cost while maintaining performance, high availability, and operational resilience requires a structured approach to instance sizing, storage configuration, lifecycle management, and licensing.

This guide outlines production best practices and actionable cost-saving strategies for Amazon RDS.

---

# Cost Optimization Strategies

## 1. Stopped State Limitations

To reduce costs, you can temporarily stop an RDS database (e.g., non-production databases during weekends).

- **The 7-Day Limit**: RDS databases can only remain stopped for **up to 7 days**. After 7 days, AWS automatically restarts the instance to check for and apply critical security patches and software updates.
- **Solution**: To keep an environment stopped long-term, use Lambda scripts to stop the database weekly when it auto-starts, or export a snapshot and delete the database, restoring only when needed.

## 2. Reserved Instances (RIs)

For production databases running 24/7, Reserved Instances offer significant cost savings (up to 60%) compared to On-Demand pricing.

- **Commitment**: 1-year or 3-year term commitments.
- **Payment Options**: No Upfront, Partial Upfront, All Upfront.
- **Sizing Flexibility**: DB instance class flexibility is supported for standard engines (MySQL, PostgreSQL, MariaDB), allowing the RI discount to apply to different sizes within the same instance family (e.g., a `db.r5.xlarge` RI can cover two `db.r5.large` instances).

## 3. Detecting and Deleting Idle Databases

Identify unused database instances by monitoring the `DatabaseConnections` metric.

- **Audit Rule**: If `DatabaseConnections` has been `0` for 14+ consecutive days, flag the database for deletion.
- **Deletion Protocol**: Always take a **final manual snapshot** before deleting the database to ensure data can be recovered in the future.

## 4. Storage Optimization (gp3 vs. gp2)

- Migrate older **gp2** volumes to **gp3** volumes. 
- gp3 provides 3,000 baseline IOPS and 125 MB/s throughput for free and is up to **20% cheaper** per GB than gp2.
- Decouples performance from storage size, eliminating the need to over-provision disk space just to get baseline IOPS.

---

# Production Best Practices

## 1. Safety Measures: Deletion Protection

Always enable **Deletion Protection** on production databases. When enabled, users cannot delete the database instance through the Console, CLI, or API until the setting is explicitly disabled.

```text
User triggers Delete-Database
          │
          ▼
Is Deletion Protection Enabled?
       ├── YES ──► Block Request (Return Error) ✗
       └── NO  ──► Proceed with Deletion ✓
```

## 2. Parameter Groups Management

- **Rule**: **Never use default parameter groups**. Default parameter groups cannot be modified.
- **Action**: Always create a custom parameter group for your database engine and version. This allows you to tune memory limits, connection timeouts, and logging levels as your workload grows.
- **Upgrades**: Create new parameter groups during major database upgrades rather than modifying old groups.

## 3. Scheduling Non-Production Databases

Non-production environments (dev/test) typically only need to run during working hours.

- **Action**: Implement auto-stop/start schedules using Systems Manager Quick Setup or AWS Instance Scheduler.
- **Savings**: Stopping a database 12 hours a day and on weekends reduces the instance run cost by **over 60%**.

---

# Schema and Connection Design Best Practices

- **Avoid Large JSON Columns**: While PostgreSQL and MySQL support JSON columns, query filtering on unindexed JSON attributes causes full table scans, consuming high CPU. Use relational columns for indexed fields.
- **Implement Connection Limits**: Set connection limits in the application client and configuration parameters to prevent database resource exhaustion.
- **Use Multi-AZ for Production**: Never run production databases in Single-AZ mode. The risk of data corruption or AZ downtime is too high.
- **Disable Auto-Minor Upgrades for High-Sensitivity Environments**: While auto-minor upgrades are convenient, they can trigger reboots at unexpected times during maintenance windows. For mission-critical databases, handle patching manually during planned maintenance windows.

---

# Key Takeaways

- Stop idle non-prod databases, but remember they **automatically restart after 7 days**.
- Use **Reserved Instances** for production databases to save up to 60% compared to On-Demand.
- Migrate gp2 storage to **gp3** to gain higher performance at a lower cost.
- **Deletion Protection** should be enabled on every production database.
- Use **custom parameter groups** from day one to ensure you can adjust configurations.
- Automate dev/test environment schedules to save on idle compute hours.

---
