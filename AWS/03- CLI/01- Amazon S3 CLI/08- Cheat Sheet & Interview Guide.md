# Cheat Sheet & Interview Guide

> A practical reference for the most frequently used Amazon S3 CLI commands, interview questions, troubleshooting techniques, and production workflows.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Quickly recall commonly used S3 CLI commands.
- Use S3 CLI efficiently in day-to-day engineering work.
- Prepare for AWS and Backend Engineering interviews.
- Troubleshoot common S3 issues.
- Follow production-ready operational workflows.
- Understand best practices used by experienced cloud engineers.

---

# Why a Cheat Sheet?

Even experienced AWS engineers don't memorize every S3 CLI command.

Instead, they remember:

- Command patterns
- Common workflows
- Troubleshooting steps
- Best practices

This chapter is designed to be your daily reference.

---

# Command Syntax

High-Level Commands

```bash
aws s3 <command> [options]
```

Example

```bash
aws s3 ls
```

---

Low-Level API Commands

```bash
aws s3api <operation> [options]
```

Example

```bash
aws s3api list-buckets
```

---

# Most Frequently Used Commands

## Verify Identity

```bash
aws sts get-caller-identity
```

Always verify before making production changes.

---

## List Buckets

```bash
aws s3 ls
```

---

## Create Bucket

```bash
aws s3 mb s3://company-backups
```

---

## Remove Empty Bucket

```bash
aws s3 rb s3://company-backups
```

---

## Remove Bucket with Contents

```bash
aws s3 rb s3://company-backups \
--force
```

---

## List Objects

```bash
aws s3 ls s3://company-backups
```

Recursive listing

```bash
aws s3 ls s3://company-backups \
--recursive
```

---

## Upload File

```bash
aws s3 cp report.pdf \
s3://company-backups/
```

---

## Download File

```bash
aws s3 cp \
s3://company-backups/report.pdf \
./
```

---

## Copy Object

```bash
aws s3 cp \
s3://company-backups/report.pdf \
s3://archive/report.pdf
```

---

## Move Object

```bash
aws s3 mv \
s3://company-backups/report.pdf \
s3://company-backups/archive/report.pdf
```

---

## Delete Object

```bash
aws s3 rm \
s3://company-backups/report.pdf
```

---

## Synchronize Directories

```bash
aws s3 sync \
./website \
s3://company-website
```

---

## Synchronize and Delete Removed Files

```bash
aws s3 sync \
./website \
s3://company-website \
--delete
```

---

## Preview Synchronization

```bash
aws s3 sync \
./website \
s3://company-website \
--dryrun
```

---

## Upload with Encryption

```bash
aws s3 cp report.pdf \
s3://company-backups \
--sse AES256
```

---

## Upload with KMS

```bash
aws s3 cp report.pdf \
s3://company-backups \
--sse aws:kms
```

---

## Upload with Metadata

```bash
aws s3 cp report.pdf \
s3://company-backups \
--metadata Department=Finance
```

---

## Upload with Storage Class

```bash
aws s3 cp backup.zip \
s3://company-backups \
--storage-class STANDARD_IA
```

---

# Useful `s3api` Commands

List Buckets

```bash
aws s3api list-buckets
```

---

Bucket Region

```bash
aws s3api get-bucket-location \
--bucket company-backups
```

---

Enable Versioning

```bash
aws s3api put-bucket-versioning \
--bucket company-backups \
--versioning-configuration Status=Enabled
```

---

Check Versioning

```bash
aws s3api get-bucket-versioning \
--bucket company-backups
```

---

List Object Versions

```bash
aws s3api list-object-versions \
--bucket company-backups
```

---

View Object Metadata

```bash
aws s3api head-object \
--bucket company-backups \
--key report.pdf
```

---

View Bucket Policy

```bash
aws s3api get-bucket-policy \
--bucket company-backups
```

---

Check Encryption

```bash
aws s3api get-bucket-encryption \
--bucket company-backups
```

---

Check Block Public Access

```bash
aws s3api get-public-access-block \
--bucket company-backups
```

---

# Global Options

| Option | Purpose |
|----------|----------|
| `--profile` | Use a named AWS profile |
| `--region` | Override default Region |
| `--output json` | JSON output |
| `--output table` | Human-readable table |
| `--query` | Filter output using JMESPath |
| `--debug` | Enable debugging |
| `--no-cli-pager` | Disable pager |
| `--dryrun` | Preview changes (supported commands) |

---

# Common Error Messages

| Error | Cause | Resolution |
|--------|-------|------------|
| AccessDenied | Missing permissions | Review IAM and Bucket Policies |
| NoSuchBucket | Bucket missing | Verify bucket name |
| NoSuchKey | Object missing | Verify object key |
| BucketNotEmpty | Objects still exist | Remove objects first |
| BucketAlreadyExists | Name already used | Choose another name |
| InvalidAccessKeyId | Invalid credentials | Verify Access Key |
| SignatureDoesNotMatch | Wrong Region or Secret Key | Verify credentials and Region |
| ExpiredToken | Temporary credentials expired | Login again or assume role |

---

# Production Workflow

```text
Verify AWS Identity
        │
        ▼
Verify Region
        │
        ▼
Verify Bucket
        │
        ▼
Dry Run
        │
        ▼
Upload / Sync
        │
        ▼
Verify Upload
        │
        ▼
Monitor
```

---

# Interview Questions

## 1. What is the difference between `aws s3` and `aws s3api`?

**Answer**

`aws s3` provides high-level commands for common file operations such as upload, download, and synchronization. `aws s3api` maps directly to the underlying Amazon S3 REST APIs and exposes advanced functionality such as versioning, lifecycle policies, encryption, and bucket configuration.

---

## 2. Why are S3 bucket names globally unique?

**Answer**

Bucket names form part of the service endpoint (for example, `https://my-bucket.s3.amazonaws.com`), so AWS requires every bucket name to be unique across all AWS accounts.

---

## 3. What is the difference between Versioning and Lifecycle Rules?

**Answer**

Versioning protects data by retaining multiple versions of an object, while Lifecycle Rules automate transitions between storage classes or delete objects after a defined retention period.

---

## 4. What is the purpose of `aws s3 sync`?

**Answer**

`sync` compares the source and destination, transferring only new or modified files. It is commonly used for deployments, backups, and directory synchronization.

---

## 5. What happens when you delete an object from a versioned bucket?

**Answer**

Amazon S3 creates a **Delete Marker** instead of permanently deleting the object. Previous versions remain available and can be recovered.

---

## 6. What is Block Public Access?

**Answer**

It is an S3 security feature that prevents public access to buckets and objects, even if a bucket policy or ACL attempts to grant public permissions.

---

## 7. Why should IAM Roles be preferred over IAM Users?

**Answer**

IAM Roles provide temporary credentials through AWS STS, reducing the security risks associated with long-lived access keys.

---

## 8. How would you troubleshoot an `AccessDenied` error?

**Answer**

I would:

1. Verify the active identity using `aws sts get-caller-identity`.
2. Confirm the correct Region.
3. Review IAM policies.
4. Review the Bucket Policy.
5. Check Block Public Access.
6. Verify KMS permissions if encryption is enabled.
7. Retry the command with `--debug`.

---

## 9. When would you use Intelligent-Tiering?

**Answer**

When access patterns are unpredictable and you want Amazon S3 to automatically optimize storage costs without manual intervention.

---

## 10. What is the difference between `cp` and `sync`?

**Answer**

`cp` copies files without comparing them, while `sync` transfers only changed files after comparing the source and destination. `sync` is more efficient for repeated deployments and backups.

---

# Daily S3 CLI Checklist

Before working with Amazon S3:

- Verify AWS account.
- Verify Region.
- Verify bucket name.
- Check Versioning.
- Confirm encryption.
- Run `--dryrun` before destructive operations.
- Verify uploads after deployment.

---

# Senior Engineer Tips

Experienced engineers typically:

- Use `sync` instead of repeated `cp` commands.
- Enable Versioning for production buckets.
- Encrypt all sensitive data.
- Enable Block Public Access.
- Prefer IAM Roles over IAM Users.
- Use Lifecycle Rules to optimize costs.
- Verify the active AWS account before making changes.
- Test deployments using `--dryrun`.
- Review CloudTrail logs for security investigations.
- Follow the Principle of Least Privilege.

---

# Quick Reference

| Task | Command |
|------|---------|
| List Buckets | `aws s3 ls` |
| Create Bucket | `aws s3 mb` |
| Delete Bucket | `aws s3 rb` |
| Upload File | `aws s3 cp` |
| Download File | `aws s3 cp` |
| Sync Directory | `aws s3 sync` |
| Delete Object | `aws s3 rm` |
| List Versions | `aws s3api list-object-versions` |
| Enable Versioning | `aws s3api put-bucket-versioning` |
| Check Encryption | `aws s3api get-bucket-encryption` |

---

# Final Thoughts

Amazon S3 is much more than a simple object storage service.

When combined with the AWS CLI, it becomes a powerful platform for:

- Static website hosting
- Backup and recovery
- CI/CD pipelines
- Data archival
- Disaster recovery
- Large-scale file synchronization
- Infrastructure automation

Mastering both the high-level `aws s3` commands and the low-level `aws s3api` operations will allow you to manage Amazon S3 efficiently in real-world production environments.

---
