# DB Instances, Storage & Networking

> Learn how to create, configure, and manage Amazon RDS DB Instances using the AWS CLI. This chapter covers DB instance classes, storage types, networking, DB subnet groups, parameter groups, option groups, endpoints, and production deployment strategies.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Create RDS DB Instances
- Choose appropriate instance classes
- Configure storage
- Configure networking
- Understand DB Subnet Groups
- Configure Parameter Groups
- Configure Option Groups
- Deploy production-ready databases

---

# RDS Deployment Architecture

A typical Amazon RDS deployment looks like:

```text
Application

↓

VPC

↓

DB Subnet Group

↓

Amazon RDS

↓

Storage
```

---

# What is a DB Instance?

A DB Instance is the compute resource that hosts your relational database.

It includes:

- Database Engine
- CPU
- Memory
- Storage
- Network Configuration
- Security Groups

---

# DB Instance Components

```text
DB Instance

│

├── Database Engine

├── Instance Class

├── Storage

├── Endpoint

├── Parameter Group

├── Option Group

└── Security Group
```

---

# DB Instance Classes

Amazon RDS provides several instance families.

```text
General Purpose

↓

db.t4g

db.m7g
```

```text
Memory Optimized

↓

db.r7g
```

```text
Burstable

↓

db.t3

db.t4g
```

---

# Choosing an Instance Class

| Workload | Recommended Class |
|----------|-------------------|
| Development | db.t4g.micro |
| Small Production | db.t4g.small |
| Medium Production | db.m7g.large |
| Memory Intensive | db.r7g.large |
| Enterprise | db.r7g.xlarge and above |

---

# List Orderable DB Classes

```bash
aws rds describe-orderable-db-instance-options \
--engine postgres
```

---

# Create a DB Instance

Example:

```bash
aws rds create-db-instance \
--db-instance-identifier production-db \
--engine postgres \
--db-instance-class db.t4g.micro \
--allocated-storage 20 \
--master-username admin \
--master-user-password MySecurePassword123
```

---

# View DB Instances

```bash
aws rds describe-db-instances
```

---

# Describe a DB Instance

```bash
aws rds describe-db-instances \
--db-instance-identifier production-db
```

Displays:

- Status
- Endpoint
- Storage
- Multi-AZ
- Engine
- Backup settings

---

# DB Instance States

Typical lifecycle:

```text
Creating

↓

Available

↓

Modifying

↓

Backing Up

↓

Deleting
```

---

# Database Endpoint

Applications connect using an endpoint.

```text
Application

↓

Endpoint

↓

Database
```

Example:

```text
production-db.xxxxxxxxx.ap-south-1.rds.amazonaws.com
```

---

# Endpoint vs IP Address

Always use:

```text
Endpoint
```

Never use:

```text
IP Address
```

Endpoints remain stable even after failover.

---

# Storage Types

Amazon RDS supports:

```text
Storage

│

├── gp3

├── io1

├── io2

└── Magnetic
```

---

# General Purpose SSD (gp3)

Recommended for:

- Most production workloads
- Development
- APIs
- Web applications

Provides:

- Low latency
- Good performance
- Cost efficiency

---

# Provisioned IOPS (io1/io2)

Recommended for:

- High transaction databases
- Financial systems
- Enterprise applications
- Large OLTP workloads

---

# Storage Scaling

Amazon RDS supports online storage scaling.

```text
20 GB

↓

100 GB

↓

500 GB
```

No application changes required.

---

# Modify Storage

```bash
aws rds modify-db-instance \
--db-instance-identifier production-db \
--allocated-storage 100 \
--apply-immediately
```

---

# Storage Auto Scaling

Enable automatic storage growth.

Benefits:

- Prevent storage exhaustion
- Reduce manual intervention
- Support unpredictable workloads

---

# Networking Overview

Amazon RDS runs inside a VPC.

```text
Amazon VPC

↓

Private Subnets

↓

Amazon RDS
```

---

# DB Subnet Group

A DB Subnet Group defines which subnets Amazon RDS may use.

```text
DB Subnet Group

│

├── Subnet A

└── Subnet B
```

Production deployments should span multiple Availability Zones.

---

# Create a DB Subnet Group

```bash
aws rds create-db-subnet-group \
--db-subnet-group-name production-subnets \
--db-subnet-group-description "Production RDS Subnets" \
--subnet-ids subnet-123 subnet-456
```

---

# Describe DB Subnet Groups

```bash
aws rds describe-db-subnet-groups
```

---

# Security Groups

Security Groups control database access.

Example:

```text
Application

↓

Security Group

↓

Amazon RDS
```

Only trusted application servers should be allowed.

---

# Public vs Private Access

Recommended:

```text
Internet

↓

Application Load Balancer

↓

Application

↓

Private RDS
```

Avoid exposing databases directly to the internet.

---

# Publicly Accessible

Possible values:

```text
true
```

```text
false
```

Production recommendation:

```text
false
```

---

# Parameter Groups

Parameter Groups manage database configuration.

Examples:

- Time zone
- Logging
- Connection limits
- Memory settings

---

# Describe Parameter Groups

```bash
aws rds describe-db-parameter-groups
```

---

# Create a Parameter Group

```bash
aws rds create-db-parameter-group \
--db-parameter-group-name production-postgres \
--db-parameter-group-family postgres16 \
--description "Production PostgreSQL Parameters"
```

---

# Modify Parameters

```bash
aws rds modify-db-parameter-group
```

Changes may require a reboot.

---

# Option Groups

Option Groups enable engine-specific features.

Examples:

- Oracle Options
- SQL Server Features
- Native Backup

---

# Describe Option Groups

```bash
aws rds describe-option-groups
```

---

# Create an Option Group

```bash
aws rds create-option-group
```

---

# Associate Parameter Group

```bash
aws rds modify-db-instance \
--db-instance-identifier production-db \
--db-parameter-group-name production-postgres
```

---

# Associate Option Group

```bash
aws rds modify-db-instance \
--db-instance-identifier production-db \
--option-group-name production-options
```

---

# Network Architecture

```text
Application

↓

Private Subnet

↓

Amazon RDS

↓

Managed Storage
```

---

# DNS Resolution

Applications connect using:

```text
Endpoint

↓

DNS

↓

Amazon RDS
```

The endpoint automatically resolves to the active database instance.

---

# Common Errors

## DBInstanceAlreadyExists

Verify:

- Instance identifier
- Existing databases

---

## InvalidSubnet

Verify:

- DB Subnet Group
- Availability Zones
- VPC

---

## InvalidParameterGroup

Verify:

- Database engine family
- Parameter Group name

---

## InvalidSecurityGroup

Verify:

- VPC
- Security Group
- Region

---

## StorageLimitExceeded

Increase:

- Allocated storage
- Storage Auto Scaling

---

# Production Best Practices

- Deploy databases in private subnets.
- Use Multi-AZ DB Subnet Groups.
- Prefer gp3 storage for most workloads.
- Enable Storage Auto Scaling.
- Never expose production databases publicly.
- Create custom Parameter Groups instead of modifying defaults.
- Separate development and production databases.
- Use meaningful DB instance identifiers.
- Monitor storage utilization continuously.

---

# Real-World Workflow

```text
Create VPC

↓

Create DB Subnet Group

↓

Create Security Group

↓

Create DB Instance

↓

Application Connection

↓

Production
```

---

# Architecture Note

```text
Application
      │
      ▼
Security Group
      │
      ▼
Amazon RDS Endpoint
      │
      ▼
DB Instance
      │
      ▼
Managed Storage
```

A production RDS deployment consists of a private DB instance inside a DB Subnet Group, protected by Security Groups and accessed through a stable DNS endpoint rather than an IP address.

---

# Interview Note

### Question

**What is the purpose of a DB Subnet Group in Amazon RDS?**

### Answer

A DB Subnet Group is a collection of subnets within a VPC that Amazon RDS uses to place database instances. It enables RDS to deploy databases across multiple Availability Zones for high availability and ensures that database instances are created only within approved network locations. Production deployments should include subnets in at least two Availability Zones.

---

# Key Takeaways

- A DB Instance is the compute resource running the database engine.
- Applications connect through an RDS endpoint, not an IP address.
- Choose instance classes based on workload requirements.
- gp3 is the preferred storage type for most workloads.
- DB Subnet Groups determine where RDS instances are deployed.
- Parameter Groups customize database behavior.
- Production databases should run in private subnets protected by Security Groups.