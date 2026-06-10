# Amazon S3 (Simple Storage Service)

## Definition
Amazon S3 is AWS's object storage service designed to store and retrieve virtually unlimited amounts of data.

## Why S3 Exists
Traditional storage systems require hardware procurement, maintenance, scaling, backups and redundancy planning.
S3 removes these concerns by providing managed object storage.

## Storage Types in AWS

| Type | Service | Example |
|--------|---------|---------|
| Block | EBS | EC2 Disk |
| File | EFS | Shared Linux Filesystem |
| Object | S3 | Images, Videos, Backups |

## Core Components
- Bucket
- Object
- Key
- Metadata
- Tags

## Durability vs Availability

Durability = Data survives failures.

S3 Durability:
99.999999999% (11 Nines)

Availability:
99.99%

## Common Use Cases
- Static Website Hosting
- Backup Storage
- Data Lakes
- Application Assets
- Log Storage
- Disaster Recovery

## Interview Question
Q: Why is S3 called object storage?
A: Because files are stored as objects consisting of data, metadata and a unique key.

## Exam Notes
- S3 = Object Storage
- Unlimited Storage
- Regional Service
- Global Bucket Namespace
