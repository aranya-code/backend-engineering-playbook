# Objects

---

# Introduction

Objects are the fundamental unit of storage in Amazon S3. Every file you upload to S3—whether it is an image, video, PDF, backup, or log file—is stored as an object.

Unlike traditional file systems that organize files into directories on disks, Amazon S3 stores self-contained objects inside buckets. Each object contains not only the data itself but also metadata and a unique identifier known as the object key.

Understanding objects is essential because every Amazon S3 feature—versioning, lifecycle management, replication, encryption, and event notifications—operates on objects.

---

# What Is an Object?

An S3 object consists of three primary components:

```text
S3 Object
│
├── Object Data
├── Metadata
└── Object Key
```

Together, these components uniquely identify and describe the stored content.

---

# Object Data

Object data is the actual content being stored.

Examples include:

- Images
- Videos
- Audio files
- PDF documents
- ZIP archives
- Log files
- JSON files
- CSV datasets
- Machine learning models

Amazon S3 treats every object as binary data. It does not interpret or modify the contents.

> 💡 **Engineering Insight**
>
> Amazon S3 is content-agnostic. Whether an object contains a photo, a database backup, or source code, S3 stores it in exactly the same way.

---

# Metadata

Metadata describes the object.

There are two categories of metadata:

## System Metadata

Managed by AWS.

Examples:

- Last Modified
- ETag
- Content-Length
- Storage Class
- Version ID
- Server-Side Encryption

## User Metadata

Defined by applications.

Examples:

```text
x-amz-meta-user-id: 1024
x-amz-meta-order-id: ORD-10025
x-amz-meta-source: mobile-app
```

Custom metadata enables applications to associate business information with stored objects.

---

# Object Keys

Every object is uniquely identified by its object key.

Example:

```text
users/1024/profile/avatar.jpg
```

Although this resembles a directory structure, the entire string is simply the object's unique identifier.

Different keys may represent similar data:

```text
users/1024/avatar.jpg
users/2048/avatar.jpg
archive/2026/avatar.jpg
```

Each represents a completely different object.

---

# Object Size

Amazon S3 supports objects ranging from a few bytes to **5 TB**.

Large objects should be uploaded using Multipart Upload for improved performance and reliability.

---

# Object Immutability

Objects are immutable.

Updating an object does not modify the existing object.

Instead, Amazon S3 stores a new object with the same key (and a new version if versioning is enabled).

This design simplifies durability and replication.

---

# Object Lifecycle

A typical object moves through several stages during its lifetime.

```text
Create
   │
Upload
   │
Store
   │
Access
   │
Transition
   │
Archive
   │
Delete
```

Lifecycle rules can automatically transition or expire objects based on business requirements.

---

# Production Example

An e-commerce application stores product images as objects.

```text
Bucket
└── products/

    ├── electronics/laptop-001.jpg
    ├── electronics/laptop-002.jpg
    ├── clothing/shirt-101.jpg
    └── furniture/chair-500.jpg
```

The database stores product information and references the corresponding object key.

This approach keeps databases lightweight while allowing Amazon S3 to manage binary content efficiently.

---

# Best Practices

- Use meaningful object keys.
- Store metadata whenever it adds business value.
- Enable versioning for important data.
- Use Multipart Upload for large files.
- Avoid repeatedly overwriting the same object.

---

# Common Mistakes

- Assuming folders physically exist.
- Storing business metadata only in filenames.
- Uploading very large files without Multipart Upload.
- Overwriting production objects accidentally.

---

# Key Takeaways

Objects are the core building blocks of Amazon S3. Every object combines data, metadata, and a unique key into a self-contained unit that can be securely stored, replicated, versioned, and managed at massive scale.

In the next chapter, we'll examine **Object Keys** and learn how naming strategies affect organization, scalability, and application design.
