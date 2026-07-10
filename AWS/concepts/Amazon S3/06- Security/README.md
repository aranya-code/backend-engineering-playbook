# Amazon S3 Security

The **Security** module focuses on protecting Amazon S3 buckets and objects from unauthorized access while enabling secure collaboration across users, applications, AWS accounts, and Regions.

Amazon S3 provides multiple layers of security, ranging from **IAM Policies** and **Bucket Policies** to **Access Points**, **Object Lambda**, and **Multi-Region Access Points**. Understanding how these mechanisms work together is essential for designing secure, scalable, and maintainable cloud storage architectures.

This module explores the complete Amazon S3 security model, explains when each security mechanism should be used, and demonstrates production-ready security patterns followed by AWS and enterprise organizations.

---

## Module Information

| Property | Value |
|----------|-------|
| Module | 06 |
| Difficulty | 🟡 Intermediate |
| Estimated Reading Time | 90–120 minutes |
| Articles | 7 |
| Hands-on Labs | Covered later in Module 17 |
| Prerequisites | Modules 01–05 |

---

# 📚 Table of Contents

- Overview
- Learning Objectives
- Topics Covered
- File Navigation
- Learning Roadmap
- Amazon S3 Security Model
- Core Concepts
- Best Practices
- Common Mistakes
- Related Modules
- Navigation

---

# Overview

Security is one of the most critical aspects of Amazon S3.

By default, newly created buckets are private, but designing a secure storage architecture requires much more than keeping buckets private. Engineers must understand how identity-based permissions, resource-based permissions, ownership controls, and specialized access mechanisms interact to enforce least-privilege access.

This module covers:

- IAM
- Bucket Policies
- ACLs
- IAM Access Analyzer
- Access Points
- Object Lambda
- Multi-Region Access Points

These services work together to create a layered security model suitable for enterprise-scale cloud environments.

---

# Learning Objectives

After completing this module, you will be able to:

- Understand the Amazon S3 security model.
- Configure IAM policies using least privilege.
- Write secure Bucket Policies.
- Understand why ACLs are considered legacy.
- Use Access Analyzer to identify security risks.
- Configure Access Points for multi-team applications.
- Use Object Lambda to transform objects securely.
- Design globally accessible architectures using Multi-Region Access Points.

---

# Topics Covered

| # | Topic | Description |
|---|-------|-------------|
| 01 | [IAM](./01-%20IAM.md) | Secure Amazon S3 using IAM users, groups, roles, and policies. |
| 02 | [Bucket Policies](./02-%20Bucket%20Policies.md) | Configure resource-based permissions for buckets and objects. |
| 03 | [ACLs](./03-%20ACLs.md) | Understand legacy Access Control Lists and modern ownership controls. |
| 04 | [Access Analyzer](./04-%20Access%20Analyzer.md) | Detect unintended public and cross-account access. |
| 05 | [Access Points](./05-%20Access%20Points.md) | Simplify secure access for applications, teams, and VPCs. |
| 06 | [Object Lambda](./06-%20Object%20Lambda.md) | Modify objects dynamically before they reach clients. |
| 07 | [Multi-Region Access Points](./07-%20Multi-Region%20Access%20Points.md) | Build globally resilient storage access with intelligent routing. |

---

# File Navigation

```text
06- Security
│
├── 01- IAM.md
├── 02- Bucket Policies.md
├── 03- ACLs.md
├── 04- Access Analyzer.md
├── 05- Access Points.md
├── 06- Object Lambda.md
├── 07- Multi-Region Access Points.md
│
└── README.md
```

---

# Learning Roadmap

```text
IAM
 │
 ▼
Bucket Policies
 │
 ▼
ACLs
 │
 ▼
Access Analyzer
 │
 ▼
Access Points
 │
 ▼
Object Lambda
 │
 ▼
Multi-Region Access Points
```

---

# Amazon S3 Security Model

```text
                  User / Application
                          │
                          ▼
                    IAM Authentication
                          │
                          ▼
                   IAM Policy Evaluation
                          │
                          ▼
                   Bucket Policy Check
                          │
                          ▼
            Ownership Controls / ACL Check
                          │
                          ▼
          Access Point (Optional Layer)
                          │
                          ▼
      Object Lambda (Optional Processing)
                          │
                          ▼
                     Amazon S3 Object
```

Amazon S3 evaluates multiple authorization layers before allowing access to an object. Understanding this evaluation flow is essential when troubleshooting **Access Denied** errors.

---

# Core Concepts

| Concept | Description |
|----------|-------------|
| IAM | Identity-based access control for AWS users, roles, and services. |
| Bucket Policy | Resource-based policy controlling access to buckets and objects. |
| ACL | Legacy permission mechanism for buckets and objects. |
| Bucket Owner Enforced | Modern ownership model that disables ACLs. |
| IAM Access Analyzer | Detects unintended public or cross-account access. |
| Access Point | Dedicated endpoint with its own access policy for shared buckets. |
| VPC Access Point | Restricts bucket access to resources within a VPC. |
| Object Lambda | Transforms object data before it is returned to the client. |
| Multi-Region Access Point | Provides a single global endpoint for replicated buckets. |

---

# Best Practices

- Enable **Block Public Access** unless public access is intentionally required.
- Follow the **Principle of Least Privilege**.
- Prefer IAM Roles over IAM Users for applications.
- Use Bucket Policies instead of ACLs.
- Enable **Bucket Owner Enforced** to disable ACLs.
- Regularly review IAM Access Analyzer findings.
- Restrict administrative permissions.
- Use VPC Access Points for private workloads.
- Monitor access with AWS CloudTrail.

---

# Common Mistakes

- Granting wildcard (`*`) permissions unnecessarily.
- Using ACLs instead of Bucket Policies.
- Disabling Block Public Access without understanding the impact.
- Ignoring cross-account permissions.
- Using root credentials for application access.
- Forgetting to validate policy conditions.
- Assuming Access Points replace IAM policies.

---

# Related Modules

| Module | Purpose |
|----------|---------|
| [Versioning](../05-%20Versioning/README.md) | Protect stored data from accidental deletion. |
| [Encryption](../07-%20Encryption/README.md) | Secure data at rest using server-side and client-side encryption. |
| [Monitoring & Auditing](../12-%20Monitoring%20&%20Auditing/README.md) | Monitor access using CloudTrail, CloudWatch, and Storage Lens. |
| [Troubleshooting](../18-%20Troubleshooting/README.md) | Resolve common Access Denied and permission-related issues. |

---

# Navigation

| Previous | Current | Next |
|----------|---------|------|
| Versioning | Security | Encryption |

- ⬆️ **Previous Module:** [Versioning](../05-%20Versioning/README.md)
- 🏠 **Parent:** [Amazon S3](../README.md)
- ➡️ **Next Module:** [Encryption](../07-%20Encryption/README.md)

---
