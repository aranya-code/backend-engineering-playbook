# Object Management

Objects are the actual data stored inside an Amazon S3 bucket.

Every file uploaded to S3 becomes an object.

An object consists of:

- Object Data
- Object Key (File Name)
- Metadata
- Storage Class
- Version ID (if Versioning is enabled)

Example:

```text
Bucket
│
├── images/logo.png
├── backups/db.sql
├── reports/report.pdf
└── logs/app.log
```

Objects are uniquely identified by their **key** within a bucket.

---

# Understanding Object Keys

An object key is the unique identifier of an object inside a bucket.

Example:

```text
s3://company-backups/database/backup.sql
```

Here:

| Component | Value |
|----------|-------|
| Bucket | company-backups |
| Object Key | database/backup.sql |

Remember:

Amazon S3 does **not** have real folders.

Everything after the bucket name is simply the object's key.

---

# Uploading Files

The most common S3 operation is uploading files.

Syntax:

```bash
aws s3 cp <local-file> <s3-uri>
```

Example:

```bash
aws s3 cp report.pdf \
s3://company-backups/
```

Output:

```text
upload:
./report.pdf
to
s3://company-backups/report.pdf
```

---

# Uploading to a Folder

Although S3 doesn't have real folders, object keys can contain prefixes.

Example:

```bash
aws s3 cp report.pdf \
s3://company-backups/reports/
```

Result:

```text
s3://company-backups/reports/report.pdf
```

---

# Upload Multiple Files

Upload an entire directory recursively.

Example:

```bash
aws s3 cp ./reports \
s3://company-backups/reports \
--recursive
```

AWS uploads every file inside the directory.

---

# Downloading Files

Syntax:

```bash
aws s3 cp <s3-uri> <local-path>
```

Example:

```bash
aws s3 cp \
s3://company-backups/report.pdf \
./
```

Output:

```text
download:
s3://company-backups/report.pdf
to
./report.pdf
```

---

# Download Entire Directories

Example:

```bash
aws s3 cp \
s3://company-backups/reports \
./reports \
--recursive
```

Every object beneath the prefix is downloaded.

---

# Copy Objects Inside S3

Copy one object to another location.

Example:

```bash
aws s3 cp \
s3://company-backups/report.pdf \
s3://company-archive/report.pdf
```

No data passes through your local machine.

The copy happens entirely inside AWS.

---

# Copy Between Buckets

Example:

```bash
aws s3 cp \
s3://company-backups/report.pdf \
s3://production-backups/report.pdf
```

Useful for:

- Disaster recovery
- Migration
- Backup
- Cross-environment promotion

---

# Moving Objects

Move an object:

```bash
aws s3 mv \
s3://company-backups/report.pdf \
s3://company-backups/archive/report.pdf
```

AWS performs:

1. Copy
2. Delete

The original object no longer exists.

---

# Rename Objects

Amazon S3 does not support renaming objects directly.

Instead:

```text
Copy

↓

Delete Original
```

Example:

```bash
aws s3 mv \
s3://company-backups/report.pdf \
s3://company-backups/report-final.pdf
```

---

# Delete Objects

Delete a single object.

```bash
aws s3 rm \
s3://company-backups/report.pdf
```

Output:

```text
delete:
s3://company-backups/report.pdf
```

---

# Delete Multiple Objects

Example:

```bash
aws s3 rm \
s3://company-backups/reports \
--recursive
```

Deletes every object beneath the prefix.

---

# Preview Before Deleting

Always verify recursive deletions.

```bash
aws s3 rm \
s3://company-backups/reports \
--recursive \
--dryrun
```

No objects are removed.

AWS displays what **would** be deleted.

---

# Synchronizing Directories

One of the most useful AWS CLI commands.

Example:

```bash
aws s3 sync \
./website \
s3://company-website
```

AWS compares:

- Local files
- Remote objects

Only changed files are transferred.

---

# Download Using Sync

Example:

```bash
aws s3 sync \
s3://company-backups \
./backups
```

Only new or changed files are downloaded.

---

# Understanding `cp` vs `sync`

| Feature | `cp` | `sync` |
|----------|------|---------|
| Copies single files | ✅ | ❌ |
| Copies directories | ✅ (`--recursive`) | ✅ |
| Compares changes | ❌ | ✅ |
| Transfers only changed files | ❌ | ✅ |
| Best for deployments | ❌ | ✅ |

---

# Deleting Removed Files During Sync

Example:

```bash
aws s3 sync \
./website \
s3://company-website \
--delete
```

Objects removed locally are also removed from S3.

Be careful.

This option can delete production assets.

---

# Preserving Metadata

Upload while specifying metadata.

Example:

```bash
aws s3 cp report.pdf \
s3://company-backups/ \
--metadata Department=Finance,Year=2026
```

Metadata is useful for:

- Automation
- Reporting
- Search
- Governance

---

# Setting Content Type

Example:

```bash
aws s3 cp index.html \
s3://company-website \
--content-type text/html
```

Useful for:

- Static websites
- Images
- CSS
- JavaScript

---

# Common Errors

## NoSuchBucket

```text
NoSuchBucket
```

Verify:

```bash
aws s3 ls
```

---

## AccessDenied

```text
AccessDenied
```

Verify:

```bash
aws sts get-caller-identity
```

Review:

- IAM Policies
- Bucket Policy
- Object Ownership

---

## NoSuchKey

```text
NoSuchKey
```

The specified object key does not exist.

Verify:

```bash
aws s3 ls s3://company-backups
```

---

# Production Tips

Before uploading files:

- Verify bucket name.
- Verify Region.
- Upload to the correct prefix.
- Use `sync` for deployments.
- Use `cp` for individual files.
- Use `--dryrun` before recursive deletion.
- Verify uploads after deployment.

---

# Real-World Workflow

## Deploying a Static Website

```text
Build Website
      │
      ▼
Verify Bucket
      │
      ▼
Sync Files
      │
      ▼
Delete Old Assets
      │
      ▼
Verify Upload
```

Commands:

```bash
aws s3 sync \
./dist \
s3://company-website \
--delete

aws s3 ls \
s3://company-website
```

---

# Architecture Note

Object operations flow through Amazon S3.

```text
Local File
      │
      ▼
AWS CLI
      │
      ▼
Amazon S3
      │
      ▼
Bucket
      │
      ▼
Object
```

Commands such as `cp`, `mv`, `rm`, and `sync` all interact with the same underlying S3 object storage service.

---

# Interview Note

### Question

**When would you use `aws s3 cp` instead of `aws s3 sync`?**

### Answer

Use `aws s3 cp` when copying individual files or performing one-time copy operations. Use `aws s3 sync` when synchronizing directories, deployments, backups, or any scenario where only changed files should be transferred. `sync` is more efficient for repeated operations because it compares the source and destination before copying.

---

# Key Takeaways

- Every file stored in S3 is an object.
- Objects are uniquely identified by their key.
- Use `cp` for individual file operations.
- Use `sync` for directory synchronization.
- Use `mv` to move or effectively rename objects.
- Use `rm` carefully, especially with `--recursive`.
- Use `--dryrun` before performing destructive recursive operations.
- `sync --delete` is powerful but should be used cautiously in production.

---

# Advanced Object Operations

Beyond uploading and downloading files, Amazon S3 provides several advanced capabilities that are commonly used in production environments.

These include:

- Include and Exclude Filters
- Storage Classes
- Server-Side Encryption
- Object Metadata
- Access Control
- Presigned URLs
- Checksums
- Performance Optimization

Mastering these features helps you build secure, efficient, and scalable storage workflows.

---

# Using Include and Exclude Filters

When copying or synchronizing directories, you often don't want to transfer every file.

AWS CLI allows filtering using:

- `--exclude`
- `--include`

---

# Exclude Files

Example:

```bash
aws s3 cp ./website \
s3://company-website \
--recursive \
--exclude "*.log"
```

Result:

All files are uploaded except:

```text
*.log
```

---

# Include Specific Files

Example:

```bash
aws s3 cp ./website \
s3://company-website \
--recursive \
--exclude "*" \
--include "*.html"
```

Only HTML files are uploaded.

---

# Upload Only Images

```bash
aws s3 sync ./images \
s3://company-images \
--exclude "*" \
--include "*.jpg" \
--include "*.png"
```

Only image files are transferred.

---

# Understanding Filter Order

AWS CLI processes filters in order.

Example:

```bash
--exclude "*"
--include "*.pdf"
```

Meaning:

```
Exclude Everything

↓

Include PDF Files
```

If the order is reversed, the result may differ.

Always verify filter order.

---

# Storage Classes

Every S3 object belongs to a Storage Class.

Storage Classes optimize cost and performance.

Common classes include:

| Storage Class | Use Case |
|---------------|----------|
| STANDARD | Frequently accessed data |
| STANDARD_IA | Infrequently accessed data |
| ONEZONE_IA | Infrequently accessed, single AZ |
| INTELLIGENT_TIERING | Automatic optimization |
| GLACIER_IR | Instant archive retrieval |
| GLACIER | Long-term archival |
| DEEP_ARCHIVE | Lowest-cost archival |

---

# Upload with a Storage Class

Example:

```bash
aws s3 cp backup.zip \
s3://company-backups \
--storage-class STANDARD_IA
```

Suitable for backups that are accessed occasionally.

---

# Intelligent Tiering

Example:

```bash
aws s3 cp logs.zip \
s3://company-logs \
--storage-class INTELLIGENT_TIERING
```

Amazon S3 automatically moves objects between access tiers based on usage patterns.

---

# Server-Side Encryption (SSE)

Encrypt objects while uploading.

---

## SSE-S3 (AWS Managed Keys)

```bash
aws s3 cp report.pdf \
s3://company-backups \
--sse AES256
```

AWS manages the encryption keys.

---

## SSE-KMS

Example:

```bash
aws s3 cp report.pdf \
s3://company-backups \
--sse aws:kms
```

Use a specific KMS key:

```bash
aws s3 cp report.pdf \
s3://company-backups \
--sse aws:kms \
--sse-kms-key-id alias/company-key
```

SSE-KMS provides:

- Better auditing
- Key rotation
- Access control
- Compliance support

---

# Viewing Object Metadata

Retrieve metadata for an object.

```bash
aws s3api head-object \
--bucket company-backups \
--key report.pdf
```

Example output:

```json
{
    "ContentLength": 24893,
    "ContentType": "application/pdf",
    "LastModified": "...",
    "StorageClass": "STANDARD"
}
```

Useful when troubleshooting uploads.

---

# Uploading Custom Metadata

Example:

```bash
aws s3 cp report.pdf \
s3://company-backups \
--metadata Department=Finance,Owner=Backend
```

Applications can later read this metadata.

---

# Setting Cache Control

Useful for websites.

Example:

```bash
aws s3 cp logo.png \
s3://company-website \
--cache-control max-age=86400
```

Improves browser caching.

---

# Setting Content Type

Example:

```bash
aws s3 cp index.html \
s3://company-website \
--content-type text/html
```

Without the correct content type, browsers may not render files correctly.

---

# Creating a Presigned URL

Generate a temporary download URL.

Example:

```bash
aws s3 presign \
s3://company-backups/report.pdf
```

Default expiration:

```
3600 seconds
```

---

## Custom Expiration

Example:

```bash
aws s3 presign \
s3://company-backups/report.pdf \
--expires-in 7200
```

The URL remains valid for:

```
2 hours
```

Presigned URLs allow temporary access without making the object public.

---

# Verify Object Integrity

When uploading important files, checksum validation helps detect corruption.

Retrieve object attributes:

```bash
aws s3api head-object \
--bucket company-backups \
--key report.pdf
```

Review checksum-related fields if checksum validation is enabled.

---

# Performance Optimization

Large uploads can be optimized using multipart uploads.

AWS CLI automatically performs multipart uploads for large files.

Advantages:

- Faster uploads
- Retry failed parts
- Improved reliability
- Parallel transfers

No additional configuration is required for most workloads.

---

# Copy Objects Between Regions

Example:

```bash
aws s3 cp \
s3://india-backups/report.pdf \
s3://us-backups/report.pdf
```

Useful for:

- Disaster Recovery
- Multi-region replication
- Migration
- Backup

---

# Common Errors

## Invalid Storage Class

```text
InvalidStorageClass
```

Verify:

```bash
--storage-class
```

uses a valid value.

---

## KMS AccessDenied

Example:

```text
AccessDenied
```

Possible causes:

- Missing KMS permissions
- Incorrect KMS Key
- Key Policy restrictions

Review IAM and KMS policies.

---

## Invalid Metadata

Metadata values must follow AWS requirements.

Avoid unsupported characters.

---

# Production Tips

For production uploads:

- Use encryption.
- Specify Content-Type.
- Configure Cache-Control for web assets.
- Use Intelligent Tiering where appropriate.
- Use metadata consistently.
- Prefer KMS encryption for sensitive information.
- Generate Presigned URLs instead of making objects public.

---

# Real-World Workflow

## Secure File Upload

```text
Verify Bucket
      │
      ▼
Choose Storage Class
      │
      ▼
Enable Encryption
      │
      ▼
Upload File
      │
      ▼
Verify Metadata
      │
      ▼
Generate Presigned URL
```

Example:

```bash
aws s3 cp report.pdf \
s3://company-backups \
--storage-class STANDARD_IA \
--sse aws:kms \
--metadata Department=Finance
```

---

# Architecture Note

Advanced object uploads involve multiple S3 features.

```text
Local File
      │
      ▼
AWS CLI
      │
      ▼
Encryption
      │
      ▼
Metadata
      │
      ▼
Storage Class
      │
      ▼
Amazon S3
```

Each feature contributes to security, performance, or cost optimization.

---

# Interview Note

### Question

**When would you use `STANDARD_IA` instead of `STANDARD`?**

### Answer

`STANDARD_IA` (Infrequent Access) is suitable for data that is accessed occasionally but still requires rapid retrieval, such as backups, compliance documents, or monthly reports. It offers lower storage costs than `STANDARD` but charges retrieval fees, making it less suitable for frequently accessed objects.

---

# Key Takeaways

- Use `--include` and `--exclude` to control uploads.
- Choose the appropriate Storage Class based on access patterns.
- Encrypt sensitive data using SSE-S3 or SSE-KMS.
- Set metadata and Content-Type during upload.
- Use Presigned URLs for temporary object sharing.
- AWS CLI automatically optimizes large uploads using multipart transfers.
- Configure uploads with security, performance, and cost in mind.

---

