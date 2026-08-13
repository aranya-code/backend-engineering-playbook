# IAM

---

# Introduction

Identity and Access Management (IAM) is the first layer of security for every Amazon S3 request. Before Amazon S3 evaluates bucket policies, encryption settings, or object ownership, AWS must determine **who** is making the request and **what** they are allowed to do.

Every operation—uploading an object, downloading a file, deleting a bucket, or changing bucket settings—is authorized through IAM.

For production systems, a well-designed IAM strategy is the foundation of a secure Amazon S3 architecture.

---

# Learning Objectives

In this chapter you'll learn:

- What IAM is
- IAM Users, Groups, and Roles
- IAM Policies
- Principle of Least Privilege
- IAM Policy Evaluation
- Explicit Deny
- Production IAM Design
- Best Practices
- Common Mistakes

---

# What is IAM?

AWS Identity and Access Management (IAM) is the AWS service responsible for authentication and authorization.

It answers two questions:

1. **Who are you?** (Authentication)
2. **What are you allowed to do?** (Authorization)

For Amazon S3, IAM controls operations such as:

- List buckets
- Create buckets
- Upload objects
- Download objects
- Delete objects
- Configure bucket settings
- Manage encryption
- Read object versions

> 💡 **Engineering Insight**
>
> IAM is identity-based access control. It determines what an authenticated identity can do across AWS.

---

# IAM Components

## IAM Users

Represent individual people.

Use cases:

- Administrators
- Security engineers
- Developers (rare in production)

Avoid embedding long-lived access keys in applications.

---

## IAM Groups

Groups simplify permission management.

Example:

```text
S3-Admins
S3-Developers
S3-ReadOnly
```

Permissions are assigned once to the group instead of each user.

---

## IAM Roles

IAM Roles are the recommended authentication mechanism for workloads.

Common examples:

- Amazon EC2
- AWS Lambda
- Amazon ECS
- AWS Batch
- Step Functions

Roles provide temporary credentials through AWS STS.

> 🏗️ **Production Pattern**
>
> Modern AWS applications should almost always use IAM Roles instead of IAM Users with access keys.

---

# IAM Policies

IAM permissions are defined using JSON policy documents.

Every statement contains:

- Effect
- Action
- Resource
- Optional Condition

Example:

```json
{
  "Effect": "Allow",
  "Action": [
    "s3:GetObject",
    "s3:PutObject"
  ],
  "Resource": "arn:aws:s3:::company-documents/*"
}
```

Avoid granting:

```text
Action: s3:*
Resource: *
```

unless absolutely necessary.

---

# Principle of Least Privilege

Grant only the permissions required to perform a task.

Example:

A thumbnail generation service requires:

- s3:GetObject
- s3:PutObject

It does **not** require:

- DeleteBucket
- PutBucketPolicy
- DeleteObjectVersion
- PutBucketAcl

Smaller permission sets reduce the attack surface and accidental damage.

---

# How AWS Evaluates IAM Policies

Authorization follows three fundamental rules:

1. Default Deny
2. Explicit Allow
3. Explicit Deny overrides every Allow

Simplified evaluation:

```text
Request
   │
Authenticate
   │
IAM Policy
   │
Bucket Policy
   │
Explicit Deny?
   │
 ┌────┴────┐
 │         │
Yes       No
 │         │
 ▼         ▼
Denied  Allowed (if permitted)
```

---

# IAM vs Bucket Policies

IAM Policies answer:

> **What can this identity do?**

Bucket Policies answer:

> **Who can access this bucket?**

Production systems typically use both.

---

# Production Architecture

```text
Application
      │
 IAM Role
      │
Temporary Credentials
      │
      ▼
Amazon S3
      ▲
      │
Bucket Policy
```

Applications authenticate with IAM Roles while Bucket Policies enforce resource-level guardrails.

---

# Best Practices

- Prefer IAM Roles over IAM Users.
- Apply the Principle of Least Privilege.
- Scope permissions to specific buckets or prefixes.
- Use conditions where appropriate.
- Rotate or eliminate long-lived credentials.
- Review unused permissions regularly.
- Use IAM Access Analyzer to identify overly permissive policies.

---

# Common Mistakes

- Using `s3:*` for applications.
- Sharing one IAM role across unrelated services.
- Embedding AWS access keys in source code.
- Ignoring explicit deny statements.
- Granting permissions on every bucket using `"*"`.

> ⚠️ **Common Mistake**
>
> Most production "Access Denied" issues are caused by missing permissions, explicit denies, or resource policies—not by Amazon S3 itself.

---

# Interview Questions

**Q:** Why are IAM Roles preferred over IAM Users?

**A:** Roles provide temporary credentials, eliminate long-lived access keys, integrate with AWS services, and reduce credential management overhead.

**Q:** What is the Principle of Least Privilege?

**A:** Grant only the permissions required to perform a task and nothing more.

---

# Key Takeaways

IAM is the first security layer for Amazon S3. By combining IAM Roles, least-privilege policies, and proper policy evaluation, organizations can build secure, scalable, and maintainable storage architectures.

In the next chapter, we'll explore **Bucket Policies** and learn how resource-based policies secure buckets, enable cross-account access, and enforce organization-wide security controls.
