# Troubleshooting & Best Practices

> Learn how to troubleshoot common Amazon S3 CLI issues, understand why operations fail, and follow production-ready best practices for secure, reliable, and efficient S3 management.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Troubleshoot common S3 CLI errors.
- Diagnose authentication and authorization failures.
- Resolve bucket and object access issues.
- Troubleshoot upload and synchronization problems.
- Optimize S3 CLI performance.
- Follow production best practices.
- Build reliable operational workflows.

---

# Why Troubleshooting Matters

Amazon S3 is one of the most reliable AWS services.

Most failures are **not** caused by S3 itself.

Instead, they are usually caused by:

- Incorrect credentials
- Wrong AWS account
- Wrong Region
- Missing IAM permissions
- Bucket Policies
- KMS permissions
- Typographical errors
- Network connectivity

Understanding where failures occur dramatically reduces troubleshooting time.

---

# S3 Troubleshooting Workflow

Whenever an S3 command fails, follow this sequence:

```text
AWS CLI Installed?
        │
        ▼
Correct AWS Account?
        │
        ▼
Correct Region?
        │
        ▼
Bucket Exists?
        │
        ▼
IAM Permissions?
        │
        ▼
Bucket Policy?
        │
        ▼
Encryption?
        │
        ▼
Retry with --debug
```

This structured approach prevents unnecessary changes.

---

# Verify Your Environment

Before troubleshooting S3:

```bash
aws --version

aws sts get-caller-identity

aws configure list

aws configure get region
```

These commands verify:

- AWS CLI installation
- Active AWS account
- IAM identity
- Region
- Credentials

---

# Error: Unable to Locate Credentials

Example:

```text
Unable to locate credentials
```

Cause:

AWS CLI cannot find valid credentials.

Verify:

```bash
aws configure list
```

If using IAM Identity Center:

```bash
aws sso login
```

---

# Error: AccessDenied

Example:

```text
AccessDenied
```

Authentication succeeded.

Authorization failed.

Possible causes:

- Missing IAM permission
- Bucket Policy
- Object Ownership
- KMS permissions
- Service Control Policy (SCP)

Always verify identity first:

```bash
aws sts get-caller-identity
```

---

# Error: NoSuchBucket

Example:

```text
NoSuchBucket
```

Possible causes:

- Incorrect bucket name
- Bucket deleted
- Wrong AWS account
- Typographical error

Verify:

```bash
aws s3 ls
```

---

# Error: BucketAlreadyExists

Example:

```text
BucketAlreadyExists
```

Cause:

Bucket names are globally unique.

Solution:

Choose another bucket name.

Example:

```text
company-backups

↓

company-backups-prod-2026
```

---

# Error: BucketAlreadyOwnedByYou

Example:

```text
BucketAlreadyOwnedByYou
```

Cause:

The bucket already exists in your AWS account.

Verify:

```bash
aws s3 ls
```

---

# Error: BucketNotEmpty

Example:

```text
BucketNotEmpty
```

Cause:

Objects still exist inside the bucket.

Verify:

```bash
aws s3 ls s3://company-backups \
--recursive
```

If Versioning is enabled:

```bash
aws s3api list-object-versions \
--bucket company-backups
```

---

# Error: NoSuchKey

Example:

```text
NoSuchKey
```

Cause:

The specified object key does not exist.

Verify:

```bash
aws s3 ls \
s3://company-backups
```

Remember:

Object keys are case-sensitive.

---

# Error: InvalidAccessKeyId

Example:

```text
InvalidAccessKeyId
```

Possible causes:

- Incorrect Access Key
- Deleted IAM User
- Disabled Access Key

Verify:

```bash
aws configure list
```

---

# Error: SignatureDoesNotMatch

Example:

```text
SignatureDoesNotMatch
```

Possible causes:

- Incorrect Secret Access Key
- Wrong Region
- System clock drift

Verify:

```bash
aws configure get region
```

Synchronize your system clock if necessary.

---

# Error: ExpiredToken

Example:

```text
ExpiredToken
```

Cause:

Temporary credentials expired.

Solution:

```bash
aws sso login
```

or assume the role again.

---

# Error: KMS AccessDenied

Occurs during upload or download of encrypted objects.

Verify:

- IAM Policy
- KMS Key Policy
- Key Grants

Ensure the IAM identity has permission to use the KMS key.

---

# Slow Upload Performance

Possible causes:

- Cross-region upload
- Slow internet connection
- Large number of small files
- High network latency

Recommendations:

- Upload from the nearest AWS Region.
- Use `sync` instead of repeated `cp`.
- Compress files where appropriate.
- Avoid unnecessary uploads.

---

# Multipart Upload Issues

Large uploads use multipart upload automatically.

Problems may occur if:

- Network interruptions happen.
- Uploads are cancelled.
- Multipart uploads remain incomplete.

List multipart uploads:

```bash
aws s3api list-multipart-uploads \
--bucket company-backups
```

Abort an upload:

```bash
aws s3api abort-multipart-upload \
--bucket company-backups \
--key backup.zip \
--upload-id <UPLOAD_ID>
```

---

# Debugging with AWS CLI

Enable debug logging:

```bash
aws s3 ls --debug
```

The output includes:

- Credential Provider Chain
- Endpoint resolution
- Request signing
- HTTP request
- HTTP response
- Retry attempts

This is often the fastest way to identify the root cause.

---

# Production Troubleshooting Checklist

Before changing permissions:

- □ Verify AWS account.
- □ Verify Region.
- □ Verify bucket name.
- □ Verify object key.
- □ Verify IAM permissions.
- □ Review Bucket Policy.
- □ Review KMS permissions.
- □ Retry using `--debug`.

Avoid making configuration changes until the actual cause is identified.

---

# S3 Best Practices

## Use Meaningful Bucket Names

Instead of:

```text
files
```

Prefer:

```text
company-prod-backups
```

---

## Enable Versioning

Protect against:

- Accidental deletion
- Accidental overwrite

Recommended for production buckets.

---

## Enable Encryption

Use:

- SSE-S3
- SSE-KMS

Never store sensitive production data without encryption.

---

## Enable Block Public Access

Unless public access is explicitly required:

```text
Enable Block Public Access
```

for every production bucket.

---

## Prefer IAM Roles

Avoid long-term Access Keys.

Recommended:

- IAM Roles
- IAM Identity Center
- Temporary credentials

---

## Verify Before Deleting

Before executing:

```bash
aws s3 rb \
--force
```

Always verify:

- Bucket
- Region
- Account
- Versioning

---

## Use Lifecycle Rules

Reduce storage costs by:

- Transitioning old objects
- Archiving backups
- Deleting temporary files

Automation is more reliable than manual cleanup.

---

## Use Sync for Deployments

Prefer:

```bash
aws s3 sync
```

instead of repeatedly using:

```bash
aws s3 cp
```

Synchronization transfers only changed files.

---

# Real-World Workflow

## Recovering From an Upload Failure

```text
Upload Failed
      │
      ▼
Verify Identity
      │
      ▼
Verify Bucket
      │
      ▼
Verify Region
      │
      ▼
Verify Permissions
      │
      ▼
Retry with --debug
      │
      ▼
Verify Upload
```

A structured approach prevents unnecessary troubleshooting.

---

# Production Deployment Checklist

Before deployment:

- Verify AWS account.
- Verify Region.
- Verify bucket.
- Run `sync --dryrun`.
- Enable logging.
- Monitor upload.
- Verify deployed files.

After deployment:

- Verify website.
- Verify object count.
- Verify permissions.
- Review CloudTrail if required.

---

# Architecture Note

An S3 request passes through multiple authorization layers.

```text
AWS CLI
      │
      ▼
Authentication
      │
      ▼
IAM Policy
      │
      ▼
Bucket Policy
      │
      ▼
Block Public Access
      │
      ▼
Object Ownership
      │
      ▼
KMS Permissions
      │
      ▼
Amazon S3
```

Failures can occur at any layer.

---

# Interview Note

### Question

**How would you troubleshoot an `AccessDenied` error while uploading an object to Amazon S3?**

### Answer

I first verify the active AWS identity using `aws sts get-caller-identity`, then confirm the correct Region and bucket. Next, I review the IAM policy attached to the user or role, followed by the bucket policy and Block Public Access settings. If the bucket uses SSE-KMS, I verify that the identity has permission to use the KMS key. Finally, I rerun the command with `--debug` to inspect the request and identify the exact failure point.

---

# Key Takeaways

- Most S3 issues are caused by configuration rather than service failures.
- Always verify your identity, Region, and bucket before troubleshooting.
- Use `--debug` for detailed diagnostics.
- Enable Versioning, Encryption, and Block Public Access in production.
- Prefer `sync` for deployments and backups.
- Follow structured troubleshooting workflows instead of making random configuration changes.

---
