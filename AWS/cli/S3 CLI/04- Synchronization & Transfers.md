# Synchronization & Large-Scale Data Transfers

Synchronization is one of the most powerful capabilities provided by the AWS CLI.

Unlike the `cp` command, which blindly copies files, `sync` compares the source and destination before transferring data.

This makes it ideal for:

- Static website deployments
- Daily backups
- CI/CD pipelines
- Disaster recovery
- Data migration
- Large file transfers

For production workloads, `sync` is almost always preferred over repeatedly using `cp`.

---

# Understanding `sync`

General syntax:

```bash
aws s3 sync <source> <destination>
```

The source and destination can be:

- Local → S3
- S3 → Local
- S3 → S3

Unlike `cp`, `sync` copies only files that have changed.

---

# Local to S3

Example:

```bash
aws s3 sync ./website \
s3://company-website
```

AWS compares:

- Local files
- Existing S3 objects

Only changed files are uploaded.

---

# S3 to Local

Download an entire bucket.

```bash
aws s3 sync \
s3://company-backups \
./backups
```

Only missing or updated files are downloaded.

---

# Bucket to Bucket Synchronization

Synchronize objects between two buckets.

```bash
aws s3 sync \
s3://production-assets \
s3://backup-assets
```

This operation occurs entirely within AWS.

Common use cases:

- Disaster Recovery
- Cross-environment promotion
- Backup
- Migration

---

# How `sync` Detects Changes

AWS CLI compares:

- File size
- Last modified timestamp

If either differs, the object is transferred.

Example:

```text
Local File

↓

Different Size

↓

Upload
```

or

```text
Same Size

↓

Different Timestamp

↓

Upload
```

---

# Exact Timestamp Matching

Download while preserving timestamps.

```bash
aws s3 sync \
s3://company-backups \
./backups \
--exact-timestamps
```

This reduces unnecessary downloads when timestamps matter.

---

# Deleting Removed Files

One of the most useful—and dangerous—options.

```bash
aws s3 sync \
./website \
s3://company-website \
--delete
```

AWS removes objects that:

- Exist in S3
- No longer exist locally

Result:

The bucket becomes an exact mirror of the local directory.

---

# Always Preview First

Before using:

```bash
--delete
```

Run:

```bash
aws s3 sync \
./website \
s3://company-website \
--delete \
--dryrun
```

AWS displays:

```text
(dryrun) upload:

(dryrun) delete:
```

Nothing is transferred.

---

# Excluding Files

Ignore log files.

```bash
aws s3 sync \
./website \
s3://company-website \
--exclude "*.log"
```

---

# Include Specific Files

Upload only HTML files.

```bash
aws s3 sync \
./website \
s3://company-website \
--exclude "*" \
--include "*.html"
```

---

# Synchronize Images Only

```bash
aws s3 sync \
./assets \
s3://company-assets \
--exclude "*" \
--include "*.png" \
--include "*.jpg"
```

---

# Preserve ACLs

Example:

```bash
aws s3 sync \
./website \
s3://company-website \
--acl private
```

Possible ACL values include:

- private
- public-read
- authenticated-read

**Note:** Modern AWS environments typically disable ACLs using **Bucket Owner Enforced** object ownership. Prefer bucket policies and IAM policies over ACLs.

---

# Synchronize with Encryption

Example:

```bash
aws s3 sync \
./backups \
s3://company-backups \
--sse AES256
```

Using KMS:

```bash
aws s3 sync \
./backups \
s3://company-backups \
--sse aws:kms
```

---

# Synchronize with Storage Class

Example:

```bash
aws s3 sync \
./archive \
s3://company-archive \
--storage-class GLACIER_IR
```

Useful for archival workloads.

---

# Controlling Symbolic Links

By default:

AWS CLI follows symbolic links.

Disable this behavior:

```bash
aws s3 sync \
./website \
s3://company-website \
--no-follow-symlinks
```

Useful when symbolic links should not be uploaded.

---

# Large File Transfers

AWS CLI automatically performs multipart uploads for large files.

Benefits:

- Parallel uploads
- Better throughput
- Automatic retry
- Resume failed parts

No additional configuration is required.

---

# Performance Optimization

When synchronizing large datasets:

- Upload from the nearest Region.
- Avoid unnecessary transfers.
- Use include/exclude filters.
- Compress files when appropriate.
- Schedule transfers during low-traffic periods.
- Use `sync` instead of repeated `cp` commands.

---

# Cost Considerations

Every synchronization may incur:

- PUT requests
- GET requests
- Data transfer charges
- Storage costs

Using `sync` minimizes unnecessary uploads, reducing request costs.

For cross-region transfers, remember that data transfer charges may apply.

---

# Common Errors

## AccessDenied

```text
AccessDenied
```

Verify:

```bash
aws sts get-caller-identity
```

Review:

- IAM Policy
- Bucket Policy
- KMS Permissions

---

## NoSuchBucket

```text
NoSuchBucket
```

Verify bucket existence:

```bash
aws s3 ls
```

---

## Slow Transfers

Possible causes:

- Network bandwidth
- Cross-region transfers
- Large numbers of small files
- High network latency

Consider running transfers closer to the target Region.

---

# Production Deployment Workflow

Deploying a frontend application.

```text
Build Application
        │
        ▼
Run Tests
        │
        ▼
Verify AWS Account
        │
        ▼
Dry Run
        │
        ▼
Sync Files
        │
        ▼
Delete Old Assets
        │
        ▼
Verify Deployment
```

Commands:

```bash
aws sts get-caller-identity

aws s3 sync \
./dist \
s3://company-website \
--delete \
--dryrun

aws s3 sync \
./dist \
s3://company-website \
--delete
```

---

# Backup Workflow

Daily backup process.

```text
Database Backup
        │
        ▼
Compress Files
        │
        ▼
Upload
        │
        ▼
Verify Upload
```

Commands:

```bash
tar -czf backup.tar.gz database/

aws s3 sync \
./backups \
s3://daily-backups
```

---

# Production Tips

- Prefer `sync` over repeated `cp` commands.
- Always perform a `--dryrun` before using `--delete`.
- Use encryption for sensitive data.
- Use storage classes appropriate to the access pattern.
- Verify uploads after deployment.
- Avoid unnecessary synchronization to reduce request costs.
- Log synchronization results in automation pipelines.

---

# Architecture Note

Synchronization compares the desired state with the current state.

```text
Local Directory
        │
        ▼
AWS CLI Sync Engine
        │
Compare Objects
        │
        ▼
Transfer Differences
        │
        ▼
Amazon S3
```

Only changed objects are transferred, making `sync` efficient for repeated operations.

---

# Interview Note

### Question

**What is the difference between `aws s3 cp` and `aws s3 sync`?**

### Answer

`aws s3 cp` copies files without comparing the source and destination, making it suitable for one-time transfers or individual files. `aws s3 sync` compares file size and timestamps, transferring only new or modified files. It also supports options such as `--delete`, making it ideal for deployments, backups, and directory synchronization.

---

# Key Takeaways

- `sync` compares source and destination before transferring data.
- Synchronization works between local systems and S3, as well as between S3 buckets.
- Use `--delete` carefully and always test with `--dryrun`.
- Include and exclude filters help reduce unnecessary transfers.
- AWS CLI automatically optimizes large file transfers with multipart uploads.
- `sync` is the preferred command for deployments, backups, and large-scale data movement.

---

