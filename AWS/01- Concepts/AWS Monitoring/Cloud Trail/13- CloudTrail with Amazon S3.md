# AWS CloudTrail with Amazon S3

Amazon S3 is the primary storage destination for AWS CloudTrail logs. When a Trail is created, CloudTrail continuously delivers log files to an S3 bucket, enabling long-term storage, auditing, compliance, and security investigations.

Without Amazon S3, CloudTrail only retains Management Events for the last 90 days in Event History.

------------------------------------------------------------------------

# Why Store CloudTrail Logs in Amazon S3?

Amazon S3 provides:

- Long-term storage
- High durability
- Scalability
- Cost-effective archival
- Lifecycle management
- Secure storage
- Compliance support

------------------------------------------------------------------------

# Architecture

```text
AWS API Call

↓

CloudTrail

↓

Trail

↓

Amazon S3

↓

JSON Log Files
```

------------------------------------------------------------------------

# How Log Delivery Works

When an API call occurs:

1. CloudTrail records the event.
2. The Trail processes the event.
3. CloudTrail creates a JSON log file.
4. The log file is delivered to the configured S3 bucket.

------------------------------------------------------------------------

# S3 Folder Structure

CloudTrail automatically organizes logs.

```text
Bucket

↓

AWSLogs

↓

Account ID

↓

CloudTrail

↓

Region

↓

Year

↓

Month

↓

Day
```

This hierarchy makes it easy to locate logs.

------------------------------------------------------------------------

# Bucket Policies

CloudTrail requires permission to write logs into the bucket.

The bucket policy should:

- Allow CloudTrail to write objects.
- Prevent unauthorized access.
- Restrict public access.
- Enforce encryption where required.

------------------------------------------------------------------------

# Encryption

CloudTrail logs should always be encrypted.

Options include:

- SSE-S3
- SSE-KMS

Using AWS KMS provides additional control and auditing capabilities.

------------------------------------------------------------------------

# Lifecycle Policies

Amazon S3 Lifecycle rules help reduce storage costs.

Example:

```text
0–90 Days

↓

S3 Standard

↓

90–365 Days

↓

S3 Standard-IA

↓

After 1 Year

↓

S3 Glacier

↓

After 7 Years

↓

Delete
```

------------------------------------------------------------------------

# Benefits

- Durable storage
- Centralized audit logs
- Compliance
- Cost optimization
- Easy integration with Athena
- Supports security investigations

------------------------------------------------------------------------

# Real-World Example

A financial organization must retain CloudTrail logs for seven years.

CloudTrail delivers logs to Amazon S3.

Lifecycle rules automatically archive older logs to Amazon S3 Glacier while preserving audit records for compliance.

------------------------------------------------------------------------

# Best Practices

- Use a dedicated S3 bucket.
- Enable Versioning.
- Enable Server-Side Encryption.
- Enable Log File Integrity Validation.
- Restrict bucket access.
- Configure Lifecycle policies.

------------------------------------------------------------------------

# Key Takeaways

- Amazon S3 is the primary storage destination for CloudTrail logs.
- Trails continuously deliver JSON log files to S3.
- Encryption, Versioning, and Lifecycle policies improve security and reduce costs.
- S3 enables long-term auditing and compliance.