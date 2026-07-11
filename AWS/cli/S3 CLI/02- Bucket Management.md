# Bucket Management

Amazon S3 stores data inside **buckets**.

A bucket is the highest-level container in Amazon S3.

Every object must belong to exactly one bucket.

Think of it like this:

```text
AWS Account
      │
      ▼
 Bucket
      │
      ├── Object 1
      ├── Object 2
      ├── Object 3
      └── ...
```

Before uploading files, you must create a bucket.

---

# Bucket Naming Rules

Bucket names are globally unique across all AWS accounts.

For example, if another AWS customer owns:

```
company-backups
```

You cannot create another bucket with the same name.

---

## Naming Requirements

Bucket names must:

- Be between **3 and 63 characters**
- Contain only lowercase letters
- Contain numbers
- Use hyphens (`-`)
- Not contain spaces
- Not contain uppercase letters
- Not resemble an IP address

---

## Valid Bucket Names

```text
company-backups

frontend-assets

logs-2026

images-prod

my-app-storage
```

---

## Invalid Bucket Names

```text
MyBucket
```

Reason:

Contains uppercase letters.

---

```text
my bucket
```

Reason:

Contains spaces.

---

```text
192.168.1.10
```

Reason:

Looks like an IP address.

---

```text
ab
```

Reason:

Less than three characters.

---

# Best Practices for Naming

Instead of:

```text
images
```

Prefer:

```text
company-images-production
```

or

```text
acme-backend-logs
```

Descriptive names make large AWS environments easier to manage.

---

# Creating a Bucket

High-level command:

```bash
aws s3 mb s3://company-backups
```

`mb` stands for:

```
Make Bucket
```

Example output:

```text
make_bucket: company-backups
```

---

# Creating a Bucket in a Specific Region

Example:

```bash
aws s3 mb s3://company-backups \
    --region ap-south-1
```

Always specify the Region in production automation.

---

# Creating a Bucket Using `s3api`

Low-level API command:

```bash
aws s3api create-bucket \
    --bucket company-backups \
    --region ap-south-1 \
    --create-bucket-configuration \
    LocationConstraint=ap-south-1
```

Notice that `s3api` requires more parameters because it maps directly to the underlying API.

---

# Why Does `us-east-1` Behave Differently?

The **US East (N. Virginia)** Region (`us-east-1`) is special.

When creating a bucket in this Region, you **must not** specify a `LocationConstraint`.

Correct:

```bash
aws s3api create-bucket \
    --bucket company-backups \
    --region us-east-1
```

Incorrect:

```bash
LocationConstraint=us-east-1
```

This often surprises engineers who are new to the S3 API.

---

# Listing Buckets

List every bucket in your AWS account:

```bash
aws s3 ls
```

Example output:

```text
2026-01-12 09:10:45 company-backups

2026-03-18 14:22:11 frontend-assets

2026-05-02 16:30:07 application-logs
```

---

# Listing Buckets Using `s3api`

```bash
aws s3api list-buckets
```

Example output:

```json
{
    "Buckets": [
        {
            "Name": "company-backups"
        },
        {
            "Name": "frontend-assets"
        }
    ]
}
```

Unlike `aws s3`, the `s3api` command returns structured JSON, making it easier to use in automation.

---

# Finding a Bucket's Region

Determine where a bucket is located:

```bash
aws s3api get-bucket-location \
    --bucket company-backups
```

Example output:

```json
{
    "LocationConstraint": "ap-south-1"
}
```

Knowing the bucket's Region is useful when troubleshooting latency, permissions, or cross-region operations.

---

# Checking if a Bucket Exists

List the bucket:

```bash
aws s3 ls s3://company-backups
```

If the bucket exists and you have permission, AWS returns its contents.

If it does not exist—or you do not have access—an error is returned.

---

# Bucket Ownership

Retrieve bucket ownership information:

```bash
aws s3api get-bucket-ownership-controls \
    --bucket company-backups
```

This command is useful when reviewing modern S3 ownership settings, especially in environments where ACLs have been disabled.

---

# Viewing Bucket Metadata

Retrieve general information about a bucket:

```bash
aws s3api head-bucket \
    --bucket company-backups
```

If the bucket exists and is accessible, the command returns a successful response with no body.

This command is commonly used by automation to verify bucket existence.

---

# Production Tip

Before creating a bucket:

- Verify the correct AWS account.
- Choose the appropriate Region.
- Select a globally unique name.
- Follow your organization's naming convention.
- Avoid generic names such as:

```text
backup

images

files

logs
```

Descriptive bucket names improve maintainability across multiple AWS accounts and environments.

---

# Architecture Note

Every S3 bucket belongs to a single AWS Region.

```text
AWS Account
      │
      ▼
Bucket (Region)
      │
      ├── Object
      ├── Object
      └── Object
```

Although bucket names are globally unique, the bucket's data resides in a specific Region.

---

# Interview Note

### Question

**Why are S3 bucket names globally unique?**

**Answer**

Amazon S3 uses a global namespace for bucket names because bucket names are incorporated into service endpoints (for example, `https://my-bucket.s3.amazonaws.com`). This design ensures that every bucket name uniquely identifies a single bucket across all AWS accounts worldwide.

---

# Key Takeaways

- Buckets are the top-level containers in Amazon S3.
- Bucket names must be globally unique.
- Use `aws s3 mb` for simple bucket creation.
- Use `aws s3api create-bucket` for API-level control.
- Always specify the Region in production.
- Remember the special behavior of `us-east-1`.
- Verify bucket existence and location before using it.

---

# Deleting & Managing Buckets

Managing S3 buckets involves more than creating them.

As your infrastructure evolves, you may need to:

- Delete unused buckets
- Empty bucket contents
- Verify bucket configuration
- Handle versioned buckets
- Troubleshoot deletion failures

Deleting buckets requires special care because Amazon S3 protects buckets that still contain objects.

---

# Removing an Empty Bucket

High-level command:

```bash
aws s3 rb s3://company-backups
```

`rb` stands for:

```
Remove Bucket
```

If the bucket is empty, the output is similar to:

```text
remove_bucket: company-backups
```

---

# Why Can't Most Buckets Be Deleted?

A bucket can only be deleted if it contains:

- No objects
- No object versions
- No delete markers

If any data exists, AWS prevents deletion.

Example error:

```text
remove_bucket failed:
BucketNotEmpty
```

This safety mechanism helps prevent accidental data loss.

---

# Force Delete a Bucket

To remove both the bucket and all of its objects:

```bash
aws s3 rb s3://company-backups \
    --force
```

AWS CLI performs two operations:

1. Deletes every object.
2. Deletes the bucket.

---

## Important Warning

```text
--force permanently deletes data.
```

There is no recycle bin.

If Versioning is disabled, the deleted objects cannot be recovered.

Always verify the bucket before using `--force`.

---

# Empty a Bucket Without Deleting It

Sometimes you want to keep the bucket but remove all objects.

Example:

```bash
aws s3 rm s3://company-backups \
    --recursive
```

This removes every object while leaving the bucket itself intact.

---

# Delete a Specific Object

Delete a single object:

```bash
aws s3 rm s3://company-backups/report.pdf
```

Output:

```text
delete: s3://company-backups/report.pdf
```

---

# Delete Objects by Prefix

Delete all objects under a logical folder:

```bash
aws s3 rm s3://company-backups/logs/ \
    --recursive
```

Only objects with the specified prefix are removed.

---

# Dry Run Before Deletion

Always preview large deletions first.

Example:

```bash
aws s3 rm s3://company-backups \
    --recursive \
    --dryrun
```

Output:

```text
(dryrun) delete:
s3://company-backups/logs/app.log
```

No objects are deleted.

This is strongly recommended before executing destructive commands.

---

# Using `s3api` to Delete a Bucket

Low-level API command:

```bash
aws s3api delete-bucket \
    --bucket company-backups
```

The bucket must already be empty.

Unlike `aws s3 rb`, `s3api` does not provide a `--force` option.

---

# Versioned Buckets

Deleting objects from a versioned bucket is more complex.

A versioned bucket may contain:

- Current object versions
- Previous object versions
- Delete markers

Even after removing visible objects, the bucket may still contain older versions.

As a result:

```text
BucketNotEmpty
```

may still occur.

---

# Viewing Bucket Versioning

Check whether versioning is enabled:

```bash
aws s3api get-bucket-versioning \
    --bucket company-backups
```

Example output:

```json
{
    "Status": "Enabled"
}
```

Possible values:

- Enabled
- Suspended
- Not configured

---

# Listing Object Versions

View every object version:

```bash
aws s3api list-object-versions \
    --bucket company-backups
```

This command displays:

- Object Versions
- Version IDs
- Delete Markers

Useful when troubleshooting bucket deletion.

---

# Common Bucket Deletion Errors

## BucketNotEmpty

Example:

```text
BucketNotEmpty
```

Cause:

Objects or versions still exist.

Solution:

- Remove objects.
- Remove object versions.
- Remove delete markers.
- Retry deletion.

---

## AccessDenied

Example:

```text
AccessDenied
```

Possible causes:

- Missing IAM permission
- Bucket policy restriction
- SCP restriction
- Cross-account ownership

Verify:

```bash
aws sts get-caller-identity
```

Review IAM permissions before retrying.

---

## NoSuchBucket

Example:

```text
NoSuchBucket
```

Possible causes:

- Incorrect bucket name
- Wrong AWS account
- Bucket already deleted

Verify:

```bash
aws s3 ls
```

---

# Safe Deletion Workflow

Before deleting a bucket:

```text
Verify AWS Account
        │
        ▼
Verify Bucket Name
        │
        ▼
List Bucket Contents
        │
        ▼
Run Dry Run
        │
        ▼
Delete Objects
        │
        ▼
Delete Bucket
```

Avoid skipping verification steps.

---

# Production Tips

Before using:

```bash
aws s3 rb --force
```

Always:

- Verify the active AWS account.
- Confirm the bucket name.
- Check for Versioning.
- Review backup requirements.
- Ensure no applications are using the bucket.
- Notify affected teams if appropriate.

Deleting a production bucket without verification can cause application outages and permanent data loss.

---

# Real-World Workflow

## Scenario

A project has been retired, and its S3 bucket needs to be removed safely.

Recommended workflow:

```text
Verify Identity
        │
        ▼
Verify Bucket
        │
        ▼
Review Versioning
        │
        ▼
List Objects
        │
        ▼
Run Dry Run
        │
        ▼
Delete Objects
        │
        ▼
Delete Bucket
        │
        ▼
Verify Removal
```

This process minimizes the risk of deleting the wrong bucket.

---

# Architecture Note

Bucket deletion follows a strict dependency order.

```text
Bucket
      │
      ▼
Objects
      │
      ▼
Object Versions
      │
      ▼
Delete Markers
      │
      ▼
Bucket Deletion
```

Amazon S3 will not delete a bucket until all dependent resources have been removed.

---

# Interview Note

### Question

**Why does `aws s3 rb --force` sometimes fail on a versioned bucket?**

### Answer

The `--force` option removes current objects, but a versioned bucket may still contain previous object versions and delete markers. Amazon S3 considers these part of the bucket's contents, so the bucket cannot be deleted until all versions and delete markers are removed.

---

# Key Takeaways

- Buckets must be empty before deletion.
- Use `aws s3 rb` to remove empty buckets.
- Use `--force` carefully, as it permanently deletes objects.
- Use `--dryrun` before large deletion operations.
- Versioned buckets require additional cleanup.
- Always verify the AWS account and bucket before deleting resources.

---
