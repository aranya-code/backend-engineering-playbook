# Amazon S3 Bucket Management

The **Bucket Management** module focuses on creating, configuring, and administering Amazon S3 buckets. While the Fundamentals module introduces what buckets are, this module explains **how to securely configure buckets for production workloads**.

You'll learn how bucket naming works, how ownership is managed, how Bucket Policies and Public Access Block protect your data, how CORS enables browser-based applications, and how to host static websites using Amazon S3.

Mastering bucket management is essential because every object stored in Amazon S3 resides inside a bucket, making bucket configuration one of the most important aspects of designing secure and scalable cloud storage solutions.

---

## Module Information

| Property | Value |
|----------|-------|
| Module | 02 |
| Difficulty | 🟢 Beginner → 🟡 Intermediate |
| Estimated Reading Time | 60–90 minutes |
| Articles | 7 |
| Hands-on Labs | Covered later in Module 17 |
| Prerequisites | Module 01 – Fundamentals |

---

# 📚 Table of Contents

- Overview
- Learning Objectives
- Topics Covered
- File Navigation
- Learning Roadmap
- Bucket Architecture
- Core Concepts
- Best Practices
- Common Mistakes
- Related Modules
- Navigation

---

# Overview

Every object stored in Amazon S3 belongs to a **Bucket**.

Although creating a bucket appears simple, production-ready bucket configuration involves much more than choosing a name.

This module covers:

- Bucket creation
- Bucket naming conventions
- Bucket Policies
- Public Access Block
- Ownership Controls
- Cross-Origin Resource Sharing (CORS)
- Static Website Hosting

Understanding these concepts ensures that your buckets remain secure, scalable, and aligned with AWS best practices.

---

# Learning Objectives

After completing this module, you will be able to:

- Create Amazon S3 buckets
- Understand global bucket naming
- Configure Bucket Policies
- Block unintended public access
- Configure Ownership Controls
- Enable CORS
- Host static websites
- Follow AWS production best practices

---

# Topics Covered

| # | Topic | Description |
|---|-------|-------------|
| 01 | [Creating Buckets](./01-%20Creating%20Buckets.md) | Creating buckets using the Console, CLI, SDKs, and Infrastructure as Code |
| 02 | [Bucket Naming](./02-%20Bucket%20Naming.md) | Global naming rules, DNS compatibility, and naming best practices |
| 03 | [Bucket Policies](./03-%20Bucket%20Policies.md) | Resource-based access control and policy management |
| 04 | [Public Access Block](./04-%20Public%20Access%20Block.md) | Preventing unintended public exposure |
| 05 | [Ownership Controls](./05-%20Ownership%20Controls.md) | Bucket Owner Enforced, object ownership, and ACL replacement |
| 06 | [CORS](./06-%20CORS.md) | Cross-Origin Resource Sharing for browser applications |
| 07 | [Static Website Hosting](./07-%20Static%20Website%20Hosting.md) | Hosting static websites directly from Amazon S3 |

---

# File Navigation

```text
02- Bucket Management
│
├── 01- Creating Buckets.md
├── 02- Bucket Naming.md
├── 03- Bucket Policies.md
├── 04- Public Access Block.md
├── 05- Ownership Controls.md
├── 06- CORS.md
├── 07- Static Website Hosting.md
│
└── README.md
```

---

# Learning Roadmap

```text
Creating Buckets
        │
        ▼
Bucket Naming
        │
        ▼
Bucket Policies
        │
        ▼
Public Access Block
        │
        ▼
Ownership Controls
        │
        ▼
CORS
        │
        ▼
Static Website Hosting
```

---

# Bucket Architecture

```text
                    Amazon S3

                        │
                        ▼
                 Amazon S3 Bucket
                        │
      ┌─────────────────┼─────────────────┐
      │                 │                 │
      ▼                 ▼                 ▼
 Bucket Policy     Ownership        Public Access
                   Controls             Block
      │                 │                 │
      └─────────────────┼─────────────────┘
                        │
                        ▼
                     Objects
```

Every bucket has its own:

- Globally unique name
- AWS Region
- Bucket Policy
- Ownership Controls
- Public Access configuration
- CORS configuration
- Lifecycle Rules (optional)
- Versioning configuration (optional)

---

# Core Concepts

| Concept | Description |
|----------|-------------|
| Bucket | Container used to store Amazon S3 objects |
| Bucket Policy | Resource-based access control policy |
| Public Access Block | AWS feature preventing accidental public exposure |
| Ownership Controls | Defines object ownership behavior |
| Bucket Owner Enforced | Disables ACLs and simplifies permissions |
| CORS | Allows browser applications to access bucket resources |
| Static Website Hosting | Serves static web content directly from Amazon S3 |

---

# Best Practices

- Use globally unique, descriptive bucket names.
- Keep buckets private by default.
- Enable **Block Public Access** unless public access is explicitly required.
- Prefer **Bucket Policies** over ACLs.
- Enable **Bucket Owner Enforced** for new buckets.
- Configure CORS only for trusted origins.
- Use CloudFront instead of exposing public website endpoints directly for production workloads.

---

# Common Mistakes

- Using generic bucket names that are already taken.
- Disabling Block Public Access without understanding the security implications.
- Relying on ACLs instead of Bucket Policies.
- Allowing unrestricted CORS (`*`) in production.
- Hosting sensitive data in buckets configured for static website hosting.
- Assuming bucket names can be changed after creation.

---

# Related Modules

| Module | Purpose |
|----------|---------|
| [Fundamentals](../01-%20Fundamentals/README.md) | Learn the core concepts of Amazon S3 |
| [Object Management](../03-%20Object%20Management/README.md) | Manage objects stored within buckets |
| [Security](../06-%20Security/README.md) | Implement advanced security controls |
| [Architecture Patterns](../14-%20Architecture%20Patterns/README.md) | Design secure production storage architectures |

---

# Navigation

| Previous | Current | Next |
|----------|---------|------|
| Fundamentals | Bucket Management | Object Management |

- ⬆️ **Previous Module:** [Fundamentals](../01-%20Fundamentals/README.md)
- 🏠 **Parent:** [Amazon S3](../README.md)
- ➡️ **Next Module:** [Object Management](../03-%20Object%20Management/README.md)

---
