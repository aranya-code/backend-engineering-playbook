# Introduction to RDS CLI

> Learn how to provision, manage, secure, monitor, and automate relational databases using **Amazon Relational Database Service (Amazon RDS)** and the **AWS Command Line Interface (AWS CLI)**. This chapter introduces Amazon RDS architecture, supported database engines, DB instances, storage, availability, and the core CLI commands required to manage production databases.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Understand Amazon RDS
- Understand managed relational databases
- Learn supported database engines
- Create DB instances
- Understand RDS architecture
- Manage databases using AWS CLI
- Build a foundation for production database administration

---

# Why Amazon RDS?

Running databases on EC2 requires you to manage:

- Operating System
- Database installation
- Patching
- Backups
- Monitoring
- High Availability
- Storage
- Failover

Amazon RDS automates these operational tasks.

Instead of:

```text
EC2

↓

Install MySQL

↓

Manage Database
```

You simply provision:

```text
Amazon RDS

↓

Managed Database
```

---

# What is Amazon RDS?

Amazon Relational Database Service (Amazon RDS) is AWS's fully managed relational database service.

Amazon RDS automates:

- Provisioning
- Patching
- Backups
- Monitoring
- Failover
- Storage management
- High Availability

---

# Supported Database Engines

Amazon RDS supports multiple engines.

```text
Amazon RDS

│

├── MySQL

├── PostgreSQL

├── MariaDB

├── Oracle

├── SQL Server

└── Amazon Aurora
```

---

# RDS Architecture

```text
Application

↓

Amazon RDS

↓

Storage
```

Applications connect using a database endpoint.

---

# Core Components

Amazon RDS consists of:

```text
Amazon RDS

│

├── DB Instance

├── Storage

├── Endpoint

├── Parameter Group

├── Option Group

└── Security Group
```

---

# What is a DB Instance?

A DB Instance is the compute resource that runs the database engine.

It includes:

- CPU
- Memory
- Database Engine
- Storage
- Networking

---

# What is an Endpoint?

Applications connect using a DNS endpoint.

```text
Application

↓

Database Endpoint

↓

Amazon RDS
```

Applications never connect directly to an IP address.

---

# Storage

Amazon RDS supports:

- General Purpose SSD (gp3)
- Provisioned IOPS SSD (io1/io2)
- Magnetic (legacy)

Choose storage based on workload requirements.

---

# High Availability

Amazon RDS supports:

```text
Single-AZ
```

or

```text
Multi-AZ
```

Multi-AZ is recommended for production workloads.

---

# Amazon RDS CLI Namespace

Amazon RDS uses:

```bash
aws rds <operation>
```

Examples:

```bash
aws rds describe-db-instances
```

```bash
aws rds create-db-instance
```

```bash
aws rds delete-db-instance
```

---

# Verify AWS Identity

```bash
aws sts get-caller-identity
```

---

# List DB Instances

```bash
aws rds describe-db-instances
```

---

# List Available Database Engines

```bash
aws rds describe-db-engine-versions
```

---

# Describe DB Instance

```bash
aws rds describe-db-instances \
--db-instance-identifier production-db
```

Displays:

- Status
- Endpoint
- Engine
- Storage
- Instance Class
- Multi-AZ

---

# Delete DB Instance

```bash
aws rds delete-db-instance \
--db-instance-identifier production-db
```

Production databases should normally be deleted only after creating a final snapshot.

---

# Production Workflow

```text
Application

↓

Amazon RDS Endpoint

↓

Managed Database

↓

Storage
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
DB Instance
      │
      ▼
Managed Storage
```

Amazon RDS removes much of the operational burden of running relational databases while providing automated backups, patching, monitoring, and high availability.

---

# Interview Note

### Question

**What is Amazon RDS?**

### Answer

Amazon Relational Database Service (Amazon RDS) is AWS's fully managed relational database service that automates infrastructure provisioning, backups, software patching, storage management, monitoring, and high availability. It supports multiple database engines such as MySQL, PostgreSQL, MariaDB, Oracle, SQL Server, and Amazon Aurora.

---

# Key Takeaways

- Amazon RDS is AWS's managed relational database service.
- A DB Instance is the compute resource running the database engine.
- Applications connect through an RDS endpoint.
- Amazon RDS automates backups, patching, monitoring, and failover.
- Multi-AZ deployments improve availability.
- Amazon RDS supports multiple relational database engines.
- The AWS CLI uses the `aws rds` namespace to manage database resources.