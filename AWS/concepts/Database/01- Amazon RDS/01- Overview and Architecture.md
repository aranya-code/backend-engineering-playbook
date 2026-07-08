# RDS Overview and Architecture

Amazon Relational Database Service (RDS) is a fully managed service that makes it easy to set up, operate, and scale relational databases in the cloud. It manages time-consuming database administration tasks like provisioning, patching, backup, recovery, failure detection, and scaling, allowing engineers to focus on application development and database design.

Understanding the underlying architecture, control plane versus data plane division, and boundaries of managed operations is essential for running high-performance databases in production.

---

# Managed vs. Self-Managed Database Operations

Deploying a database on EC2 (or on-premises) requires manual management of every layer of the infrastructure. RDS automates the operational heavy lifting, shifting the operational workload from the customer to AWS.

```text
Database on EC2 (Self-Managed)             Amazon RDS (Managed)
┌───────────────────────────────┐          ┌───────────────────────────────┐
│     Application Schema        │          │     Application Schema        │
├───────────────────────────────┤          ├───────────────────────────────┤
│     Query Optimization        │          │     Query Optimization        │
├───────────────────────────────┤          ├───────────────────────────────┤
│    Database Engine Tuning     │          │    Database Engine Tuning     │
├───────────────────────────────┤          ├───────────────────────────────┤
│   Replication & High Avail    │          │  Replication & High Avail (M) │
├───────────────────────────────┤          ├───────────────────────────────┤
│   Backups & Point-in-Time     │          │  Backups & Point-in-Time  (M) │
├───────────────────────────────┤          ├───────────────────────────────┤
│    Database Patching & OS     │          │  Database Patching & OS   (M) │
├───────────────────────────────┤          ├───────────────────────────────┤
│      Storage Auto Scaling     │          │     Storage Auto Scaling  (M) │
├───────────────────────────────┤          ├───────────────────────────────┤
│    Server Provisioning / VM   │          │   Server Provisioning / VM (M)│
└───────────────────────────────┘          └───────────────────────────────┘
(M) = Managed by AWS
```

---

# Control Plane vs. Data Plane Architecture

RDS is architecturally split into two distinct operational planes:

## 1. The Control Plane

The Control Plane is the AWS-managed management layer. It handles administrative requests and orchestration.

- **Purpose**: Executes API operations (e.g., `CreateDBInstance`, `ModifyDBInstance`, `CreateDBSnapshot`).
- **Mechanism**: Orchestrates provisioning VMs, attaching EBS volumes, setting up replication, performing automated backups, and running health checks.
- **Access**: Accessed via the AWS Console, CLI, SDKs, or CloudFormation.
- **Isolation**: Runs in a separate AWS internal network, isolated from user data.

## 2. The Data Plane

The Data Plane is where your actual database instance runs and processes user queries.

- **Purpose**: Handles client connections, SQL execution, transaction processing, and replication streams.
- **Mechanism**: Run on optimized EC2 virtual machines (managed by AWS, hidden from customer view) attached to EBS volumes for persistent storage.
- **Access**: Accessed directly via database protocol ports (e.g., `3306` for MySQL, `5432` for PostgreSQL) from permitted clients inside your VPC.
- **Isolation**: Runs inside the customer's specified subnets and security groups.

---

# Under the Hood: Inside an RDS Instance

An RDS instance is not a serverless abstract entity; it is a specialized EC2 instance running in a dedicated AWS-managed utility account, mapped into your VPC using Elastic Network Interfaces (ENIs).

```text
Customer VPC
┌────────────────────────────────────────────────────────┐
│  Application Subnet                                    │
│  ┌───────────────────────┐                             │
│  │   Application Instance│                             │
│  └───────────┬───────────┘                             │
│              │ (Traffic inside VPC)                    │
│              ▼                                         │
│  Database Subnet                                       │
│  ┌───────────────────────┐                             │
│  │  Elastic Network      │                             │
│  │  Interface (ENI)      │                             │
│  └───────────▲───────────┘                             │
└──────────────┼─────────────────────────────────────────┘
               │ (Secure hypervisor-level mapping)
AWS Managed Account (Private)
┌──────────────┼─────────────────────────────────────────┐
│              ▼                                         │
│     ┌──────────────────┐                               │
│     │   RDS EC2 Host   │                               │
│     │  ┌────────────┐  │                               │
│     │  │ DB Engine  │  │                               │
│     │  └─────┬──────┘  │                               │
│     └────────┼─────────┘                               │
│              ▼ (EBS Protocol over AWS Network)         │
│     ┌──────────────────┐                               │
│     │   EBS Volume     │                               │
│     │  (Data + Logs)   │                               │
│     └──────────────────┘                               │
└────────────────────────────────────────────────────────┘
```

- **No OS Access**: You cannot SSH into the EC2 instance running RDS. This is a critical security boundary. OS-level changes must be executed using parameter groups or RDS API operations.
- **Network Attachment**: The database ENI resides in your subnet, inheriting the security groups and NACL configurations you apply.
- **Storage Attachment**: Data and transaction logs are stored on network-attached Amazon EBS volumes.

---

# DB Instance Classes and Configurations

RDS supports three categories of database deployments:

## 1. Single-AZ

A single database instance deployed in a single Availability Zone. There is no standby instance. If the underlying host or the AZ fails, the database is unavailable until a new instance is provisioned and data is restored from backup.

## 2. Multi-AZ (Active-Passive)

One active primary database instance and one synchronous standby instance in a different AZ. Traffic is automatically failed over to the standby if the primary fails. (Deep dive in `03- High Availability and Multi-AZ.md`).

## 3. Multi-AZ DB Cluster (Active-Two Passives)

One writer instance and two reader instances across three AZs, utilizing optimized EBS replication for faster failover and read scaling capabilities.

---

# Operational Lifecycle Events

RDS manages database lifecycles through specific operational events:

- **Maintenance Windows**: Weekly user-defined windows during which AWS applies OS patches, database engine updates, and hardware maintenance. Critical security patches may be applied outside this window.
- **Rebooting**: Reboots can be done with or without failover. A reboot updates dynamic parameter groups and clears operating system state.
- **Engine Upgrades**: Split into **Minor Upgrades** (generally backwards compatible, e.g., PostgreSQL 15.2 to 15.3) and **Major Upgrades** (may require application changes, e.g., PostgreSQL 14 to 15). Minor upgrades can be configured to run automatically.

---

# Key Takeaways

- RDS is a **managed relational database service** that splits control operations (Control Plane) from database workloads (Data Plane).
- You lose OS access (no SSH) in exchange for automated backups, HA, scaling, and patching.
- Under the hood, RDS runs on a dedicated EC2 instance inside an AWS-managed account, mapped to your VPC via an ENI.
- Always configure maintenance windows to align with off-peak application traffic.
- Relational engines supported include Aurora, PostgreSQL, MySQL, MariaDB, Oracle, and Microsoft SQL Server.

---
