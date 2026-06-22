# 09- Elastic Beanstalk Storage

---

# Introduction

Storage is one of the most misunderstood areas in Elastic Beanstalk.

Many beginners assume:

```text id="9v1cxr"
Application Running
        ↓
Files Saved
        ↓
Files Stay Forever
```

This assumption is dangerous.

Elastic Beanstalk environments are designed to be:

```text id="4w9tme"
Elastic
Scalable
Replaceable
Disposable
```

This means instances can be terminated and recreated at any time.

Understanding storage is therefore critical for:

* Data Persistence
* File Uploads
* Application Reliability
* Backup Strategy
* Disaster Recovery

---

# Storage Architecture Overview

A typical Elastic Beanstalk environment contains multiple storage layers.

```text id="ks7g3d"
Application
      ↓
EC2 Instance
      ↓
EBS Volume

Additional Services
      ↓
S3
EFS
RDS
```

Each storage option serves a different purpose.

---

# Types of Storage in Elastic Beanstalk

The most common storage options are:

```text id="2a0k4n"
Instance Storage
EBS
S3
EFS
RDS
```

Understanding when to use each one is essential.

---

# Instance Storage

Every EC2 instance contains local storage.

Example:

```text id="v5e4mp"
/tmp
/var
/home
```

Applications can write files here.

---

# Advantages

```text id="0s9d6l"
Fast
Simple
Local Access
```

---

# Disadvantages

```text id="g7k8rh"
Not Persistent
Lost On Instance Termination
Not Shared
```

---

# Why Local Storage Is Dangerous

Consider:

```text id="i2q8wd"
User Uploads File
      ↓
Stored On EC2
      ↓
Auto Scaling Terminates Instance
```

Result:

```text id="5z8vxa"
File Lost
```

This is one of the most common beginner mistakes.

---

# Understanding Ephemeral Storage

Instance storage is often called:

```text id="8h2c7p"
Ephemeral Storage
```

Meaning:

```text id="w6k9qd"
Temporary
Disposable
```

Never store important business data on local instance storage.

---

# Amazon EBS

Elastic Block Store (EBS) provides persistent block storage for EC2 instances.

---

# Architecture

```text id="z3j7qn"
EC2
 ↓
EBS Volume
```

Think of EBS as a virtual hard drive.

---

# Why EBS Exists

Without EBS:

```text id="s7v4mk"
Terminate Instance
      ↓
Lose Everything
```

With EBS:

```text id="r1m5tx"
Terminate Instance
      ↓
Volume Can Persist
```

---

# Common EBS Use Cases

```text id="n9f4qs"
Application Logs
Temporary Data
Caching
Application Runtime Files
```

---

# EBS Volume Types

Common types:

```text id="v7d2ko"
gp3
gp2
io1
io2
st1
sc1
```

---

# Recommended Choice

For most applications:

```text id="f6j9wa"
gp3
```

offers the best balance between:

```text id="u4x8mv"
Performance
Cost
```

---

# EBS Limitations

EBS is attached to a specific instance.

Example:

```text id="l7p4sm"
EC2-A
 ↓
EBS-A
```

Another instance cannot automatically share the same storage.

---

# Amazon S3

Amazon S3 is the most important storage service when working with Elastic Beanstalk.

---

# What Is S3?

Amazon S3 is an object storage service.

Designed for:

```text id="g8q5dw"
Durability
Scalability
Availability
```

---

# Architecture

```text id="x5m3pk"
Application
      ↓
S3 Bucket
```

---

# Why S3 Matters

Elastic Beanstalk already uses S3 internally.

Example:

```text id="r4n9wb"
Application Versions
```

are stored in:

```text id="y8d1qx"
Amazon S3
```

---

# Common S3 Use Cases

```text id="d5w8pe"
User Uploads
Images
Videos
Documents
Backups
Static Assets
```

---

# Django Example

Bad Approach:

```text id="e7m4vn"
User Upload
      ↓
EC2 Storage
```

Good Approach:

```text id="k3q9rp"
User Upload
      ↓
S3 Bucket
```

---

# Benefits

```text id="a8j4tw"
Durable
Scalable
Shared
Highly Available
```

---

# S3 Storage Workflow

```text id="x7n5ke"
User Upload
      ↓
Application
      ↓
S3
      ↓
Store Object
```

---

# S3 For Static Files

Django Example:

```text id="h9v1mq"
CSS
JavaScript
Images
```

Stored in:

```text id="n2k8qs"
S3
```

and delivered through:

```text id="w6j3px"
CloudFront
```

---

# Why Use S3 For Static Assets?

Benefits:

```text id="q4m7tv"
Reduced EC2 Load
Faster Delivery
Lower Costs
```

---

# Amazon EFS

Elastic File System (EFS) provides shared file storage.

---

# Architecture

```text id="y1n4qs"
EC2-A
   ↓

EFS

   ↑
EC2-B
```

Multiple instances can access the same files.

---

# Why EFS Exists

Problem:

```text id="f8w3dj"
Multiple Instances
       ↓
Need Shared Files
```

Solution:

```text id="p6m9kr"
Amazon EFS
```

---

# EFS Characteristics

```text id="b2x7qp"
Shared
Persistent
Scalable
Managed
```

---

# Common EFS Use Cases

```text id="q5v8kt"
Shared Uploads
Shared Content
CMS Systems
Legacy Applications
```

---

# EFS vs EBS

| Feature            | EBS    | EFS      |
| ------------------ | ------ | -------- |
| Shared             | No     | Yes      |
| Persistent         | Yes    | Yes      |
| Multiple Instances | No     | Yes      |
| Performance        | Higher | Moderate |

---

# When To Use EFS

Use EFS when:

```text id="d8q2pm"
Multiple EC2 Instances
Need Shared Files
```

---

# Amazon RDS

Applications need storage for structured data.

Elastic Beanstalk itself does not provide databases.

Most applications use:

```text id="q3w8nv"
Amazon RDS
```

---

# Typical Architecture

```text id="t9j2kr"
Elastic Beanstalk
        ↓
Django
        ↓
RDS PostgreSQL
```

---

# Supported Databases

```text id="u8k4mx"
PostgreSQL
MySQL
MariaDB
SQL Server
Oracle
```

---

# Why Use RDS

Benefits:

```text id="e4p9qk"
Managed
Backups
Patching
Monitoring
High Availability
```

---

# Database Best Practice

Avoid:

```text id="f1m5rv"
Database On EC2
```

Prefer:

```text id="j7q3nx"
Amazon RDS
```

---

# Storage For Logs

Applications generate logs.

Examples:

```text id="z6w2kp"
Application Logs
Nginx Logs
Deployment Logs
System Logs
```

---

# Log Storage Options

```text id="r3m8qt"
EC2
CloudWatch Logs
S3
```

---

# Recommended Approach

```text id="c8k1mv"
CloudWatch Logs
```

because:

```text id="d9p4rx"
Centralized
Searchable
Persistent
```

---

# Backup Strategy

Production systems require backups.

---

# Example Architecture

```text id="k5q7jw"
Application
      ↓
RDS Snapshot

S3 Versioning

CloudWatch Logs
```

---

# Disaster Recovery

Always assume:

```text id="x2n8kd"
Instance Failure
```

will occur.

Design storage accordingly.

---

# Storage Design Principles

Good architecture:

```text id="w4j6pv"
Stateless Application
        ↓
Persistent Storage Externalized
```

---

# Stateless Architecture

Application:

```text id="a5k8rq"
Elastic Beanstalk
```

Stores no critical data locally.

Data lives in:

```text id="u7n4mx"
S3
RDS
EFS
```

---

# Common Storage Mistakes

---

## Storing Uploads On EC2

Risk:

```text id="g1m7vx"
Data Loss
```

---

## Storing Database On EC2

Risk:

```text id="f3q8kr"
Operational Complexity
```

---

## No Backups

Risk:

```text id="k6m2qw"
Permanent Data Loss
```

---

## Ignoring EFS

Shared applications may require:

```text id="t8n5dv"
Shared Storage
```

---

## Keeping Logs Locally

Risk:

```text id="z4m1pk"
Lost Troubleshooting Data
```

---

# Real World Storage Architecture

Typical Django Application:

```text id="r7w9mq"
Users
 ↓
ALB
 ↓
Elastic Beanstalk
 ↓
Django
 ↓
RDS PostgreSQL

Uploads
 ↓
S3

Logs
 ↓
CloudWatch
```

---

# Enterprise Storage Architecture

```text id="x1q4pv"
Application
      ↓
Aurora

Files
 ↓
S3

Shared Files
 ↓
EFS

Logs
 ↓
CloudWatch
```

---

# Interview Questions

## Is EC2 Storage Persistent?

Not always.

Local instance storage is ephemeral.

---

## Where Should User Uploads Be Stored?

```text id="w2n7kd"
Amazon S3
```

---

## What Is EFS?

A managed shared file system.

---

## Difference Between EBS And EFS?

EBS is attached to a single instance.

EFS can be shared by multiple instances.

---

## Why Use RDS Instead Of EC2 Databases?

Managed backups, patching, monitoring, and availability.

---

## What Storage Service Does Elastic Beanstalk Use For Application Versions?

```text id="u4j9qm"
Amazon S3
```

---

# Senior Engineer Perspective

One of the most important cloud architecture principles is:

```text id="p9m5rw"
Applications Should Be Stateless
```

Elastic Beanstalk instances should be treated as:

```text id="v3q8nk"
Disposable Compute Resources
```

All critical data should live outside the instances.

A mature production architecture typically follows:

```text id="a7k2mv"
Compute
 ↓
Elastic Beanstalk

Database
 ↓
RDS

Uploads
 ↓
S3

Shared Files
 ↓
EFS

Logs
 ↓
CloudWatch
```

This approach maximizes:

```text id="x8m4qp"
Scalability
Reliability
Recoverability
```

---

# Key Takeaways

* Local EC2 storage is temporary.
* EBS provides persistent block storage.
* S3 is the preferred solution for uploads and static assets.
* EFS provides shared file storage.
* RDS should be used for relational databases.
* CloudWatch should be used for centralized logging.
* Production applications should be stateless.
* Critical data should never depend on EC2 instance lifecycle.
* Proper storage design is essential for scalability and disaster recovery.
