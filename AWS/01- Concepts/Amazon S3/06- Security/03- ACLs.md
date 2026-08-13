# ACLs & Ownership Controls

---

# Introduction

Before Amazon S3 introduced Bucket Policies and IAM-based authorization, **Access Control Lists (ACLs)** were the primary mechanism for controlling access to buckets and objects. While ACLs still exist for backward compatibility, AWS now recommends using **IAM Policies**, **Bucket Policies**, and **Bucket Owner Enforced Object Ownership** instead.

Modern Amazon S3 architectures rarely rely on ACLs because they are harder to manage, less expressive, and often lead to ownership and permission issues in multi-account environments.

This chapter explains how ACLs work, why Object Ownership was introduced, and why most production systems disable ACLs completely.

---

# Learning Objectives

In this chapter you'll learn:

- What ACLs are
- Bucket ACL vs Object ACL
- Object Ownership
- Bucket Owner Enforced
- ACLs vs Bucket Policies
- When ACLs are still needed
- Best practices
- Common mistakes

---

# What Are ACLs?

An **Access Control List (ACL)** is a legacy authorization mechanism attached directly to a bucket or an object.

Unlike IAM or Bucket Policies, ACLs grant a limited set of permissions to predefined principals.

Supported permissions include:

- READ
- WRITE
- READ_ACP
- WRITE_ACP
- FULL_CONTROL

> 💡 **Engineering Insight**
>
> ACLs are simple permission lists. They cannot express conditions such as IP restrictions, HTTPS requirements, or encryption enforcement.

---

# Bucket ACL vs Object ACL

## Bucket ACL

Controls access to bucket-level operations.

Examples:

- List bucket
- Read bucket ACL
- Write bucket ACL

---

## Object ACL

Controls access to individual objects.

Examples:

- Read object
- Write object ACL
- Full control

Historically, Object ACLs were widely used for cross-account uploads.

---

# The Ownership Problem

Consider two AWS accounts.

```text
Account A
     │
Uploads Object
     ▼
Bucket Owned by Account B
```

Without ownership controls:

- Account A owns the uploaded object.
- Account B owns the bucket.
- Bucket administrators may be unable to manage the object.

This often resulted in confusing "Access Denied" errors.

---

# Object Ownership

AWS introduced **Object Ownership** to eliminate these issues.

Available modes are:

## Bucket Owner Enforced (Recommended)

- ACLs are disabled.
- Bucket owner owns every uploaded object.
- Authorization relies entirely on IAM and Bucket Policies.

This is the default recommendation for all new production buckets.

---

## Bucket Owner Preferred

The bucket owner becomes the object owner when uploads include the appropriate ACL.

ACLs remain enabled.

---

## Object Writer

The uploading account owns the object.

Primarily maintained for legacy compatibility.

> 🏗️ **Production Pattern**
>
> Enable **Bucket Owner Enforced** unless a legacy integration explicitly requires ACLs.

---

# ACLs vs Bucket Policies

| ACLs | Bucket Policies |
|------|-----------------|
| Legacy feature | Modern approach |
| Limited permissions | Fine-grained permissions |
| No conditions | Supports conditions |
| No IP restrictions | IP, VPC, HTTPS, encryption conditions |
| Harder to manage | Centralized management |
| AWS discourages new usage | AWS recommended |

---

# When Are ACLs Still Used?

ACLs are still encountered in:

- Legacy applications
- Older third-party integrations
- Historical cross-account upload workflows

For new applications, AWS recommends disabling ACLs and using policy-based authorization instead.

---

# Migration Strategy

For existing environments:

1. Review bucket and object ACLs.
2. Replace ACL permissions with IAM or Bucket Policies.
3. Enable **Bucket Owner Enforced**.
4. Test application access.
5. Remove unnecessary ACL dependencies.

---

# Best Practices

- Use **Bucket Owner Enforced** for new buckets.
- Prefer IAM and Bucket Policies over ACLs.
- Keep buckets private by default.
- Audit legacy buckets for ACL usage.
- Test cross-account uploads before disabling ACLs.

---

# Common Mistakes

- Mixing ACLs with Bucket Policies unnecessarily.
- Assuming the bucket owner always owns uploaded objects.
- Leaving public READ ACLs on legacy buckets.
- Using ACLs for new application development.

> ⚠️ **Common Mistake**
>
> Many authorization issues in older S3 deployments are caused by object ownership conflicts. Enabling **Bucket Owner Enforced** removes this entire class of problems.

---

# Interview Questions

**Q:** Why does AWS recommend disabling ACLs?

**A:** Because IAM Policies and Bucket Policies provide more expressive, centralized, and secure access control. Disabling ACLs also eliminates ownership conflicts.

**Q:** What does Bucket Owner Enforced do?

**A:** It disables ACLs and ensures that the bucket owner automatically owns every object uploaded to the bucket.

---

# Key Takeaways

ACLs are a legacy access-control mechanism that has largely been replaced by IAM Policies and Bucket Policies. Modern Amazon S3 architectures should enable **Bucket Owner Enforced** Object Ownership, disable ACLs whenever possible, and manage authorization through policy-based access control for simpler, more secure, and more maintainable systems.

In the next chapter, we'll explore **IAM Access Analyzer** and learn how AWS identifies unintended public or cross-account access before it becomes a security incident.


## Current platform note

ACLs are disabled by default for new general-purpose buckets through Bucket owner enforced Object Ownership. Prefer IAM, bucket policies, and access-point policies. If a legacy integration requires ACLs, document the exception and test both writer and owner paths.
