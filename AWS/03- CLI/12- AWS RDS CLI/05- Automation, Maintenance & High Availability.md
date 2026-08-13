# Automation, Maintenance & High Availability

> Learn how to automate Amazon RDS administration using the AWS CLI. This chapter covers maintenance windows, automatic minor version upgrades, scaling, storage management, failover, event notifications, RDS Proxy, Blue/Green deployments, and production operational best practices.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Configure maintenance windows
- Perform database upgrades
- Scale RDS instances
- Manage storage automatically
- Configure High Availability
- Understand Blue/Green deployments
- Monitor database events
- Apply production operational practices

---

# Production Operations

Managing an RDS database is an ongoing process.

```text
Provision

↓

Monitor

↓

Maintain

↓

Scale

↓

Upgrade

↓

Backup

↓

Recover
```

---

# Maintenance Window

Amazon RDS performs maintenance during a configurable maintenance window.

Examples include:

- OS patching
- Minor engine updates
- Security updates
- Infrastructure maintenance

---

# Maintenance Workflow

```text
Maintenance Window

↓

Patch

↓

Restart (if required)

↓

Database Available
```

---

# View Maintenance Window

```bash
aws rds describe-db-instances \
--db-instance-identifier production-db
```

Review:

```text
PreferredMaintenanceWindow
```

---

# Modify Maintenance Window

```bash
aws rds modify-db-instance \
--db-instance-identifier production-db \
--preferred-maintenance-window Mon:02:00-Mon:03:00
```

---

# Choosing a Maintenance Window

Best practice:

```text
Lowest Database Traffic

↓

Maintenance
```

Avoid business hours.

---

# Automatic Minor Version Upgrades

Amazon RDS can automatically install:

- Security patches
- Bug fixes
- Minor engine upgrades

Example:

```text
PostgreSQL 16.1

↓

16.2
```

---

# Enable Auto Minor Upgrade

```bash
aws rds modify-db-instance \
--db-instance-identifier production-db \
--auto-minor-version-upgrade
```

---

# Major Version Upgrade

Major upgrades require planning.

Example:

```text
PostgreSQL 15

↓

PostgreSQL 16
```

Always test before production.

---

# Upgrade Workflow

```text
Snapshot

↓

Testing

↓

Upgrade

↓

Validation

↓

Production
```

---

# Modify Engine Version

```bash
aws rds modify-db-instance \
--db-instance-identifier production-db \
--engine-version 16.2
```

---

# Storage Scaling

Storage can grow online.

```text
20 GB

↓

100 GB

↓

500 GB
```

Applications continue running.

---

# Enable Storage Auto Scaling

Benefits:

- Prevent storage exhaustion
- Automatic growth
- Less operational effort

---

# Scale Compute Resources

Increase DB Instance Class.

Example:

```text
db.t4g.medium

↓

db.m7g.large

↓

db.r7g.large
```

---

# Modify Instance Class

```bash
aws rds modify-db-instance \
--db-instance-identifier production-db \
--db-instance-class db.m7g.large
```

---

# Scaling Strategy

```text
CPU High

↓

Larger Instance

────────────

Storage Full

↓

Increase Storage
```

---

# Blue/Green Deployments

Amazon RDS supports Blue/Green deployments for supported engines.

Architecture:

```text
Blue

↓

Current Production

────────────

Green

↓

Upgraded Database
```

---

# Blue/Green Workflow

```text
Production

↓

Clone

↓

Upgrade

↓

Testing

↓

Switchover
```

Benefits:

- Minimal downtime
- Safer upgrades
- Easy validation

---

# Failover

In Multi-AZ deployments:

```text
Primary Failure

↓

Automatic Failover

↓

Standby Promoted
```

Applications continue using the same endpoint.

---

# Reboot Database

```bash
aws rds reboot-db-instance \
--db-instance-identifier production-db
```

---

# Force Failover

```bash
aws rds reboot-db-instance \
--db-instance-identifier production-db \
--force-failover
```

Useful for testing High Availability.

---

# Event Notifications

Amazon RDS generates events for:

- Failovers
- Backups
- Maintenance
- Storage
- Replication
- Instance failures

---

# View Events

```bash
aws rds describe-events
```

---

# Example Events

```text
Backup Completed
```

```text
Failover Started
```

```text
Storage Full
```

```text
Maintenance Complete
```

---

# Amazon SNS Integration

Typical workflow:

```text
Amazon RDS

↓

Event

↓

Amazon SNS

↓

Email

↓

Operations Team
```

---

# Event Categories

Common categories:

- Availability
- Backup
- Configuration Change
- Failure
- Maintenance
- Recovery

---

# High Availability Architecture

```text
Application

↓

RDS Endpoint

↓

Primary

↓

Standby
```

Applications remain unaware of failover.

---

# Operational Checklist

Regularly verify:

- Backup success
- Snapshot status
- Storage usage
- CPU utilization
- Connection count
- Replication lag
- Maintenance schedule

---

# Capacity Planning

Monitor:

```text
CPU

↓

Memory

↓

Connections

↓

Storage

↓

IOPS
```

Scale before limits are reached.

---

# Database Health Checks

Review:

- CloudWatch Metrics
- Performance Insights
- Slow Query Logs
- Enhanced Monitoring

---

# Automation Workflow

```text
CloudWatch Alarm

↓

SNS

↓

Engineer

↓

AWS CLI

↓

Resolution
```

---

# Common Errors

## Maintenance Delayed

Verify:

- Maintenance window
- Pending modifications

---

## Upgrade Failed

Possible causes:

- Unsupported version
- Extension compatibility
- Parameter incompatibility

---

## Storage Modification Pending

Storage changes may take time.

Monitor:

```bash
aws rds describe-db-instances
```

---

## Failover Didn't Occur

Verify:

- Multi-AZ enabled
- Instance health
- Region support

---

## Blue/Green Deployment Failed

Verify:

- Engine compatibility
- Version support
- Parameter Groups
- Replication health

---

# Production Best Practices

- Enable automatic minor version upgrades.
- Schedule maintenance during off-peak hours.
- Take manual snapshots before upgrades.
- Test major upgrades in staging.
- Use Blue/Green deployments whenever supported.
- Enable Multi-AZ for production databases.
- Configure CloudWatch alarms and SNS notifications.
- Monitor capacity trends continuously.
- Perform periodic failover testing.
- Document maintenance procedures.

---

# Real-World Workflow

```text
Deploy Database

↓

Enable Multi-AZ

↓

Configure Monitoring

↓

Configure Maintenance Window

↓

Enable Auto Upgrades

↓

Monitor Capacity

↓

Scale When Required

↓

Production
```

---

# Architecture Note

```text
Application
      │
      ▼
Amazon RDS Endpoint
      │
      ▼
Primary DB
      │
      ├── Standby (Multi-AZ)
      ├── Automated Backups
      ├── CloudWatch
      ├── Performance Insights
      └── SNS Notifications
```

Production Amazon RDS environments combine automated maintenance, high availability, proactive monitoring, and scalable infrastructure to minimize downtime and operational overhead.

---

# Interview Note

### Question

**How would you safely perform a production database upgrade in Amazon RDS?**

### Answer

I would first create a manual snapshot of the production database and test the upgrade in a staging environment. If supported, I would use an Amazon RDS Blue/Green deployment to create an upgraded copy of the database, validate application compatibility, and then perform a controlled switchover with minimal downtime. I would schedule the upgrade during the maintenance window, monitor CloudWatch metrics and database logs throughout the process, and keep a rollback plan based on the pre-upgrade snapshot.

---

# Key Takeaways

- Maintenance windows control when Amazon RDS performs updates.
- Automatic minor version upgrades improve security and stability.
- Storage and compute resources can be scaled independently.
- Blue/Green deployments reduce downtime during upgrades.
- Multi-AZ provides automatic failover and high availability.
- Amazon SNS can notify teams about database events.
- Regular maintenance, monitoring, and capacity planning are essential for reliable production databases.