# Bucket Policies

---

# Introduction

Identity-based permissions alone are not enough to secure Amazon S3. While IAM determines what an authenticated identity can do, **Bucket Policies** allow the bucket owner to define who can access the bucket, what actions are allowed, and under which conditions.

Bucket Policies are **resource-based policies** attached directly to an S3 bucket. They are heavily used in production for cross-account access, AWS service integrations, enforcing HTTPS, restricting access to VPC endpoints, and implementing organization-wide security guardrails.

For backend engineers, Bucket Policies are one of the most important Amazon S3 security features because they allow security to be enforced independently of application code.

---

# Learning Objectives

In this chapter you'll learn:

- What Bucket Policies are
- Policy structure
- IAM Policies vs Bucket Policies
- Cross-account access
- Common policy conditions
- Production use cases
- Best practices
- Common mistakes

---

# What is a Bucket Policy?

A Bucket Policy is a JSON document attached to an Amazon S3 bucket.

Unlike IAM policies, which are attached to users or roles, Bucket Policies remain with the bucket regardless of who is making the request.

They answer the question:

> **Who can access this bucket and under what conditions?**

> 💡 **Engineering Insight**
>
> Think of IAM as controlling identities and Bucket Policies as protecting resources.

---

# Policy Structure

A Bucket Policy consists of one or more statements.

Each statement contains:

- Version
- Effect
- Principal
- Action
- Resource
- Optional Condition

Example:

```json
{
  "Version":"2012-10-17",
  "Statement":[
    {
      "Effect":"Allow",
      "Principal":{
        "AWS":"arn:aws:iam::111122223333:role/ImageService"
      },
      "Action":"s3:GetObject",
      "Resource":"arn:aws:s3:::company-images/*"
    }
  ]
}
```

---

# Understanding the Principal

The **Principal** identifies who receives the permission.

Common principals include:

- IAM Users
- IAM Roles
- Entire AWS Accounts
- AWS Services
- Federated identities

Examples:

```text
arn:aws:iam::123456789012:role/AppRole

cloudtrail.amazonaws.com

cloudfront.amazonaws.com
```

Avoid using:

```text
Principal: "*"
```

unless the bucket is intentionally public.

---

# IAM Policies vs Bucket Policies

| IAM Policy | Bucket Policy |
|------------|---------------|
| Identity-based | Resource-based |
| Attached to users or roles | Attached to buckets |
| Defines what an identity can do | Defines who can access a bucket |
| Best for application permissions | Best for bucket guardrails |

Production environments typically use both together.

---

# Common Conditions

Conditions allow Bucket Policies to enforce additional security requirements.

Examples:

### Require HTTPS

```text
aws:SecureTransport = true
```

### Restrict by Source IP

```text
aws:SourceIp
```

### Restrict to a VPC Endpoint

```text
aws:SourceVpce
```

### Require Encryption

```text
s3:x-amz-server-side-encryption
```

These controls help enforce organizational security standards without changing application code.

> 🏗️ **Production Pattern**
>
> A common enterprise policy denies all requests that are not made over HTTPS and requires server-side encryption for every uploaded object.

---

# Cross-Account Access

Bucket Policies are the preferred mechanism for granting controlled access to another AWS account.

Example workflow:

```text
Account A
   │
Bucket Policy
   │
Allow
   ▼
Account B IAM Role
```

This pattern is widely used for:

- Centralized logging
- Shared datasets
- CI/CD pipelines
- Backup repositories

---

# Authorization Flow

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
Denied  Allowed (if explicitly permitted)
```

An explicit deny in the Bucket Policy overrides an allow in an IAM policy.

---

# Best Practices

- Grant access to specific principals.
- Require HTTPS using `aws:SecureTransport`.
- Scope resources to specific prefixes where possible.
- Use Bucket Policies for cross-account access.
- Review policies regularly with IAM Access Analyzer.
- Keep buckets private by default.

---

# Common Mistakes

- Using `Principal: "*"` unintentionally.
- Granting access to every object when only one prefix is required.
- Duplicating IAM permissions unnecessarily.
- Forgetting that explicit deny overrides allow.
- Treating Bucket Policies as application authorization logic.

> ⚠️ **Common Mistake**
>
> Bucket Policies should enforce security boundaries—not implement business logic. Authorization decisions specific to your application should remain in your backend.

---

# Interview Questions

**Q:** When should you use a Bucket Policy instead of an IAM Policy?

**A:** Use Bucket Policies for resource-level controls, cross-account access, AWS service integrations, and bucket-wide guardrails. Use IAM Policies for identity permissions.

**Q:** Can a Bucket Policy deny access even if an IAM Policy allows it?

**A:** Yes. An explicit deny in any applicable policy always overrides an allow.

---

# Key Takeaways

Bucket Policies are resource-based policies that complement IAM by securing Amazon S3 buckets directly. They are essential for cross-account access, enforcing HTTPS, integrating AWS services, and applying organization-wide security controls while keeping buckets private by default.

In the next chapter, we'll explore **ACLs & Ownership Controls** and learn why modern Amazon S3 architectures disable ACLs in favor of policy-based access control.
