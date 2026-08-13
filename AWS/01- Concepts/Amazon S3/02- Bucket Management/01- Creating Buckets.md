# Creating Buckets

---

# Introduction

Before storing a single object in Amazon S3, you must first create a bucket. Every object in Amazon S3 belongs to exactly one bucket, making bucket creation the first step in designing any storage architecture.

Although creating a bucket appears simple, the decisions you make during creation—such as Region selection, naming, ownership, and security—have long-term architectural consequences.

---

# Why Buckets Matter

A bucket is more than a container for objects.

It acts as the:

- Security boundary
- Configuration boundary
- Billing boundary
- Lifecycle boundary
- Replication boundary
- Logging boundary

> 💡 **Engineering Insight**
>
> Renaming or moving a bucket later is not supported. Design bucket names and Regions carefully from the beginning.

---

# Bucket Creation Workflow

```text
Choose Region
      │
      ▼
Choose Bucket Name
      │
      ▼
Configure Ownership
      │
      ▼
Configure Block Public Access
      │
      ▼
Configure Versioning
      │
      ▼
Configure Encryption
      │
      ▼
Create Bucket
```

---

# Choosing the AWS Region

When creating a bucket, the first architectural decision is selecting its AWS Region.

Choose a Region based on:

- Application latency
- Data residency requirements
- Disaster recovery strategy
- Compliance
- Cost

Example:

- `ap-south-1` – Mumbai
- `eu-west-1` – Ireland
- `us-east-1` – N. Virginia

> 🏗️ **Production Pattern**
>
> Keep your compute resources (EC2, ECS, Lambda) in the same Region as your bucket whenever possible to minimize latency and inter-Region data transfer costs.

---

# Bucket Name Requirements

Bucket names must:

- Be globally unique
- Contain 3–63 characters
- Use lowercase letters, numbers, and hyphens
- Start and end with a letter or number
- Not contain spaces or underscores

Good examples:

```text
acme-prod-assets
acme-stage-backups
acme-application-logs
```

Poor examples:

```text
MyBucket
bucket_01
test
```

---

# Block Public Access

AWS enables **Block Public Access** by default.

This feature prevents accidental exposure of sensitive data by blocking public ACLs and bucket policies.

Unless your workload explicitly requires public access (for example, a static website), leave this setting enabled.

---

# Object Ownership

Modern Amazon S3 recommends using:

- **Bucket owner enforced**

This disables ACLs and makes the bucket owner the owner of all uploaded objects.

Benefits include:

- Simpler permission management
- Consistent ownership
- Reduced security complexity

---

# Default Encryption

Enable default server-side encryption during bucket creation.

Available options include:

- SSE-S3
- SSE-KMS

For most production workloads, encryption should be enabled by default rather than relying on application developers to specify it for every upload.

---

# Versioning

Consider enabling versioning during bucket creation for:

- Critical business data
- User uploads
- Backups
- Compliance-sensitive workloads

Versioning protects against accidental overwrites and deletions.

---

# Best Practices

- Choose the correct Region.
- Adopt a consistent naming convention.
- Leave Block Public Access enabled unless required.
- Enable default encryption.
- Consider enabling versioning from the beginning.
- Use Infrastructure as Code for repeatable deployments.

---

# Common Mistakes

- Choosing the wrong Region.
- Using generic bucket names.
- Disabling Block Public Access unnecessarily.
- Forgetting to enable encryption.
- Mixing production and development workloads in the same bucket.

---

# Key Takeaways

Creating a bucket is one of the first architectural decisions in an Amazon S3 deployment. Region selection, naming, ownership, security, and encryption all influence the long-term maintainability, security, and scalability of your solution.

In the next chapter, we'll explore **Bucket Naming** and learn how naming strategies affect scalability, governance, automation, and long-term operations.
