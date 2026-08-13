# 08 - Import from Amazon S3

## Overview

Amazon DynamoDB Import from Amazon S3 allows you to **bulk load datasets stored in Amazon S3 directly into a new DynamoDB table** without writing custom ETL pipelines or consuming Write Capacity Units (WCUs).

Unlike traditional import methods that require applications, scripts, or AWS Glue jobs to perform millions of PutItem requests, DynamoDB imports data directly into storage using a fully managed server-side process.

This feature is ideal for:

- Initial data migration
- Large-scale data ingestion
- Database modernization
- Data lake integration
- Disaster recovery
- Environment provisioning
- Historical data loading
- Analytics workflows

Import from S3 is designed for **large datasets**, ranging from millions to billions of records.

---

# Why Import from S3 Exists

Suppose your company is migrating from an on-premises database.

```text
Oracle Database

↓

3 Billion Records

↓

Move to DynamoDB
```

Traditional migration:

```text
CSV

↓

Application

↓

Millions of PutItem Calls

↓

Slow

↓

Expensive
```

Using Import from S3:

```text
CSV

↓

Amazon S3

↓

DynamoDB Import

↓

Ready
```

AWS performs the import internally without stressing the application.

---

# Internal Architecture

```text
             Amazon S3

                  │

        Import Configuration

                  │

                  ▼

      DynamoDB Import Service

                  │

          Parallel Processing

                  │

                  ▼

         Newly Created Table
```

Applications are not involved during the import.

---

# Import Workflow

```text
Prepare Dataset

↓

Upload to Amazon S3

↓

Start Import

↓

AWS Validates Files

↓

Parallel Import

↓

Table Ready
```

Everything is managed by DynamoDB.

---

# Supported File Formats

Import supports several common formats.

Examples include:

```text
CSV

JSON

Amazon Ion
```

This makes migration from many existing databases straightforward.

---

# New Table Creation

Import always creates:

```text
New DynamoDB Table
```

It does **not** import into an existing table.

Example:

```text
orders.csv

↓

Import

↓

Orders Table
```

---

# Parallel Import

Internally, DynamoDB divides the workload.

```text
Large Dataset

↓

Chunk 1

Chunk 2

Chunk 3

Chunk 4

↓

Parallel Workers

↓

Table Created
```

This enables high-performance ingestion.

---

# Schema Mapping

During import, AWS maps file fields into DynamoDB attributes.

Example:

```text
CSV

CustomerID

OrderID

Amount
```

becomes

```text
CustomerID

OrderID

Amount
```

inside DynamoDB items.

---

# Import vs BatchWriteItem

| Feature | Import from S3 | BatchWriteItem |
|----------|----------------|----------------|
| Billions of Records | ✅ | Limited |
| Uses WCUs | No | Yes |
| Requires Application | No | Yes |
| Parallel Processing | Automatic | Manual |
| New Table Only | Yes | No |

Import is designed for large migrations.

---

# Import vs Data Migration Scripts

Traditional migration:

```text
CSV

↓

Python Script

↓

BatchWriteItem

↓

Retry Logic

↓

Monitoring
```

Import:

```text
CSV

↓

Amazon S3

↓

AWS Import
```

Much simpler.

---

# Import vs AWS Glue

| Feature | Import | AWS Glue |
|----------|---------|----------|
| Bulk Load | Excellent | Good |
| Data Transformation | Limited | Excellent |
| ETL Support | No | Yes |
| Application Required | No | No |

Glue transforms data.

Import loads data.

---

# Import Workflow Example

```text
Customer Database

↓

Export CSV

↓

Upload S3

↓

Import

↓

Production DynamoDB
```

No custom migration application is required.

---

# Real-World Example — Database Modernization

Legacy application:

```text
SQL Server

↓

Export Data

↓

Amazon S3

↓

Import

↓

DynamoDB
```

Organizations modernize applications without lengthy migration scripts.

---

# Real-World Example — Data Lake Integration

Historical data:

```text
Amazon S3

↓

Import

↓

Operational API
```

Archived information becomes available for real-time applications.

---

# Real-World Example — Environment Provisioning

Development team needs:

```text
Production-like Dataset
```

Workflow:

```text
S3

↓

Import

↓

Development Table
```

Every environment starts with identical data.

---

# Real-World Example — Disaster Recovery

Archived export:

```text
Amazon S3

↓

Import

↓

New DynamoDB Table
```

Data is restored into a fresh environment.

---

# Security Considerations

Protect imported data using:

- IAM Roles
- S3 Bucket Policies
- AWS KMS Encryption
- VPC Endpoints (where applicable)
- Least-Privilege Access

Import jobs should only access approved S3 locations.

---

# Performance Considerations

Import is optimized for very large datasets.

Advantages:

- No WCU consumption
- Automatic parallelization
- No application bottlenecks
- Highly scalable

Factors affecting duration include:

- Dataset size
- File count
- Object size
- Attribute complexity

---

# Best Practices

- Split large datasets into multiple files.
- Compress files when appropriate.
- Validate data before importing.
- Use dedicated S3 buckets for migration.
- Encrypt data at rest using AWS KMS.
- Monitor import progress with CloudWatch.

---

# Common Mistakes

## Using BatchWriteItem for Massive Imports

Poor:

```text
Python

↓

Millions of API Calls
```

Better:

```text
Amazon S3

↓

Import Service
```

---

## Importing Dirty Data

Validate:

- Required attributes
- Data types
- Duplicate keys
- Invalid values

before starting the import.

---

## Assuming Import Updates Existing Tables

Incorrect.

Import creates a **new table**.

It cannot append data to an existing table.

---

## Ignoring File Organization

Large datasets should be organized into multiple files instead of one enormous object.

This improves scalability and operational management.

---

# Architecture Perspective

```text
          Source Database

                 │

           Export Dataset

                 │

            Amazon S3

                 │

      DynamoDB Import Service

                 │

      Automatic Parallel Load

                 │

        New DynamoDB Table
```

Import simplifies large-scale migrations while minimizing operational overhead.

---

# Production Considerations

Import from S3 is commonly used for:

- Enterprise migrations
- Cloud modernization
- Initial table population
- Disaster recovery
- Environment provisioning
- Historical data restoration
- Data lake synchronization

A typical enterprise migration workflow:

```text
Oracle

↓

Amazon S3

↓

AWS Database Migration Service (Optional)

↓

DynamoDB Import

↓

Production Application
```

Organizations often combine Import from S3 with AWS Database Migration Service (DMS), AWS Glue, and Infrastructure as Code to automate end-to-end migration pipelines.

---

# Interview Notes

A common interview question is:

> **What is DynamoDB Import from Amazon S3?**

It is a fully managed feature that bulk loads data stored in Amazon S3 directly into a new DynamoDB table without consuming write capacity or requiring application code.

Another common question is:

> **Does Import from S3 consume Write Capacity Units (WCUs)?**

No. The import process is handled internally by DynamoDB and does not consume WCUs.

Another common question is:

> **Can Import from S3 load data into an existing table?**

No. It always creates a new DynamoDB table.

Another common question is:

> **When should Import from S3 be used instead of BatchWriteItem?**

Use Import from S3 for large-scale migrations or initial data loads involving millions or billions of records. BatchWriteItem is better suited for application-driven bulk writes.

---

# Key Takeaways

- Import from Amazon S3 provides a fully managed way to bulk load data into DynamoDB.
- It creates a new table and does not modify existing tables.
- The import process does not consume Write Capacity Units.
- Automatic parallel processing enables efficient ingestion of massive datasets.
- It is ideal for database migrations, disaster recovery, and environment provisioning.
- Combining Import from S3 with DMS, AWS Glue, and S3 creates scalable enterprise data migration pipelines.