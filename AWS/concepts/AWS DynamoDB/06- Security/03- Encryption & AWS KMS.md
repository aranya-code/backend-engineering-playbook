# 03 - Encryption & AWS KMS

## Overview

Data security is one of the core responsibilities of any production database. Amazon DynamoDB provides **encryption at rest** by integrating with **AWS Key Management Service (AWS KMS)**.

Every item written to a DynamoDB table is encrypted before it is stored on disk and decrypted transparently when it is read by an authorized request.

Unlike application-level encryption, DynamoDB encryption is completely managed by AWS and requires no code changes.

Encryption protects:

- Table data
- Secondary indexes
- Backups
- Point-in-Time Recovery (PITR)
- DynamoDB Streams
- Global Table replicas

---

# Learning Objectives

After completing this chapter, you will understand:

- How DynamoDB encryption works
- AWS KMS integration
- AWS-owned vs AWS-managed vs Customer-managed keys
- Encryption at rest
- Encryption in transit
- Envelope encryption
- Key rotation
- Production security best practices

---

# Encryption Layers

A production application usually has two encryption layers.

```text
Client

↓

TLS Encryption

↓

DynamoDB API

↓

AWS KMS

↓

Encrypted Storage
```

The first protects data in transit.

The second protects stored data.

---

# Encryption in Transit

When an application communicates with DynamoDB:

```text
Application

↓

HTTPS (TLS)

↓

AWS Endpoint

↓

DynamoDB
```

AWS requires HTTPS for all DynamoDB API operations.

Benefits:

- Prevents packet sniffing
- Prevents man-in-the-middle attacks
- Protects credentials
- Protects request payloads

---

# Encryption at Rest

When DynamoDB stores data:

```text
Application

↓

Write Request

↓

Encryption

↓

SSD Storage
```

The stored bytes are unreadable without the encryption key.

---

# Internal Encryption Workflow

```text
Application

↓

PutItem

↓

Generate Data Key

↓

Encrypt Data

↓

Store Encrypted Item

↓

Encrypted Storage
```

Reads follow the reverse process.

```text
Encrypted Item

↓

Decrypt

↓

Return Plain Data
```

---

# Envelope Encryption

DynamoDB uses **envelope encryption**.

Instead of encrypting every item directly with the master key:

```text
Master Key

↓

Data Encryption Key (DEK)

↓

Encrypt Data
```

This approach improves:

- Performance
- Scalability
- Security

---

# AWS KMS Integration

Encryption keys are managed by AWS KMS.

Architecture:

```text
Application

↓

DynamoDB

↓

AWS KMS

↓

Encryption Keys
```

DynamoDB automatically requests encryption keys when needed.

Applications never communicate directly with KMS for standard table operations.

---

# Types of KMS Keys

DynamoDB supports three key types.

---

## AWS Owned Key

Simplest option.

```text
AWS

↓

Creates Key

↓

Manages Key

↓

Rotates Key
```

No configuration required.

Suitable for:

- Development
- Small applications
- Internal systems

---

## AWS Managed Key

Key example:

```text
alias/aws/dynamodb
```

AWS manages:

- Creation
- Rotation
- Availability

Customers can view usage through KMS.

---

## Customer Managed Key (CMK)

Organization creates the key.

```text
Security Team

↓

Customer KMS Key

↓

DynamoDB
```

Benefits:

- Full control
- Key policies
- Cross-account access
- Manual disable
- Audit control
- Compliance support

---

# Comparison

| Feature | AWS Owned | AWS Managed | Customer Managed |
|----------|-----------|-------------|------------------|
| Configuration | None | Minimal | Full |
| Key Rotation | AWS | AWS | Configurable |
| IAM Control | No | Limited | Full |
| KMS Policy Control | No | Limited | Yes |
| Compliance | Basic | Good | Excellent |

---

# Key Rotation

Encryption keys should be rotated periodically.

```text
Old Key

↓

Rotate

↓

New Key
```

Applications continue operating without changes because DynamoDB manages encryption transparently.

---

# Production Architecture

```text
             Client

                │

          HTTPS (TLS)

                │

                ▼

           DynamoDB API

                │

                ▼

         AWS KMS Encryption

                │

                ▼

      Encrypted Table Storage

                │

                ▼

 Secondary Indexes

 Backups

 PITR

 Streams
```

All stored data remains encrypted.

---

# Global Tables

Encryption is maintained across Regions.

```text
US-East-1

↓

Encrypt

↓

Replicate

↓

EU-West-1

↓

Encrypt
```

Each regional replica uses KMS within its Region.

---

# Backup Encryption

When backups are created:

```text
Table

↓

Backup

↓

Encrypted Backup
```

The backup remains encrypted.

The same applies to:

- PITR
- Export operations
- Global Tables

---

# KMS Permissions

Applications may require permission to use customer-managed keys.

Example permissions:

```text
kms:Encrypt

kms:Decrypt

kms:GenerateDataKey

kms:DescribeKey
```

Without appropriate KMS permissions, DynamoDB operations using customer-managed keys may fail.

---

# Monitoring Encryption

Monitor using:

- AWS CloudTrail
- AWS CloudWatch
- AWS KMS Logs
- AWS Config

Track:

- Key usage
- Failed decrypt operations
- Disabled keys
- Unauthorized access attempts

---

# Best Practices

- Enable encryption for every production table.
- Use customer-managed keys for regulated workloads.
- Enable automatic key rotation where appropriate.
- Restrict KMS permissions using least privilege.
- Audit KMS usage regularly.
- Separate development and production keys.
- Monitor key usage with CloudTrail.

---

# Common Mistakes

## Assuming HTTPS Is Enough

HTTPS protects:

```text
Network
```

It does not protect stored data.

Encryption at rest is still required.

---

## Sharing One KMS Key Everywhere

Poor:

```text
One Key

↓

All Applications
```

Better:

```text
Payments Key

Orders Key

Customer Key
```

Separate keys reduce blast radius and improve auditing.

---

## Disabling a Customer Key

Disabling a KMS key can prevent DynamoDB from decrypting protected data.

Always validate the operational impact before disabling or deleting keys.

---

## Ignoring Key Policies

IAM permissions alone are not sufficient when using customer-managed keys.

KMS key policies must also permit the required operations.

---

# Production Considerations

Large enterprises commonly implement:

```text
AWS Organizations

↓

Security Account

↓

Customer Managed Keys

↓

Application Accounts

↓

DynamoDB
```

This provides:

- Centralized key management
- Compliance reporting
- Controlled access
- Security auditing

Industries such as banking, healthcare, insurance, and government frequently require customer-managed keys to satisfy regulatory requirements.

---

# Interview Notes

A common interview question is:

> **Is DynamoDB encrypted by default?**

Yes. DynamoDB encrypts all table data at rest using AWS KMS. Encryption is enabled by default for all new tables.

---

Another common question is:

> **What is the difference between AWS-owned, AWS-managed, and customer-managed KMS keys?**

AWS-owned keys are fully managed by AWS and require no configuration. AWS-managed keys (such as `alias/aws/dynamodb`) are managed by AWS but visible within your account. Customer-managed keys provide full control over policies, rotation, auditing, and lifecycle management.

---

Another common question is:

> **Does DynamoDB encrypt backups and Global Tables?**

Yes. Encryption extends to backups, Point-in-Time Recovery (PITR), secondary indexes, Streams, and Global Table replicas.

---

Another common question is:

> **What is envelope encryption?**

Envelope encryption uses a data encryption key (DEK) to encrypt the data, while the DEK itself is protected by a master key stored in AWS KMS. This provides better scalability and performance than encrypting all data directly with the master key.

---

# Key Takeaways

- DynamoDB provides encryption at rest using AWS KMS.
- HTTPS (TLS) protects data in transit, while KMS protects data at rest.
- DynamoDB uses envelope encryption for secure and efficient key management.
- Customer-managed KMS keys offer the highest level of control and are preferred for regulated production workloads.
- Encryption automatically covers tables, indexes, backups, PITR, Streams, and Global Tables.
- Combining IAM, KMS, CloudTrail, and CloudWatch provides a comprehensive security foundation for production DynamoDB deployments.