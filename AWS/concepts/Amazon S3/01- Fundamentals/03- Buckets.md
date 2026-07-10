# Buckets

---

# Introduction

A bucket is the highest-level logical container in Amazon S3. Every object stored in Amazon S3 must reside inside a bucket.

Unlike traditional file systems where files are organized into drives and folders, Amazon S3 organizes data using buckets and object keys. Buckets provide the namespace, configuration boundary, and security boundary for stored objects.

Think of a bucket as a globally unique container that holds related objects and defines how those objects are managed.

---

# Why Do Buckets Exist?

Buckets solve several important engineering problems:

- Provide logical isolation between datasets.
- Act as the security boundary for IAM and bucket policies.
- Store configuration such as versioning, encryption, lifecycle rules, and replication.
- Enable billing, logging, and monitoring at a logical level.

Without buckets, managing billions of objects with different security and lifecycle requirements would be impractical.

> 💡 **Engineering Insight**
>
> In production, bucket design is an architectural decision. A poorly designed bucket strategy becomes difficult to change later.

---

# Bucket Characteristics

Every bucket has the following characteristics:

- Globally unique name
- Created in a specific AWS Region
- Can store virtually unlimited objects
- Supports bucket-level configuration
- Cannot exist inside another bucket

Although a bucket is created in one Region, AWS automatically replicates data across multiple Availability Zones within that Region for durability.

---

# Global Bucket Namespace

Bucket names must be globally unique across all AWS accounts.

For example:

```text
company-images
```

If another AWS customer has already created that bucket, the name cannot be reused.

Common naming strategies include:

```text
acme-prod-images
acme-dev-backups
mycompany-logs-us-east-1
```

Avoid generic names because they are often unavailable.

---

# Bucket-Level Configuration

Many Amazon S3 features are configured at the bucket level:

- Versioning
- Default encryption
- Lifecycle rules
- Replication
- Event notifications
- Access logging
- Bucket policies
- Public access settings

Objects inherit the bucket's configuration unless explicitly overridden by supported features.

---

# Production Design Considerations

When designing buckets, consider:

- Environment separation (dev, test, prod)
- Application ownership
- Compliance requirements
- Data residency
- Access patterns
- Lifecycle policies

Example:

```text
acme-dev-assets
acme-stage-assets
acme-prod-assets
acme-audit-logs
acme-backups
```

Avoid putting unrelated workloads into a single bucket simply because it is convenient.

> 🏗️ **Production Pattern**
>
> Organize buckets around security boundaries and lifecycle requirements rather than around teams or projects alone.

---

# Common Mistakes

- Using one bucket for every application.
- Making bucket names environment-agnostic.
- Mixing production and development data.
- Ignoring bucket-level encryption.
- Using public buckets when presigned URLs are sufficient.

---

# Best Practices

- Enable Block Public Access by default.
- Enable versioning for important workloads.
- Enable default encryption.
- Use meaningful naming conventions.
- Apply least-privilege bucket policies.
- Enable access logging where appropriate.

---

# Key Takeaways

Buckets are much more than containers for objects. They define the security, configuration, governance, and operational boundaries of data stored in Amazon S3.

A well-designed bucket strategy simplifies security, compliance, monitoring, and long-term maintenance.

In the next chapter, we'll examine **Objects**, the fundamental unit of storage in Amazon S3.
