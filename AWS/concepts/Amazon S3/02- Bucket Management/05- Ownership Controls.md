# Object Ownership

---

# Introduction

Object ownership determines **who owns an object after it is uploaded to an Amazon S3 bucket**. While this may sound straightforward, ownership becomes an important consideration when multiple AWS accounts, applications, or services upload objects into the same bucket.

Historically, Amazon S3 relied on **Access Control Lists (ACLs)** to manage object ownership. Modern AWS best practices, however, recommend disabling ACLs and using **Bucket Owner Enforced** ownership together with IAM and bucket policies.

---

# Why Object Ownership Matters

Consider a centralized logging bucket shared by multiple AWS accounts.

```text
AWS Account A
        │
        │ Upload Logs
        ▼
Shared S3 Bucket
        ▲
        │
AWS Account B
```

If uploaded objects are owned by different AWS accounts, the bucket owner may not automatically have permission to manage or delete those objects.

This creates unnecessary operational and security complexity.

> 💡 **Engineering Insight**
>
> Ownership affects administration. If you don't own an object, you may not be able to modify or delete it, even if you own the bucket.

---

# Ownership Models

Amazon S3 supports three ownership modes.

## Bucket Owner Enforced (Recommended)

- ACLs are disabled.
- Bucket owner automatically owns every uploaded object.
- Permissions are managed using IAM and bucket policies.

This is the recommended configuration for almost all new workloads.

---

## Bucket Owner Preferred

Objects can still use ACLs.

If upload requests include the appropriate ACL, ownership transfers to the bucket owner.

Used primarily for backward compatibility.

---

## Object Writer

The uploading AWS account owns the object.

This is the legacy behavior and can introduce cross-account management challenges.

---

# Why AWS Recommends Bucket Owner Enforced

Using Bucket Owner Enforced simplifies administration by:

- Disabling ACLs
- Eliminating ownership conflicts
- Centralizing permission management
- Reducing security risks
- Simplifying cross-account collaboration

Instead of combining IAM, bucket policies, and ACLs, engineers only manage IAM policies and bucket policies.

> 🏗️ **Production Pattern**
>
> Modern production environments should disable ACLs unless there is a specific legacy requirement that cannot be migrated.

---

# ACLs vs Bucket Owner Enforced

| Feature | ACLs Enabled | Bucket Owner Enforced |
|---------|--------------|-----------------------|
| Uses ACLs | Yes | No |
| Object ownership varies | Yes | No |
| Permission model | IAM + Bucket Policy + ACL | IAM + Bucket Policy |
| Complexity | Higher | Lower |
| Recommended | Legacy only | Yes |

---

# Best Practices

- Use **Bucket Owner Enforced** for all new buckets.
- Disable ACLs whenever possible.
- Manage permissions through IAM and bucket policies.
- Avoid legacy ownership models unless required by existing applications.

---

# Common Mistakes

- Using ACLs for new applications.
- Mixing ACLs with bucket policies unnecessarily.
- Assuming bucket ownership automatically grants ownership of uploaded objects.
- Ignoring cross-account upload scenarios.

> ⚠️ **Common Mistake**
>
> Many access issues are caused by legacy ACLs rather than IAM policies. Before troubleshooting permissions, verify whether ACLs are enabled.

---

# Key Takeaways

Object ownership determines who controls uploaded objects within a bucket. Modern Amazon S3 deployments should use **Bucket Owner Enforced**, which disables ACLs and simplifies permission management by relying solely on IAM and bucket policies.

In the next chapter, we'll explore **Cross-Origin Resource Sharing (CORS)** and understand how browsers securely access objects stored in Amazon S3.


## Current platform note

For new general-purpose buckets, Bucket owner enforced is the default Object Ownership setting. It disables ACLs and makes the bucket owner own all objects. Keep this default for modern systems and migrate legacy ACL dependencies deliberately.
