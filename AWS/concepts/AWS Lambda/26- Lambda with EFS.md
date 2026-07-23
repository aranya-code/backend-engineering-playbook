# 26- Lambda with EFS

# Introduction

AWS Lambda provides ephemeral storage (`/tmp`) that is suitable for temporary files during a single invocation. However, many enterprise applications require persistent, shared storage that survives across invocations and can be accessed by multiple Lambda functions simultaneously.

Amazon Elastic File System (Amazon EFS) solves this problem by providing a fully managed, scalable Network File System (NFS) that can be mounted by Lambda functions.

This chapter explores how Lambda integrates with Amazon EFS, when to use it, architecture patterns, performance considerations, security, limitations, and production best practices.

---

# Why Lambda Needs Shared Storage

Normally, Lambda functions are stateless.

```
Invocation 1

↓

Creates File

↓

Ends

↓

File Lost
```

Every execution environment is temporary.

Sometimes applications require:

- Shared files
- Persistent storage
- Machine Learning models
- Shared configuration
- Large datasets
- Temporary processing across invocations

This is where Amazon EFS becomes useful.

---

# What is Amazon EFS?

Amazon Elastic File System is a managed NFS file system.

Characteristics:

- Fully managed
- Elastic storage
- Shared across multiple clients
- POSIX compliant
- Persistent
- Multi-AZ

```
EC2

↓

EFS

↑

Lambda

↑

ECS
```

Multiple compute services can access the same filesystem.

---

# Lambda Without EFS

```
Lambda

↓

/tmp

↓

Lost after environment is destroyed
```

Characteristics:

- Temporary
- Local storage
- Maximum 10 GB
- Not shared

---

# Lambda With EFS

```
Lambda

↓

Mount

↓

Amazon EFS

↓

Persistent Files
```

Files remain available even after Lambda execution completes.

---

# Architecture Overview

```
Users

↓

API Gateway

↓

Lambda

↓

Amazon EFS

↓

Shared Files
```

---

# Mount Targets

EFS creates mount targets inside each Availability Zone.

```
Availability Zone A

↓

Mount Target

------------------

Availability Zone B

↓

Mount Target
```

Lambda connects through these mount targets.

---

# VPC Requirement

Amazon EFS resides inside a VPC.

Therefore:

```
Lambda

↓

Must Be Inside VPC

↓

Mount EFS
```

Lambda cannot mount EFS without VPC networking.

---

# Connection Flow

```
Lambda

↓

Elastic Network Interface

↓

Security Group

↓

Mount Target

↓

Amazon EFS
```

---

# Access Points

AWS recommends using EFS Access Points.

Benefits:

- Simplified permissions
- Application isolation
- Fixed root directory
- User identity enforcement

Example:

```
Lambda A

↓

Access Point A

----------------

Lambda B

↓

Access Point B
```

Each function accesses only its designated directory.

---

# File System Structure

Example:

```
/models

/uploads

/logs

/config

/reports
```

Different Lambda functions can work within separate directories.

---

# Common Use Cases

## Machine Learning Models

Instead of downloading a model every invocation:

```
Lambda

↓

EFS

↓

Load Model

↓

Inference
```

This reduces startup time.

---

## Shared Configuration

```
Lambda A

↓

Shared Config

↑

Lambda B
```

Configuration files are stored once and reused.

---

## Image Processing

```
Upload Image

↓

Lambda

↓

Store Intermediate File

↓

EFS

↓

Process

↓

Upload Result
```

---

## PDF Generation

```
Lambda

↓

Generate Report

↓

Save

↓

EFS
```

Useful for multi-step document generation.

---

## Shared Templates

```
Email Templates

↓

EFS

↓

Lambda

↓

Send Email
```

No need to package templates with every deployment.

---

# Storage Capacity

Amazon EFS automatically scales.

```
1 GB

↓

100 GB

↓

10 TB

↓

100 TB+
```

Applications do not need to provision storage in advance.

---

# Performance Modes

Amazon EFS provides two performance modes.

## General Purpose

Designed for:

- Web applications
- Lambda
- Content management
- Development

Lowest latency.

---

## Max I/O

Designed for:

- Large analytics workloads
- Massive parallel processing

Higher throughput but increased latency.

---

# Throughput Modes

## Bursting

Performance scales automatically with stored data.

Suitable for most workloads.

---

## Provisioned Throughput

Specify desired throughput.

Useful when consistent performance is required.

---

## Elastic Throughput

Automatically adjusts throughput based on workload.

Recommended for unpredictable serverless applications.

---

# Security

EFS supports encryption:

## At Rest

```
KMS

↓

Encrypted Files
```

---

## In Transit

```
Lambda

↓

TLS

↓

EFS
```

Communication remains encrypted.

---

# IAM Permissions

Lambda execution role requires permission to mount EFS.

Example permissions:

- elasticfilesystem:ClientMount
- elasticfilesystem:ClientWrite
- elasticfilesystem:ClientRootAccess (only when necessary)

---

# Security Groups

Example:

```
Lambda SG

↓

2049

↓

EFS SG
```

Port **2049 (NFS)** must be allowed.

---

# Performance Considerations

Reading from EFS is slower than reading from local memory.

Comparison:

| Storage | Speed |
|----------|------:|
| Memory | Fastest |
| /tmp | Very Fast |
| Amazon EFS | Moderate |
| Amazon S3 | Slower (per object request) |

Frequently accessed data should still be cached in memory.

---

# Cost Considerations

Costs depend on:

- Stored data
- Throughput mode
- Access frequency
- Backup usage

Unlike `/tmp`, EFS incurs ongoing storage charges even when Lambda is idle.

---

# Lambda vs EFS vs S3

| Feature | `/tmp` | EFS | S3 |
|---------|---------|-----|----|
| Persistent | ❌ | ✅ | ✅ |
| Shared | ❌ | ✅ | Object-based |
| POSIX Filesystem | ❌ | ✅ | ❌ |
| Max Size | 10 GB | Elastic | Virtually Unlimited |
| Mountable | ❌ | ✅ | ❌ |

---

# Common Mistakes

## Using EFS for Small Temporary Files

Bad choice:

```
Lambda

↓

Small Temp File

↓

EFS
```

Better:

```
Lambda

↓

/tmp
```

---

## Incorrect Security Groups

Symptoms:

- Mount timeout
- Connection refused
- Unable to access filesystem

Verify:

- Port 2049
- Security Groups
- Mount Targets

---

## Forgetting VPC Configuration

Without VPC:

```
Lambda

↓

EFS

❌ Cannot Connect
```

---

# Best Practices

✅ Use EFS only for persistent shared storage.

✅ Use Access Points for application isolation.

✅ Enable encryption at rest and in transit.

✅ Keep Lambda and EFS in the same VPC.

✅ Cache frequently used files in memory.

✅ Use `/tmp` for temporary processing.

✅ Monitor throughput and latency using CloudWatch.

---

# Real-World Architecture

```
                Users

                  │

            API Gateway

                  │

               Lambda

                  │

        ┌─────────┴─────────┐

        │                   │

   Amazon EFS          Secrets Manager

        │

 Machine Learning Models

 Shared Templates

 Reports

 Configuration Files
```

---

# Senior Backend Engineering Perspective

Amazon EFS extends Lambda beyond purely stateless workloads by providing durable, shared storage that multiple functions and compute services can access simultaneously.

However, EFS should not be treated as a replacement for object storage or databases. Senior engineers choose EFS only when a shared POSIX-compliant filesystem is required, such as for machine learning models, shared assets, or multi-step file processing.

A production-ready implementation typically combines:

- Private subnets
- EFS Access Points
- Least-privilege IAM policies
- Proper Security Group configuration
- Encryption
- CloudWatch monitoring

Choosing between `/tmp`, Amazon EFS, and Amazon S3 is an important architectural decision based on persistence, sharing requirements, latency, and cost.

---

# Key Takeaways

- Amazon EFS provides persistent, shared file storage for AWS Lambda.
- Lambda must be attached to a VPC to mount EFS.
- EFS Access Points simplify permissions and improve isolation.
- `/tmp` is suitable for temporary files, while EFS is designed for persistent shared storage.
- EFS is commonly used for ML models, shared templates, configuration files, and large-scale file processing in enterprise serverless applications.