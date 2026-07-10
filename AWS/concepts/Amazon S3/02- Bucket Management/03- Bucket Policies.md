# Bucket Policies

---

# Introduction

Bucket policies are JSON-based resource policies attached directly to an Amazon S3 bucket. They define **who** can access the bucket, **what** actions are permitted, and **under which conditions** those actions are allowed or denied.

Unlike IAM policies, which are attached to users, groups, or roles, bucket policies are attached to the bucket itself. This makes them one of the most important security controls in Amazon S3.

---

# Why Bucket Policies Matter

As applications grow, multiple users, AWS accounts, services, and applications may require access to the same bucket.

Bucket policies allow you to centrally control access without modifying every individual IAM identity.

Typical use cases include:

- Cross-account access
- Public website hosting
- Restricting uploads
- Enforcing encryption
- Restricting access to specific VPCs
- Granting AWS service access

> 💡 **Engineering Insight**
>
> Think of a bucket policy as the bucket's own firewall. Every request is evaluated against the policy before access is granted.

---

# How Bucket Policies Work

A bucket policy consists of one or more statements.

Each statement defines:

- Effect (Allow or Deny)
- Principal
- Action
- Resource
- Optional Conditions

```text
Request
   │
   ▼
Authentication
   │
   ▼
Bucket Policy Evaluation
   │
   ▼
IAM Evaluation
   │
   ▼
Access Granted / Denied
```

---

# Policy Structure

A simple policy contains:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::example-bucket/*"
    }
  ]
}
```

Every element has a specific purpose and should be reviewed carefully before deployment.

---

# Common Use Cases

Bucket policies are commonly used to:

- Allow CloudFront to read objects
- Allow AWS Lambda to access objects
- Allow another AWS account to upload files
- Restrict access to a corporate IP range
- Require HTTPS
- Enforce server-side encryption

---

# Explicit Deny

In AWS policy evaluation, an explicit **Deny** always overrides an **Allow**.

Example:

- IAM policy allows object deletion.
- Bucket policy explicitly denies object deletion.

Result:

```text
Access Denied
```

> ⚠️ **Common Mistake**
>
> Many engineers troubleshoot IAM permissions without checking for an explicit deny in the bucket policy.

---

# Best Practices

- Follow the principle of least privilege.
- Prefer IAM roles for application access.
- Use bucket policies for bucket-level controls.
- Require HTTPS using policy conditions.
- Enforce encryption where appropriate.
- Review policies regularly.

---

# Common Mistakes

- Using `"Principal": "*"` unnecessarily.
- Allowing broad permissions such as `s3:*`.
- Ignoring explicit deny statements.
- Forgetting to test policy changes.
- Mixing bucket policies and ACLs without understanding precedence.

---

# Key Takeaways

Bucket policies are a core security mechanism in Amazon S3. They provide centralized, resource-based access control and are commonly used to secure production workloads, enable cross-account access, and enforce organizational security requirements.

In the next chapter, we'll explore **Block Public Access** and understand why AWS recommends enabling it for nearly every production bucket.
